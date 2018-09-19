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

from multiprocessing import Process
from Logger import Logger
import Strings
import Globals


class SnifferProcess(Process):

    """
    Spawn a new process that will sniff packets from the specified CANData instance.
    Captured data will be transmitted via the ``snifferSendPipe``.
    """

    def __init__(self, snifferSendPipe, sharedEnabledFlag, snifferName, CANData=None):
        """
        Set the passed parameters.

        :param snifferSendPipe: The multiprocessing pipe to send received data to
        :param sharedEnabledFlag: The multiprocessing value to handle disabling
        :param snifferName: The name of the sniffer process, used for logging
        :param CANData: Optional: The CANData instance to query for data.
                        If this is not specified, the global interface is being used
        """

        Process.__init__(self)
        self.CANData = CANData if CANData is not None else Globals.CANData
        self.snifferSendPipe = snifferSendPipe
        self.sharedEnabledFlag = sharedEnabledFlag
        self.snifferName = snifferName

        self.logger = Logger(Strings.snifferProcessLoggerName +
                             " (" + self.snifferName + ")").getLogger()

    def run(self):
        """
        As long as the process hasn't been disabled: Read a frame using :func:`~src.CANData.CANData.readPacketAsync`
        and transmit the received pyvit frame via the pipe.
        """
        errorCount = 0
        while self.sharedEnabledFlag.value == 1:
            # This will either return a packet or None (timeout)
            try:
                frame = self.CANData.readPacketAsync()
            except OSError:
                if errorCount % 10000 == 0:
                    self.logger.error(Strings.OSError +
                                      " (" + self.snifferName + ")")
                    errorCount = 1
                errorCount += 1

            if frame is not None:
                self.snifferSendPipe.send(frame)
