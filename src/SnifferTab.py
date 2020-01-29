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
Created on May 18, 2017

@author: pschmied
"""

from PySide.QtCore import Qt
from Logger import Logger
import SnifferTabElement
import Toolbox
import Globals
import Strings


class SnifferTab():
    """
    This class handles the logic of the sniffer tab.
    Subtabs are being handled in :class:`~src.SnifferTabElement.SnifferTabElement`.
    """

    #: The index of the sniffer tab in the main tab bar
    indexInMainTabBar = 1
    #: Consinsts of all SnifferTabElements, interface names as key
    snifferTabs = {}

    #: The tab specific logger
    logger = Logger(Strings.snifferTabLoggerName).getLogger()

    @staticmethod
    def prepareUI():
        """
        This adds a placeholder of no instance of :class:`~src.SnifferTabElement.SnifferTabElement`
        was created previously.
        """

        if len(SnifferTab.snifferTabs) == 0:
            SnifferTab.clearAndAddPlaceholder()

    @staticmethod
    def clearAndAddPlaceholder():
        """
        Add a placeholder where normally sniffer tabs are displayed
        """

        Globals.ui.tabWidgetSnifferTabs.clear()

        placeholderWidget = Toolbox.Toolbox.widgetFromUIFile(
            Strings.snifferPlaceHolderTemplatePath)

        Globals.ui.tabWidgetSnifferTabs.insertTab(
            0, placeholderWidget, Strings.snifferTabPlaceHolderTabText)

    @staticmethod
    def addSniffer(snifferTabName):
        """
        Appends a new sniffer tab to the sub tab bar.

        :param snifferTabName: The displayed name of the tab. Normally, this corresponds to the
                               CAN interface the tab is managing
        """

        if snifferTabName in SnifferTab.snifferTabs:
            SnifferTab.logger.debug(Strings.snifferTabElementAlreadyPresent)
            return

        # Try to remove the placeholder
        for tabIndex in range(Globals.ui.tabWidgetSnifferTabs.count()):
            curTabText = Globals.ui.tabWidgetSnifferTabs.tabText(tabIndex)
            if curTabText == Strings.snifferTabPlaceHolderTabText:
                Globals.ui.tabWidgetSnifferTabs.removeTab(tabIndex)

        # Read the template and add a tab
        newSnifferTabWidget = Toolbox.Toolbox.widgetFromUIFile(
            Strings.snifferTemplatePath)

        tabIndex = Globals.ui.tabWidgetSnifferTabs.count()
        # Insert the new tab
        Globals.ui.tabWidgetSnifferTabs.insertTab(
            tabIndex, newSnifferTabWidget, snifferTabName)

        # Create a SnifferTabElement object which uses the created Widget
        snifferTabElement = SnifferTabElement.SnifferTabElement(
            newSnifferTabWidget, snifferTabName)

        # Add it to the dict
        SnifferTab.snifferTabs[snifferTabName] = snifferTabElement

        # Add clickhandlers and button logic
        newSnifferTabWidget.buttonSniff.clicked.connect(
            snifferTabElement.toggleSniffing)
        newSnifferTabWidget.buttonClearPackets.clicked.connect(
            snifferTabElement.clear)
        newSnifferTabWidget.buttonApplyNewKnownPacketsSniffer.clicked.connect(
            snifferTabElement.applyNewKnownPackets)
        newSnifferTabWidget.tableViewSnifferXData.customContextMenuRequested.connect(
            snifferTabElement.handleRightCick)
        newSnifferTabWidget.buttonSnifferXInterfaceSettings.clicked.connect(
            snifferTabElement.handleInterfaceSettingsDialog)
        newSnifferTabWidget.buttonSnifferXIgnoredPackets.clicked.connect(
            snifferTabElement.handleManageIgnoredPacketsDialog)

    @staticmethod
    def removeSniffer(snifferTabElement=None, snifferTabName=None):
        """
        Remove a sniffer from the sub tab bar. This method gets called from an instance of
        :class:`~src.SnifferTabElement.SnifferTabElement` by :func:`~src.SnifferTabElement.SnifferTabElement.removeSender`.
        One can either specify ``snifferTabElement`` *or* ``snifferTabName`` to delete a tab. If both are used,
        the object parameter is used.

        :param senderTabElement: Optional: The :class:`~src.SnifferTabElement.SnifferTabElement` instance to remove
        :param snifferTabName: Optional: The name of the :class:`~src.SenderTabElement.SenderTabElement` instance to remove
        """

        # Delete by value or by name
        if snifferTabElement is None and len(snifferTabName) > 0:
            try:
                snifferTabElement = SnifferTab.snifferTabs[snifferTabName]
            except KeyError:
                return

        snifferTabElement.terminateThreads()
        # Remove the tab and the object
        Globals.ui.tabWidgetSnifferTabs.removeTab(snifferTabElement.tabIndex())
        del SnifferTab.snifferTabs[snifferTabElement.tabName]
        # Set the focus to the left element
        Globals.ui.tabWidgetSnifferTabs.tabBar().setCurrentIndex(
            Globals.ui.tabWidgetSnifferTabs.count() - 1)

        # Add a placeholder if no interfaces are remaining
        if Globals.ui.tabWidgetSnifferTabs.count() == 0:
            SnifferTab.clearAndAddPlaceholder()

    @classmethod
    def updateInterfaceLabel(cls):
        """
        This invokes :func:`~src.AbstractTab.updateInterfaceLabel` every sniffer tab
        """
        for snifferTab in list(SnifferTab.snifferTabs.values()):
            snifferTab.updateInterfaceLabel()

    @staticmethod
    def toggleActive():
        """
        If there is at least one tab sniffing then the tab bar title will be red.
        """

        if SnifferTabElement.SnifferTabElement.amountThreadsRunning > 0:
            Globals.ui.tabWidgetMain.tabBar().setTabTextColor(
                Globals.ui.tabWidgetMain.currentIndex(), Qt.red)
        else:
            Globals.ui.tabWidgetMain.tabBar().setTabTextColor(
                Globals.ui.tabWidgetMain.currentIndex(), Qt.black)
