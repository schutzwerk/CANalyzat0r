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

import logging
import Globals
import Settings


class Logger(object):
    """
    This class implements a simple logger with a formatter.
    """

    minLogLevel = logging.INFO

    def __init__(self, className):
        """
        Along with set statements, a formatter is being applied here.

        :param className: The tag for the logger
        """

        logger = logging.getLogger(Settings.APP_NAME + "." + className)
        logger.setLevel(logging.DEBUG)

        handler = LogHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(levelname)s: %(filename)s: %(name)s: %(funcName)s: %(lineno)d: %(message)s"
            ))
        logger.addHandler(handler)

        self._logger = logger

    def getLogger(self):
        return self._logger


class LogHandler(logging.Handler):
    """
    To manage different log levels and custom logging to the log box/text browser, this class is needed.
    """

    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        """
        This checks to loglevel and also logs to log box/text browser.

        :param record: The record to log
        """

        # Simple filtering of logged messages
        if record.levelno < Logger.minLogLevel:
            return

        record = self.format(record)
        # Log to the GUI element if possible
        if Globals.textBrowserLogs is not None:
            Globals.textBrowserLogs.append("{}".format(record))
        print("{}".format(record))
