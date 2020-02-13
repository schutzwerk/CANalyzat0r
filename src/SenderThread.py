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
Created on Jun 08, 2017

@author: pschmied
"""

import time

import Globals
import Strings
from PySide import QtCore
from Logger import Logger


class LoopSenderThread(QtCore.QThread):
    """
    Spawns a new thread that will send the passed packets in a loop.
    """

    def __init__(self, packets, sleepTime, CANData, threadName):
        QtCore.QThread.__init__(self)
        self.packets = packets
        self.sleepTime = sleepTime
        self.CANData = CANData
        self.threadName = threadName
        self.enabled = True

        self.logger = Logger(Strings.senderThreadLoggerName + " (" +
                             self.threadName + ")").getLogger()

    def run(self):
        """
        Send the packets in a loop and wait accordingly until the thread is disabled.
        """

        errorCount = 0
        slept = 0
        # Send until the thread gets terminated
        while self.enabled:
            for packet in self.packets:
                if not self.enabled:
                    return

                slept = 0
                try:
                    self.CANData.sendPacket(packet)
                except OSError:
                    if errorCount % 10000 == 0:
                        self.logger.error(Strings.OSError)
                        errorCount = 1
                    errorCount += 1

                while slept < self.sleepTime:
                    if not self.enabled:
                        return
                    time.sleep(0.1)
                    slept += 0.1

    def disable(self):
        """
        This sets the ``enabled`` flag to False which causes the main loop to terminate.
        """

        self.enabled = False


####


class FuzzSenderThread(QtCore.QThread):
    """
    Spawns a new thread that will send random data in a loop.
    """

    def __init__(self, sleepTime, fuzzerSendPipe, CANData, threadName):
        QtCore.QThread.__init__(self)
        self.sleepTime = sleepTime
        self.fuzzerSendPipe = fuzzerSendPipe
        self.CANData = CANData
        self.threadName = threadName
        self.enabled = True

        self.logger = Logger(Strings.fuzzSenderThreadLoggerName + " (" +
                             self.threadName + ")").getLogger()

    def run(self):
        """
        Send the packets in a loop and wait accordingly until the thread is disabled.
        """
        errorCount = 1
        slept = 0
        while self.enabled:
            slept = 0
            packet = Globals.fuzzerTabInstance.generateRandomPacket()
            if packet is None:
                continue

            # Building the packet worked -- let's send
            try:
                self.CANData.sendPacket(packet)
            except OSError:
                if errorCount % 10000 == 0:
                    self.logger.error(Strings.OSError)
                    errorCount = 1
                errorCount += 1

            # Also send the data over the pipe to add it on the GUI
            self.fuzzerSendPipe.send(packet)

            while slept < self.sleepTime:
                if not self.enabled:
                    return

                time.sleep(0.1)
                slept += 0.1

    def disable(self):
        """
        This sets the ``enabled`` flag to False which causes the main loop to terminate.
        """

        self.enabled = False

####


class UDSSenderThread(QtCore.QThread):
    """
    Spawns a new thread that will send sequential UDS packets in a loop.
    """

    def __init__(self, UDSTab, sleepTime, UDSSendPipe, CANData, threadName):
        QtCore.QThread.__init__(self)
        self.UDSTab = UDSTab
        self.sleepTime = sleepTime
        self.UDSSendPipe = UDSSendPipe
        self.CANData = CANData
        self.threadName = threadName
        self.enabled = True

        self.logger = Logger(Strings.UDSSenderThreadLoggerName + " (" +
                             self.threadName + ")").getLogger()


    def run(self):
        """
        Send the packets in a loop and wait accordingly until the thread is disabled.
        """
        errorCount = 1
        slept = 0
        done = False
        packet = None
        while self.enabled and not done:
            slept = 0
            done, packet = Globals.UDSTabInstance.generateNextUDSPacket(packet)
            if packet is None:
                continue

            # Building the packet worked -- let's send
            try:
                self.CANData.sendPacket(packet)
            except OSError:
                if errorCount % 10000 == 0:
                    self.logger.error(Strings.OSError)
                    errorCount = 1
                errorCount += 1

            # Also send the data over the pipe to add it on the GUI
            self.UDSSendPipe.send(packet)

            if done:
                # Tell the GUI that we're finished
                self.UDSTab.toggleUDSFuzzing()
                # disable this thread
                self.disable()
                continue

            while slept < self.sleepTime:
                if not self.enabled:
                    return

                time.sleep(0.1)
                slept += 0.1


    def disable(self):
        """
        This sets the ``enabled`` flag to False which causes the main loop to terminate.
        """

        self.enabled = False
