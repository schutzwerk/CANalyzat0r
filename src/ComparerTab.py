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
Created on Jun 30, 2017

@author: pschmied
"""

from PySide import QtGui
import Strings
from AbstractTab import AbstractTab


class ComparerTab(AbstractTab):
    """
    This handles the logic of the comparer tab.
    """

    def __init__(self, tabWidget):
        """
        This just sets data and adds click handlers.
        """

        AbstractTab.__init__(
            self,
            tabWidget,
            Strings.comparerTabLoggerName, [2, 3, 4],
            Strings.comparerTabPacketViewName,
            allowTablePaste=False)

        self.rawPacketSet1 = []
        self.rawPacketSet2 = []

        # Get all GUI elements
        self.buttonComparerLoadSet1 = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonComparerLoadSet1")
        self.buttonComparerLoadSet2 = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonComparerLoadSet2")
        self.buttonComparerStartCompare = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonComparerStartCompare")

        assert all(GUIElem is not None for GUIElem in [
            self.buttonComparerLoadSet1,
            self.buttonComparerLoadSet2,
            self.buttonComparerStartCompare,
        ]), "GUI Elements not found"

        self.buttonComparerLoadSet1.clicked.connect(self.setPacketSet1)
        self.buttonComparerLoadSet2.clicked.connect(self.setPacketSet2)
        self.buttonComparerStartCompare.clicked.connect(self.compare)

        self.prepareUI()

    def setPacketSet1(self):
        """
        Opens a :class:`~src.PacketsDialog.PacketsDialog` to load packet set 1 into ``rawPacketSet1``.
        """

        newValue = self.getPacketSet(self.rawPacketSet1)
        # Only if the user didn't press cancel
        if newValue is not None:
            self.rawPacketSet1 = newValue

    def setPacketSet2(self):
        """
        Opens a :class:`~src.PacketsDialog.PacketsDialog` to load packet set 2 into ``rawPacketSet2``.
        """

        newValue = self.getPacketSet(self.rawPacketSet2)
        # Only if the user didn't press cancel
        if newValue is not None:
            self.rawPacketSet2 = newValue

    def getPacketSet(self, rawPacketList):
        """
        Opens a :class:`~src.PacketsDialog.PacketsDialog` to load selected packets into the passed raw packet list.

        :param rawPacketList: The raw packet list
        """

        from PacketsDialog import PacketsDialog
        packetsDialog = PacketsDialog(rawPacketList=rawPacketList)
        return packetsDialog.open()

    def compare(self):
        """
        Compares ``rawPacketSet1`` and ``rawPacketSet2`` and display the packet they have in common on the GUI.
        """

        if len(self.rawPacketSet1) == len(self.rawPacketSet2) == 0:
            return

        # Remove the timestamp
        for rawList in [self.rawPacketSet1, self.rawPacketSet2]:
            for rawElement in rawList:
                rawElement[self.timestampColIndex] = ""

        self.clear()
        # Compare using sets of tuples --> Performance over 9000!!1!
        rawPacketSetSets1 = set(
            tuple(rawPacket) for rawPacket in self.rawPacketSet1)
        rawPacketSetSets2 = set(
            tuple(rawPacket) for rawPacket in self.rawPacketSet2)

        resultSets = list(rawPacketSetSets1 & rawPacketSetSets2)
        result = [list(resultSet) for resultSet in resultSets]

        self.packetTableModel.appendRows(result)
        self.rawData = result
