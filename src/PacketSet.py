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
from datetime import datetime


class PacketSet():

    """
    This class is being used to handle packet set data.
    It's more comfortable to use a object to pass data
    than to use lists and list indexes. Please note that
    this costs much more performance, so please use lists
    if you have to deal with much data.
    """

    def __init__(self, id, projectID, name, date=None):
        """
        The date of a PacketSet will be automatically set to the current date as string
        """

        self.id = id
        self.projectID = projectID
        self.name = name
        self.date = date if date is not None else str(datetime.now())

    def toComboBoxString(self):
        """
        Calculate a string that will be displayed in a ComboBox

        :return: String representation of a PacketSet object
        """

        return self.name + " (" + self.date.split(".")[0] + ")"

    def toJSON(self):
        """
        To export a PacketSet, all data is being formatted as JSON.
        The internal attribute __dict__ is being used to gather the data.
        This data will then be formatted.

        :return: The formatted JSON data of the object

        """

        return json.dumps(self,
                          default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    @staticmethod
    def fromJSON(importJSON):
        """
        This class method creates a PacketSet object using a JSON string.

        :param importJSON: The JSON string containing the object data

        :returns:  A PacketSet object with the values set accordingly

        """

        packetSet = PacketSet(None, None, None)
        packetSet.__dict__ = json.loads(importJSON)
        return packetSet
