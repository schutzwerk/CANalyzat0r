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

#: Display logs in the GUI
textBrowserLogs = None

#: Instance to interact with the bus
CANData = None

#: The general UI
ui = None

#: Object to handle db connections
db = None

#: Manage the currently selected project
project = None

#: Stores all known packets for the current project
#: Key: CAN ID and data concatenated and separated with a "#"
#: Value: Description
knownPackets = {}

# Objects to manage the instance of the tabs
fuzzerTabInstance = None
comparerTabInstance = None
searcherTabInstance = None
filterTabInstance = None
managerTabInstance = None

# the rootshell to manage the CAN interfaces
rootshell = None
