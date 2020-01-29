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

from PySide import QtCore
import can


class ItemAdderThread(QtCore.QThread):
    """
    This thread receives data from a process and
    emits a signal which causes the main thread to add the packets
    to the table.
    """

    #: Emit a signal to the main thread when items are ready to be added
    #: Parameters: valueList
    appendRow = QtCore.Signal(list)

    def __init__(self, receivePipe, tableModel, rawData, useTimestamp=True):
        # Call the superclass constructor
        QtCore.QThread.__init__(self)
        # Attributes to manage the sniffer process
        self.receivePipe = receivePipe
        self.tableModel = tableModel
        self.useTimestamp = useTimestamp
        self.rawData = rawData
        self.enabled = True

    def frameToRow(self, frame):
        """
        Converts a can.Message object to a raw value list. This list will be emitted using the signal
        ``appendRow`` along with the table data and rawData list.

        :param frame: can.Message CAN frame
        """

        # Extract the data to be displayed
        id = str(hex(frame.arbitration_id)).replace("0x", "").upper()

        if len(id) <= 3:
            neededLength = 3
        else:
            neededLength = 8

        while len(id) < neededLength:
            id = "0" + id

        # cut "0x" and always use an additional leading zero if needed
        data = "".join(hex(value)[2:].zfill(2) for value in frame.data).upper()
        length = frame.dlc
        timestamp = str(frame.timestamp) if frame.timestamp is not None else ""

        values = [id, data, length]
        if self.useTimestamp:
            values.append(timestamp)

        self.appendRow.emit(values)

    def disable(self):
        """
        This sets the enabled flag to False which causes the infinite loop in :func:`run` to exit.
        """

        self.enabled = False

    def run(self):
        """
        As long as the thread is enabled: Receive a frame from the pipe and pass it to :func:`frameToRow`.
        """

        while self.enabled:
            frame = None
            try:
                # Receive data from a process via a pipe
                if self.receivePipe.poll(1):
                    frame = self.receivePipe.recv()
            except EOFError:
                continue
            if frame is not None:
                self.frameToRow(frame)
