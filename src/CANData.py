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
Created on May 17, 2017

@author: pschmied
"""
from pyvit import can
from pyvit.hw import socketcan
from socket import timeout as TimeoutException
import subprocess
import os
import socket
import select

from Logger import Logger
import Globals
import Strings
import Toolbox


class CANData():

    #: This dictionary stores all currently available CANData instances. The key
    #: of the dictionary is the interface name
    CANDataInstances = {}

    #: Class specific logger instance
    logger = Logger(Strings.CANDataLoggerName).getLogger()

    def __init__(self, ifaceName, bitrate=500000):
        """
        This method initializes the pyvit CAN interface using the passed parameters and the start() method.
        Please note the active-flag which protects the object from being deleted while being in use.

        :param ifaceName: Name of the interface as displayed by ``ifconfig -a``
        :param bitrate: Desired bitrate of the interface
        """

        self.ifaceName = ifaceName
        self.VCAN = self.checkVCAN()

        self.bitrate = bitrate if not self.VCAN else -1

        self.iface = socketcan.SocketCanDev(ifaceName)
        self.updateBitrate(bitrate)

        #: 100 ms read timeout for async reads (see :func:`readPacketAsync`)
        self.timeout = 0.1

        self.active = False
        self.iface.start()

    def clearSocket(self):
        """
        Clear the socket by reading and discarding all contained data
        Fixes #4
        """

        sock = [self.iface.socket]
        while True:
            available, _, _ = select.select(sock, [], [], 0.0)
            if len(available) == 0: return
            for b in available:
                b.recv(1)

    def sendPacket(self, packet):
        """
        Sends a packet using the SocketCAN interface.

        :param packet: A packet as pyvit frame (see :func:`tryBuildPacket`)
        """

        assert self.iface is not None
        self.iface.send(packet)

    def readPacket(self):
        """
        Read a packet from the queue using the SocketCAN interface.
        Note: This blocks as long as no packet is being received.
        You can use :func:`readPacketAsync` to read
        packets with a timeout.

        :return: A packet as pyvit frame
        """

        self.iface.socket.settimeout(0)
        return self.iface.recv()

    def readPacketAsync(self):
        """
        Read a packet from the queue using the SocketCAN interface **and a timeout**.

        :return: A packet as pyvit frame or None of no packet was received
        """

        # If no packet is received within timeout second --> break
        # this is used to be able to stop sniffing processes which will then
        # use nonblocking recv-calls
        self.iface.socket.settimeout(self.timeout)
        # If no packet is received withing the timeout
        # return no data
        try:
            return self.iface.recv()
        except TimeoutException:
            return None

    def toString(self):
        """
        Return a string to display the currently used settings and interface name on the GUI

        :return: A string which consists of either: The interface name (for virtual CAN devices where no bitrate is available)
                 or the interface name along with the currently used bitrate in kBit/s
        """

        if self.VCAN:
            return self.ifaceName

        else:
            return self.ifaceName + " (" + str(
                self.bitrate / 1000) + " kBit/s)"

    def checkVCAN(self):
        """
        Checks if the SocketCAN device is physical or virtual using a ``ls`` call to ``/sys/devices/virtual/net``.

        :return: A boolean value indicating if the device is virtual (True) or not (False)
        """

        virtualIfaces = os.listdir("/sys/devices/virtual/net")
        for virtualIface in virtualIfaces:
            if virtualIface == self.ifaceName:
                CANData.logger.info(Strings.CANDataDetectedVirtualInterface +
                                    self.ifaceName)
                return True
        return False

    def updateBitrate(self, bitrate):
        """
        Updates the bitrate of the SocketCAN interface (if possible).

        :param bitrate: The desired bitrate in bit/s
        :return: A boolean value indicating success of updating the bitrate value
        """

        # Physical CAN or virtual CAN ?
        if not self.VCAN:
            # Put interface down first so the new bitrate can be applied
            cmd = "ip link set " + self.ifaceName + " down"
            output, error = Toolbox.Toolbox.runRootshell(cmd)
            # prepare cmd for next call
            cmd = "ip link set " + self.ifaceName + \
                " up type can bitrate " + str(bitrate)

        else:
            cmd = "ip link set up " + self.ifaceName

        # Apply
        output, error = Toolbox.Toolbox.runRootshell(cmd)
        if output.decode("utf-8") == "" and error.decode("utf-8") == "":
            if self.VCAN:
                self.bitrate = -1
            else:
                self.bitrate = bitrate

            self.iface = socketcan.SocketCanDev(self.ifaceName)
            self.iface.start()

            return True

        else:
            CANData.logger.error(error.decode("utf-8"))
            return False

    @staticmethod
    def getGlobalOrFirstInstance():
        """
        Tries to return an available CANData instance (e.g. for startup of the application).

        :return:
         - The global CANData instance if available.
         - Else: The first element of all available instances.
         - Else: None of no interface is present
        """

        try:
            return Globals.CANData if Globals.CANData is not None else \
                sorted(list(CANData.CANDataInstances.values()),
                       key=lambda x: x.ifaceName)[0]
        except IndexError:
            CANData.logger.debug(Strings.CANDataNoInstanceAvailable)
            return None

    @staticmethod
    def tryBuildPacket(CANID, data):
        """
        Builds a pyvit frame using the passed parameters.
        This method automatically uses the extended CAN format if needed.

        :param CANID: The CAN ID as hex string
        :param data: The desired packet data (length must be even)
        :return: A packet as pyvit frame containing the passed data or None of no frame can be created
        """

        assert len(data) % 2 == 0, "the data length has to be even"

        arbID = int(CANID, 16)
        data = list(bytearray.fromhex(data))

        try:
            # Convert id to hexvalue
            # Convert data to list of bytes
            packet = can.Frame(arb_id=arbID, data=data)
        except ValueError:

            # Uh oh, try to create an extended packet
            try:
                packet = can.Frame(
                    arb_id=arbID, data=data, is_extended_id=True)
            except TypeError:

                # The flag to mark an extended packet was changed in some git commit - try that
                try:
                    packet = can.Frame(arb_id=arbID, data=data, extended=True)
                except Exception as e:
                    CANData.logger.error(Strings.packetBuildError + ": " +
                                         str(e))
                    return None

        return packet

    @staticmethod
    def readCANFile(filePath):
        """
        Reads a file in SocketCAN format (as generated by candump from can-utils)
        and returns a list of SocketCANPacket objects (see :class:`~src.CANData.SocketCANPacket`).

        :param filePath: The path of the dump file that has to be read
        :return: A list of SocketCANPackets
        """

        packets = []
        with open(filePath) as f:
            lines = f.readlines()
        # Remove \n at the end of each line
        lines = [line.strip() for line in lines]
        packets = CANData.parseSocketCANLines(lines)

        return packets

    @staticmethod
    def parseSocketCANLines(lines):
        """
        Parses a list of SocketCAN lines  and generates a list of SocketCANPackets.
        Note: The expected line format is e.g.:

        ``(1493280437.565631) can0 1FD#0000000000000000``

        :param lines: List of lines in SocketCAN format
        :return: List of SocketCANPacket objects
        """

        socketCANPackets = []

        for line in lines:
            # Check for 3 columns (Timestamp, Iface, (ID#Data))
            if len(line.split(" ")) < 3:
                if line == "":
                    line = Strings.CANDataParseSocketCANEmptyLine
                CANData.logger.warning(Strings.CANDataInvalidSocketCANLine +
                                       ": " + line)
            else:
                valueList = line.split(" ")
                # Remove ( and )
                curTimestamp = valueList[0].replace("(", "").replace(")", "")
                curIface = valueList[1]
                IDAndData = valueList[2].split("#")
                if len(IDAndData) == 2:
                    curID = IDAndData[0]
                    curData = IDAndData[1]
                    socketCANPacket = SocketCANPacket(curTimestamp, curIface,
                                                      curID, curData)
                    socketCANPackets.append(socketCANPacket)
                else:
                    CANData.logger.warning(
                        Strings.CANDataInvalidSocketCANLine + ": " + line)

        return socketCANPackets

    @staticmethod
    def writeCANFile(filePath, packets):
        """
        Writes/Exports SocketCANPacket objects to a textfile.

        :param filePath: Path of the file to be saved to
        :param packets: List of SocketCANPacket objects
        """

        # Open or create
        with open(filePath, "w+") as dumpFile:
            for socketCANPacket in packets:
                dumpFile.write(socketCANPacket.toString() + "\n")

    @staticmethod
    def createCANDataInstance(ifaceName, bitrate=500000, returnObject=False):
        """
        Creates a CANData instance with the desired data and either returns the object
        or adds it to the CANDataInstances dictionary.

        :param ifaceName: The desired interface name
        :param bitrate: The bitrate
        :param returnObject: Boolean value indicating whether the created object will be
               returned or appended to the dictionary (XOR)
        :return: The created CANData object if returnObject is True
        """

        if ifaceName not in CANData.CANDataInstances:
            newCANData = CANData(ifaceName, bitrate)

            # Used to rebuild the dict
            if returnObject:
                return newCANData
            else:
                CANData.CANDataInstances[ifaceName] = newCANData
        return None

    @staticmethod
    def deleteCANDataInstance(ifaceName):
        """
        Removes a CANData object from the CANDataInstances dictionary.
        Note: CANData objects only will be deleted if the active flag is set to False
        to prevent running operations from failing.

        :param ifaceName: The name of the interface that will be deleted
        :return: A Boolean value indicating the success of the delete operation
        """

        try:
            if CANData.CANDataInstances[ifaceName].active:
                CANData.logger.error(Strings.CANDataCantExecuteInterfaceActive)
                return False
            del CANData.CANDataInstances[ifaceName]
            return True
        except KeyError:
            CANData.logger.error(Strings.CANDataCantExecuteNoSuchInterface +
                                 ifaceName)
            return False

    @staticmethod
    def rebuildCANDataInstances(CANIfaceNameList):
        """
        Refreshes the CANDataInstances dictionary with up-to-date values using the parameter CANIfaceNameList.
        Old objects will be kept, new ones will be created and missing ones will be deleted.

        :param CANIfaceNameList: Names of interfaces that must be present in the dictionary after this method
        :return: A list of removed interface names to handle the consequences of deleting an object.
        """

        tmpDict = {}
        for CANIfaceName in CANIfaceNameList:
            # Object already present, keep it --> running threads won't have problems
            if CANIfaceName in CANData.CANDataInstances:
                tmpDict[CANIfaceName] = CANData.CANDataInstances[CANIfaceName]

            # Object not present, create a new one
            else:
                newCANData = CANData.createCANDataInstance(
                    CANIfaceName, returnObject=True)
                if newCANData is not None:
                    tmpDict[CANIfaceName] = newCANData
                    CANData.logger.info(Strings.CANDataNewInterfaceAdded +
                                        CANIfaceName)

        removedInterfaceNames = []
        for CANDataInstanceName in list(CANData.CANDataInstances.keys()):
            if CANDataInstanceName not in tmpDict:
                removedInterfaceNames.append(CANDataInstanceName)

        # Assign the new dict -- work is done
        CANData.CANDataInstances = tmpDict

        return removedInterfaceNames


class SocketCANPacket():
    """
    This class is used to manage data from/to SocketCAN format in a nice manner <:
    """

    def __init__(self, timestamp, iface, id, data):
        """
        This just sets data.

        :param timestamp: Timestamp of the packet
        :param iface: Interface the packet was captured from
        :param id: CAN ID
        :param data: Data payload
        """

        self.timestamp = timestamp if len(timestamp) > 0 else ".".join(
            ["0" * 10, "0" * 6])
        self.iface = iface if len(iface) > 0 else "can0"
        self.id = id
        self.data = data

    def toString(self):
        """
        Returns the string representation of the current object.
        ID lengths will be padded:

         - length <= 3 --> length = 3
         - length > 3 --> length = 8

        :return: A string with the data of the current object
        """

        paddedID = self.id
        if len(paddedID) <= 3:
            neededLength = 3
        else:
            neededLength = 8

        while len(paddedID) < neededLength:
            paddedID = "0" + paddedID

        return "(" + self.timestamp + ") " + self.iface + " " + paddedID + "#" + self.data
