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
Created on Jun 23, 2017

@author: pschmied
"""

from PySide import QtGui, QtCore
from PySide.QtGui import QMessageBox

import Strings
import Toolbox
from AbstractTab import AbstractTab


class PacketsDialog(AbstractTab):
    """
    This class handles the logic of the "manage packets" dialog. For example, this can be found in the
    :class:`~src.SnifferTabElement.SnifferTabElement`.
    """

    def __init__(self,
                 packets=None,
                 rawPacketList=None,
                 returnPacketsAsRawList=True):
        """
        This basically just sets data and reads the widget from the ``.ui`` file.

        :param packets: Optional: List that contains the elements that will be pre loaded into the GUI table
                               in the following format: ``<CAN ID>#<Data>``.
                               This is used for the :class:`~src.SnifferTabElement.SnifferTabElement`

        :param rawPacketList: Optional: Raw packet list that contains the elements that will be pre loaded into the GUI table.
                              If this is specified, ``packets`` will be ignored.

        :param returnPacketsAsRawList: Boolean value indicating whether the displayed packets will be returned
                                       as raw packet list. If this is False, the values will be returned as list
                                       in the following format: ``<CAN ID>#<Data>``.
        """

        self.packets = packets
        self.rawPacketList = rawPacketList
        self.widget = Toolbox.Toolbox.widgetFromUIFile(
            Strings.packetsDialogUIPath)

        AbstractTab.__init__(
            self,
            self.widget,
            Strings.packetsDialogLoggerName, [2, 3],
            Strings.packetsDialogTableViewName,
            labelInterfaceValueName=None,
            hideTimestampCol=False)

        self.returnPacketsAsRawList = returnPacketsAsRawList

        # Get all GUI elements
        self.buttonManagePacketsDialogAdd = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonManagePacketsDialogAdd")
        self.buttonManagePacketsDialogClear = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonManagePacketsDialogClear")
        self.buttonManagePacketsDialogUniquePackets = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonManagePacketsDialogUniquePackets")
        self.buttonManagePacketsDialogUniqueIDs = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonManagePacketsDialogUniqueIDs")

        assert all(GUIElem is not None for GUIElem in [
            self.buttonManagePacketsDialogAdd,
            self.buttonManagePacketsDialogClear,
            self.buttonManagePacketsDialogUniquePackets,
            self.buttonManagePacketsDialogUniqueIDs,
        ]), "GUI Elements not found"

        self.buttonManagePacketsDialogAdd.clicked.connect(self.manualAddPacket)
        self.buttonManagePacketsDialogClear.clicked.connect(self.clear)
        self.buttonManagePacketsDialogUniquePackets.clicked.connect(
            self.getUniquePackets)
        self.buttonManagePacketsDialogUniqueIDs.clicked.connect(
            self.getUniqueIDs)

        self.prepareUI()

    def prepareUI(self):
        """
        Prepare the GUI elements and add keyboard shortcuts. Also, pre populate the table
        """

        AbstractTab.prepareUI(self)

        # Pre populate the table
        if self.rawPacketList is not None:
            self.rawData = self.rawPacketList
            self.packetTableModel.appendRows(self.rawPacketList)

        elif self.packets is not None:
            for packet in self.packets:
                vals = packet.split("#")
                CANID = vals[0]
                data = vals[1] if vals[1] != "*" else ""
                self.addPacket([CANID, data])

    def open(self):
        """
        Show the widget, extract data and return it

        :return: Raw packet list if the user didn't press Cancel and if ``returnPacketsAsRawList`` is True.
                 Else: list of values of the following form: ``<CAN ID>#<Data>`` if the user didn't press Cancel.
                 Else None.
        """

        pressedButton = self.widget.exec_()
        if pressedButton == QMessageBox.Accepted:
            rawPackets = Toolbox.Toolbox.tableExtractAllRowData(
                self.widget.tableViewManagePacketsDialogData)

            if self.returnPacketsAsRawList:
                return rawPackets
            else:
                returnedPackets = []
                for rawPacket in rawPackets:

                    CANID = rawPacket[self.IDColIndex]
                    data = rawPacket[self.dataColIndex]
                    # Manage wildcards
                    data = "*" if len(data) == 0 else data

                    returnedPackets.append(CANID + "#" + data)
                return returnedPackets

        else:
            return None

    def getUniquePackets(self):
        """
        Filters all unique packets out of ``rawData`` and displays them on the GUI table.
        This uses :func:`displayUniquePackets`.
        """

        self.displayUniquePackets()

    def getUniqueIDs(self):
        """
        Filters all unique IDs out of ``rawData`` and displays them on the GUI table.
        Unique ID means that the data column will be ignored and left blank for wildcard ignores.
        This uses :func:`displayUniquePackets`.
        """

        self.displayUniquePackets(IDOnly=True)

    def displayUniquePackets(self, IDOnly=False):
        """
        Filter the currently displayed data for unique packets and display them on the table.
        :param IDOnly: If this is True, only the ID will be matched to compare data. This allows wildcard ignores.
        """

        from multiprocessing.pool import Pool

        progressDialog = Toolbox.Toolbox.getWorkingDialog(
            Strings.dialogFiltering)
        progressDialog.open()

        try:
            rawData = self.clear(returnOldPackets=True)

            if len(rawData) == 0:
                return

            for rawPacket in rawData:

                # Ignore the timestamp and length column --> make it blank
                rawPacket[self.timestampColIndex] = ""
                rawPacket[self.lengthColIndex] = ""

                if IDOnly:
                    rawPacket[self.dataColIndex] = ""

            # Use asynchronous processing
            pool = Pool(processes=1)
            # We need to pass a tuple of args
            async_result = pool.apply_async(PacketsDialog.getUniqueRawPackets,
                                            (rawData, ))

            refreshCounter = 0
            while not async_result.ready():
                if refreshCounter % 100 == 0:
                    QtCore.QCoreApplication.processEvents()
                    refreshCounter = 0
                refreshCounter += 1

            filteredDataTuples = async_result.get()

            for filteredPacketTuple in filteredDataTuples:
                filteredPacket = list(filteredPacketTuple)
                self.addPacket(filteredPacket)
        finally:
            progressDialog.close()

    @staticmethod
    def getUniqueRawPackets(rawPacketList):
        """
        Helper method to extract unique raw packets out of a given raw packet list
        which has been cleaned before (Only necessary data fields are present, all others are
        set to an empty string)

        :param rawPacketList: The cleaned list of raw packets
        :return: A list of unique raw packet lists
        """

        return list(set(tuple(rawPacket) for rawPacket in rawPacketList))
