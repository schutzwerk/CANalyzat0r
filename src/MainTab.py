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
Created on May 22, 2017

@author: pschmied
"""

import logging
import subprocess
from PySide.QtGui import *
from PySide import QtCore

from Database import *
import Strings
import Settings
import Globals
from CANData import CANData
import SnifferTab
import Toolbox
from Logger import Logger


class MainTab:

    """
    This class handles the logic of the main tab
    """

    #: The tab specific logger
    logger = Logger(Strings.mainTabLoggerName).getLogger()

    #: Statusbar labels
    statusBarApplicationStatus = None
    #: These text will appear in the status bar
    statusBarActiveStatuses = []
    statusBarInterface = None
    statusBarProject = None

    # Add the font
    QFontDatabase.addApplicationFont(":/fonts/ui/res/OCRA.ttf");

    ___playing = False

    @staticmethod
    def addApplicationStatus(status):
        """
        Add a new status to the status bar by name (ordered).
        If no status is present, it will display ``Strings.statusBarReady``

        :param status: The new status to add
        """

        if status is not None and status != Strings.statusBarReady:
            if status not in MainTab.statusBarActiveStatuses:
                MainTab.statusBarActiveStatuses.append(status)
            # Sort to keep order
            MainTab.statusBarApplicationStatus.setText(
                ", ".join(sorted(MainTab.statusBarActiveStatuses)).title())

        else:
            MainTab.statusBarApplicationStatus.setText(Strings.statusBarReady)

    @staticmethod
    def removeApplicationStatus(status):
        """
        Remove a status from the status bar.
        For statuses with mutiple possible values (e.g. ``Sending (X Threads)``
        the search will be done using a substring search

        :param status: The status to remove
        :return:
        """

        if status is not None:
            if status in MainTab.statusBarActiveStatuses:
                MainTab.statusBarActiveStatuses.remove(status)
            # For sender threads: search via substring
            else:
                # If a substring search matches get the element
                matchingStatus = None
                matchingStatusList = [
                    value for value in MainTab.statusBarActiveStatuses if status in value]
                if len(matchingStatusList) > 0:
                    matchingStatus = matchingStatusList[0]
                if matchingStatus is not None:
                    MainTab.statusBarActiveStatuses.remove(matchingStatus)
            if len(MainTab.statusBarActiveStatuses) == 0:
                MainTab.statusBarApplicationStatus.setText(
                    Strings.statusBarReady)
            else:
                MainTab.statusBarApplicationStatus.setText(
                    ", ".join(sorted(MainTab.statusBarActiveStatuses)).title())

    @staticmethod
    def setGlobalInterfaceStatus(red=False):
        """
        Sets the text of the global interface status in the status bar.
        If the global CANData instance is None then the text will read "None".

        :param red: Optional; If this is set to True, the text will appear red. Else black.
        """

        if red:
            MainTab.statusBarInterface.setStyleSheet("QLabel { color : red; }")
        else:
            MainTab.statusBarInterface.setStyleSheet(
                "QLabel { color : black; }")

        if Globals.CANData is not None:
            MainTab.statusBarInterface.setText(
                "Global interface: " + Globals.CANData.toString())
        else:
            MainTab.statusBarInterface.setText("Global interface: None")

    @staticmethod
    def setProjectStatus(projectName, red=False):
        """
        Sets the text of the project status in the status bar.

        :param projectName: The text to put as the new project name
        :param red: Optional; If this is set to True, the text will appear red. Else black.
        """

        if not red:
            MainTab.statusBarProject.setStyleSheet("QLabel { color : black; }")
        else:
            MainTab.statusBarProject.setStyleSheet("QLabel { color : red; }")

        MainTab.statusBarProject.setText("Project: " + projectName)

    @staticmethod
    def populateProjects(keepCurrentIndex=False):
        """
        This populates the project ComboBox in the main tab.

        :param keepCurrentIndex: If this is set to True, the previously selected index will be re-selected in the end
        """

        # Save the index
        if keepCurrentIndex:
            currentIndex = Globals.ui.comboBoxProjectSet.currentIndex()

        projectComboBox = Globals.ui.comboBoxProjectSet
        projectComboBox.clear()

        projects = Globals.db.getProjects()

        for i in range(len(projects)):
            projectComboBox.addItem(projects[i].toComboBoxString())
            projectComboBox.setItemData(i, projects[i])

        # If theres only 1 project then set it as active
        # if len(projects) == 1:
        #    Globals.project = MainTab.setProject()

        if keepCurrentIndex:
            # Set the remembered index
            Globals.ui.comboBoxProjectSet.setCurrentIndex(currentIndex)

    @staticmethod
    def setProject(wasDeleted=False, setNone=False):
        """
        This sets the current project to the currently selected project in the corresponding ComboBox.
        Also, the status bar and project specific ComboBoxes and GUI Elements will be updated.

        :param wasDeleted: This is set to True if the current selected project was deleted. This causes
                           ``Globals.project`` to become None, too.
        :param wasNull: This is set to True, if the project has to be set to None. Default: False
        """

        if not wasDeleted and not setNone:
            Globals.project = Globals.ui.comboBoxProjectSet.itemData(
                Globals.ui.comboBoxProjectSet.currentIndex()
            )

            if Globals.project is None:
                return

            MainTab.setProjectStatus(Globals.project.name)

        elif setNone:
            Globals.project = None
            MainTab.setProjectStatus(Strings.statusBarNoProject, red=True)

        else:
            Globals.project = None
            MainTab.setProjectStatus(
                Strings.statusBarProjectWasDeleted, red=True)

        MainTab.logger.info(Strings.mainTabLoadingProjectData)

        # Update the project data that is managed
        Globals.managerTabInstance.getKnownPacketsForCurrentProject()
        Globals.managerTabInstance.populatePacketSets()
        Globals.managerTabInstance.populateKnownPackets()
        Toolbox.Toolbox.toggleDisabledProjectGUIElements()

        MainTab.logger.info(Strings.mainTabProjectSet + " " +
                            Globals.project.name if Globals.project is not None else "None")

    @staticmethod
    def loadKernelModules():
        """
        Load kernel modules to interact with CAN networks (``can`` and ``vcan``).
        """

        cmds = ["modprobe can", "modprobe vcan"]
        for cmd in cmds:
            process = subprocess.Popen(
                cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()

    @staticmethod
    def easterEgg(event):
        """
        Nothing to see here
        :return: fun
        """
        if Strings.musicFilePath in Toolbox.Toolbox.mp3Processes:
            Toolbox.Toolbox.stopMP3(Strings.musicFilePath)
        else:
            Toolbox.Toolbox.playMP3(Strings.musicFilePath)

    @staticmethod
    def addVCANInterface():
        """
        Manually add a virtual CAN interface. This uses a syscall to ``ip link``.
        If this call succeeds, a new CANDataInstance will be created using :func:`~src.CANData.createCANDataInstance`.
        The detected CAN interfaces will be refreshed, too.
        """

        vifaceName = "vcan" + str(Globals.ui.spinBoxVCANIndex.value())
        cmds = ["ip link add dev " + vifaceName +
                " type vcan", "ip link set up " + vifaceName]
        for cmd in cmds:
            process = subprocess.Popen(
                cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()

        if error is not None and error.decode("utf-8") == "":
            CANData.createCANDataInstance(vifaceName)
            MainTab.logger.info(Strings.mainTabVCANAdded + " " + vifaceName)
        else:
            MainTab.logger.warn(error.decode("utf-8"))

        MainTab.detectCANInterfaces()

    @staticmethod
    def removeVCANInterface():
        """
        This removes the currently selected VCAN interface. This uses a syscall to ``ip link``.
        If the removed interface was the current global interface, the global interface will become None.
        :return:
        """

        vifaceName = "vcan" + str(Globals.ui.spinBoxVCANIndex.value())

        wasGlobalInterface = False
        if Globals.CANData is not None and vifaceName == Globals.CANData.ifaceName:
            wasGlobalInterface = True

        # Interface still used or not present -- abort
        if not CANData.deleteCANDataInstance(vifaceName):
            return

        cmd = "ip link delete " + vifaceName
        process = subprocess.Popen(
            cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        SnifferTab.SnifferTab.removeSniffer(snifferTabName=vifaceName)
        MainTab.detectCANInterfaces()

        Toolbox.Toolbox.updateInterfaceLabels()
        Toolbox.Toolbox.toggleDisabledSenderGUIElements()

        if error.decode("utf-8") == "":
            MainTab.logger.info(Strings.mainTabVCANRemoved + " " + vifaceName)
            if wasGlobalInterface:
                Globals.CANData = None
        else:
            MainTab.logger.warn(error.decode("utf-8"))

        MainTab.setGlobalInterfaceStatus(red=True)

    @staticmethod
    def updateVCANButtons():
        """
        Update the text of the buttons to add and remove VCAN interfaces.
        """

        currentVal = str(Globals.ui.spinBoxVCANIndex.value())
        Globals.ui.buttonVCANAdd.setText("Add vcan" + currentVal)
        Globals.ui.buttonVCANRemove.setText("Remove vcan" + currentVal)

    @staticmethod
    def detectCANInterfaces(updateLabels=True):
        """
        Detect CAN and VCAN interfaces available in the system. A syscall to ``/sys/class/net`` is being used for this.
        For every detected interface a new CANData instance will be
        created using :func:`~src.CANData.createCANDataInstance`.

        Also, interface labels and the global interface ComboBox will be updated.

        :param updateLabels: Whether to update the interface labels or not
        """

        ifaces = sorted(os.listdir("/sys/class/net"))
        CANIfaces = []
        for iface in ifaces:
            if "can" in iface:
                CANIfaces.append(iface)

        removedInterfaceNames = CANData.rebuildCANDataInstances(CANIfaces)
        for removedInterfaceName in removedInterfaceNames:
            SnifferTab.SnifferTab.removeSniffer(
                snifferTabName=removedInterfaceName)

        Toolbox.Toolbox.populateInterfaceComboBox(
            Globals.ui.comboBoxInterface, reselectCurrentItem=False)

        Toolbox.Toolbox.updateCANDataInstances(
            CANData.getGlobalOrFirstInstance())

        for CANIface in CANIfaces:
            SnifferTab.SnifferTab.addSniffer(CANIface)

        if updateLabels:
            Toolbox.Toolbox.updateInterfaceLabels()

    @staticmethod
    def preselectUseBitrateCheckBox():
        """
        Preselect the VCAN CheckBox state because we can't use the bitrate along with VCAN interfaces.
        """

        currentInterface = Globals.ui.comboBoxInterface.itemData(
            Globals.ui.comboBoxInterface.currentIndex())

        if currentInterface is None:
            return

        if currentInterface.VCAN:
            Globals.ui.checkBoxMainUseVCAN.setChecked(True)
        else:
            Globals.ui.checkBoxMainUseVCAN.setChecked(False)
        MainTab.VCANCheckboxChanged()

    @staticmethod
    def applyGlobalInterfaceSettings():
        """
        Set the currently selected interface as the global interface.
        Also, the bitrate will be updated and GUI elements will be toggled.
        The CANData instances of all **inactive** tabs will also be set to the global interface.
        """

        selectedInterfaceName = Globals.ui.comboBoxInterface.currentText()

        if len(selectedInterfaceName) == 0:
            return

        selectedBitrate = Globals.ui.spinBoxBitrate.value()
        selectedCANData = CANData.CANDataInstances[selectedInterfaceName]

        # Set all inactive interfaces to the global interface
        Toolbox.Toolbox.updateCANDataInstances(selectedCANData)
        Globals.CANData = selectedCANData
        MainTab.setGlobalInterfaceStatus()

        # It's still active, we set it but won't save the settings though
        if selectedCANData.active:
            MainTab.logger.info(
                Strings.activeCANDataWontSave + selectedCANData.ifaceName)
            Globals.ui.spinBoxBitrate.setValue(selectedCANData.bitrate)
            Globals.ui.checkBoxMainUseVCAN.setChecked(
                QtCore.Qt.Checked if selectedCANData.VCAN else QtCore.Qt.Unchecked)
            return

        # It's not active, updated VCAN and the bitrate
        else:
            selectedCANData.VCAN = Globals.ui.checkBoxMainUseVCAN.isChecked()
            if selectedCANData.updateBitrate(selectedBitrate):
                Globals.ui.buttonApplyInterface.setStyleSheet(
                    "background-color: green")

            else:
                Globals.ui.buttonApplyInterface.setStyleSheet(
                    "background-color: red")
                return

        MainTab.logger.info(Strings.mainTabCANConfigUpdated)
        # Enable all disabled buttons because an interface was set
        Toolbox.Toolbox.toggleDisabledSenderGUIElements()

        # Update all labels to the new global interface settings
        Toolbox.Toolbox.updateInterfaceLabels()

    @staticmethod
    def applyLogLevelSetting():
        """
        Set the minimum logging level to display messages for.
        """

        selectedLevel = Globals.ui.comboBoxLoglevel.currentText()
        if selectedLevel == "INFO":
            Logger.minLogLevel = logging.INFO
        elif selectedLevel == "DEBUG":
            Logger.minLogLevel = logging.DEBUG
        elif selectedLevel == "WARNING":
            Logger.minLogLevel = logging.WARN
        elif selectedLevel == "ERROR":
            Logger.minLogLevel = logging.ERROR
        elif selectedLevel == "CRITICAL":
            Logger.minLogLevel = logging.CRITICAL

        MainTab.logger.debug(Strings.mainTabLogLevelChanged)

    @staticmethod
    def setupStatusBar():
        """
        Add labels to the status bar and prepare it.
        """

        MainTab.statusBarApplicationStatus = QLabel(
            Strings.statusBarReady, Globals.ui)
        MainTab.statusBarInterface = QLabel(
            Strings.statusBarSelectGlobalInterface, Globals.ui)
        MainTab.statusBarProject = QLabel(
            Strings.statusBarNoProject, Globals.ui)
        MainTab.setProjectStatus(Strings.statusBarNoProject)

        MainTab.statusBarApplicationStatus.setFrameStyle(
            QFrame.Panel | QFrame.Sunken)
        MainTab.statusBarInterface.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        MainTab.statusBarProject.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        MainTab.statusBarApplicationStatus.setStyleSheet(
            "QLabel { color : black; }")
        MainTab.statusBarInterface.setStyleSheet("QLabel { color : red; }")
        MainTab.statusBarProject.setStyleSheet("QLabel { color : red; }")

        Globals.ui.statusBar().addPermanentWidget(
            MainTab.statusBarApplicationStatus, 1)
        Globals.ui.statusBar().addPermanentWidget(MainTab.statusBarInterface, 2)
        Globals.ui.statusBar().addPermanentWidget(MainTab.statusBarProject, 3)

    @staticmethod
    def prepareUI():
        """
         1. Setup the status bar
         2. Detect CAN interfaces and preselect the VCAN CheckBox
         3. Populate project ComboBoxes
         4. Add the logo
        """

        MainTab.setupStatusBar()
        MainTab.detectCANInterfaces()
        MainTab.populateProjects()
        MainTab.preselectUseBitrateCheckBox()

        # Setup the "fork me" ribbon
        pixmapLogo = QPixmap(Settings.ICON_PATH)
        Globals.ui.labelMainLogo.setPixmap(pixmapLogo)

    @staticmethod
    def VCANCheckboxChanged():
        """
        Clickhandler for the VCAN CheckBox which causes the SpinBox to be toggled.
        """

        if Globals.ui.checkBoxMainUseVCAN.isChecked():
            Globals.ui.spinBoxBitrate.setEnabled(False)
        else:
            Globals.ui.spinBoxBitrate.setEnabled(True)
