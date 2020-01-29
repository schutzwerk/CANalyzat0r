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
Created on May 31, 2017

@author: pschmied
"""

import random
from multiprocessing import Pipe

import Globals
import Strings
from PySide import QtGui
from PySide import QtCore

from AbstractTab import AbstractTab
import Toolbox
import MainTab
from CANData import CANData
import SenderThread
from ItemAdderThread import ItemAdderThread


class FuzzerTab(AbstractTab):
    """
    This class handles the logic of the fuzzer tab
    """

    def __init__(self, tabWidget):
        AbstractTab.__init__(
            self,
            tabWidget,
            Strings.fuzzerTabLoggerName, [2, 3, 4],
            Strings.fuzzerTabPacketTableViewName,
            Strings.fuzzerTabLabelInterfaceValueName,
            allowTablePaste=False)

        #: The ID is 8 chars max. - initialize it with only X chars
        self.IDMask = "X" * 8
        #: Default: allow the max value of extended frames
        self.IDMaxValue = 0x1FFFFFFF

        #: The data is 16 chars max.
        self.dataMask = "X" * 16
        self.dataMinLength = 0
        #: This length corresponds the length when interpreted as bytes
        self.dataMaxLength = 8

        #: Sending takes place in a loop in a separate thread
        self.fuzzSenderThread = None
        #: Adding items also takes place in a separate thread to avoid blocking the GUI thread
        self.itemAdderThread = None

        #: These values will be available in the fuzzing mode ComboBox
        self.fuzzingModeComboBoxValuePairs = [("User specified values", 0),
                                              ("11 bit IDs", 1),
                                              ("29 bit IDs", 2)]

        #: Used to avoid spamming the log box when the user specified wrong parameters while sending
        self.packetBuildErrorCount = 0

        # Get all GUI elements
        self.comboBoxFuzzingMode = self.tabWidget.findChild(
            QtGui.QComboBox, "comboBoxFuzzingMode")
        self.lineEditFuzzerTabIDMask = self.tabWidget.findChild(
            QtGui.QLineEdit, "lineEditFuzzerTabIDMask")
        self.lineEditFuzzerTabDataMask = self.tabWidget.findChild(
            QtGui.QLineEdit, "lineEditFuzzerTabDataMask")
        self.horizontalSliderFuzzerMinLength = self.tabWidget.findChild(
            QtGui.QSlider, "horizontalSliderFuzzerMinLength")
        self.horizontalSliderFuzzerMaxLength = self.tabWidget.findChild(
            QtGui.QSlider, "horizontalSliderFuzzerMaxLength")
        self.doubleSpinBoxFuzzerPacketGap = self.tabWidget.findChild(
            QtGui.QDoubleSpinBox, "doubleSpinBoxFuzzerPacketGap")
        self.buttonFuzzerInterfaceSettings = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonFuzzerInterfaceSettings")
        self.buttonFuzzerTabToggleFuzzing = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonFuzzerTabToggleFuzzing")
        self.buttonFuzzerClear = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonFuzzerClear")
        self.labelFuzzerMinLengthValue = self.tabWidget.findChild(
            QtGui.QLabel, "labelFuzzerMinLengthValue")
        self.labelFuzzerMaxLengthValue = self.tabWidget.findChild(
            QtGui.QLabel, "labelFuzzerMaxLengthValue")
        self.labelFuzzerCountValue = self.tabWidget.findChild(
            QtGui.QLabel, "labelFuzzerCountValue")

        assert all(GUIElem is not None for GUIElem in [
            self.comboBoxFuzzingMode, self.lineEditFuzzerTabIDMask, self.
            lineEditFuzzerTabDataMask, self.horizontalSliderFuzzerMinLength,
            self.horizontalSliderFuzzerMaxLength, self.
            doubleSpinBoxFuzzerPacketGap, self.buttonFuzzerInterfaceSettings,
            self.buttonFuzzerTabToggleFuzzing, self.buttonFuzzerClear, self.
            labelFuzzerMinLengthValue, self.labelFuzzerMaxLengthValue, self.
            labelFuzzerCountValue
        ]), "GUI Elements not found"

        self.buttonFuzzerInterfaceSettings.clicked.connect(
            self.handleInterfaceSettingsDialog)
        self.buttonFuzzerClear.clicked.connect(self.clear)
        self.horizontalSliderFuzzerMinLength.valueChanged.connect(
            self.sliderChanged)
        self.horizontalSliderFuzzerMaxLength.valueChanged.connect(
            self.sliderChanged)
        self.lineEditFuzzerTabIDMask.textChanged.connect(self.IDMaskChanged)
        self.lineEditFuzzerTabDataMask.textChanged.connect(
            self.dataMaskChanged)
        self.comboBoxFuzzingMode.currentIndexChanged.connect(
            self.fuzzingModeChanged)
        self.buttonFuzzerTabToggleFuzzing.clicked.connect(self.toggleFuzzing)

        self.prepareUI()

    def toggleFuzzing(self):
        """
        This starts and stops fuzzing.
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

            validatedIDMask = self.validateIDMaskInput()
            if validatedIDMask is None:
                return
            self.IDMask = validatedIDMask

            validatedDataMask = self.validateDataMaskInput()
            if validatedDataMask is None:
                return
            self.dataMask = validatedDataMask

            # in ms
            sleepTime = self.doubleSpinBoxFuzzerPacketGap.value() / 1000

            fuzzerReceivePipe, fuzzerSendPipe = Pipe()

            # Start the Threads
            # First start the ItemAdderThread...
            self.itemAdderThread = ItemAdderThread(
                fuzzerReceivePipe, self.packetTableModel, self.rawData)

            self.itemAdderThread.appendRow.connect(self.addPacket)
            self.itemAdderThread.start()

            # ... then start the fuzzing thread
            self.fuzzSenderThread = SenderThread.FuzzSenderThread(
                sleepTime, fuzzerSendPipe, self.CANData, self.loggerName)
            self.fuzzSenderThread.start()
            self.logger.info(Strings.fuzzerTabFuzzerThreadStarted)

            self.active = True
            self.CANData.active = True
            self.buttonFuzzerInterfaceSettings.setEnabled(False)
            self.doubleSpinBoxFuzzerPacketGap.setEnabled(False)
            self.buttonFuzzerClear.setEnabled(False)

            # Refresh UI
            self.buttonFuzzerTabToggleFuzzing.setText(
                Strings.fuzzerTabFuzzerButtonEnabled)
            self.toggleLoopActive()
            MainTab.MainTab.addApplicationStatus(Strings.statusBarFuzzing)

        # Stop fuzzing
        else:
            # Stop the fuzzer
            if self.fuzzSenderThread is not None:
                self.fuzzSenderThread.disable()
                self.fuzzSenderThread.quit()

            # Stop the ItemAdder
            self.itemAdderThread.disable()
            self.itemAdderThread.wait()
            self.itemAdderThread.quit()
            self.logger.debug(Strings.itemAdderThreadTerminated)

            self.active = False
            self.CANData.active = False
            self.buttonFuzzerInterfaceSettings.setEnabled(True)
            self.doubleSpinBoxFuzzerPacketGap.setEnabled(True)
            self.buttonFuzzerClear.setEnabled(True)

            # Refresh UI
            self.buttonFuzzerTabToggleFuzzing.setText(
                Strings.fuzzerTabFuzzerButtonDisabled)
            self.toggleLoopActive()
            self.logger.info(Strings.fuzzerTabFuzzerThreadStopped)
            MainTab.MainTab.removeApplicationStatus(Strings.statusBarFuzzing)

    def generateRandomPacket(self):
        """
        This generates a random can.Message object using :func:`~src.CANData.tryBuildPacket`

        :return: can.Message object with random data (random ID, data length and data)
        """

        # Has a length of 3 or 8
        randomCANID = ""

        randomData = ""

        # Genrate random CANID
        while randomCANID == "" or int(randomCANID, 16) > self.IDMaxValue:
            randomCANID = ""
            for hexCharIndex in range(len(self.IDMask)):
                if self.IDMask[hexCharIndex].upper() == "X":
                    # Generate 1 random hex char
                    randomCANID += '%01x' % random.randrange(16)
                else:
                    randomCANID += self.IDMask[hexCharIndex]

        # Generate random data
        randomLength = -1
        while randomLength < 0 or randomLength % 2 == 1:
            # *2 --> 1 byte = 2 chars
            randomLength = random.randint(self.dataMinLength * 2,
                                          self.dataMaxLength * 2)

        for hexCharIndex in range(randomLength):
            if self.dataMask[hexCharIndex] == "X":
                # Generate 1 random hex char
                randomData += '%01x' % random.randrange(16)
            else:
                randomData += self.dataMask[hexCharIndex]

        # Try to build the packet but don't spam the output <:
        try:
            packet = CANData.tryBuildPacket(randomCANID, randomData)
            self.packetBuildErrorCount = 0
            return packet

        except ValueError:
            # Don't spam the log box
            if self.packetBuildErrorCount % 1000000 == 0:
                self.logger.warn(Strings.fuzzerTabBuildPacketValueError)
            self.packetBuildErrorCount += 1
            return None

    def prepareUI(self):
        AbstractTab.prepareUI(self)
        self.lineEditFuzzerTabIDMask.setPlaceholderText("X" * 8)
        self.lineEditFuzzerTabDataMask.setPlaceholderText("X" * 16)

        # Prepare the combobox
        self.comboBoxFuzzingMode.clear()
        for i in range(len(self.fuzzingModeComboBoxValuePairs)):
            valuePair = self.fuzzingModeComboBoxValuePairs[i]
            self.comboBoxFuzzingMode.addItem(valuePair[0])
            self.comboBoxFuzzingMode.setItemData(i, valuePair[1])

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
        self.labelFuzzerCountValue.setText(str(len(self.rawData)))

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
        self.labelFuzzerCountValue.setText("0")

        return savedPackets

    def validateIDMaskInput(self):
        """
        Validates the user specified ID mask:
         - The length must be either 3 or 8
         - It must be a valid hex string
         - Has to be < 0x1FFFFFFF which is the max. value for extended frames

        :return: A validated ID mask or None if it's not possible to validate the input
        """

        IDMaskInput = self.lineEditFuzzerTabIDMask.text()

        if len(IDMaskInput) != 3 and \
                len(IDMaskInput) != 8 or \
                not Toolbox.Toolbox.isHexString(IDMaskInput.replace("X", "")):
            self.logger.error(Strings.fuzzerTabInvalidIDMaskLength)
            return None

        # If the value is a fixed extended value
        if len(IDMaskInput) == 8:
            if "X" not in IDMaskInput:
                # Check the max value
                if int(IDMaskInput, 16) > 0x1FFFFFFF:
                    self.logger.error(
                        Strings.fuzzerTabInvalidExtendedIDMaskValue)
                    return None

        return IDMaskInput

    def validateDataMaskInput(self):
        """
        Validates the user specified data mask:
         - The length must be <= 16
         - It must be a valid hex string
         - Value will be padded to 16 chars (8 bytes)

        :return: A validated data mask or None if it's not possible to validate the input
        """

        extended = False
        dataMaskInput = self.lineEditFuzzerTabDataMask.text()
        if len(dataMaskInput) > 16 or \
                not Toolbox.Toolbox.isHexString(dataMaskInput.replace("X", "")):
            self.logger.error(Strings.fuzzerTabInvalidDataMaskLength)
            return None

        # Force 8 bytes (16 chars) --> Padding
        else:
            while len(dataMaskInput) < 16:
                dataMaskInput += "X"
                extended = True

        if extended:
            self.logger.info(Strings.fuzzerTabExtendedDataMask + dataMaskInput)

        return dataMaskInput

    def toggleLoopActive(self):
        """
        If there is a FuzzerThread sending then the tab title will be red.
        """

        #
        if self.active:
            Globals.ui.tabWidgetMain.tabBar().setTabTextColor(
                Globals.ui.tabWidgetMain.currentIndex(), QtCore.Qt.red)
        else:
            Globals.ui.tabWidgetMain.tabBar().setTabTextColor(
                Globals.ui.tabWidgetMain.currentIndex(), QtCore.Qt.black)

    def sliderChanged(self):
        """
        This method gets called if one of the two length sliders (min. and max. value) are changed.
        ``dataMinLength`` and ``dataMaxLength`` will be directly updated and available
        to a running FuzzerThread.
        """

        self.horizontalSliderFuzzerMinLength.setMaximum(
            self.horizontalSliderFuzzerMaxLength.value())

        newMinLength = self.horizontalSliderFuzzerMinLength.value()
        newMaxLength = self.horizontalSliderFuzzerMaxLength.value()

        self.labelFuzzerMinLengthValue.setText(str(newMinLength))
        self.labelFuzzerMaxLengthValue.setText(str(newMaxLength))

        self.dataMinLength = newMinLength
        self.dataMaxLength = newMaxLength

    def IDMaskChanged(self):
        """
        This allows changing the ID mask values on the fly because a new value
        will only be set if the new value is valid.
        """

        if self.active:
            newIDMask = self.validateIDMaskInput()
            if newIDMask is not None:
                self.IDMask = newIDMask

    def dataMaskChanged(self):
        """
        This allows changing the data mask values on the fly because a new value
        will only be set if the new value is valid.
        """

        if self.active:
            newDataMask = self.validateDataMaskInput()
            if newDataMask is not None:
                self.dataMask = newDataMask

    def fuzzingModeChanged(self):
        """
        This gets called if the ComboBox gets changed to update the active fuzzing mode.
        The other GUI elements will be set and enabled depending on the selected mode.
        """

        selectedData = self.comboBoxFuzzingMode.itemData(
            self.comboBoxFuzzingMode.currentIndex())

        # 11 bit IDs
        if selectedData == 1:
            self.IDMaxValue = 0x7FF
            self.lineEditFuzzerTabIDMask.setEnabled(False)
            self.lineEditFuzzerTabIDMask.setText("X" * 3)
            self.IDMask = ("X" * 3)

        # 29 bit IDs
        elif selectedData == 2:
            self.IDMaxValue = 0x1FFFFFFF
            self.lineEditFuzzerTabIDMask.setEnabled(False)
            self.lineEditFuzzerTabIDMask.setText("X" * 8)
            self.IDMask = ("X" * 8)

        # Fallback: user specified
        else:
            self.IDMaxValue = 0x1FFFFFFF
            self.lineEditFuzzerTabIDMask.setEnabled(True)

        QtCore.QCoreApplication.processEvents()

    def toggleGUIElements(self, state):
        """
        {En, Dis}able all GUI elements that are used to change fuzzer settings

        :param state: Boolean value to indicate whether to enable or disable elements
        """

        for GUIElement in [
                self.buttonFuzzerInterfaceSettings,
                self.buttonFuzzerTabToggleFuzzing, self.comboBoxFuzzingMode,
                self.lineEditFuzzerTabIDMask, self.lineEditFuzzerTabDataMask,
                self.horizontalSliderFuzzerMinLength,
                self.horizontalSliderFuzzerMaxLength,
                self.doubleSpinBoxFuzzerPacketGap, self.buttonFuzzerClear,
                self.packetTableView
        ]:
            GUIElement.setEnabled(state)
