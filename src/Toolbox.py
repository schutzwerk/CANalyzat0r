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
from PySide import QtGui, QtCore
from PySide.QtGui import QApplication, QProgressDialog, QMessageBox, QFileDialog, QProgressBar, QHBoxLayout
from PySide.QtUiTools import QUiLoader
from PySide.QtCore import QFile

import Globals
import Strings
import SnifferTab
from SenderTab import SenderTab
from Logger import Logger
from CANData import CANData
from MainTab import MainTab


class Toolbox():
    """
    This calls offers helpful static methods that every tab can use to unify program logic and simplify code.
    """

    #: The dialog widget to set the interface settings
    interfaceDialogWidget = None

    #: The toolbox also has its own logger instance
    logger = Logger(Strings.toolboxLoggerName).getLogger()

    #: Used to keep track of the processes that play mp3 files.
    #: Key = filepath, value: multiprocessing Process object
    mp3Processes = {}

    @staticmethod
    def getKnownPacketDescription(CANID, data):
        """
        Get a description for a known packet. This will use the dictionary defined in
        ``Globals`` to find data

        :param CANID: CAN ID
        :param data: Data

        :return: The description if one can be found, else an empty string
        """

        data = data if data is not None else ""
        strIdx = Toolbox.getPacketDictIndex(CANID, data)
        # Check for a known packet and assign the description
        if strIdx in Globals.knownPackets:
            return Globals.knownPackets[str(CANID) + "#" + data]

        # Check for wildcard in a known packet
        elif str(str(CANID) + "#*").upper() in Globals.knownPackets:
            return Globals.knownPackets[str(CANID) + "#*"]

        else:
            return ""

    @staticmethod
    def tableExtractSelectedRowData(table):
        """
        Get the **selected** contents of a GUI table

        :param table: The ``QTableView`` object to gather data from
        :return: A list of raw row data --> List of lists
        """

        colCount = table.model().columnCount()
        # Only check selected rows
        selectionModel = table.selectionModel()
        selectedRows = selectionModel.selectedRows()

        if len(selectedRows) == 0:
            QtGui.QMessageBox.critical(
                Globals.ui.tabWidgetMain, Strings.messageBoxErrorTitle,
                Strings.rowSelectionHint, QtGui.QMessageBox.Ok)
            return

        rawData = []
        for row in selectedRows:
            # Don't let the GUI freeze
            QApplication.processEvents()
            rowData = []
            for colIdx in range(colCount):
                curItemValue = table.model().getValue(row.row(), colIdx)
                rowData.append(
                    curItemValue if curItemValue is not None else "")
            rawData.append(rowData)
        return rawData

    @staticmethod
    def tableExtractAllRowData(table):
        """
        Get **all** contents of a GUI table

        :param table: The ``QTableView`` object to gather data from
        :return: A list of raw row data --> List of lists
        """

        model = table.model()
        colCount = model.columnCount()
        rawData = []
        for row in range(model.rowCount()):
            rowData = []
            for colIdx in range(0, colCount):
                curItemValue = model.getValue(row, colIdx)
                rowData.append(
                    curItemValue if curItemValue is not None else "")
            rawData.append(rowData)
        return rawData

    @staticmethod
    def toggleDisabledProjectGUIElements():
        """
        This toggles specific GUI elements that should only be active if a project has been selected
        """

        state = Globals.project is not None
        for GUIElement in [
                Globals.ui.buttonManagerDeleteDump,
                Globals.ui.buttonManagerUpdateDump,
                Globals.ui.buttonManagerCreateDump,
                Globals.ui.buttonAddKnownPacket,
                Globals.ui.buttonKnownPacketRemove,
                Globals.ui.buttonManagerEditKnownPacket,
                Globals.ui.comboBoxManagerDumps
        ]:
            GUIElement.setEnabled(state)

    @staticmethod
    def toggleDisabledSenderGUIElements():
        """
        This toggles specific GUI elements that should only be active if a CANData instance is present
        """

        state = len(CANData.CANDataInstances) > 0

        for tab in [
                SenderTab, Globals.fuzzerTabInstance,
                Globals.searcherTabInstance, Globals.filterTabInstance
        ]:
            tab.toggleGUIElements(state)
            tab.updateInterfaceLabel()

        for senderTab in SenderTab.senderTabs:
            senderTab.setSendButtonState(state)

    @staticmethod
    def widgetFromUIFile(filePath):
        """
        Reads an ``.ui`` file and creates a new widget object from it.

        :param filePath: Where to find the ``.ui`` file
        :return: The new created widget
        """

        loader = QUiLoader()
        UIFile = QFile(filePath)
        UIFile.open(QFile.ReadOnly)
        widget = loader.load(UIFile)
        UIFile.close()
        return widget

    @staticmethod
    def getWorkingDialog(text):
        """
        Generates a working dialog object which blocks the UI.

        :param text: Text to display while working
        :return: The created working dialog widget
        """

        progressDialog = QProgressDialog(
            text, "", 0, 0, parent=Globals.ui.tabWidgetMain)

        progressDialog.setMinimumDuration(0)
        progressDialog.setMinimum(0)
        progressDialog.setMaximum(0)
        progressDialog.setRange(0, 0)

        progressDialog.setFixedSize(progressDialog.width(),
                                    progressDialog.height())

        # No cancel button <:
        progressDialog.setCancelButton(None)
        # No X button
        progressDialog.setWindowFlags(
            progressDialog.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)

        progressBar = progressDialog.findChild(QProgressBar)
        # :S:S
        progressBar.setMinimumWidth(progressDialog.width() + 20)

        return progressDialog

    @staticmethod
    def askUserConfirmAction():
        """
        Spawns a MessageBox that asks the user to confirm an action

        :return: True if the user has clicked on Yes, else False
        """

        return Toolbox.yesNoBox(Strings.confirmDeleteMessageBoxTitle,
                                Strings.confirmDeleteMessageBoxText)

    @staticmethod
    def yesNoBox(title, text):
        """
        Spawns a MessageBox that asks the user a Yes-No question.

        :return: True if the user has clicked on Yes, else False
        """

        answer = QMessageBox.question(Globals.ui.tabWidgetMain, title, text,
                                      QMessageBox.Yes | QMessageBox.No)

        return answer == QMessageBox.Yes

    @staticmethod
    def interfaceSettingsDialog(currentCANData, CANDataOverrideValues=None):
        """
        Handles the logic of the interface settings dialog.

        :param CANDataOverrideValues: Optional: List of CANData instances that will be selectable instead of all values.

        :return: A new CANData instances with the selected values. None if no editable CANData instance exists
        """

        Toolbox.interfaceDialogWidget = Toolbox.widgetFromUIFile(
            Strings.toolboxNewInterfaceSettingsDialogUIPath)

        if CANDataOverrideValues is None:
            Toolbox.populateInterfaceComboBox(
                Toolbox.interfaceDialogWidget.comboBoxDialogInterface)
        else:
            for CANDataOverrideValue in sorted(
                    CANDataOverrideValues, key=lambda x: x.ifaceName):
                Toolbox.interfaceDialogWidget.comboBoxDialogInterface.addItem(
                    CANDataOverrideValue.ifaceName, CANDataOverrideValue)

        if Toolbox.interfaceDialogWidget.comboBoxDialogInterface.count() == 0:
            return

        # Check if there are active CANData instances
        for i in range(
                Toolbox.interfaceDialogWidget.comboBoxDialogInterface.count()):
            CANDataInstance = Toolbox.interfaceDialogWidget.comboBoxDialogInterface.itemData(
                i)
            if CANDataInstance.active:
                Toolbox.logger.info(Strings.activeCANDataWontSave +
                                    CANDataInstance.ifaceName)

        # Prepopulate the elements
        Toolbox.interfaceDialogWidget.comboBoxDialogInterface.setCurrentIndex(
            0)
        initialSelectedCANData = Toolbox.interfaceDialogWidget.comboBoxDialogInterface.itemData(
            0)

        Toolbox.interfaceDialogWidget.spinBoxDialogBitrate.setValue(
            initialSelectedCANData.bitrate)

        Toolbox.interfaceDialogWidget.spinBoxDialogFDBitrate.setValue(
            initialSelectedCANData.fdBitrate)

        if initialSelectedCANData.VCAN:
            Toolbox.interfaceDialogWidget.checkBoxDialogIsVCAN.setChecked(True)
            Toolbox.interfaceDialogWidget.spinBoxDialogBitrate.setEnabled(
                False)
        else:
            Toolbox.interfaceDialogWidget.checkBoxDialogIsVCAN.setChecked(
                False)
            Toolbox.interfaceDialogWidget.spinBoxDialogBitrate.setEnabled(True)

        if initialSelectedCANData.isFD:
            Toolbox.interfaceDialogWidget.checkBoxDialogIsFD.setChecked(True)
            Toolbox.interfaceDialogWidget.spinBoxDialogFDBitrate.setEnabled(
                True)
        else:
            Toolbox.interfaceDialogWidget.checkBoxDialogIsFD.setChecked(False)
            Toolbox.interfaceDialogWidget.spinBoxDialogFDBitrate.setEnabled(
                False)

        Toolbox.interfaceDialogWidget.comboBoxDialogInterface.currentIndexChanged.connect(
            Toolbox.interfaceSettingsDialogComboBoxChanged)
        Toolbox.interfaceDialogWidget.checkBoxDialogIsVCAN.stateChanged.connect(
            Toolbox.interfaceSettingsDialogCheckBoxChanged)

        Toolbox.interfaceDialogWidget.checkBoxDialogIsFD.stateChanged.connect(
            Toolbox.interfaceSettingsDialogFDCheckBoxChanged)

        # If the CANData instance is active, we can't update the values, only select or deselect it
        # --> Disable edit GUI elements
        if initialSelectedCANData.active:
            Toolbox.interfaceDialogWidget.checkBoxDialogIsVCAN.setEnabled(
                False)
            Toolbox.interfaceDialogWidget.spinBoxDialogBitrate.setEnabled(
                False)

        pressedButton = Toolbox.interfaceDialogWidget.exec_()

        if pressedButton == QMessageBox.Accepted:

            # Get the CANData instance the user selected
            selectedCANData = Toolbox.interfaceDialogWidget.comboBoxDialogInterface.itemData(
                Toolbox.interfaceDialogWidget.comboBoxDialogInterface.
                currentIndex())

            # Only create a new instance if the interface isn't active
            if not selectedCANData.active:
                if not selectedCANData.VCAN:
                    # Physical interface - lets update the bitrate too
                    if selectedCANData.updateBitrate(
                            Toolbox.interfaceDialogWidget.spinBoxDialogBitrate.
                            value(),
                            Toolbox.interfaceDialogWidget.
                            spinBoxDialogFDBitrate.value(),
                            fd=Toolbox.interfaceDialogWidget.checkBoxDialogIsFD.isChecked()):
                        selectedCANData.isFD = Toolbox.interfaceDialogWidget.checkBoxDialogIsFD.isChecked()
                        Toolbox.logger.info(Strings.mainTabCANConfigUpdated)
                    else:
                        Toolbox.logger.info(Strings.mainTabCANConfigUpdated)
                else:
                    Toolbox.logger.info(Strings.mainTabCANConfigUpdated)

                MainTab.setGlobalInterfaceStatus()
                return selectedCANData

            else:
                MainTab.setGlobalInterfaceStatus()
                return selectedCANData

        else:
            return None

    @staticmethod
    def interfaceSettingsDialogCheckBoxChanged(state):
        """
        Gets called when the use VCAN CheckBox of the interface dialog gets changed to
        handle the enabled state of the bitrate SpinBox

        :param state: Not used, state is determined by ``isChecked``
        """

        Toolbox.interfaceDialogWidget.spinBoxDialogBitrate.setEnabled(
            not Toolbox.interfaceDialogWidget.checkBoxDialogIsVCAN.isChecked())

        Toolbox.interfaceDialogWidget.spinBoxDialogFDBitrate.setEnabled(
            not Toolbox.interfaceDialogWidget.checkBoxDialogIsVCAN.isChecked())

        Toolbox.interfaceDialogWidget.checkBoxDialogIsFD.setEnabled(
            not Toolbox.interfaceDialogWidget.checkBoxDialogIsVCAN.isChecked())

        if Toolbox.interfaceDialogWidget.checkBoxDialogIsVCAN.isChecked():
            Toolbox.interfaceDialogWidget.checkBoxDialogIsFD.setChecked(False)
            Toolbox.interfaceDialogWidget.checkBoxDialogIsFD.setEnabled(False)

        __class__.interfaceSettingsDialogFDCheckBoxChanged("1337")

    @staticmethod
    def interfaceSettingsDialogFDCheckBoxChanged(state):
        """
        Gets called when the "use FD" CheckBox of the interface dialog gets changed to
        handle the enabled state of the FD bitrate SpinBox

        :param state: Not used, state is determined by ``isChecked``
        """

        Toolbox.interfaceDialogWidget.spinBoxDialogFDBitrate.setEnabled(
            Toolbox.interfaceDialogWidget.checkBoxDialogIsFD.isChecked())

        Toolbox.interfaceDialogWidget.spinBoxDialogFDBitrate.setEnabled(
            not Toolbox.interfaceDialogWidget.checkBoxDialogIsVCAN.isChecked())

    @staticmethod
    def interfaceSettingsDialogComboBoxChanged():
        """
        Gets called when the interface ComboBox of the interface dialog gets changed to
        pre-populate the GUI elements accordingly.
        """
        selectedCANData = Toolbox.interfaceDialogWidget.comboBoxDialogInterface.itemData(
            Toolbox.interfaceDialogWidget.comboBoxDialogInterface.
            currentIndex())
        isVCAN = selectedCANData.VCAN
        isActive = selectedCANData.active

        if isVCAN:
            newCheckState = QtCore.Qt.Checked
        else:
            newCheckState = QtCore.Qt.Unchecked

        Toolbox.interfaceDialogWidget.checkBoxDialogIsVCAN.setCheckState(
            newCheckState)

        Toolbox.interfaceDialogWidget.checkBoxDialogIsVCAN.setEnabled(
            not isActive)
        Toolbox.interfaceDialogWidget.spinBoxDialogBitrate.setEnabled(
            not isVCAN and not isActive)

    @staticmethod
    def getSaveFileName(dialogTitle):
        """
        Spawns a "save file dialog" to get a file path to save to.

        :param dialogTitle: The displayed dialog title
        :return: The file path of the selected file
        """

        filePath = QFileDialog.getSaveFileName(Globals.ui.tabWidgetMain,
                                               dialogTitle,
                                               QtCore.QDir.homePath())[0]
        return filePath

    @staticmethod
    def isHexString(hexString):
        """
        Checks if a hexString is a valid hex string of base 16

        :param hexString: The hex string
        :return: Boolean value indicating the correctness of the hex string
        """

        if len(hexString) == 0:
            return True
        try:
            int(hexString, 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def checkProjectIsNone(project=-1):
        """
        Checks if a project is ``None`` and displays a MessageBox if True.

        :param project: Optional. The project to check. Default: -1 wich causes the global project to be checked
        :return: Boolean value indicating whether the checked project is ``None``
        """

        if project == -1:
            project = Globals.project

        if project is None:
            QMessageBox.information(Globals.ui.tabWidgetMain,
                                    Strings.noProjectSelectedMessageBoxTitle,
                                    Strings.noProjectSelectedMessageBoxText,
                                    QMessageBox.Ok)
            return True
        return False

    @staticmethod
    def populateInterfaceComboBox(comboBoxWidget,
                                  reselectCurrentItem=True,
                                  ignoreActiveInstances=False):
        """
        Inserts all available interface values into the passed ComboBox widget

        :param comboBoxWidget: The GUI element to fill with items
        :param reselectCurrentItem: Optional: If this is true, the previously selected index will be re-selected
                                    Default: True
        """

        if reselectCurrentItem:
            savedText = comboBoxWidget.currentText()

        comboBoxWidget.clear()

        CANDataInstances = sorted(
            list(CANData.CANDataInstances.values()), key=lambda x: x.ifaceName)

        for i in range(len(CANDataInstances)):
            CANDataInstance = CANDataInstances[i]

            if ignoreActiveInstances and CANDataInstance.active:
                Toolbox.logger.info(Strings.ignoringCANDataStillActive +
                                    CANDataInstance.ifaceName)
                continue

            comboBoxWidget.addItem(CANDataInstance.ifaceName, CANDataInstance)

        if reselectCurrentItem and savedText != "":
            # Select the previously selected item
            comboBoxWidget.setCurrentIndex(comboBoxWidget.findText(savedText))

    @staticmethod
    def updateCANDataInstances(CANDataInstance):
        """
        Calls ``updateCANDataInstance`` for every tab.

        :param CANDataInstance: The new CANData instance
        """

        SenderTab.updateCANDataInstance(CANDataInstance, delegate=True)
        for tab in [
                Globals.fuzzerTabInstance, Globals.searcherTabInstance,
                Globals.filterTabInstance
        ]:
            tab.updateCANDataInstance(CANDataInstance)

    @staticmethod
    def updateInterfaceLabels():
        """
        Calls ``updateInterfaceLabel`` for every tab.
        """

        for tab in [
                SnifferTab.SnifferTab, SenderTab, Globals.fuzzerTabInstance,
                Globals.searcherTabInstance, Globals.filterTabInstance
        ]:
            tab.updateInterfaceLabel()

    @staticmethod
    def getPacketDictIndex(CANID, data):
        """
        Calculates the index of a packet with a specific CAN ID and data in a dictionary.

        :param CANID: CAN ID
        :param data: Data
        :return: The index of a packet in a dictionary
        """

        return str(str(CANID) + "#" + data).upper()

    @staticmethod
    def playMP3(filePath):
        """
        Plays an mp3 sound file using ffmpeg

        :param filePath: Path of the mp3 file
        """
        import subprocess
        import os
        devnull = open(os.devnull, 'w')
        process = subprocess.Popen(
            "ffplay -autoexit -nodisp -loglevel panic " + filePath,
            stdout=devnull,
            stderr=devnull,
            shell=True,
            preexec_fn=os.setsid)

        Toolbox.mp3Processes[filePath] = process

    @staticmethod
    def stopMP3(filePath):
        """
        Stops the playback of a given mp3 file
        :param filePath: Path of the mp3 file
        """
        import os
        import signal
        process = Toolbox.mp3Processes[filePath]
        os.killpg(process.pid, signal.SIGTERM)
        del Toolbox.mp3Processes[filePath]
