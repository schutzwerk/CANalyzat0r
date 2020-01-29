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
import operator
from PySide.QtCore import Qt
import re

import Packet
import Toolbox
from PySide import QtCore

# With guidance from:
# https://www.daniweb.com/programming/software-development/code/447834/applying-pyside-s-qabstracttablemodel


class PacketTableModel(QtCore.QAbstractTableModel, QtCore.QObject):

    """
    A custom TableModel is needed to allow efficient handling of **many** values.
    """

    #: Emits rowIndex and columnIndex of the changed cell
    cellChanged = QtCore.Signal(int, int)

    def __init__(self,
                 parent,
                 dataList,
                 header,
                 readOnlyCols,
                 IDColIndex=1,
                 dataColIndex=2,
                 lengthColIndex=3,
                 timestampColIndex=4,
                 descriptionColIndex=5,
                 *args):

        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.parent = parent
        self.dataList = dataList
        self.header = header
        self.readOnlyCols = readOnlyCols

        self.IDColIndex = IDColIndex
        self.dataColIndex = dataColIndex
        self.lengthColIndex = lengthColIndex
        self.timestampColIndex = timestampColIndex
        self.descriptionColIndex = descriptionColIndex

    def columnCount(self, parent=None):
        """
        Returns the current column count by returning the length of the header list.

        :param parent: Dummy parameter to keep the needed signature
        :return: The column count as integer
        """

        return len(self.header)

    def rowCount(self, parent=None):
        """
        Returns the current row count by returning the length of the data list.

        :param parent: Dummy parameter to keep the needed signature
        :return: The row count as integer
        """

        return len(self.dataList)

    def setRowCount(self, count):
        """
        Sets the row count by removing lines / adding empty lines.
        This also emits the ``layoutChanged`` signal to let the GUI know that the layout has been changed.

        :param count: The desired amount of rows
        """

        # If additional rows are needed
        if count > len(self.dataList):
            while len(self.dataList) < count:
                self.dataList.append([])
                # Fill the columns with empty data
                for colIndex in range(self.columnCount()):
                    self.dataList[-1].append("")
        # Rows have to be removed
        elif count < len(self.dataList):
            while len(self.dataList) > count:
                self.dataList.pop()

        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def clear(self):
        """
        Clears all managed data from the ``dataList``.
        This is a shortcut to :func:`setRowCount` with parameter ``0``.
        """

        self.dataList = []
        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def appendRow(self, dataList=[], addAtFront=False, emit=True, resolveDescription=False):
        """
        Inserts the ``dataList`` list into ``self.dataList`` to add a whole row with values at once.

        :param dataList: The list containing data. The length must be equal to :func:`rowCount`.
        :param addAtFront: Values will be added to the front of ``self.dataList`` if this is True.
                           Else: They will be appended at the end
        :param emit: Optional: If the GUI will be notified of the data change or not. This is used for batch
                               imports where the GUI isn't notified after each row to increase speed
                               Default: True (Emit everytime)
        :param resolveDescription: If this is set to True, the description of the potential known packet will
                                   be resolved. Default: False

        :return: The description of the known packet. If ``resolveDescription`` is False, an empty string is returned.
                 Else None.

        This also emits the ``dataChanged`` and ``layoutChanged`` signals to let the GUI know that
        the data/layout has been changed.
        """

        if not isinstance(dataList, list):
            return

        # Fill the columns with empty data
        while len(dataList) < self.columnCount():
            dataList.append("")

        assert len(dataList) == self.columnCount(), "Invalid data list length"

        if resolveDescription:
            description = Toolbox.Toolbox.getKnownPacketDescription(dataList[0],
                                                                    dataList[1])
            dataList[self.descriptionColIndex] = description

        # Set the length
        dataList[self.lengthColIndex] = str(Packet.Packet.getDisplayDataLength(dataList[self.IDColIndex],
                                                                               dataList[self.dataColIndex]))

        if addAtFront:
            self.dataList.insert(0, dataList[:])
        else:
            # Slice --> insert a copy to avoid the references being all the same
            self.dataList.append(dataList[:])

        for colIndex in range(len(self.header)):
            if emit:
                self.dataChanged.emit(self.rowCount(), colIndex)
                self.cellChanged.emit(self.rowCount(), colIndex)

        if emit:
            self.emit(QtCore.SIGNAL("layoutChanged()"))

        if resolveDescription:
            return description
        else:
            return None

    def appendRows(self, rowList, addAtFront=False, resolveDescriptions=True):
        """
        This allows appending a whole set of rows at once using the best possible speed

        :param rowList: List of raw data lists to append
        :param addAtFront: Values will be added to the front of ``self.dataList`` if this is True.
                           Else: They will be appended at the end
        :param resolveDescriptions: If this is set to true, the description for every packet will be resolved.
                                    Default: True

        :return: If ``resolveDescriptions`` is True, a list of known packet descriptions will be returned. If no
                 description for a particular packet can be resolved, an empty string will be inserted in the list
                 to keep indexes. Else None will be returned
        """

        self.emit(QtCore.SIGNAL("beginInsertRows()"), QtCore.QModelIndex(),
                  self.rowCount(), self.rowCount() + len(rowList))
        descriptions = []

        for rowIdx in range(len(rowList)):
            # Only notify the layout after every X rows
            doEmit = rowIdx < 10 or rowIdx % 10000 == 0

            if doEmit:
                QtCore.QCoreApplication.processEvents()

            while len(rowList[rowIdx]) < self.columnCount():
                rowList[rowIdx].append("")

            if resolveDescriptions:
                descriptions.append(self.appendRow(
                    rowList[rowIdx], addAtFront, emit=doEmit, resolveDescription=True))
            else:
                self.appendRow(rowList[rowIdx], addAtFront, emit=doEmit)

            if doEmit:
                QtCore.QCoreApplication.processEvents()

        self.emit(QtCore.SIGNAL("endInsertRows()"))
        self.emit(QtCore.SIGNAL("layoutChanged()"))

        if resolveDescriptions:
            return descriptions

        else:
            return None

    def insertRow(self, dataList=[]):
        """
        This is just an alias to :func:`appendRow` for compatibility.

        :param dataList: A list that stores the data that will be added
        """

        self.appendRow(dataList)

    def removeRow(self, rowIndex):
        """
        Removes the specified row from the table model.
        This also emits the ``layoutChanged`` signal to let the GUI know that the layout has been changed.

        :param rowIndex: The row index to delete
        """

        del self.dataList[rowIndex]
        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def removeRows(self, rowIndexes):
        """
        Remove multiple rows at once.

        :param rowIndexes: The rows that will be deleted
        """

        # Make the indexes persistent first to be able to
        # delete multiple selections at once
        persistentRowIndexes = []
        # Reverse the delete order --> no need to worry about shifting indexes <:
        for rowIndex in sorted(rowIndexes, reverse=True):
            persistentRowIndexes.append(QtCore.QPersistentModelIndex(rowIndex))

        for persistentRowIndex in persistentRowIndexes:
            self.removeRow(persistentRowIndex.row())

    def data(self, index, role):
        """
        Return managed data depending on the ``role`` parameter.

        :param index: Index object containing row and column index
        :param role: The display role that requests data
        :return:
         - If the index is invalid: None
         - ``AlignCenter`` if ``role = TextAlignmentRole``
         - Column data if ``role = DisplayRole`` or ``EditRole``
        """

        if not index.isValid():
            return None
        elif role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter

        elif role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            rowIndex = index.row()
            colIndex = index.column()

            if len(self.dataList) - 1 >= rowIndex:
                try:
                    return self.dataList[rowIndex][colIndex]
                except IndexError:
                    return None
            else:
                return None

        return None

    def getValue(self, rowIndex, colIndex):
        """
        Get the data from the table at the given indexes.

        :param rowIndex: Row index
        :param colIndex: Column index
        :return: The data at the specified index (if possible); Else None
        """

        if len(self.dataList) - 1 >= rowIndex:
            try:
                return self.dataList[rowIndex][colIndex]
            except IndexError:
                return None
        else:
            return None

    def setText(self, rowIndex, colIndex, data):
        """
        Sets the text of at the given indexes.
        If ``data`` is None the text will be an empty string.
        This method also emits the ``dataChanged`` and ``layoutChanged`` signals to let the GUI know that
        the data/layout has been changed.

        :param rowIndex: Row index
        :param colIndex: Column index
        :param data: New data for the column
        """

        if data is None:
            data = ""
        data = str(data)

        if len(self.dataList) - 1 >= rowIndex and \
                len(self.dataList[rowIndex]) - 1 >= colIndex:

            self.dataList[rowIndex][colIndex] = data
            self.cellChanged.emit(rowIndex, colIndex)
            self.dataChanged.emit(rowIndex, colIndex)
            self.emit(QtCore.SIGNAL("layoutChanged()"))

    def setData(self, index, value, role=Qt.EditRole):
        """
        This gets called to change the element on the GUI at the given indexes
        This also emits the ``layoutChanged`` signal to let the GUI know that the layout has been changed.

        :param index: Index object containing row and column index
        :param value: The new value
        :param role: Optional: The role calling this method. Default: EditRole
        :return: True if the operation succeeded
        """

        rowIndex = index.row()
        colIndex = index.column()
        value = re.sub("[^A-Fa-f0-9]+", "", str(value)).upper()
        self.dataList[rowIndex][colIndex] = value

        self.cellChanged.emit(rowIndex, colIndex)
        self.dataChanged.emit(rowIndex, colIndex)
        self.emit(QtCore.SIGNAL("layoutChanged()"))
        return True

    def headerData(self, headerIndex, orientation, role):
        """
        Returns the header data to properly display the managed data on the GUI.

        :param headerIndex: Which column of the data is requested
        :param orientation: This can be either ``Horizontal`` or ``Vertical``:

                              - ``Horizontal``: Return a value from ``self.header``
                              - ``Vertical``: Return the ``headerIndex``

        :param role: This is always expected to be ``DisplayRole``
        :return: See ``orientation``. None is returned if ``orientation`` or ``role`` do not match
        """

        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[headerIndex]
        elif orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return headerIndex
        return None

    def sort(self, colIndex, order):
        """
        Sort the data by given column number.
        This also emits the ``layoutChanged`` signal to let the GUI know that the layout has been changed.

        :param colIndex: The column index to sort for
        :param order: Either ``DescendingOrder`` or ``AscendingOrder``
        """

        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        self.dataList = sorted(self.dataList,
                               key=operator.itemgetter(colIndex))
        if order == QtCore.Qt.DescendingOrder:
            self.dataList.reverse()
        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def flags(self, index):
        """
        Return the flags for cell at a given index.

        :param index: Index object containing row and column index
        :return: A flags object containing whether an object is editable, selectable or enabled
        """

        flags = super(self.__class__, self).flags(index)
        if index.column() not in self.readOnlyCols:
            flags |= Qt.ItemIsEditable
        flags |= Qt.ItemIsSelectable
        flags |= Qt.ItemIsEnabled
        return flags
