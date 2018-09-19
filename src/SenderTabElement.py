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
Created on May 23, 2017

@author: pschmied
"""

import time
from PySide import QtCore

import Globals
import Strings
import SenderTab
from SenderThread import LoopSenderThread
from CANData import CANData
import MainTab
import Toolbox
from AbstractTab import AbstractTab


class SenderTabElement(AbstractTab):

    """
    This class handles the logic of the sender sub tab.
    The main tab is being handled in :class:`~src.SenderTab.SenderTab`.
    """

    #: Static attribute of send buttons to manage {en, dis}abled states
    sendButtonList = []

    #: Amount of sending threads running to display in the status bar
    amountThreadsRunning = 0

    def __init__(self, tabWidget, tabName):
        """
        Set all passed data. Also, add the own send button to ``SenderTab.sendButtonList`` to
        allow managing it globally.

        :param tabWidget: The element in the tab bar. **Not** the table widget.
        """

        AbstractTab.__init__(self,
                             tabWidget,
                             Strings.senderTabLoggerName +
                             " (" + tabName + ")",
                             [2, 3, 4],
                             Strings.senderTabElementPacketTableViewName,
                             Strings.senderTabElementLabelInterfaceValueName)

        self.tabName = tabName

        self.tabIndex = self.getTabIndex()
        if self.tabIndex == -1:
            raise ValueError("tabWidget not present in tab bar")

        # Append the own send button to the list
        SenderTabElement.sendButtonList.append(self.tabWidget.buttonSendAll)

        #: The thread that runs when sending takes place in a loop
        self.loopSenderThread = None

        self.prepareUI()

    def sendAll(self):
        """
        Send all packets in the GUI table. By default, this just sends the packet once using simple calls.
        If the user requests to send the packets in a loop, an instance of :class:`~src.SenderThread.LoopSenderThread`
        is being used to send the packets.
        Also, GUI elements like the status bar are being updated.
        """

        if len(self.rawData) == 0:
            return

        # Set the CANData instance
        if not self.CANData:
            return

        # Check if theres a sending thread running
        if not self.active:
            # in ms
            sleepTime = self.tabWidget.doubleSpinBoxGap.value() / 1000
            packetsToSend = []
            for packetData in self.rawData:
                packetToSend = CANData.tryBuildPacket(
                    packetData[0], packetData[1])
                if packetToSend is not None:
                    packetsToSend.append(packetToSend)
                else:
                    self.logger.error(
                        Strings.packetBuildError + ": " + packetData[0] + " " + packetData[1])

            if len(packetsToSend) == 0 or packetsToSend[0] is None:
                return

            # If a sending loop is requested: Create a thread and set the current tab to active
            if self.tabWidget.checkBoxSendingLoop.isChecked():

                self.loopSenderThread = LoopSenderThread(
                    packetsToSend, sleepTime, self.CANData, self.tabName)
                self.loopSenderThread.start()
                self.logger.info(Strings.senderTabElementSenderThreadStarted)

                self.toggleGUIElements(False)
                self.active = True
                self.CANData.active = True
                self.toggleLoopActive()
                SenderTabElement.amountThreadsRunning += 1

                self.updateStatusBar()

            # Else just send the packets once - no need for a new thread
            else:
                progressDialog = Toolbox.Toolbox.getWorkingDialog(
                    Strings.dialogSending)
                progressDialog.show()
                QtCore.QCoreApplication.processEvents()

                try:
                    for packetIdx in range(len(packetsToSend)):
                        packetToSend = packetsToSend[packetIdx]
                        self.CANData.sendPacket(packetToSend)
                        time.sleep(sleepTime)

                        if packetIdx % 500 == 0:
                            QtCore.QCoreApplication.processEvents()

                    self.logger.info(Strings.senderTabPacketsSentOK)

                finally:
                    progressDialog.close()

        # Stop the thread and reset logic
        else:
            self.stopSending()

    def stopSending(self):
        """
        This stops the currently running instance of :class:`~src.SenderThread.LoopSenderThread` from sending.
        Also, GUI elements like the status bar are being updated.
        """

        if self.loopSenderThread is not None:
            self.loopSenderThread.disable()
            self.loopSenderThread.wait()
            self.loopSenderThread.quit()

        if self.active:
            SenderTabElement.amountThreadsRunning -= 1
            self.toggleLoopActive()

        self.active = False
        self.CANData.active = False

        self.toggleGUIElements(True)

        self.logger.info(Strings.senderTabElementSenderThreadStopped)
        self.updateStatusBar()

    def updateStatusBar(self):
        """
        Updates the status bar label to display the correct amount of sending tabs (if any)
        """

        # Remove the previous sending status from the status bar first (if any) ...
        MainTab.MainTab.removeApplicationStatus(Strings.statusBarSending)
        # ... and add the new element afterwards if amount > 0
        if SenderTabElement.amountThreadsRunning > 0:
            status = Strings.statusBarSending +\
                " (" +\
                str(SenderTabElement.amountThreadsRunning) +\
                " " +\
                ("Threads" if SenderTabElement.amountThreadsRunning > 1 else "Thread") +\
                ")"

            MainTab.MainTab.addApplicationStatus(status)

    def toggleLoopActive(self):
        """
        Toggles the current sub tab to (in)active. This also calls :func:`~src.SenderTab.SenderTab.toggleActive` to manage
        the color of the main tab (parent tab).
        """

        # Set the attributes according to the currently set text color
        if Globals.ui.tabWidgetSenderTabs.tabBar().tabTextColor(self.tabIndex) == QtCore.Qt.red:
            Globals.ui.tabWidgetSenderTabs.tabBar().setTabTextColor(
                self.tabIndex, QtCore.Qt.black)
            self.tabWidget.buttonSendAll.setText(Strings.senderTabSendAll)
            SenderTab.SenderTab.currentlySendingTabs -= 1

        else:
            Globals.ui.tabWidgetSenderTabs.tabBar().setTabTextColor(
                self.tabIndex, QtCore.Qt.red)
            self.tabWidget.buttonSendAll.setText(Strings.senderTabStopSending)
            SenderTab.SenderTab.currentlySendingTabs += 1

        SenderTab.SenderTab.toggleActive()

    def removeSender(self):
        """
        This gets called when the remove sender button is pressed on the sub tab.
        This stops the sender thread and calls the parents method (:func:`~src.SenderTab.SenderTab.removeSender`)
        to remove the sender form the tab bar.
        """

        if self.active and not Toolbox.Toolbox.askUserConfirmAction():
            return

        # Stop the thread first
        self.stopSending()
        SenderTab.SenderTab.removeSender(self)

    def prepareUI(self):
        """
        Prepare the tab specific GUI elements, add keyboard shortcuts and set a CANData instance
        """
        AbstractTab.prepareUI(self)

        sendButtonEnabledState = self.CANData is not None
        self.setSendButtonState(sendButtonEnabledState)

    def setSendButtonState(self, state):
        """
        This sets the enabled state of the send button.

        :param state: The desired enabled state as boolean value
        """

        self.tabWidget.buttonSendAll.setEnabled(state)

    def toggleGUIElements(self, state):
        """
        {En, Dis}able all GUI elements that are used to change filter settings

        :param state: Boolean value to indicate whether to enable or disable elements
        """

        for GUIElement in [self.tabWidget.checkBoxSendingLoop,
                           self.tabWidget.buttonSenderXInterfaceSettings,
                           self.tabWidget.buttonAddPacket,
                           self.tabWidget.doubleSpinBoxGap,
                           self.tabWidget.tableViewSenderXData,
                           self.tabWidget.buttonApplyNewKnownPacketsSender,
                           self.tabWidget.buttonSenderXDataClear]:
            GUIElement.setEnabled(state)

    def getTabIndex(self):
        """
        Get the **current** tab index of the sub tab element

        :return: The tab index of the sender tab
        """

        return Globals.ui.tabWidgetSenderTabs.indexOf(self.tabWidget)
