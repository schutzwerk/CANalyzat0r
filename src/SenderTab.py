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
Created on May 22, 2017

@author: pschmied
"""

from PySide.QtGui import *
from PySide.QtCore import QFile, Qt

from CANData import CANData
import Globals
import Strings
import SenderTabElement
import Toolbox
from Logger import Logger


class SenderTab():
    """
    This class handles the logic of the sender tab.
    Subtabs are being handled in :class:`~src.SenderTabElement.SenderTabElement`.
    """

    #: The index of the sender tab in the main tab bar
    indexInMainTabBar = 2
    #: Used to handle the font color of the sender tab
    currentlySendingTabs = 0
    #: Consinsts of all SenderTabElements
    senderTabs = []

    active = False

    labelInterfaceValue = None

    #: The tab specific CANData instance
    CANData = None

    #: The tab specific logger
    logger = Logger(Strings.senderTabLoggerName).getLogger()

    @staticmethod
    def sendSinglePacket():
        """
        Sends a single packet using the specified interface.
        All packet values are read from the GUI elements.
        """

        id = Globals.ui.lineEditSinglePacketID.text()
        data = Globals.ui.lineEditSinglePacketData.text()
        packet = CANData.tryBuildPacket(id, data)
        if packet is not None:
            SenderTab.CANData.sendPacket(packet)
        else:
            SenderTab.logger.error(Strings.packetBuildError + ": " + id + " " +
                                   data)

    @staticmethod
    def prepareUI():
        """
        Prepare the tab specific GUI elements, add sender tab and keyboard shortcuts. Also set a CANData instance.
        """

        SenderTab.labelInterfaceValue = Globals.ui.labelSenderSingleInterfaceValue
        SenderTab.setInitialCANData()

        # Add one sender to the tab bar
        SenderTab.addSender("Sender 1")
        # Turn the last tab into an add-button and add a click handler
        SenderTab.addButton = QPushButton()
        SenderTab.addButton.setText("+")
        Globals.ui.tabWidgetSenderTabs.setTabEnabled(2, False)
        Globals.ui.tabWidgetSenderTabs.tabBar().setTabButton(
            2, QTabBar.RightSide, SenderTab.addButton)
        Globals.ui.tabWidgetSenderTabs.tabBar().setTabText(2, "")
        SenderTab.addButton.clicked.connect(SenderTab.addSender)

    @staticmethod
    def addSender(senderTabName=None):
        """
        Appends a new sender tab to the sub tab bar.

        :param senderTabName: Optional; The displayed name of the tab.
                              If this is None, the user is requested to enter a name
        """

        # Read the template and add a tab
        newSenderTabWidget = Toolbox.Toolbox.widgetFromUIFile(
            Strings.senderTabSenderTemplatePath)

        if senderTabName is None:
            # Get the name of the new sender tab from the tuple returned by the dialog
            senderTabNameObject = QInputDialog.getText(
                Globals.ui.tabWidgetMain,
                Strings.senderTabNewSenderMessageBoxTitle,
                Strings.senderTabNewSenderMessageBoxText,
            )
            if senderTabNameObject is None or senderTabNameObject[1] is False:
                return

            senderTabName = senderTabNameObject[0]

        if len(senderTabName) == 0:
            SenderTab.logger.error(Strings.senderTabSenderInvalidName)
            return

        # Insert the new tab just before the add-button
        Globals.ui.tabWidgetSenderTabs.insertTab(
            Globals.ui.tabWidgetSenderTabs.count() - 1, newSenderTabWidget,
            senderTabName)

        # Create a SenderTabElement object which uses the created Widget
        senderTabElement = SenderTabElement.SenderTabElement(
            newSenderTabWidget, senderTabName)

        SenderTab.senderTabs.append(senderTabElement)

        # Add clickhandlers and button logic
        newSenderTabWidget.buttonRemoveTab.clicked.connect(
            senderTabElement.removeSender)
        newSenderTabWidget.buttonSendAll.clicked.connect(
            senderTabElement.sendAll)
        newSenderTabWidget.buttonAddPacket.clicked.connect(
            senderTabElement.manualAddPacket)
        newSenderTabWidget.buttonApplyNewKnownPacketsSender.clicked.connect(
            senderTabElement.applyNewKnownPackets)
        newSenderTabWidget.buttonSenderXDataClear.clicked.connect(
            senderTabElement.clear)
        newSenderTabWidget.buttonSenderXInterfaceSettings.clicked.connect(
            senderTabElement.handleInterfaceSettingsDialog)

        # Set the new tab as the currently active tab
        Globals.ui.tabWidgetSenderTabs.tabBar().setCurrentIndex(
            Globals.ui.tabWidgetSenderTabs.count() - 2)
        Globals.ui.tabWidgetMain.tabBar().setCurrentIndex(
            SenderTab.indexInMainTabBar)

        # Return the index of the new tab to eventually fill it with data
        return SenderTab.senderTabs.index(senderTabElement)

    @staticmethod
    def addSenderWithData(listOfRawPackets=None, listOfPackets=None):
        """
        Uses :func:`addSender` to add a new sender tab with data already filled in into the GUI table.
        You must specify ``listOfRawPackets`` **or** ``listOfPackets``. If both are specified,
        ``listOfRawPackets`` will be used.

        :param listOfRawPackets: Optional; List of raw packets to add to the table.
        :param listOfPackets: Optional; List of packet objects to add to the table.
        :return:
        """

        # First create a new empty sender
        senderIndex = SenderTab.addSender()

        if senderIndex is None:
            return

        newSenderTab = SenderTab.senderTabs[senderIndex]

        if newSenderTab is None:
            return

        if listOfRawPackets is not None:
            for rawPacket in listOfRawPackets:
                newSenderTab.addPacket(rawPacket)

        else:
            # Iterate over every packet object that will be inserted
            for packet in listOfPackets:
                newSenderTab.addPacket(
                    [packet.CANID, packet.data, packet.length])

    @staticmethod
    def removeSender(senderTabElement):
        """
        Remove a sender from the sub tab bar. This method gets called from an instance of
        :class:`~src.SenderTabElement.SenderTabElement` by :func:`~src.SenderTabElement.SenderTabElement.removeSender`.

        :param senderTabElement: The :class:`~src.SenderTabElement.SenderTabElement` instance to remove
        """

        # Remove the tab and the object
        Globals.ui.tabWidgetSenderTabs.removeTab(
            senderTabElement.getTabIndex())
        SenderTab.senderTabs.remove(senderTabElement)
        # Set the focus to the left element
        Globals.ui.tabWidgetSenderTabs.tabBar().setCurrentIndex(
            Globals.ui.tabWidgetSenderTabs.count() - 2)

    @staticmethod
    def toggleActive():
        """
        If there is at least one tab sending then the tab bar title will be red.
        """

        if SenderTab.currentlySendingTabs > 0:
            Globals.ui.tabWidgetMain.tabBar().setTabTextColor(
                Globals.ui.tabWidgetMain.currentIndex(), Qt.red)
        else:
            Globals.ui.tabWidgetMain.tabBar().setTabTextColor(
                Globals.ui.tabWidgetMain.currentIndex(), Qt.black)

    @staticmethod
    def toggleGUIElements(state):
        """
        {En, Dis}able all GUI elements that are used to change filter settings

        :param state: Boolean value to indicate whether to enable or disable elements
        """

        for GUIElement in [
                Globals.ui.buttonSenderSingleInterfaceSettings,
                Globals.ui.lineEditSinglePacketID,
                Globals.ui.lineEditSinglePacketData,
                Globals.ui.buttonSingleSend
        ]:
            GUIElement.setEnabled(state)

    @classmethod
    def updateCANDataInstance(cls, CANDataInstance, delegate=False):
        """
        This invokes :func:`~src.AbstractTab.updateCANDataInstance` for the class

        :param CANDataInstance: The new CANData instance
        :param delegate: Boolean indicating if all sender sub tabs will be updated too. Default: False
        """

        import AbstractTab
        SenderTab.labelInterfaceValue = Globals.ui.labelSenderSingleInterfaceValue
        AbstractTab.AbstractTab.updateCANDataInstance(cls, CANDataInstance)

        if delegate:
            for senderTab in cls.senderTabs:
                senderTab.updateCANDataInstance(CANDataInstance)

    @classmethod
    def updateInterfaceLabel(cls):
        """
        This invokes :func:`~src.AbstractTab.updateInterfaceLabel` for the class
        """

        import AbstractTab
        AbstractTab.AbstractTab.updateInterfaceLabel(cls)

        for senderTab in SenderTab.senderTabs:
            senderTab.updateInterfaceLabel()

    @classmethod
    def setInitialCANData(cls):
        """
        This invokes :func:`~src.AbstractTab.setInitialCANData` for the class
        """

        import AbstractTab
        AbstractTab.AbstractTab.setInitialCANData(cls)

    @classmethod
    def handleInterfaceSettingsDialog(cls):
        """
        This invokes :func:`~src.AbstractTab.handleInterfaceSettingsDialog` for the class
        """

        import AbstractTab
        AbstractTab.AbstractTab.handleInterfaceSettingsDialog(cls)
