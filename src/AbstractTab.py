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
Created on Jun 26, 2017

@author: pschmied
"""

from PySide import QtCore, QtGui
import ast
from multiprocessing.pool import Pool

import Strings
import CANData
import Packet
from Logger import Logger
import PacketTableModel
import Toolbox


class AbstractTab():
    """
    This is a base class for *most* tabs. If you're using a tab that uses the following things, you can use this class:
    - Non-static tab - you create instances from it
    - a QTableView to display data
    - ``rawData`` as raw packet list
    - Copy, paste and/or delete actions by shortcuts and context menus

    Just take care of ``packetTableViewName`` and ``labelInterfaceValueName`` as they're necessary for this to work.
    """

    def __init__(self,
                 tabWidget,
                 loggerName,
                 readOnlyCols,
                 packetTableViewName,
                 labelInterfaceValueName=None,
                 CANData=None,
                 hideTimestampCol=True,
                 sendToSenderContextMenu=True,
                 saveAsPacketSetContextMenu=True,
                 allowTableCopy=True,
                 allowTablePaste=True,
                 allowTableDelete=True):

        #: The specific GUI tab
        self.tabWidget = tabWidget
        #: Tab specific read only columns as list of indexes
        self.readOnlyCols = readOnlyCols
        # Whether we hide the timestamp column or not
        self.hideTimestampCol = hideTimestampCol
        #: Raw packet data that corresponds to the data displayed in the GUI table
        self.rawData = []
        #: Custom packet model of the GUI table
        self.packetTableModel = None
        #: The tab specific CANData instance
        self.CANData = CANData
        #: Whether the tab is currently active (using ``CANData``)
        self.active = False

        # Default indexes for GUI tables
        self.IDColIndex = 0
        self.dataColIndex = 1
        self.lengthColIndex = 2
        self.timestampColIndex = 3
        self.descriptionColIndex = 4

        # Context menu settings
        self.sendToSenderContextMenu = sendToSenderContextMenu
        self.saveAsPacketSetContextMenu = saveAsPacketSetContextMenu

        # Shortcut settings
        self.allowTableCopy = allowTableCopy
        self.allowTablePaste = allowTablePaste
        self.allowTableDelete = allowTableDelete

        self.packetTableView = self.tabWidget.findChild(
            QtGui.QTableView, packetTableViewName)
        if labelInterfaceValueName is not None:
            self.labelInterfaceValue = self.tabWidget.findChild(
                QtGui.QLabel, labelInterfaceValueName)
            assert (self.packetTableView
                    and self.labelInterfaceValue), "GUI elements not found"
        else:
            self.labelInterfaceValue = None
            assert (self.packetTableView), "tableView not found"

        #: The tab specific logger
        self.loggerName = loggerName
        self.logger = Logger(self.loggerName).getLogger()

    def prepareUI(self):
        """
        Prepare the tab specific GUI elements, add keyboard shortcuts and set a CANData instance
        """

        header = ["ID", "Data", "Length", "Timestamp", "Description"]

        self.packetTableModel = PacketTableModel.PacketTableModel(
            self.packetTableView, [],
            header,
            self.readOnlyCols,
            IDColIndex=self.IDColIndex,
            dataColIndex=self.dataColIndex,
            lengthColIndex=self.lengthColIndex,
            timestampColIndex=self.timestampColIndex,
            descriptionColIndex=self.descriptionColIndex)
        self.packetTableView.setModel(self.packetTableModel)

        if self.hideTimestampCol:
            # Hide the timestamp column
            self.packetTableView.setColumnHidden(self.timestampColIndex, True)

        self.packetTableView.resizeColumnsToContents()
        self.packetTableView.setSortingEnabled(True)
        self.packetTableView.setAlternatingRowColors(True)
        self.packetTableView.customContextMenuRequested.connect(
            self.handleRightCick)
        self.packetTableModel.cellChanged.connect(self.handleCellChanged)

        # Bind custom handlers
        if self.allowTableCopy:
            QtGui.QShortcut(
                QtGui.QKeySequence("Ctrl+c"),
                self.packetTableView).activated.connect(self.handleCopy)

        if self.allowTablePaste:
            QtGui.QShortcut(
                QtGui.QKeySequence("Ctrl+v"),
                self.packetTableView).activated.connect(self.handlePaste)

        if self.allowTableDelete:
            QtGui.QShortcut(QtGui.QKeySequence("Del"),
                            self.packetTableView).activated.connect(
                                self.removeSelectedPackets)

        if self.CANData is None:
            self.setInitialCANData()
        self.updateInterfaceLabel()

    def addPacket(self,
                  valueList,
                  addAtFront=False,
                  append=True,
                  emit=True,
                  addToRawDataOnly=False):
        """
        Add a packet to the GUI table.

        :param valueList: Packet data as raw value list
        :param addAtFront: Optional. Indicates whether the packets will be inserted at the start of ``rawData``.
                           Default: False

        :param append: Optional. Indicates whether data will be added to ``self.rawData`` or not. Default: True
        :param emit: Optional. Indicates whether the GUI will be notified using signals. Default: True
        :param addToRawDataOnly: Optional. Indicates whether only ``self.rawData`` will be updated, ignoring
                                 the packet table model. Default: False
        """

        assert isinstance(valueList,
                          list), "You have to call this with a value list!"

        CANID = valueList[self.IDColIndex]
        data = valueList[self.dataColIndex]

        # Try to get a description for a potential known packet
        descr = Toolbox.Toolbox.getKnownPacketDescription(CANID, data)

        if len(valueList) == self.packetTableModel.columnCount():
            valueList[-1] = descr
        else:
            valueList.append(descr)

        # Fill the columns with empty data
        while len(valueList) < self.packetTableModel.columnCount():
            valueList.append("")

        # Should be enough values now
        assert len(valueList) == self.packetTableModel.columnCount(
        ), "Lengths must be equal"

        # Make sure the length is OK
        valueList[self.lengthColIndex] = Packet.Packet.getDisplayDataLength(
            CANID, data)

        # Also add the data to the objects rawData element
        if append:
            if addAtFront:
                self.rawData.insert(0, valueList)
            else:
                self.rawData.append(valueList)

        if not addToRawDataOnly:
            self.packetTableModel.appendRow(valueList, addAtFront, emit=emit)
        return descr

    def manualAddPacket(self):
        """
        Manually add an empty packet row to the GUI table. This also updates ``rawData``.
        """

        # Also add the data to the objects rawData element
        self.rawData.append([])
        for colIndex in range(self.packetTableModel.columnCount()):
            self.rawData[-1].append("")

        # Lists are passed by ref so no need to copy the entire list
        self.packetTableModel.appendRow([])

    def removeSelectedPackets(self):
        """
        Remove selected rows from a table and also delete those rows from a ``rawData`` list.
        :return: A list of indexes of the removed rows. None if no rows have been selected
        """

        # We return the indexes of the removed rows
        removedRows = []
        tableModel = self.packetTableModel
        selectionModel = self.packetTableView.selectionModel()
        selectedRows = selectionModel.selectedRows()

        if len(selectedRows) == 0:
            QtGui.QMessageBox.critical(
                self.tabWidget, Strings.messageBoxErrorTitle,
                Strings.rowSelectionHint, QtGui.QMessageBox.Ok)
            return

        # Pass the QModelIndex to the method
        # --> persistent indexes
        tableModel.removeRows(selectedRows)
        # Reverse the delete order --> no need to worry about shifting indexes <:
        for row in sorted(selectedRows, reverse=True):
            rowIndex = row.row()
            # Also delete the row in rawData
            del self.rawData[rowIndex]
            removedRows.append(row.row())

        return removedRows

    def clear(self, returnOldPackets=False):
        """
        Clear the currently displayed data on the GUI and in the rawData list

        :param returnOldPackets: If this is true, then the previously displayed packets will
               be returned as raw data list
        :return: Previously displayed packets as raw data list (if returnOldPackets is True), else an empty list
        """

        self.packetTableModel.clear()
        # Provides the old values for applying new known packets
        savedPackets = []
        if returnOldPackets:
            # This creates a copy of the list (fastest way)
            savedPackets = self.rawData[:]

        # Reset the sniffed packets
        self.rawData = []

        return savedPackets

    def applyNewKnownPackets(self):
        """
        Apply new known packets which have been saved in the mean time. This reloads the packets into the GUI table.
        """

        progressDialog = Toolbox.Toolbox.getWorkingDialog(
            Strings.applyingKnownPackets)
        progressDialog.open()
        try:
            counter = 0
            # Get the saved packets
            self.rawData = self.clear(returnOldPackets=True)
            for rawDataPacket in self.rawData:
                descr = self.addPacket(rawDataPacket, append=False)
                rawDataPacket[self.descriptionColIndex] = descr
                if counter % 1000 == 0:
                    QtCore.QCoreApplication.processEvents()
        finally:
            progressDialog.close()

    def handleCopy(self):
        """
        Handle copying **selected** rows from a GUI table.
        This copies the raw data list **to the clipboard**.
        """

        # Extract the data from the table and copy it to the clipboard as text
        clipboard = QtGui.QApplication.clipboard()
        selectedRawPackets = Toolbox.Toolbox.tableExtractSelectedRowData(
            self.packetTableView)
        clipboard.setText(str(selectedRawPackets))

    def handlePaste(self):
        """
        Handle pasting rows into a GUI table.
        Data is being gathered from the clipboard and be of the following types:
        - Raw data list (list of lists which consist of column data) - Parsing takes place asynchronously
        - SocketCAN format (see :class:`~src.CANData.SocketCANFormat`)
        """

        # First, show a progress dialog because this can take longer
        progressDialog = Toolbox.Toolbox.getWorkingDialog(
            Strings.toolboxImportingPastedData)
        progressDialog.open()

        QtCore.QCoreApplication.processEvents()

        try:
            # Extract the data from the clipboard and iterate over it
            clipboard = QtGui.QApplication.clipboard()
            # Parse the list in memory to a python list
            try:
                pool = Pool(processes=1)
                # We need to pass a tuple of args
                async_result = pool.apply_async(ast.literal_eval,
                                                (clipboard.text(), ))

                refreshCounter = 0
                while not async_result.ready():
                    if refreshCounter % 10000 == 0:
                        QtGui.QApplication.processEvents()
                        refreshCounter = 0
                    refreshCounter += 1

                rawPackets = async_result.get()
            except:
                rawPackets = None

            # First try parsing it as a python list in string format
            if rawPackets is not None:
                # First put it in the GUI table

                if not isinstance(rawPackets, list):
                    return

                self.packetTableModel.appendRows(rawPackets)
                refreshCounter = 0
                # Also update rawData
                for row in rawPackets:
                    if refreshCounter % 10000 == 0:
                        QtCore.QCoreApplication.processEvents()
                        refreshCounter += 1
                    self.rawData.append(row)
                    refreshCounter = 0

            # Last try: try parsing in SocketCAN format
            else:
                socketCANPackets = CANData.CANData.parseSocketCANLines(
                    clipboard.text().split("\n"))
                if len(socketCANPackets) > 0:
                    for socketCANPacketIndex in range(len(socketCANPackets)):

                        if socketCANPacketIndex % 700 == 0:
                            QtCore.QCoreApplication.processEvents()

                        socketCANPacket = socketCANPackets[
                            socketCANPacketIndex]
                        CANID = socketCANPacket.id
                        data = socketCANPacket.data
                        timestamp = socketCANPacket.timestamp

                        dataList = []

                        # Append the data to the GUI table and to the rawData list
                        # Prepare the datalist
                        for colIdx in range(
                                self.packetTableModel.columnCount()):
                            dataList.append("")
                        dataList[self.IDColIndex] = CANID
                        dataList[self.dataColIndex] = data
                        dataList[self.timestampColIndex] = timestamp
                        self.packetTableModel.appendRow(dataList)
                        self.rawData.append(dataList)

        except Exception as e:
            self.logger.exception(str(e))
            progressDialog.close()
        finally:
            progressDialog.close()

    def handleRightCick(self):
        """
        This spawns a custom context menu right next to the cursor if a user has right clicked on a table cell.
        """

        import SenderTab
        import Globals

        # First create a new menu object and add items as needed
        menu = QtGui.QMenu()

        sendToSender = None
        if self.sendToSenderContextMenu:
            sendToSender = menu.addAction(Strings.contextMenuSendToSender)

        saveAsPacketSet = None
        if self.saveAsPacketSetContextMenu:
            saveAsPacketSet = menu.addAction(
                Strings.contextMenuSaveAsPacketSet)

        # Get the users input
        action = menu.exec_(QtGui.QCursor.pos())

        # Execute accordingly
        if action == sendToSender:

            if self.rawData is None or len(self.rawData) == 0:
                return
            SenderTab.SenderTab.addSenderWithData(
                listOfRawPackets=self.rawData)

        elif action == saveAsPacketSet:
            if self.rawData is None or len(self.rawData) == 0:
                return
            Globals.managerTabInstance.createDump(rawPackets=self.rawData)

    def handleCellChanged(self, rowIndex, colIndex):
        """
        To update the rawData element and
        to put the length of the changed data field into the length field.

        :param rowIndex: The changed row
        :param colIndex: The changed column
        :return:
        """

        item = self.packetTableModel.getValue(rowIndex, colIndex)
        if item is not None:
            self.rawData[rowIndex][colIndex] = self.packetTableModel.getValue(
                rowIndex, colIndex)

        # Only if the id or data column has changed (--> if values are present)
        # This makes sure that the length column is always != Null
        if colIndex == self.dataColIndex or colIndex == self.IDColIndex:
            CANID = self.packetTableModel.getValue(rowIndex, self.IDColIndex)
            data = self.packetTableModel.getValue(rowIndex, self.dataColIndex)
            length = self.packetTableModel.getValue(rowIndex,
                                                    self.lengthColIndex)

            # Update the length
            if data is not None and length is not None:

                # Must be even --> bytes!
                if len(data) % 2 == 0:
                    dataLengthRes = str(len(data) // 2)
                else:
                    dataLengthRes = Strings.toolboxInvalidLength

                # Don't display a 0 when there's no data and no ID
                if data == "" and CANID == "":
                    dataLengthRes = ""

                self.packetTableModel.setText(rowIndex, self.lengthColIndex,
                                              dataLengthRes)
                # Update this value in rawData too
                self.rawData[rowIndex][self.lengthColIndex] = 0

            # Update the description
            descr = Toolbox.Toolbox.getKnownPacketDescription(CANID, data)
            self.packetTableModel.setText(rowIndex, self.descriptionColIndex,
                                          descr)

    def handleInterfaceSettingsDialog(self, allowOnlyOwnInterface=False):
        """
        Open a dialog to change interface settings and set the updated CANData instance.

        :param allowOnlyOwnInterface: If this is true, you can only edit the CANData instance that is already selected
                                      for the current tab. This is being used for the sniffer tabs.
        """

        newCANData = Toolbox.Toolbox.interfaceSettingsDialog(
            self.CANData, [self.CANData] if allowOnlyOwnInterface else None)
        if newCANData is not None:
            self.updateCANDataInstance(newCANData)

    def updateInterfaceLabel(self):
        """
        Set the text of the interface label to the updated value, if the label is present.
        Uses the text "None" if no interface is set.
        """

        if self.labelInterfaceValue is None:
            return

        self.labelInterfaceValue.setText(
            self.CANData.toString() if self.CANData is not None else "None")

    def updateCANDataInstance(self, CANDataInstance):
        """
        Updates the tab specific CANData instance to the passed parameter.
        This only takes place if the tab is not active to prevent errors.
        This also calls :func:`updateInterfaceLabel` to update the label.

        :param CANDataInstance: The new CANData instance
        """

        if not self.active:
            self.CANData = CANDataInstance
        Toolbox.Toolbox.updateInterfaceLabels()
        self.toggleGUIElements(self.CANData is not None)

    def setInitialCANData(self):
        """
        Try to get initial an initial CANData instance.
        This method also updates GUI elements.

        :return: A boolean value which indicates the success
        """

        self.CANData = CANData.CANData.getGlobalOrFirstInstance()
        if self.CANData is not None:
            self.toggleGUIElements(True)
            self.updateInterfaceLabel()
            return True
        else:
            self.CANData = None
            self.toggleGUIElements(False)
            return False

    #: Dummies, overriden by subclasses if needed
    def toggleGUIElements(self, state):
        pass
