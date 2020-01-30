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

from PySide import QtGui
from PySide import QtCore
from sqlite3 import IntegrityError

import Globals
import Strings
from CANData import CANData, SocketCANPacket
from PacketSet import PacketSet
import Packet
from KnownPacket import KnownPacket
from Project import Project
import Database
import MainTab
import Toolbox
from AbstractTab import AbstractTab


class ManagerTab(AbstractTab):
    """
    This class handles the logic of the manager tab
    """

    def __init__(self, tabWidget):
        AbstractTab.__init__(self, tabWidget, Strings.managerTabLoggerName,
                             [2, 3, 4], Strings.managerTabPacketTableViewName)

        #: Kepps track between the association of
        #: table row <-> database id of the packet
        #: e.g. row 2 - database ID 5
        self.dumpsRowIDs = []
        self.dumpsCurrentlyDisplayedPacketSet = None
        self.dumpsDeletedPacketIDs = []

        #: Disallow copying while loading data
        self.loadingData = False

        # Get all GUI elements
        # Projects
        self.lineEditProjectName = self.tabWidget.findChild(
            QtGui.QLineEdit, "lineEditProjectName")
        self.lineEditProjectDescription = self.tabWidget.findChild(
            QtGui.QLineEdit, "lineEditProjectDescription")
        self.buttonProjectCreate = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonProjectCreate")
        self.comboBoxProjectDelete = self.tabWidget.findChild(
            QtGui.QComboBox, "comboBoxProjectDelete")
        self.buttonProjectDelete = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonProjectDelete")
        self.comboBoxProjectEdit = self.tabWidget.findChild(
            QtGui.QComboBox, "comboBoxProjectEdit")
        self.lineEditProjectEditName = self.tabWidget.findChild(
            QtGui.QLineEdit, "lineEditProjectEditName")
        self.lineEditProjectEditDescription = self.tabWidget.findChild(
            QtGui.QLineEdit, "lineEditProjectEditDescription")
        self.buttonProjectEdit = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonProjectEdit")
        # Dumps
        self.comboBoxManagerDumps = self.tabWidget.findChild(
            QtGui.QComboBox, "comboBoxManagerDumps")
        self.buttonManagerDeleteDump = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonManagerDeleteDump")
        self.buttonManagerDumpsAddPacket = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonManagerDumpsAddPacket")
        self.buttonManagerUpdateDump = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonManagerUpdateDump")
        self.buttonManagerCreateDump = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonManagerCreateDump")
        self.buttonManagerDumpsSaveToFile = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonManagerDumpsSaveToFile")
        self.buttonManagerClearDump = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonManagerClearDump")
        # KnownPackets
        self.lineEditKnownPacketID = self.tabWidget.findChild(
            QtGui.QLineEdit, "lineEditKnownPacketID")
        self.lineEditKnownPacketData = self.tabWidget.findChild(
            QtGui.QLineEdit, "lineEditKnownPacketData")
        self.lineEditKnownPacketDescription = self.tabWidget.findChild(
            QtGui.QLineEdit, "lineEditKnownPacketDescription")
        self.buttonAddKnownPacket = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonAddKnownPacket")
        self.comboBoxDeleteKnownPackets = self.tabWidget.findChild(
            QtGui.QComboBox, "comboBoxDeleteKnownPackets")
        self.buttonKnownPacketRemove = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonKnownPacketRemove")
        self.comboBoxEditKnownPackets = self.tabWidget.findChild(
            QtGui.QComboBox, "comboBoxEditKnownPackets")
        self.lineEditKnownPacketEditID = self.tabWidget.findChild(
            QtGui.QLineEdit, "lineEditKnownPacketEditID")
        self.lineEditKnownPacketEditData = self.tabWidget.findChild(
            QtGui.QLineEdit, "lineEditKnownPacketEditData")
        self.lineEditKnownPacketEditDescription = self.tabWidget.findChild(
            QtGui.QLineEdit, "lineEditKnownPacketEditDescription")
        self.buttonManagerEditKnownPacket = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonManagerEditKnownPacket")
        # Import/Export
        self.buttonManagerImport = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonManagerImport")
        self.comboBoxManagerExportProject = self.tabWidget.findChild(
            QtGui.QComboBox, "comboBoxManagerExportProject")
        self.buttonManagerExport = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonManagerExport")

        assert all(GUIElem is not None for GUIElem in [
            self.lineEditProjectName,
            self.lineEditProjectDescription,
            self.buttonProjectCreate,
            self.comboBoxProjectDelete,
            self.buttonProjectDelete,
            self.comboBoxProjectEdit,
            self.lineEditProjectEditName,
            self.lineEditProjectEditDescription,
            self.buttonProjectEdit,
            self.comboBoxManagerDumps,
            self.buttonManagerDeleteDump,
            self.buttonManagerDumpsAddPacket,
            self.buttonManagerUpdateDump,
            self.buttonManagerCreateDump,
            self.buttonManagerDumpsSaveToFile,
            self.buttonManagerClearDump,
            self.lineEditKnownPacketID,
            self.lineEditKnownPacketData,
            self.lineEditKnownPacketDescription,
            self.buttonAddKnownPacket,
            self.comboBoxDeleteKnownPackets,
            self.buttonKnownPacketRemove,
            self.comboBoxEditKnownPackets,
            self.lineEditKnownPacketEditID,
            self.lineEditKnownPacketEditData,
            self.lineEditKnownPacketEditDescription,
            self.buttonManagerEditKnownPacket,
            self.buttonManagerImport,
            self.comboBoxManagerExportProject,
            self.buttonManagerExport,
        ]), "GUI Elements not found"

        # Add click handlers
        self.buttonProjectCreate.clicked.connect(self.createProject)
        self.buttonProjectDelete.clicked.connect(self.deleteProject)
        self.buttonAddKnownPacket.clicked.connect(self.addKnownPacket)
        self.buttonKnownPacketRemove.clicked.connect(self.removeKnownPacket)
        self.buttonManagerDumpsAddPacket.clicked.connect(self.manualAddPacket)
        self.buttonManagerCreateDump.clicked.connect(self.createDump)
        self.comboBoxManagerDumps.currentIndexChanged.connect(self.getDump)
        self.buttonManagerDeleteDump.clicked.connect(self.deleteDump)
        self.buttonManagerClearDump.clicked.connect(self.clear)
        self.buttonManagerDumpsSaveToFile.clicked.connect(self.saveToFile)
        self.buttonManagerUpdateDump.clicked.connect(self.updateDump)
        self.buttonProjectEdit.clicked.connect(self.editProject)
        self.comboBoxProjectEdit.currentIndexChanged.connect(
            self.populateProjectEditLineEdits)
        self.comboBoxEditKnownPackets.currentIndexChanged.connect(
            self.populateKnownPacketEditLineEdits)
        self.buttonManagerEditKnownPacket.clicked.connect(self.editKnownPacket)
        self.buttonManagerExport.clicked.connect(self.exportProject)
        self.buttonManagerImport.clicked.connect(self.importProject)

        self.prepareUI()

    def addKnownPacket(self, CANID=None, data=None, description=None):
        """
        Save a known packet to the current project (and database)
        Default: Get values from the GUI elements. But you can also specify the values
        using the optional parameters.

        :param CANID: Optional: CAN ID
        :param data:  Optional: Payload data
        :param description: Optional: Description of the known packet
        :return:
        """

        if Globals.project is None:
            QtGui.QMessageBox.information(
                Globals.ui.tabWidgetMain,
                Strings.noProjectSelectedMessageBoxTitle,
                Strings.noProjectSelectedMessageBoxText, QtGui.QMessageBox.Ok)
            return

        if CANID is None:
            CANID = self.lineEditKnownPacketID.text()

        if data is None:
            data = self.lineEditKnownPacketData.text()

        if description is None:
            description = self.lineEditKnownPacketDescription.text()

        if len(CANID) < 1 or len(data) < 1 or len(description) < 1:
            self.logger.info(Strings.managerTabKnownPacketNotAdded)
            return

        knownPacket = KnownPacket(None, Globals.project.id, CANID, data,
                                  description)
        Globals.db.saveKnownPacket(knownPacket)
        self.populateKnownPackets()
        # Update the dictionary of known values
        self.getKnownPacketsForCurrentProject()

        self.lineEditKnownPacketID.clear()
        self.lineEditKnownPacketData.clear()
        self.lineEditKnownPacketDescription.clear()
        self.logger.info(Strings.managerTabKnownPacketAdded)

    def removeKnownPacket(self):
        """
        Remove a known packet from the current project (and the database)
        """

        selectedKnownPacket = Globals.ui.comboBoxDeleteKnownPackets.itemData(
            Globals.ui.comboBoxDeleteKnownPackets.currentIndex())

        if selectedKnownPacket == None:
            return

        if not Toolbox.Toolbox.yesNoBox(Strings.confirmDeleteMessageBoxTitle,
                                        Strings.confirmDeleteMessageBoxText):
            return

        Globals.db.deleteKnownPacket(selectedKnownPacket)
        # Update the dictionary of known values
        self.getKnownPacketsForCurrentProject()

        self.populateKnownPackets()
        self.logger.info(Strings.managerTabKnownPacketRemoved)

    def prepareUI(self):
        """
        Prepare the tab specific GUI elements, add keyboard shortcuts and set a CANData instance
        """

        AbstractTab.prepareUI(self)

        self.populateProjects()
        self.populateProjectEditLineEdits()

    def populateProjectEditLineEdits(self):
        """
        Sets the GUI elements concerning editing projects to the current selected project data.
        """

        # If no project has been selected: Set empty strings
        if self.comboBoxProjectEdit.count() == 0:
            self.lineEditProjectEditName.setText("")
            self.lineEditProjectEditDescription.setText("")
            return

        # Else: Use the project attributes to fill the GUI elements text
        selectedProject = self.comboBoxProjectEdit.itemData(
            self.comboBoxProjectEdit.currentIndex())

        if selectedProject is not None:
            self.lineEditProjectEditName.setText(selectedProject.name)
            self.lineEditProjectEditDescription.setText(
                selectedProject.description)

        else:
            self.lineEditProjectEditName.setText("")
            self.lineEditProjectEditDescription.setText("")

    def populateKnownPacketEditLineEdits(self):
        """
        Sets the GUI elements concerning editing known packets to the current selected known packet data.
        """

        # If no known packet has been selected: Use empty strings
        if self.comboBoxEditKnownPackets.count() == 0:
            self.lineEditKnownPacketEditID.setText("")
            self.lineEditKnownPacketEditData.setText("")
            self.lineEditKnownPacketEditDescription.setText("")
            return

        selectedKnownPacket = self.comboBoxEditKnownPackets.itemData(
            self.comboBoxEditKnownPackets.currentIndex())

        if selectedKnownPacket is not None:
            self.lineEditKnownPacketEditID.setText(selectedKnownPacket.CANID)
            self.lineEditKnownPacketEditData.setText(selectedKnownPacket.data)
            self.lineEditKnownPacketEditDescription.setText(
                selectedKnownPacket.description)

        else:
            self.lineEditKnownPacketEditID.setText("")
            self.lineEditKnownPacketEditData.setText("")
            self.lineEditKnownPacketEditDescription.setText("")

    def populatePacketSets(self, IDtoChoose=None):
        """
        Populate the dumps ComboBox in the dumps tab.
        Reloading dump data is being handled by the triggered event

        :param IDtoChoose: Optional: Preselect a specific PacketSet in the ComboBox
        """

        if Globals.project is None:
            self.comboBoxManagerDumps.clear()
            return

        # First clear the displayed data and get the updated data
        self.comboBoxManagerDumps.clear()
        packetSets = Globals.db.getPacketSets()

        if packetSets is None or len(packetSets) == 0:
            return

        for i in range(len(packetSets)):
            self.comboBoxManagerDumps.addItem(packetSets[i].toComboBoxString())
            self.comboBoxManagerDumps.setItemData(i, packetSets[i])

            # Select the desired item (if valid)
            if IDtoChoose is not None and packetSets[i].id == IDtoChoose:
                self.comboBoxManagerDumps.setCurrentIndex(i)
                self.getDump()

        # Fallback
        if self.comboBoxManagerDumps.count() > 0 and \
                IDtoChoose is None:
            self.comboBoxManagerDumps.setCurrentIndex(0)
            self.getDump()

    def populateKnownPackets(self, keepCurrentIndex=False):
        """
        Populate the known packet ComboBoxex (delete and edit).

        :param keepCurrentIndex: Optional: Reselect a specific KnownPacket in the ComboBox
        """

        if Globals.project is None:
            return

        # Save the index
        if keepCurrentIndex:
            currentKnownPacketDeleteIndex = self.comboBoxDeleteKnownPackets.currentIndex(
            )
            currentKnownPacketEditIndex = self.comboBoxEditKnownPackets.currentIndex(
            )

        knownPacketComboBoxes = [
            self.comboBoxDeleteKnownPackets, self.comboBoxEditKnownPackets
        ]

        # Clear them all
        for knownPacketComboBox in knownPacketComboBoxes:
            knownPacketComboBox.clear()

        knownPackets = Globals.db.getKnownPackets()

        if knownPackets is None or len(knownPackets) == 0:
            return

        # Sort them
        knownPackets.sort(key=lambda x: x.description)

        for i in range(len(knownPackets)):
            for knownPacketComboBox in knownPacketComboBoxes:
                knownPacketComboBox.addItem(knownPackets[i].toComboBoxString())
                knownPacketComboBox.setItemData(i, knownPackets[i])

        if keepCurrentIndex:
            # Set the remembered index
            self.comboBoxDeleteKnownPackets.setCurrentIndex(
                currentKnownPacketDeleteIndex)
            self.comboBoxEditKnownPackets.setCurrentIndex(
                currentKnownPacketEditIndex)

        self.populateKnownPacketEditLineEdits()

    def createDump(self, rawPackets=None):
        """
        Save a new dump to the database. This creates a new PacketSet along with associated Packet objects.
        If only one packet is saved, the user will be asked if he wants to create a known packet entry for the
        just saved packet.

        :param rawPackets: Optional: If this is not None, the values from ``rawPackets`` will be used instead of
               the data that is currently being displayed in the GUI table.
        """

        if rawPackets is None:
            rawPackets = self.rawData

        if len(rawPackets) == 0:
            return

        if Toolbox.Toolbox.checkProjectIsNone():
            return

        # Get the name from the tuple returned by the dialog
        packetSetName = QtGui.QInputDialog.getText(
            self.packetTableView,
            Strings.packetSetSaveMessageBoxTitle,
            Strings.packetSetSaveMessageBoxText,
        )[0]

        if len(packetSetName) == 0:
            self.logger.error(Strings.packetSetInvalidName)
            return

        progressDialog = Toolbox.Toolbox.getWorkingDialog(
            Strings.managerTabSavingPackets)
        progressDialog.open()
        try:
            # We've got data, lets save it
            packetSetID = Globals.db.savePacketSetWithData(
                packetSetName, rawPackets=rawPackets)
            if packetSetID is not None and packetSetID > 0:
                # Reload is being handled by the triggered event anyway
                self.populatePacketSets(IDtoChoose=packetSetID)

                if len(rawPackets) == 1:
                    # The user added a PacketSet with size 1 -- maybe he wants to add it as a known packet too
                    if Toolbox.Toolbox.yesNoBox(
                            Strings.managerTabAddAsKnownPacketMessageBoxTitle,
                            Strings.managerTabAddAsKnownPacketMessageBoxText):

                        rawPacket = rawPackets[0]
                        CANID = rawPacket[0]
                        data = rawPacket[1]

                        # Get the description from the tuple returned by the dialog
                        description = QtGui.QInputDialog.getText(
                            self.packetTableView,
                            Strings.
                            managerTabAskKnownPacketDescriptionMessageBoxTitle,
                            Strings.
                            managerTabAskKnownPacketDescriptionMessageBoxText,
                        )[0]

                        if len(description) == 0:
                            self.logger.error(
                                Strings.knownPacketInvalidDescription)
                            return

                        # Create the object and save it
                        knownPacket = KnownPacket(None, Globals.project.id,
                                                  CANID, data, description)
                        Globals.db.saveKnownPacket(knownPacket)
                        self.populateKnownPackets()
        finally:
            progressDialog.close()

    def deleteDump(self):
        """
        Delete the currently selected PacketSet from the database. This also re-populates the table with the data
        of another dump (if existing)
        """

        selectedPacketSet = self.comboBoxManagerDumps.itemData(
            self.comboBoxManagerDumps.currentIndex())
        if selectedPacketSet is None:
            return

        if not Toolbox.Toolbox.askUserConfirmAction():
            return

        Globals.db.deletePacketSet(selectedPacketSet)
        self.populatePacketSets()
        self.getDump()

    def getDump(self):
        """
        Display the data of the selected PacketSet in the GUI table. This also updates ``rawData``
        """

        selectedPacketSet = self.comboBoxManagerDumps.itemData(
            self.comboBoxManagerDumps.currentIndex())
        if selectedPacketSet is None:
            return

        self.dumpsDeletedPacketIDs = []
        self.loadingData = True

        self.logger.info(Strings.managerTabLoadingDumpDataStart)

        # First disable the GUI elements
        self.comboBoxManagerDumps.setEnabled(False)
        self.buttonManagerDumpsAddPacket.setEnabled(False)
        self.buttonManagerUpdateDump.setEnabled(False)
        self.buttonManagerCreateDump.setEnabled(False)
        self.buttonManagerDumpsSaveToFile.setEnabled(False)
        self.buttonManagerClearDump.setEnabled(False)

        self.clear()

        self.logger.debug(Strings.managerTabGettingPacketData)
        rawPacketsFromDB = Globals.db.getPacketsOfPacketSet(
            selectedPacketSet, raw=True)

        if rawPacketsFromDB is None:
            self.logger.warn(Strings.managerTabNoPacketsFromPacketSet)
            return

        # We don't use ID and PacketSetID for the tables --> filter
        rawPacketsFiltered = [subList[2:5] for subList in rawPacketsFromDB]

        # Use a batch import --> Performance over 9000
        packetDescriptions = self.packetTableModel.appendRows(
            rawPacketsFiltered, resolveDescriptions=True)

        assert len(packetDescriptions) == len(
            rawPacketsFiltered), "Lengths must be equal"
        assert (len(rawPacketsFromDB) == len(rawPacketsFiltered)
                ), "Lengths must be equal"

        for i in range(len(rawPacketsFromDB)):

            # Check the ID
            assert rawPacketsFromDB[i][0] is not None

            # To keep track of the association
            # --> Allows updating the table via GUI
            self.dumpsRowIDs.append((i, rawPacketsFromDB[i][0]))

            # Also update rawData
            self.rawData.append(rawPacketsFiltered[i])

        self.dumpsCurrentlyDisplayedPacketSet = selectedPacketSet

        self.comboBoxManagerDumps.setEnabled(True)
        self.buttonManagerDumpsAddPacket.setEnabled(True)
        self.buttonManagerUpdateDump.setEnabled(True)
        self.buttonManagerCreateDump.setEnabled(True)
        self.buttonManagerDumpsSaveToFile.setEnabled(True)
        self.buttonManagerClearDump.setEnabled(True)

        self.loadingData = False
        self.logger.info(Strings.managerTabLoadingDumpDataFinished)

    def updateDump(self):
        """
        Users can change the data displayed in the GUI table. This method allows the changed data
        to be saved to the database.
        """

        # No need to extract the data, we already have it here
        rawPackets = self.rawData

        colValueIDList = []

        # Build the colValueIDList: [[(CANID, value), (data, value), ID], [(CANID, value) (data, value), ID]]
        for i in range(len(rawPackets)):
            currentColValueIDList = []
            # As value list
            rawPacket = rawPackets[i]

            # Try to get the ID of the changed packet
            try:
                # It's a tuple of (rowNumber, PacketID) --> get the PacketID
                packetID = self.dumpsRowIDs[i][1]

            # It must be a new row --> mark it as a new packet
            except IndexError:
                packetID = -1

            currentColValueIDList.append(
                (Database.DatabaseStatements.packetTableCANIDColName,
                 rawPacket[self.IDColIndex]))

            currentColValueIDList.append(
                (Database.DatabaseStatements.packetTableDataColName,
                 rawPacket[self.dataColIndex]))

            currentColValueIDList.append(packetID)

            colValueIDList.append(currentColValueIDList)

        # Make the DB call
        Globals.db.updatePackets(colValueIDList,
                                 self.dumpsCurrentlyDisplayedPacketSet,
                                 self.dumpsDeletedPacketIDs)

        # Reset the list
        self.dumpsDeletedPacketIDs.clear()

        self.logger.info(Strings.managerTabDumpUpdated)

    def clear(self, returnOldPackets=False):
        """
        Clear the GUI table displaying PacketSets along with data lists.
        """

        AbstractTab.clear(self)
        self.dumpsDeletedPacketIDs.clear()

        for rowIDTuple in self.dumpsRowIDs:
            # Append the ID of every deleted row
            self.dumpsDeletedPacketIDs.append(rowIDTuple[1])

        self.dumpsRowIDs = []
        self.dumpsCurrentlyDisplayedPacketSetID = -1

    def removeSelectedPackets(self):
        """
        Pass the remove requested event to the super class.
        After that, add the **database** IDs of the deleted packets to ``dumpsDeletedPacketIDs``.
        The deleted rows will be removed from ``dumpsRowIDs``, too.
        """

        removedRows = AbstractTab.removeSelectedPackets(self)

        # Also remove the rows from the dumpsRowIDs list
        # Reverse the delete order --> no need to worry about shifting indexes <:
        for row in sorted(removedRows, reverse=True):
            # Add the ID of the deleted packet as Value of they Key (Rownumber)
            try:
                self.dumpsDeletedPacketIDs.append(self.dumpsRowIDs[row][1])
                del self.dumpsRowIDs[row]
            except IndexError:
                self.logger.debug(
                    Strings.managerTabDebuggingDumpsRowIDsIndexError +
                    str(row))

    def populateProjects(self, keepCurrentIndex=False):
        """
        Populate the project ComboBoxes (delete, Edit, export project).

        :param keepCurrentIndex: If this is set to True, the previously selected index will be reselected
        """

        # Save the index
        if keepCurrentIndex:
            currentProjectDeleteIndex = self.comboBoxProjectDelete.currentIndex(
            )
            currentProjectEditIndex = self.comboBoxProjectEdit.currentIndex()

        projectComboBoxes = [
            self.comboBoxProjectDelete, self.comboBoxProjectEdit,
            self.comboBoxManagerExportProject
        ]

        # Clear them all
        for projectComboBox in projectComboBoxes:
            projectComboBox.clear()

        projects = Globals.db.getProjects()

        for i in range(len(projects)):
            # Fill them all
            for projectComboBox in projectComboBoxes:
                projectComboBox.addItem(projects[i].toComboBoxString())
                projectComboBox.setItemData(i, projects[i])

        if keepCurrentIndex:
            # Set the remembered index
            self.comboBoxProjectDelete.setCurrentIndex(
                currentProjectDeleteIndex)
            self.comboBoxProjectEdit.setCurrentIndex(currentProjectEditIndex)

        self.populateProjectEditLineEdits()

    def getKnownPacketsForCurrentProject(self):
        """
        (Re-)Populate the dictionary ``Globals.knownPackets`` with up-to-date data.
        If no project is set, the dictionary will be cleared only.
        """

        Globals.knownPackets = {}

        if Globals.project is None:
            return

        knownPackets = Globals.db.getKnownPackets()

        if len(knownPackets) == 0:
            return

        for knownPacket in knownPackets:
            # separate CANID and data with a # to identify them at a later point
            strIdx = Toolbox.Toolbox.getPacketDictIndex(
                knownPacket.CANID, knownPacket.data)

            if strIdx in Globals.knownPackets:
                self.logger.warn(
                    Strings.managerTabWarningKnownPacketOverwritten +
                    knownPacket.CANID + " " + knownPacket.data)

            Globals.knownPackets[strIdx] = knownPacket.description

    def deleteProject(self):
        """
        Delete a project along with associated data. This also updates the project ComboBoxes.
        """

        selectedProject = self.comboBoxProjectDelete.itemData(
            self.comboBoxProjectDelete.currentIndex())
        if selectedProject is None:
            return

        if not Toolbox.Toolbox.askUserConfirmAction():
            return

        Globals.db.deleteProjectAndData(selectedProject)

        MainTab.MainTab.populateProjects()

        wasDeleted = False
        setNone = Globals.project is None

        # If the current project was deleted
        if Globals.project == selectedProject:
            wasDeleted = True
            if Globals.ui.comboBoxProjectSet.count() != 0:
                Globals.project = Globals.ui.comboBoxProjectSet.itemData(0)
            else:
                Globals.project = None

        # Update the comboboxes afterwards
        MainTab.MainTab.populateProjects()
        self.populateProjects()

        # Select another project
        MainTab.MainTab.setProject(wasDeleted=wasDeleted, setNone=setNone)

    def createProject(self):
        """
        Create a new project and save it to the database. This also updates the project ComboBoxes.
        """

        if len(self.lineEditProjectName.text()) == 0:
            return

        projectToSave = Project(None, self.lineEditProjectName.text(),
                                self.lineEditProjectDescription.text())

        Globals.db.saveProject(projectToSave)

        # Reset the values
        self.lineEditProjectName.clear()
        self.lineEditProjectDescription.clear()

        # Update the comboboxes afterwards
        MainTab.MainTab.populateProjects()
        self.populateProjects()

    def editProject(self):
        """
        Update a project with new specified values.
        """

        selectedProject = self.comboBoxProjectEdit.itemData(
            self.comboBoxProjectEdit.currentIndex())
        if selectedProject is None:
            return

        newName = self.lineEditProjectEditName.text()

        if len(newName) == 0:
            return

        newDescription = self.lineEditProjectEditDescription.text()

        updatedProject = Project(selectedProject.id, newName, newDescription)
        Globals.db.updateProject(updatedProject)

        # Also update all comboboxes that manage projects
        self.populateProjects(keepCurrentIndex=True)
        MainTab.MainTab.populateProjects(keepCurrentIndex=True)

        # If the current project has been edited
        # --> Re-set it as the current project
        if Globals.project is not None and selectedProject.id == Globals.project.id:
            MainTab.MainTab.setProject()

    def editKnownPacket(self):
        """
        Update a known packet with new specified values.
        """

        selectedKnownPacket = self.comboBoxEditKnownPackets.itemData(
            self.comboBoxEditKnownPackets.currentIndex())
        if selectedKnownPacket is None:
            return

        oldCANID = selectedKnownPacket.CANID
        oldData = selectedKnownPacket.data

        newCANID = self.lineEditKnownPacketEditID.text()
        newData = self.lineEditKnownPacketEditData.text()
        newDescription = self.lineEditKnownPacketEditDescription.text()

        if len(newCANID) == 0 or len(newData) == 0 or len(newDescription) == 0:
            self.logger.warn(Strings.managerTabKnownPacketNotEdited)
            return

        updatedKnownPacket = KnownPacket(selectedKnownPacket.id,
                                         Globals.project.id, newCANID, newData,
                                         newDescription)

        Globals.db.updateKnownPacket(updatedKnownPacket)

        # Also update the comboboxes
        self.populateKnownPackets(keepCurrentIndex=True)

        # Also update the global variable that stores all descriptions
        oldStrIdx = Toolbox.Toolbox.getPacketDictIndex(oldCANID, oldData)
        # Delete the old value
        Globals.knownPackets.pop(oldStrIdx, None)
        # Inser the new value
        newStrIdx = Toolbox.Toolbox.getPacketDictIndex(newCANID, newData)
        Globals.knownPackets[newStrIdx] = newDescription

        self.logger.info(Strings.managerTabKnownPacketUpdated)

        # Todo: also call getNewKnownPackets for every table that needs it

    def exportProject(self):
        """
        Export a project as JSON string to a textfile.
        The ``toJSON()`` method is called for every object to be exported.
        """

        selectedProject = self.comboBoxProjectDelete.itemData(
            self.comboBoxProjectDelete.currentIndex())
        if selectedProject is None:
            return

        # A tuple is returned --> only use the first element which represents the absolute file path
        filePath = Toolbox.Toolbox.getSaveFileName(Strings.saveDialogTitle)

        if filePath:

            progressDialog = Toolbox.Toolbox.getWorkingDialog(
                Strings.managerTabExportingProject)
            progressDialog.open()
            try:
                # Get the objects that have to be exported
                # Get PacketSets
                packetSets = Globals.db.getPacketSets(project=selectedProject)

                # Get Packets
                packetLists = []
                for packetSet in packetSets:
                    QtCore.QCoreApplication.processEvents()
                    packetLists.append(
                        Globals.db.getPacketsOfPacketSet(packetSet))
                # Make a flat list out of the list of lists
                packets = sum(packetLists, [])

                # Get known packets
                knownPackets = Globals.db.getKnownPackets(
                    project=selectedProject)

                # Do the actual work
                # Open or create
                with open(filePath, "w+") as exportFile:

                    # Write the header first
                    exportFile.write(Strings.projectExportHeader)
                    exportFile.write(Strings.projectExportEndSectionMarker)

                    # Write Project data
                    exportFile.write(Strings.projectExportProjectHeader + "\n")
                    jsonProject = selectedProject.toJSON()
                    exportFile.write(jsonProject)
                    exportFile.write(Strings.projectExportEndSectionMarker)

                    # Write the PacketSet data
                    exportFile.write(Strings.projectExportPacketSetHeader +
                                     "\n")
                    for packetSet in packetSets:
                        QtCore.QCoreApplication.processEvents()
                        jsonPacketSet = packetSet.toJSON()
                        exportFile.write(jsonPacketSet +
                                         Strings.projectExportEndElementMarker)
                    exportFile.write(Strings.projectExportEndSectionMarker)

                    # Write the Packet data
                    exportFile.write(Strings.projectExportPacketHeader + "\n")
                    for packet in packets:
                        QtCore.QCoreApplication.processEvents()
                        jsonPacket = packet.toJSON()
                        exportFile.write(jsonPacket +
                                         Strings.projectExportEndElementMarker)
                    exportFile.write(Strings.projectExportEndSectionMarker)

                    # Write the KnownPacket data
                    exportFile.write(Strings.projectExportKnownPacketHeader +
                                     "\n")
                    for knownPacket in knownPackets:
                        QtCore.QCoreApplication.processEvents()
                        jsonKnownPacket = knownPacket.toJSON()
                        exportFile.write(jsonKnownPacket +
                                         Strings.projectExportEndElementMarker)
                    exportFile.write(Strings.projectExportEndSectionMarker)

                self.logger.info(Strings.managerTabProjectExported)

            finally:
                progressDialog.close()
        else:
            self.logger.info(Strings.dataNotWritten)

    def importProject(self):
        """
        Import a project from a JSON file.
        The ``fromJSON()`` method of every class is called to re-create objects.
        """

        # A tuple is returned --> only use the first element which represents the absolute file path
        filePath = QtGui.QFileDialog.getOpenFileName(self.packetTableView,
                                                     Strings.openDialogTitle,
                                                     QtCore.QDir.homePath())[0]

        importedProject = None
        importedPacketSets = []
        importedPackets = []
        importedKnownPackets = []

        if filePath:

            with open(filePath, "r") as importFile:
                importData = importFile.read()

            if importData == "":
                self.logger.warn(Strings.managerTabNoProjectFound)
                return

            progressDialog = Toolbox.Toolbox.getWorkingDialog(
                Strings.managerTabImportingProject)
            progressDialog.open()
            try:
                sections = importData.split(
                    Strings.projectExportEndSectionMarker)

                if len(sections) == 0 or not any(sections):
                    self.logger.info(Strings.managerTabNoDataToImport)
                    return

                # For every section, ignoring the header
                for sectionIndex in range(1, len(sections)):
                    section = sections[sectionIndex]
                    values = section.split(
                        Strings.projectExportEndElementMarker)

                    firstValue = True
                    className = None
                    for value in values:
                        QtCore.QCoreApplication.processEvents()
                        if len(value) == 0:
                            continue

                        # The first value determines the objet type (~ class)
                        if firstValue:
                            firstValue = False
                            className = value.splitlines()[0]
                            # Remove the first line as it contains the class name
                            value = "".join(value.splitlines()[1:])

                        if len(value) == 0:
                            continue

                        # We've got the class name and the data --> lets create objects
                        if className == Strings.projectExportProjectHeader:
                            importedProject = Project.fromJSON(value)

                        elif className == Strings.projectExportPacketSetHeader:
                            packetSet = PacketSet.fromJSON(value)
                            importedPacketSets.append(packetSet)

                        elif className == Strings.projectExportPacketHeader:
                            packet = Packet.Packet.fromJSON(value)
                            importedPackets.append(packet)

                        elif className == Strings.projectExportKnownPacketHeader:
                            knownPacket = KnownPacket.fromJSON(value)
                            importedKnownPackets.append(knownPacket)

                self.logger.info(Strings.managerTabObjectsImported)

                if importedProject is None:
                    self.logger.warn(Strings.managerTabNoProjectFound)
                    return

                # Objects created, let's save them to the DB with the new project ID

                # We don't know how many attempts the user needs to find a new name for a
                # project name collision
                while True:
                    try:
                        newProjectID = Globals.db.saveProject(importedProject)

                    # Theres already a project with the same name --> get new name
                    except IntegrityError:
                        # Get the name from the tuple returned by the dialog
                        newProjectName = QtGui.QInputDialog.getText(
                            self.packetTableView,
                            Strings.
                            managerTabDBIntegrityNewProjectNameMessageBoxTitle,
                            Strings.
                            managerTabDBIntegrityNewProjectNameMessageBoxText,
                        )[0]

                        if len(newProjectName) == 0:
                            self.logger.error(
                                Strings.managerTabInvalidProjectName)
                            return

                        else:
                            # Try it again with a new name
                            importedProject.name = newProjectName
                            continue
                    break

                # Import the packet sets along with the packets
                for importedPacketSet in importedPacketSets:
                    packetsOfPacketSet = [
                        packet for packet in importedPackets
                        if packet.packetSetID == importedPacketSet.id
                    ]

                    Globals.db.savePacketSetWithData(
                        importedPacketSet.name,
                        packets=packetsOfPacketSet,
                        project=importedProject)

                # Import known packets
                for importedKnownPacket in importedKnownPackets:
                    QtCore.QCoreApplication.processEvents()
                    importedKnownPacket.projectID = newProjectID
                    Globals.db.saveKnownPacket(importedKnownPacket)

                self.logger.info(Strings.managerTabObjectsWritten)

                QtCore.QCoreApplication.processEvents()

                # Populate all GUI elements accordingly
                MainTab.MainTab.populateProjects()
                self.populateProjects()
                self.populatePacketSets()
                self.populateKnownPackets()

            finally:
                progressDialog.close()
        else:
            self.logger.info(Strings.managerTabProjectNoFileGiven)

    def saveToFile(self):
        """
        Save the packets in the GUI table to a file in SocketCAN format.
        """

        # Convert raw data to SocketCAN format
        socketCANPackets = []

        packetsToSave = self.rawData
        if len(packetsToSave) == 0:
            return

        for packet in packetsToSave:
            socketCANPacket = SocketCANPacket(
                packet[3], Globals.CANData.ifaceName if
                Globals.CANData is not None else "can0", packet[0], packet[1])

            socketCANPackets.append(socketCANPacket)
            self.logger.debug(Strings.snifferTabElementSocketCANConvertOK)

        # A tuple is returned --> only use the first element which represents the absolute file path
        filePath = Toolbox.Toolbox.getSaveFileName(Strings.saveDialogTitle)
        if filePath:
            CANData.writeCANFile(filePath, socketCANPackets)
            self.logger.info(Strings.dataWritten + " " +
                             str(len(socketCANPackets)))
        else:
            self.logger.info(Strings.dataNotWritten)

    def handlePaste(self):
        """
        Pass the paste event to the Toolbox, but only if no data is being loaded
        """

        if self.loadingData:
            self.logger.info(Strings.managerTabNoActionLoadingData)
            return

        AbstractTab.handlePaste(self)

    def handleCopy(self):
        """
        Pass the copy event to the Toolbox, but only if no data is being loaded
        """

        if self.loadingData:
            self.logger.info(Strings.managerTabNoActionLoadingData)
            return

        AbstractTab.handleCopy(self)
