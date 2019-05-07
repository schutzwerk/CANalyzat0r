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

import sys
import os
import traceback
import atexit

from PySide.QtGui import *

import Database
import Settings
import Strings
import Globals
from ui.mainWindow import Ui_CANalyzatorMainWindow
import MainTab
import SenderTab
from Logger import Logger

#: Logger instance to log uncaught exceptions using :func:`~src.CANalyzat0r.globalLoggingHandler`
uncaughtExceptionLogger = Logger(
    Strings.uncaughtExceptionLoggerName).getLogger()


class MainWindow(QMainWindow, Ui_CANalyzatorMainWindow):
    def __init__(self):
        """
        This method has to take care of the following things:
         0. Lazy import tab modules
         1. Initialize the main UI
         2. Setup the database connection and ensure all tables are present
         3. Detect all currently attached CAN devices
         4. Call the prepareUI()-method of every tab
         5. {En, Dis}able GUI elements based on the presence of a CAN device
         6. Setup logging
         7. Install a globlal exception hook that will catch all "remaining" exceptions
            to log it to the GUI
         8. Load the CAN kernel modules
         9. Check if superuser privileges are present - exit if not present
         10. Install event handlers for GUI elements (assignWidgets())
        """

        from SnifferTab import SnifferTab
        from SenderTab import SenderTab
        from FuzzerTab import FuzzerTab
        from FilterTab import FilterTab
        from SearcherTab import SearcherTab
        from ManagerTab import ManagerTab
        from ComparerTab import ComparerTab
        from AboutTab import AboutTab
        from Toolbox import Toolbox

        super(MainWindow, self).__init__()
        self.setWindowIcon(QIcon(Settings.ICON_PATH))
        Globals.ui = self

        # Setup logging
        self.logger = Logger(self.__class__.__name__).getLogger()

        # Redirect exception logs to the textBrowser
        sys.excepthook = globalLoggingHandler

        # Check privileges
        if not self.checkSU():
            self.logger.fatal(Strings.mainTabNoSU)
            QMessageBox.critical(None, Strings.messageBoxErrorTitle,
                                 Strings.mainTabMessageBoxNoSUHint,
                                 QMessageBox.Ok)
            exit(1)

        self.setupUi(self)
        atexit.register(MainWindow.cleanup)

        # Prepare main ui
        Globals.textBrowserLogs = self.textBrowserLogs
        sys.stdout.write(Strings.banner)
        # init and connect to the db
        Globals.db = Database.Database()

        # Create the tab instances
        Globals.fuzzerTabInstance = FuzzerTab(Globals.ui.tabFuzzer)
        Globals.comparerTabInstance = ComparerTab(Globals.ui.tabComparer)
        Globals.searcherTabInstance = SearcherTab(Globals.ui.tabSearcher)
        Globals.filterTabInstance = FilterTab(Globals.ui.tabFilter)
        Globals.managerTabInstance = ManagerTab(Globals.ui.tabManager)

        MainTab.MainTab.detectCANInterfaces(updateLabels=False)
        MainTab.MainTab.applyLogLevelSetting()

        # Let each static tab initialize
        SenderTab.prepareUI()
        MainTab.MainTab.prepareUI()
        SnifferTab.prepareUI()
        AboutTab.prepareUI()
        Toolbox.toggleDisabledSenderGUIElements()
        Toolbox.toggleDisabledProjectGUIElements()

        # Set each QTabWidget to the first tab
        tabWidgets = Globals.ui.findChildren(QTabWidget)
        for tabWidget in tabWidgets:
            if tabWidget.count() > 0:
                tabWidget.setCurrentIndex(0)

        MainTab.MainTab.loadKernelModules()

        # Add handlers
        self.assignWidgets()
        self.show()

    def assignWidgets(self):
        """
        This method connects all GUI elements of the static tabs to their event handlers.
        For all other tabs (those that inherit from :class:`~src.AbstractTab.AbstractTab`, this is
        done in the constructor
        """

        from MainTab import MainTab

        self.buttonSetProject.clicked.connect(MainTab.setProject)
        self.buttonApplyInterface.clicked.connect(
            MainTab.applyGlobalInterfaceSettings)
        self.comboBoxLoglevel.currentIndexChanged.connect(
            MainTab.applyLogLevelSetting)
        self.comboBoxInterface.currentIndexChanged.connect(
            MainTab.preselectUseBitrateCheckBox)
        self.checkBoxMainUseVCAN.stateChanged.connect(
            MainTab.VCANCheckboxChanged)
        self.buttonReadInterfaces.clicked.connect(MainTab.detectCANInterfaces)
        self.buttonVCANAdd.clicked.connect(MainTab.addVCANInterface)
        self.buttonVCANRemove.clicked.connect(MainTab.removeVCANInterface)
        self.labelMainLogo.mousePressEvent = MainTab.easterEgg
        self.spinBoxVCANIndex.valueChanged.connect(MainTab.updateVCANButtons)
        self.buttonSenderSingleInterfaceSettings.clicked.connect(
            SenderTab.SenderTab.handleInterfaceSettingsDialog)
        self.buttonSingleSend.clicked.connect(
            SenderTab.SenderTab.sendSinglePacket)

    def checkSU(self):
        """
        This method gets the effective UID and returns a
        boolean value indicating if root privileges are available.

        Returns:
            A boolean value indicating the superuser status

        """

        return os.geteuid() == 0

    @staticmethod
    def cleanup():
        """
        This gets called when exiting.
        This cleans up everything <:
        """

        import Toolbox
        for mp3Path in list(Toolbox.Toolbox.mp3Processes.keys()):
            Toolbox.Toolbox.stopMP3(mp3Path)


def globalLoggingHandler(type, value, tb):
    """
    This is the handler method for the global exception hook which parses the message in the traceback (tb).
    Using this it is possible to log the exception and the last executed line of code.

    :param type: Exception class
    :param value: Exception value (the object)
    :param tb: Traceback object containing the previously exectuted lines of code
    """

    # Let's parse the traceback
    tb_list = traceback.format_list(traceback.extract_tb(tb))
    relevantLine = tb_list[-1]
    splittedRelevantLine = relevantLine.split(",")
    fileName = splittedRelevantLine[0].split("/")[-1].replace('"', "")
    line = splittedRelevantLine[1][1:]
    method = splittedRelevantLine[2].split("\n")[0].replace(" in ", "")

    # Log the exception
    uncaughtExceptionLogger.exception(
        Strings.uncaughtExceptionLabel + ": \n " + fileName + " (" + line +
        "): " + method + ": " + "{0}".format(str(value)))


def __smoketest__():
    """
    Make quick smoketest to check if the application is ready to run.
    """
    from pyvit import can
    import PySide.QtGui

    # We need the "ip" command available
    import distutils.spawn
    if len(distutils.spawn.find_executable("ip")) == 0:
        exit(1)

    print("It works")


if __name__ == '__main__':

    if len(sys.argv) > 1 and sys.argv[1] == "smoketest":
        __smoketest__()
        sys.exit(0)

    app = QApplication(sys.argv)
    QFontDatabase.addApplicationFont(":/fonts/ui/res/OCRA.ttf")
    mainWin = MainWindow()
    mainWin.setFixedSize(mainWin.size())
    ret = app.exec_()
    sys.exit(ret)
