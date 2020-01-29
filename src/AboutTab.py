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
Created on Jun 26, 2017

@author: pschmied
"""

from PySide import QtGui
from PySide import QtCore
import Globals
import Settings


class AboutTab:
    """
    This class handles the logic of the about tab.
    """

    @staticmethod
    def prepareUI():
        """
        This just sets up the GUI elements.
        """

        # Setup the "fork me" ribbon
        pixmapForkMe = QtGui.QPixmap(Settings.FORKME_PATH)
        Globals.ui.labelAboutForkMe.setPixmap(pixmapForkMe)
        Globals.ui.labelAboutForkMe.setTextInteractionFlags(
            QtCore.Qt.TextBrowserInteraction)
        Globals.ui.labelAboutForkMe.setOpenExternalLinks(True)
        Globals.ui.labelAboutForkMe.mousePressEvent = AboutTab.browseGitHub

        # Setup the logo
        Globals.ui.labelSWLogo.setMaximumWidth(300)
        Globals.ui.labelSWLogo.setMaximumHeight(19)
        pixmapSWLogo = QtGui.QPixmap(Settings.LOGO_PATH)
        Globals.ui.labelSWLogo.setPixmap(pixmapSWLogo)
        Globals.ui.labelSWLogo.setTextInteractionFlags(
            QtCore.Qt.TextBrowserInteraction)
        Globals.ui.labelSWLogo.setOpenExternalLinks(True)
        Globals.ui.labelSWLogo.mousePressEvent = AboutTab.browseSW

    @staticmethod
    def browseSW(event):
        """
        Opens the SCHUTZWERK website.

        :param event: Dummy, not used.
        """

        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl("https://www.schutzwerk.com",
                        QtCore.QUrl.TolerantMode))

    @staticmethod
    def browseGitHub(event):
        """
        Opens the SCHUTZWERK website.

        :param event: Dummy, not used.
        """

        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl(Settings.GITHUB_URL, QtCore.QUrl.TolerantMode))
