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
Created on May 19, 2017

@author: pschmied
"""

import json

import Toolbox


class Packet():
    """
    This class is being used to handle packet data.
    It's more comfortable to use a object to pass data
    than to use lists and list indexes. Please note that
    this costs much more performance, so please use lists
    if you have to deal with much data.
    """

    def __init__(self,
                 packetSetID,
                 CANID,
                 data,
                 timestamp="",
                 iface="",
                 length=None,
                 id="137"):
        """
        The parameters ``CANID`` and ``data`` must be valid hex strings.
        If length is not specified, it will be calculated automatically.
        """

        assert Toolbox.Toolbox.isHexString(CANID), "CANID is no hex string"
        assert Toolbox.Toolbox.isHexString(data), "data is no hex string"

        self.packetSetID = packetSetID
        self.CANID = CANID
        self.data = data
        self.id = id

        if len(self.id) <= 3:
            neededLength = 3
        else:
            neededLength = 8

        while len(self.id) < neededLength:
            self.id = "0" + self.id

        # Use the parameter or calculate it
        if length is None:
            # 1 byte = 8 bit = 2x 4 bit; 2^4 = 16 --> 2 chars
            self.length = int(len(data) / 2)
        else:
            self.length = self.lengthStringToInt(length)

        self.timestamp = timestamp
        self.iface = iface

    def lengthStringToInt(self, string):
        """
        This makes sure that the specified length is an int
        :return: The length as integer (if possible) - else None by exception)
        :raises ValueError if the length isn't an integer
        """

        try:
            return int(string)
        except ValueError:
            assert False, "length is no integer -- INVALID"

    def toJSON(self):
        """
        To export a Packet, all data is being formatted as JSON.
        The internal attribute __dict__ is being used to gather the data.
        This data will then be formatted.

        :return: The formatted JSON data of the object

        """

        return json.dumps(
            self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    @staticmethod
    def fromJSON(importJSON):
        """
        This class method creates a Packet object using a JSON string.

        :param importJSON: The JSON string containing the object data

        :returns:  A packet object with the values set accordingly

        """

        # Use dummy data first
        packet = Packet(None, "C0FFEE", "BEEF")
        packet.__dict__ = json.loads(importJSON)
        return packet

    @staticmethod
    def getDisplayDataLength(CANID, hexData):
        """
        This makes sure that the displayed length is correct.
        If CANID is empty, the length will also be empty.
        If the length if hexData is odd, the length will read "INVALID" which prevents saving to the database.
        Else the length will be the amount of chars / 2

        :param CANID: CAN ID
        :param hexData: Payload data as hex string
        :return: The correct length as string
        """

        length = "0"
        if CANID != "" and hexData != "" and len(hexData) % 2 == 0:
            length = int(len(hexData) / 2)

        # Don't display a length of 0 if theres no ID
        elif CANID == "":
            length = ""

        elif len(hexData) % 2 == 1:
            length = "INVALID"

        return length
