#! /usr/bin/python3
# -*- coding: utf-8 -*-

#  This file is part of CANalyzat0r.
#
#  CANalyzat0r is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  CANalyzat0r is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with CANalyzat0r.  If not, see <http://www.gnu.org/licenses/>.
"""
Created on February 13, 2020

@author: pschmied
"""

from multiprocessing import Pipe
import Globals
import Strings
import re
from PySide import QtGui
from PySide import QtCore

from AbstractTab import AbstractTab
import Toolbox
import MainTab
from CANData import CANData
import SenderThread
from ItemAdderThread import ItemAdderThread


class UDSTab(AbstractTab):
    """
    This class handles the logic of the UDS tab
    """

    def __init__(self, tabWidget):
        AbstractTab.__init__(
            self,
            tabWidget,
            Strings.UDSTabLoggerName, [2, 3, 4],
            Strings.UDSTabPacketViewName,
            Strings.UDSTabLabelInterfaceValueName,
            allowTablePaste=False)

        self.active = False

        #: Sending takes place in a loop in a separate thread
        self.UDSSenderThread = None
        #: Adding items also takes place in a separate thread to avoid blocking the GUI thread
        self.itemAdderThread = None

        #: These values will be available in the fuzzing mode ComboBox
        self.UDSModeComboBoxValuePairs = [("Read Data By ID", 0),
                                          ("Routine Control", 1)]

        # Get all GUI elements
        self.comboBoxUDSMode = self.tabWidget.findChild(
            QtGui.QComboBox, "comboBoxUDSMode")
        self.lineEditUDSTabUDSID = self.tabWidget.findChild(
            QtGui.QLineEdit, "lineEditUDSTabUDSID")
        self.doubleSpinBoxUDSPacketGap = self.tabWidget.findChild(
            QtGui.QDoubleSpinBox, "doubleSpinBoxUDSPacketGap")
        self.buttonUDSInterfaceSettings = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonUDSInterfaceSettings")
        self.buttonUDSTabToggleFuzzing = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonUDSTabToggleFuzzing")
        self.buttonUDSClear = self.tabWidget.findChild(QtGui.QPushButton,
                                                       "buttonUDSClear")
        self.labelUDSCountValue = self.tabWidget.findChild(
            QtGui.QLabel, "labelUDSCountValue")

        assert all(GUIElem is not None for GUIElem in [
            self.comboBoxUDSMode, self.doubleSpinBoxUDSPacketGap, self.
            buttonUDSInterfaceSettings, self.buttonUDSTabToggleFuzzing, self.
            buttonUDSClear, self.labelUDSCountValue
        ]), "GUI Elements not found"

        self.buttonUDSInterfaceSettings.clicked.connect(
            self.handleInterfaceSettingsDialog)
        self.buttonUDSClear.clicked.connect(self.clear)
        self.comboBoxUDSMode.currentIndexChanged.connect(self.UDSModeChanged)
        self.buttonUDSTabToggleFuzzing.clicked.connect(self.toggleUDSFuzzing)

        self.prepareUI()

    def UDSModeChanged(self):
        pass

    def generateNextUDSPacket(self, packet):

        """
        Generates a UDS packet from a given template.

        :param packet: The previous `can.Message` object that was sent using the UDS fuzzer. It's being used to
                       determine the next packet that's about to be generated. This can be None - in this case
                       this method will use "00" for the initial values.
        """

        done = False
        # where to replace stuff in the template
        idxX = -1
        idxY = -1

        # read data by id / identification string
        if self.selectedMode == 0:
            template = ["03", "22", "XX", "YY", "CC", "CC", "CC", "CC"]

        # Routine Control
        elif self.selectedMode == 1:
            template = ["04", "31", "01", "XX", "YY", "CC", "CC", "CC"]

        idxX = template.index("XX")
        idxY = template.index("YY")

        assert idxX >= 0
        assert idxY >= 0

        if packet is None:
            # first round
            template[idxX] = "00"
            template[idxY] = "00"
        else:
            data = list(packet.data)
            # increment
            template[idxY] = format(data[idxY] + 1, "x").zfill(2).upper()
            # get old value
            template[idxX] = format(data[idxX], "x").zfill(2).upper()

            if template[idxX] == "FF" and template[idxY] == "FF":
                done = True

            elif template[idxY] == "FF":
                template[idxX] = format(data[idxX] + 1, "x").zfill(2).upper()
                template[idxY] = "00"

        try:
            packet = self.CANData.tryBuildPacket(self.UDSID,
                                                 "".join(template))
        except Exception as e:
            packet = None
            self.logger.error(Strings.fuzzerTabBuildPacketValueError)
        return done, packet

    def toggleUDSFuzzing(self):
        """
        This starts and stops UDS fuzzing.
         - Starting:
           - Input values are read and validated
           - ItemAdderThread and FuzzSenderThread (see :class:`~src.SenderThread.FuzzSenderThread`) are started
           - Some GUI elements will be disabled

         - Stopping:
           - The threads will be disabled
           - Disabled GUI elements will be enabled again
        """

        # Start fuzzing
        if not self.active:

            if not self.CANData:
                return

            self.selectedMode = self.comboBoxUDSMode.itemData(
                self.comboBoxUDSMode.currentIndex())

            # Filter invalid lengths and chars
            self.UDSID = self.lineEditUDSTabUDSID.text()
            self.UDSID = re.sub("[^A-Fa-f0-9]+", "", str(self.UDSID)).upper()
            if len(self.UDSID) > 8:
                self.UDSID = self.UDSID[:8]
            if len(self.UDSID) == 0:
                self.UDSID = "000"
            self.lineEditUDSTabUDSID.setText(self.UDSID)

            # in ms
            sleepTime = self.doubleSpinBoxUDSPacketGap.value() / 1000

            UDSReceivePipe, UDSSendPipe = Pipe()

            # Start the Threads
            # First start the ItemAdderThread...
            self.itemAdderThread = ItemAdderThread(
                UDSReceivePipe, self.packetTableModel, self.rawData)

            self.itemAdderThread.appendRow.connect(self.addPacket)
            self.itemAdderThread.start()

            # ... then start the fuzzing thread
            self.UDSSenderThread = SenderThread.UDSSenderThread(
                self, sleepTime, UDSSendPipe, self.CANData, self.loggerName)
            self.UDSSenderThread.start()
            self.logger.info(Strings.UDSTabUDSThreadStarted)

            self.active = True
            self.CANData.active = True
            self.buttonUDSInterfaceSettings.setEnabled(False)
            self.doubleSpinBoxUDSPacketGap.setEnabled(False)
            self.buttonUDSClear.setEnabled(False)

            # Refresh UI
            self.buttonUDSTabToggleFuzzing.setText(
                Strings.UDSTabUDSButtonEnabled)
            self.toggleLoopActive()
            MainTab.MainTab.addApplicationStatus(Strings.statusBarUDSFuzzing)

        # Stop fuzzing
        else:
            # Stop the fuzzer
            if self.UDSSenderThread is not None:
                self.UDSSenderThread.disable()
                self.UDSSenderThread.quit()

            # Stop the ItemAdder
            self.itemAdderThread.disable()
            self.itemAdderThread.wait()
            self.itemAdderThread.quit()
            self.logger.debug(Strings.itemAdderThreadTerminated)

            self.active = False
            self.CANData.active = False
            self.buttonUDSInterfaceSettings.setEnabled(True)
            self.doubleSpinBoxUDSPacketGap.setEnabled(True)
            self.buttonUDSClear.setEnabled(True)

            # Refresh UI
            self.buttonUDSTabToggleFuzzing.setText(
                Strings.UDSTabUDSButtonDisabled)
            self.toggleLoopActive()
            self.logger.info(Strings.UDSTabUDSThreadStopped)
            MainTab.MainTab.removeApplicationStatus(Strings.statusBarFuzzing)

    def prepareUI(self):
        AbstractTab.prepareUI(self)

        # Prepare the combobox
        self.comboBoxUDSMode.clear()
        for i in range(len(self.UDSModeComboBoxValuePairs)):
            valuePair = self.UDSModeComboBoxValuePairs[i]
            self.comboBoxUDSMode.addItem(valuePair[0])
            self.comboBoxUDSMode.setItemData(i, valuePair[1])

    def addPacket(self,
                  valueList,
                  addAtFront=True,
                  append=True,
                  emit=True,
                  addToRawDataOnly=False):
        """
        Override the parents class method to add packets at front and to update the counter label
        """

        AbstractTab.addPacket(
            self,
            valueList=valueList,
            addAtFront=addAtFront,
            append=append,
            emit=emit,
            addToRawDataOnly=addToRawDataOnly)
        # Also update the label
        self.labelUDSCountValue.setText(str(len(self.rawData)))

    def clear(self, returnOldPackets=False):
        """
        Clear the currently displayed data on the GUI and in the rawData list

        :param returnOldPackets: If this is true, then the previously displayed packets will
               be returned as raw data list
        :return: Previously displayed packets as raw data list (if returnOldPackets is True), else an empty list
        """

        savedPackets = AbstractTab.clear(
            self, returnOldPackets=returnOldPackets)

        # Reset the label too
        self.labelUDSCountValue.setText("0")

        return savedPackets

    def toggleLoopActive(self):
        """
        If there is a UDSThread sending then the tab title will be red.
        """

        #
        if self.active:
            Globals.ui.tabWidgetMain.tabBar().setTabTextColor(
                Globals.ui.tabWidgetMain.currentIndex(), QtCore.Qt.red)
        else:
            Globals.ui.tabWidgetMain.tabBar().setTabTextColor(
                Globals.ui.tabWidgetMain.currentIndex(), QtCore.Qt.black)

    def fuzzingModeChanged(self):
        """
        This gets called if the ComboBox gets changed to update the active UDS fuzzing mode.
        The other GUI elements will be set and enabled depending on the selected mode.
        """

        selectedData = self.comboBoxUDSMode.itemData(
            self.comboBoxUDSMode.currentIndex())

        QtCore.QCoreApplication.processEvents()

    def toggleGUIElements(self, state):
        """
        {En, Dis}able all GUI elements that are used to change fuzzer settings

        :param state: Boolean value to indicate whether to enable or disable elements
        """

        for GUIElement in [
                self.buttonUDSInterfaceSettings,
                self.buttonUDSTabToggleFuzzing, self.comboBoxUDSMode,
                self.doubleSpinBoxUDSPacketGap, self.buttonUDSClear,
                self.packetTableView
        ]:
            GUIElement.setEnabled(state)
