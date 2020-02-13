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
Created on Jun 16, 2017

@author: pschmied
"""

from multiprocessing import Pipe, Value
from PySide import QtCore
from PySide.QtGui import QMessageBox

import Strings
import Globals
import MainTab
import SnifferTab
import SnifferProcess
import ItemAdderThread
import PacketsDialog
import Toolbox
from CANData import CANData
from AbstractTab import AbstractTab


class SnifferTabElement(AbstractTab):
    """
    This class handles the logic of the sniffer sub tab.
    The main tab is being handled in :class:`~src.SnifferTab.SnifferTab`.
    """

    #: Amount of sniffing threads running to display in the status bar
    amountThreadsRunning = 0

    def __init__(self, tabWidget, tabName, ifaceName=None):
        """
        Set parameters and initialize the CANData instance

        :param tabWidget: The element in the tab bar. **Not** the table widget.
        :param tabName: The name of the tab
        :param ifaceName: Optional: The interface name. If this is None, then the ``tabName`` will be used
        """

        self.ifaceName = ifaceName if ifaceName is not None else tabName

        AbstractTab.__init__(
            self,
            tabWidget,
            Strings.snifferTabElementLoggerName + " (" + tabName + ")",
            [0, 1, 2, 3, 4],
            Strings.snifferTabElementPacketTableViewName,
            labelInterfaceValueName=Strings.
            snifferTabElementLabelInterfaceValueName,
            CANData=CANData.CANDataInstances[self.ifaceName],
            hideTimestampCol=False,
            allowTablePaste=False)

        self.tabName = tabName

        # Amount of packets received on an interface to prevent freezes
        self.packetCount = self.getPacketCount()
        self.tooMuchData = False
        self.valueListsToProcess = []

        # Can be managed using the button
        self.ignoredPackets = []
        # whether to invert the packet ignore mechanism --> do a whitelist instead of a blacklist
        self.invert = False

        self.snifferProcess = None
        self.itemAdderThread = None

        # These flags are shared with the processes/threads
        # to terminate them
        self.sharedSnifferEnabledFlag = Value("i", 1)

        self.prepareUI()

    def toggleSniffing(self):
        """
        This starts and stops sniffing for a specific sniffer tab.
        Instances of :class:`~src.ItemAdderThread.ItemAdderThread` and :class:`~src.SnifferProcess.SnifferProcess` are
        used to gather and display data.
        """

        if self.CANData is None:
            QMessageBox.critical(
                Globals.ui.tabWidgetMain,
                Strings.snifferTabElementInterfaceMissingMessageBoxTitle,
                Strings.snifferTabElementInterfaceMissingMessageBoxText,
                QMessageBox.Ok)
            return

        # Stop the thread and process
        if self.active:
            self.terminateThreads()

            # If too much data was received process it now
            if self.tooMuchData:
                progressDialog = Toolbox.Toolbox.getWorkingDialog(
                    Strings.snifferTabElementDialogProcessing)
                progressDialog.open()
                try:
                    self.packetTableModel.clear()
                    for listIdx in range(len(self.valueListsToProcess)):
                        if listIdx % 1500 == 0:
                            QtCore.QCoreApplication.processEvents()
                        self.addPacket(
                            self.valueListsToProcess[listIdx],
                            ignorePacketRate=True)
                finally:
                    progressDialog.close()
                    self.packetTableView.setEnabled(True)
                    self.tooMuchData = False

        # Start sniffer process, item generator process and item adder thread
        else:

            # Reset the flag
            self.sharedSnifferEnabledFlag = Value("i", 1)

            snifferReceivePipe, snifferSendPipe = Pipe()

            # First start the ItemAdderThread...
            self.itemAdderThread = ItemAdderThread.ItemAdderThread(
                snifferReceivePipe,
                self.packetTableModel,
                self.rawData,
                useTimestamp=True)

            self.itemAdderThread.appendRow.connect(self.addPacket)
            self.itemAdderThread.start()

            # ... then start the SnifferProcess
            self.snifferProcess = SnifferProcess.SnifferProcess(
                snifferSendPipe,
                self.sharedSnifferEnabledFlag,
                self.tabName,
                CANData=self.CANData)
            self.snifferProcess.start()

            SnifferTabElement.amountThreadsRunning += 1
            self.updateStatusBar()
            self.tabWidget.buttonSniff.setText(
                Strings.snifferTabElementSniffingButtonEnabled)

            self.active = True
            self.CANData.active = True
            self.toggleActive()
            self.logger.info(Strings.snifferTabElementSniffingStarted)

    def updateStatusBar(self):
        """
        Updates the status bar label to display the correct amount of sniffer tabs (if any)
        """

        # Remove the previous sending status from the status bar first (if any) ...
        MainTab.MainTab.removeApplicationStatus(Strings.statusBarSniffing)
        # ... and add the new element afterwards if amount > 0
        if SnifferTabElement.amountThreadsRunning > 0:
            status = Strings.statusBarSniffing +\
                " (" +\
                str(SnifferTabElement.amountThreadsRunning) +\
                " " +\
                ("Threads" if SnifferTabElement.amountThreadsRunning > 1 else "Thread") +\
                ")"

            MainTab.MainTab.addApplicationStatus(status)

    def addPacket(self,
                  valueList,
                  addAtFront=True,
                  append=True,
                  emit=True,
                  addToRawDataOnly=False,
                  ignorePacketRate=False):
        """
        Override the parents method to add packets at front and to update the counter label.
        If too much data is received, the data will be added after sniffing to prevent freezes.
        Also, only add packets if the data isn't present in ``self.ignoredPackets``

        :param ignorePacketRate: Additional optional parameter: Boolean value indicating whether the rate of
                                 packets per second will be ignored or not. This is set to False by Default.
                                 We need to set it to True to process ``self.valueList`` after sniffing if too much
                                 data was received.

        """

        # Check if we want to ignore the packet
        CANID = valueList[self.IDColIndex]
        data = valueList[self.dataColIndex]
        strIdx = Toolbox.Toolbox.getPacketDictIndex(CANID, data)

        print("ignored: %s" % (self.ignoredPackets))
        print("strIdx: %s" % (strIdx))

        accepted = True
        if strIdx in self.ignoredPackets:
            accepted = False
        # Check wildcard
        elif str(str(CANID) + "#*").upper() in self.ignoredPackets:
            accepted = False

        if self.invert:
            accepted = not accepted

        if not accepted:
            return

        # Save the values for later
        if not ignorePacketRate and self.tooMuchData:
            self.valueListsToProcess.append(valueList)
            # Also update the label
            self.tabWidget.labelSnifferCountValue.setText(
                str(len(self.rawData) + len(self.valueListsToProcess)))
            return

        else:
            # Check periodically
            if len(self.rawData) % 500 == 0 and len(
                    self.rawData
            ) > 0 and not ignorePacketRate and not self.tooMuchData:
                packetCount = self.getPacketCount()
                # if we add one packet to the GUI, X packets are received on the socket
                # --> this is too much data
                # --> save data to process it after the sniffing has stopped to prevent freezes
                if packetCount != 0 and packetCount - self.packetCount > 7200:
                    self.tooMuchData = True
                    self.packetTableView.setEnabled(False)
                    self.logger.warn(Strings.snifferTabElementTooMuchData)

                # Update the value for the next call
                self.packetCount = packetCount

            AbstractTab.addPacket(
                self,
                valueList=valueList,
                addAtFront=addAtFront,
                append=append,
                emit=emit)
            # Also update the label
            self.tabWidget.labelSnifferCountValue.setText(
                str(len(self.rawData)))

    def handleInterfaceSettingsDialog(self, allowOnlyOwnInterface=True):
        """
        Override the parents method to only allow the currently set CAN interface
        """

        AbstractTab.handleInterfaceSettingsDialog(
            self, allowOnlyOwnInterface=allowOnlyOwnInterface)

    def clear(self, returnOldPackets=False):
        """
        Clear the currently displayed data on the GUI and in the lists.

        :param returnOldPackets: Optional: If this is True then the previously displayed data will be returned as
                                 raw data list. Default is False

        """

        savedPackets = AbstractTab.clear(
            self, returnOldPackets=returnOldPackets)
        self.valueListsToProcess.clear()
        # Reset the label too
        self.tabWidget.labelSnifferCountValue.setText("0")

        return savedPackets

    def toggleActive(self):
        """
        Toggles the current sub tab to (in)active. This also calls :func:`~src.SnifferTab.SnifferTab.toggleActive` to manage
        the color of the main tab (parent tab).
        """

        if self.active:
            Globals.ui.tabWidgetSnifferTabs.tabBar().setTabTextColor(
                self.tabIndex(), QtCore.Qt.red)
        else:
            Globals.ui.tabWidgetSnifferTabs.tabBar().setTabTextColor(
                self.tabIndex(), QtCore.Qt.black)

        SnifferTab.SnifferTab.toggleActive()

    def terminateThreads(self):
        """
        This stops the processes/threads called ``snifferProcess`` and ``itemAdderThread``.
        Also, the CANData instance will be set to inactive and GUI elements will be toggled.
        """

        # Stop the Sniffer
        if self.snifferProcess is not None:
            with self.sharedSnifferEnabledFlag.get_lock():
                self.sharedSnifferEnabledFlag.value = 0
            self.snifferProcess.join()
            self.logger.debug(Strings.snifferProcessTerminated)

        # Stop the ItemAdder
        if self.itemAdderThread is not None:
            self.itemAdderThread.disable()
            self.itemAdderThread.wait()
            self.itemAdderThread.quit()
            self.logger.debug(Strings.itemAdderThreadTerminated)

        # Reset settings and the UI
        self.tabWidget.buttonSniff.setText(
            Strings.snifferTabElementSniffingButtonDisabled)
        SnifferTabElement.amountThreadsRunning -= 1
        self.updateStatusBar()
        self.active = False
        self.CANData.active = False
        self.toggleActive()
        SnifferTab.SnifferTab.toggleActive()
        self.logger.info(Strings.snifferTabElementSniffingStopped)

    def removeSniffer(self):
        """
        This gets called when associated interface disappears after a re-check.
        This stops the sniffer thread and calls the parents method (:func:`~src.SnifferTab.SnifferTab.removeSender`)
        to remove the sniffer form the tab bar.
        """

        # Stop the thread first
        self.terminateThreads()
        SnifferTab.SnifferTab.removeSniffer(self)

    def handleManageIgnoredPacketsDialog(self):
        """
        Open a dialog to manage ignored packets when sniffing
        """

        dialog = PacketsDialog.PacketsDialog(
            packets=self.ignoredPackets, returnPacketsAsRawList=False, invert=self.invert)
        res = dialog.open()
        if res is None:
            return

        invert, ignoredPackets = res

        self.invert = invert

        # Only if the user didn't press cancel
        if ignoredPackets is not None:
            self.ignoredPackets = ignoredPackets
            self.logger.info(Strings.snifferTabElementIgnoredPacketsUpdated)

    def tabIndex(self):
        """
        Get the **current** tab index of the sub tab element

        :return: The tab index of the sniffer tab
        """

        return Globals.ui.tabWidgetSnifferTabs.indexOf(self.tabWidget)

    def getPacketCount(self):
        """
        This uses a call to ``/sys/class/net/<ifaceName>/statistics/rx_packets`` to return the number
        of total received packets of the current interface

        :return: Received packet count of the current interface as itneger
        """

        with open("/sys/class/net/" + self.ifaceName +
                  "/statistics/rx_packets") as statisticsFile:
            return int(statisticsFile.readlines()[0].strip())
