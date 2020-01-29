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

import sqlite3
import os
from PySide.QtGui import QMessageBox, QInputDialog
from PySide import QtCore

import Toolbox
import Packet
from Logger import Logger
from Project import Project
from PacketSet import PacketSet
from KnownPacket import KnownPacket
import Globals
import Settings
import Strings


class DatabaseStatements():
    """
    This class is used to store and generate database statements.
    """

    #: Statement which gets the names of all currently available tables in the database
    #: to check the integrity
    checkTablesPresentStatement = "SELECT name FROM sqlite_master WHERE type='table'"

    projectTableName = "Project"
    projectTableNameColName = "Name"
    projectTableDescriptionColName = "Description"

    packetTableName = "Packet"
    packetTableCANIDColName = "CANID"
    packetTableDataColName = "Data"

    packetSetTableName = "PacketSet"

    knownPacketTableName = "KnownPacket"
    knownPacketTableCANIDColName = "CANID"
    knownPacketTableDataColName = "Data"
    knownPacketTableDescriptionColName = "Description"

    #: Project names are unique
    createProjectTableStatement = """CREATE TABLE `Project` (
	`ID`	INTEGER PRIMARY KEY,
	`Name`	TEXT NOT NULL UNIQUE,
	`Description`	TEXT,
	`Date`	TEXT NOT NULL
    );"""

    createPacketTableStatement = """CREATE TABLE `Packet` (
	`ID`	INTEGER PRIMARY KEY,
	`PacketSetID`	INTEGER NOT NULL,
	`CANID`	TEXT NOT NULL,
	`Data`	TEXT,
	`Timestamp`	TEXT,
	`Interface`	TEXT,
	FOREIGN KEY(PacketSetID) REFERENCES PacketSet(ID)
    );"""

    #: Note: Unique index for the combination of
    #: Project ID and Name
    #: --> A PacketSets name is unique for a project
    createPacketSetTableStatement = """CREATE TABLE `PacketSet` (
	`ID`	INTEGER PRIMARY KEY,
	`ProjectID`	INTEGER NOT NULL,
	`Name`	TEXT NOT NULL,
	`Date`	TEXT NOT NULL,
	UNIQUE(ProjectID, Name),
	FOREIGN KEY(ProjectID) REFERENCES Project(ID)
    );"""

    createKnownPacketTableStatement = """CREATE TABLE `KnownPacket` (
	`ID`	INTEGER PRIMARY KEY,
	`ProjectID`	INTEGER NOT NULL,
	`CANID`	TEXT NOT NULL,
	`Data`	TEXT,
	`Description`	TEXT NOT NULL,
	FOREIGN KEY(ProjectID) REFERENCES Project(ID)
    );"""

    #: Holds all needed create table statements
    createTableStatementsList = [
        createProjectTableStatement, createPacketTableStatement,
        createPacketSetTableStatement, createKnownPacketTableStatement
    ]

    #: The Amount of tables that must be present
    tableCount = len(createTableStatementsList)

    @staticmethod
    def getInsertStatement(tableName, columnList, valuesList):
        """
        Builds a SQL insert statement using the passed parameters

        :param tableName: The table name to insert into
        :param columnList: List of column names that will be affected
        :param valuesList: List of values to put into the columns
        :return: An SQL insert statement with the desired values mapped to the columns

                 e.g. ``INSERT INTO TABLE1 (col1, col2) VALUES (1, 2)``
        """

        rawStatement = "INSERT INTO " + tableName + " (?)" + " VALUES (?)"

        columnMask = ", ".join(columnList)
        # Insert 's for the SQL statement
        valuesList = ["'" + str(value) + "'" for value in valuesList]
        valuesMask = ", ".join(valuesList)

        finalStatement = rawStatement
        # replace ? with values
        for value in [columnMask, valuesMask]:
            # Only replace first occurrence of dummy (?)
            finalStatement = finalStatement.replace("?", value, 1)
        return finalStatement

    @staticmethod
    def getUpdateByIDStatement(tableName, colValuePairs, ID):
        """
        Builds a SQL update statement using the passed parameters **and an ID**

        :param tableName: The table name to update
        :param colValuePairs: List of tuples: (column, desired value)
        :param ID: The ID of the record to update
        :return: An SQL update statement with the desired values mapped to the columns using the ID

                 e.g. ``UPDATE TABLE1 SET col1 = 1, col2 = 2 WHERE ID = 1337``
        """

        rawStatement = "UPDATE " + tableName + " SET ? WHERE ID = ?"

        # List of 'column = value'-pairs
        singleSetStatements = [
            str(colName) + " = " + "'" + str(value) + "'"
            for colName, value in colValuePairs
        ]
        setStatement = ", ".join(singleSetStatements)

        finalStatement = rawStatement
        for value in [setStatement, str(ID)]:
            # Only replace first occurrence of dummy (?)
            finalStatement = finalStatement.replace("?", value, 1)
        return finalStatement

    @staticmethod
    def getInsertProjectStatement(name, desription, date):
        """
        Returns an SQL insert statement for a project using :func:`getInsertStatement`.

        :param name: Projectname
        :param desription: Project description
        :param date: Project date
        :return: The SQL insert statement with all project specific values set
        """

        return DatabaseStatements.getInsertStatement(
            DatabaseStatements.projectTableName,
            ["Name", "Description", "Date"], [name, desription, date])

    @staticmethod
    def getInsertPacketSetStatement(projectID, name, date):
        """
        Returns an SQL insert statement for a PacketSet using :func:`getInsertStatement`.

        :param projectID: The project ID the record belongs to
        :param name: The name of the PacketSet
        :param date: Date
        :return: The SQL insert statement with all PacketSet specific values set
        """

        return DatabaseStatements.getInsertStatement(
            DatabaseStatements.packetSetTableName,
            ["ProjectID", "Name", "Date"], [projectID, name, date])

    @staticmethod
    def getInsertPacketStatement(packetSetID, CANID, data, timestamp, iface):
        """
        Returns an SQL insert statement for a Packet using :func:`getInsertStatement`.

        :param packetSetID: The PacketSet this Packet belongs to
        :param CANID: CAN ID
        :param data: Payload data
        :param timestamp: Timestamp of the packet
        :param iface: Interface name from which this packet was captured from
        :return: The SQL insert statement with all Packet specific values set
        """

        return DatabaseStatements.getInsertStatement(
            DatabaseStatements.packetTableName,
            ["PacketSetID", "CANID", "Data", "Timestamp", "Interface"],
            [packetSetID, CANID, data, timestamp, iface])

    @staticmethod
    def getInsertKnownPacketStatement(projectID, CANID, data, description):
        """
        Returns an SQL insert statement for a KnownPacket using :func:`getInsertStatement`.

        :param projectID: The project this KnownPacket belongs to
        :param CANID: CAN ID
        :param data: Payload data
        :param description: What this specific Packet does
        :return: The SQL insert statement with all KnownPacket specific values set
        """

        return DatabaseStatements.getInsertStatement(
            DatabaseStatements.knownPacketTableName,
            ["ProjectID", "CANID", "Data", "Description"],
            [projectID, CANID, data, description])

    @staticmethod
    def getSelectAllStatement(tableName):
        """
        Returns an SQL select statement to get all data from a table.

        :param tableName: The table name from which data will be selected
        :return: The resulting SQL select statement

                 e.g.: ``SELECT * FROM TABLE1``
        """

        return "SELECT * from ?".replace("?", tableName)

    @staticmethod
    def getSelectAllStatementWhereEquals(tableName, column, value):
        """
        Returns an SQL select statement to gather all data from a table using a where clause

        :param tableName: The table name from which data will be selected
        :param column: The column which the where clause affects
        :param value: The desired value of the column
        :return: The resulting SQL statement with where clause

                 e.g.: ``SELECT * FROM TABLE1 WHERE ID = 1337``
        """

        rawStatement = "SELECT * from ? WHERE ?=?"

        finalStatement = rawStatement
        valueWithQuotes = "'" + str(value) + "'"
        for value in [tableName, column, valueWithQuotes]:
            # Only replace first occurrence of dummy (?)
            finalStatement = finalStatement.replace("?", value, 1)
        return finalStatement

    @staticmethod
    def getOverallCountStatement(tableName):
        """
        Returns an SQL select count statement for the desired table using all rows

        :param tableName: The table name to get the rowcount from
        :return: The resulting SQL statement

                 e.g.: ``SELECT COUNT(*) FROM TABLE1``
        """

        return "SELECT COUNT(*) from ?".replace("?", tableName)

    @staticmethod
    def getDeleteByIDStatement(tableName, id):
        """
        Returns an SQL delete statement using an ID where clause using :func:`getDeleteByValueStatement`

        :param tableName: The table name to delete from
        :param id: Desired ID value for the where clause
        :return: The resulting SQL statement

                 e.g.: ``DELETE FROM TABLE1 WHERE ID = 1337``
        """

        return DatabaseStatements.getDeleteByValueStatement(
            tableName, "ID", id)

    @staticmethod
    def getDeleteByValueStatement(tableName, column, value):
        """
        Returns an SQL delete statement using a where clause using :func:`getDeleteByValueStatement`

        :param tableName: The table name to delete from
        :param column: Desired column for the where clause
        :param value: Desired column value for the where clause
        :return: The resulting SQL statement

                 e.g.: ``DELETE FROM TABLE1 WHERE NAME = 'BANANA'``
        """

        rawStatement = "DELETE FROM ? WHERE ?=?"
        finalStatement = rawStatement
        valueWithQuotes = "'" + str(value) + "'"
        for value in [tableName, column, valueWithQuotes]:
            # Only replace first occurrence of dummy (?)
            finalStatement = finalStatement.replace("?", value, 1)
        return finalStatement


class Database():
    """
    This class handles the database connection and is responsible for creating, deleting and updating values
    """

    def __init__(self):
        """
        This method does the following things:
         1. Setup logging
         2. Create a DB connection and check the integrity
         3. Create tables if necessary
        """

        self.logger = Logger(Strings.databaseLoggerName).getLogger()
        self.connection = self.connect()

        if not self.checkDB():
            self.createTables()
            # Welcome message
            QMessageBox.information(Globals.ui.tabWidgetMain,
                                    Strings.databaseFirstRunMessageBoxTitle,
                                    Strings.databaseFirstRunMessageBoxText,
                                    QMessageBox.Ok)

        self.logger.debug(Strings.databaseSetupOK)

    def connect(self):
        """
        Connect to the hard coded SQLite database path (see Settings).

        Note: If a DatabaseError is encountered, the application will close with error code 1

        :return: A SQLite3 connection object
        """

        try:

            # Get the parent folder if the database file
            dbFolder = os.path.abspath(
                os.path.join(Settings.DB_PATH, os.pardir))
            if not os.path.exists(dbFolder):
                os.makedirs(dbFolder)

            connection = sqlite3.connect(
                Settings.DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
            self.logger.info(Strings.databaseConnectionOK)
            return connection

        except sqlite3.DatabaseError as e:
            self.logger.error(Strings.databaseConnectionFailed)
            exit(1)

    def checkDB(self):
        """
        Checks if all the table count of the SQLite database matches the needed table count.
        If the check does pass the user will be notified to create a project if no project is exisiting yet.
        If the check does not pass the user will be prompted for an action:
        - Truncate the database and create an empty one
        - Keep the database and exit

        :return: A boolean value indicating the database integrity status (True = good)
        """

        cursor = self.connection.cursor()
        cursor.execute(DatabaseStatements.checkTablesPresentStatement)
        data = cursor.fetchall()

        # All tables present
        if len(data) == DatabaseStatements.tableCount:
            # Check if theres at least one project
            if self.getOverallTableCount(
                    DatabaseStatements.projectTableName) > 0:
                return True

            # Tell the user to setup a project
            else:
                QMessageBox.information(
                    Globals.ui.tabWidgetMain,
                    Strings.databaseFirstRunMessageBoxTitle,
                    Strings.databaseFirstRunMessageBoxText, QMessageBox.Ok)
                return True

        # Empty DB
        elif len(data) == 0:
            return False

        # Table missing -- corrupt DB
        elif len(data) > 0 and len(data) < DatabaseStatements.tableCount:
            # Ask user for action
            answer = QMessageBox.question(
                Globals.ui.tabWidgetMain,
                Strings.databaseCorruptMessageBoxTitle,
                Strings.databaseCorruptMessageBoxText,
                QMessageBox.Yes | QMessageBox.No)
            if (answer == QMessageBox.Yes):
                self.logger.info(Strings.databaseCorruptAction)
                # Delete sqlite file and create a fresh db in the next step
                os.remove(Settings.DB_PATH)
                # Update the connection object
                self.connection = self.connect()
                return False

            else:
                self.logger.info(Strings.databaseCorruptNoAction)
                exit(1)

    def createTables(self):
        """
        Creates all needed tables.
        Check :class:`~src.Database.DatabaseStatements` for the SQL statements.
        """

        assert self.connection is not None
        cursor = self.connection.cursor()
        self.logger.debug(Strings.databaseCreatingTablesStart)

        for createTableStatement in DatabaseStatements.createTableStatementsList:
            cursor.execute(createTableStatement)
        self.connection.commit()
        self.logger.debug(Strings.databaseCreatingTablesOK)

    def getOverallTableCount(self, tableName):
        """
        Returns the count(*) of a table.

        :param tableName: The table to count the rows of
        :return: The number of rows as integer
        """

        cursor = self.connection.cursor()
        cursor.execute(DatabaseStatements.getOverallCountStatement(tableName))
        value = cursor.fetchone()[0]
        return value

    def getProjects(self):
        """
        Get all available projects as Project objects.

        :return: A list of all projects as Project objects
        """

        cursor = self.connection.cursor()
        cursor.execute(
            DatabaseStatements.getSelectAllStatement(
                DatabaseStatements.projectTableName))
        rows = cursor.fetchall()
        projects = []
        for row in rows:
            assert len(row) == 4
            projects.append(Project(row[0], row[1], row[2]))
        return projects

    def getKnownPackets(self, project=None):
        """
        Get all known packets of a Project as objects.
        Uses the global project if no project is given.

        :param project: Optional parameter to specify the project to use
        :return: A list of all known packets as KnownPacket objects
        """

        if project is None:
            project = Globals.project
        if Toolbox.Toolbox.checkProjectIsNone(project):
            return

        cursor = self.connection.cursor()
        cursor.execute(
            DatabaseStatements.getSelectAllStatementWhereEquals(
                DatabaseStatements.knownPacketTableName, "ProjectID",
                project.id))
        rows = cursor.fetchall()
        knownPackets = []
        for row in rows:
            assert len(row) == 5
            knownPackets.append(
                KnownPacket(row[0], row[1], row[2], row[3], row[4]))
        return knownPackets

    def getPacketSets(self, project=None):
        """
        Get all packet sets of a Project as objects.
        Uses the global project if no project is given.

        :param project: Optional parameter to specify the project to use
        :return: A list of all known packets as PacketSet objects
        """

        if project is None:
            project = Globals.project
        if Toolbox.Toolbox.checkProjectIsNone(project):
            return

        cursor = self.connection.cursor()
        cursor.execute(
            DatabaseStatements.getSelectAllStatementWhereEquals(
                DatabaseStatements.packetSetTableName, "ProjectID",
                project.id))
        rows = cursor.fetchall()
        packetSets = []
        for row in rows:
            assert len(row) == 4
            packetSets.append(PacketSet(row[0], row[1], row[2], row[3]))
        return packetSets

    def getPacketsOfPacketSet(self, packetSet, raw=False):
        """
        Get all packets of a specific packet set.
        Note: Use raw=True for better performance.

        :param packetSet: All returned packets will belong to this packet set
        :param raw: Boolean value to indicate if the packets will be returned as raw data list (True)
                    or as list of objects (False)
        :return: Depending on the value of raw:
                  - True: List of value lists (raw data)
                  - False: List of Packet objects
        """

        cursor = self.connection.cursor()
        cursor.execute(
            DatabaseStatements.getSelectAllStatementWhereEquals(
                DatabaseStatements.packetTableName, "PacketSetID",
                packetSet.id))
        rows = cursor.fetchall()
        packets = []
        for row in rows:
            assert len(row) == 6
            # Return as objects or as raw list
            if raw:
                packets.append([field for field in row])
            else:
                packets.append(
                    Packet.Packet(
                        packetSet.id,
                        row[2],
                        row[3],
                        row[4],
                        row[5],
                        id=row[0]))

        return packets

    def deleteFromTableByID(self, tableName, id):
        """
        Delete a row from a table with a specific ID.

        :param tableName: The table to delete from
        :param id: ID of the record to delete
        """

        cursor = self.connection.cursor()
        statement = DatabaseStatements.getDeleteByIDStatement(tableName, id)
        self.logger.debug(Strings.databaseLogDeleteStatement + " " + statement)
        cursor.execute(statement)
        self.connection.commit()

    def deleteFromTableByValue(self, tableName, column, value):
        """
        Delete rows from a table with a specific value.

        :param tableName: The table to delete from
        :param column: The column to check
        :param value: The value to search for
        """

        cursor = self.connection.cursor()
        statement = DatabaseStatements.getDeleteByValueStatement(
            tableName, column, value)
        self.logger.debug(Strings.databaseLogDeleteStatement + " " + statement)
        cursor.execute(statement)
        self.connection.commit()

    def deleteProjectAndData(self, project):
        """
        Delete a project and all associated data.

        :param project: The Project object to delete
        """

        # Get the IDs of all associated PacketSets
        cursor = self.connection.cursor()
        statement = DatabaseStatements.getSelectAllStatementWhereEquals(
            DatabaseStatements.packetSetTableName, "ProjectID", project.id)
        cursor.execute(statement)
        rows = cursor.fetchall()
        packetSetIDs = []
        for row in rows:
            assert len(row) == 4
            packetSetIDs.append(row[0])

        # Delete the associated PacketSets
        self.deleteFromTableByValue(DatabaseStatements.packetSetTableName,
                                    "ProjectID", project.id)

        # Delete the associated KnownPackets
        self.deleteFromTableByValue(DatabaseStatements.knownPacketTableName,
                                    "ProjectID", project.id)

        # Delete the packets
        for packetSetID in packetSetIDs:
            self.deleteFromTableByValue(DatabaseStatements.packetTableName,
                                        "PacketSetID", packetSetID)

        # Delete the project
        self.deleteFromTableByID(DatabaseStatements.projectTableName,
                                 project.id)
        self.connection.commit()
        self.logger.info(Strings.databaseProjectDeleted)

    def deletePacketSet(self, packetSet):
        """
        Delete a PacketSet along with the associated packets

        :param packetSet: The PacketSet object to delete
        :return:
        """

        # Delete the PacketSet
        self.deleteFromTableByValue(DatabaseStatements.packetSetTableName,
                                    "ID", packetSet.id)
        # Delete the packets
        self.deleteFromTableByValue(DatabaseStatements.packetTableName,
                                    "PacketSetID", packetSet.id)

    def deleteKnownPacket(self, knownPacket):
        """
        Delete a KnownPacket object

        :param knownPacket: The KnownPacket object to delete
        :return:
        """

        cursor = self.connection.cursor()
        statement = DatabaseStatements.getDeleteByIDStatement(
            DatabaseStatements.knownPacketTableName, knownPacket.id)
        cursor.execute(statement)
        self.connection.commit()

    def saveProject(self, project):
        """
        Save a Project objet to the database

        :param project: The project to save
        :return: The assigned database ID
        """

        cursor = self.connection.cursor()
        statement = DatabaseStatements.getInsertProjectStatement(
            project.name, project.description, project.date)
        self.logger.debug(Strings.databaseLogInsertStatement + " " + statement)
        cursor.execute(statement)
        self.connection.commit()
        self.logger.info(Strings.databaseProjectSaved)
        # Return the ID of the created object
        return cursor.lastrowid

    def updateProject(self, project):
        """
        Update a Project object in the database.

        :param project: The Project object which holds the updated values
        """

        cursor = self.connection.cursor()

        colValuePairs = []

        colValuePairs.append((DatabaseStatements.projectTableNameColName,
                              project.name))
        colValuePairs.append(
            (DatabaseStatements.projectTableDescriptionColName,
             project.description))

        cursor.execute(
            DatabaseStatements.getUpdateByIDStatement(
                DatabaseStatements.projectTableName, colValuePairs,
                project.id))

        self.connection.commit()

        self.logger.info(Strings.databaseProjectUpdated)

    def updateKnownPacket(self, knownPacket):
        """
        Update a known packet object in the database

        :param knownPacket: The KnownPacket object which holds the updated values
        :return:
        """

        cursor = self.connection.cursor()

        colValuePairs = []

        colValuePairs.append((DatabaseStatements.knownPacketTableCANIDColName,
                              knownPacket.CANID))
        colValuePairs.append((DatabaseStatements.knownPacketTableDataColName,
                              knownPacket.data))
        colValuePairs.append(
            (DatabaseStatements.knownPacketTableDescriptionColName,
             knownPacket.description))

        cursor.execute(
            DatabaseStatements.getUpdateByIDStatement(
                DatabaseStatements.knownPacketTableName, colValuePairs,
                knownPacket.id))

        self.connection.commit()

    def savePacketSet(self, packetSet):
        """
        Save a PacketSet to the database.
        If there's a name collision, the user will be prompted for a new and unique name.

        :param packetSet: The PacketSet to save
        """

        currentName = packetSet.name
        while True:
            try:
                cursor = self.connection.cursor()
                cursor.execute(
                    DatabaseStatements.getInsertPacketSetStatement(
                        packetSet.projectID, packetSet.name, packetSet.date))
                self.connection.commit()
                # Return the ID of the created object
                return cursor.lastrowid

            # Uh oh, PacketSet with same name already present for the project
            except sqlite3.IntegrityError:
                # Get the name from the tuple returned by the dialog
                newPacketSetName = QInputDialog.getText(
                    Globals.ui.tabWidgetManagerTabs,
                    Strings.
                    managerTabDBIntegrityNewPacketSetNameMessageBoxTitle,
                    Strings.managerTabDBIntegrityNewPacketSetNameMessageBoxText
                    + currentName,
                )[0]

                if len(newPacketSetName) == 0:
                    self.logger.error(Strings.managerTabInvalidPacketSetName)
                    return

                else:
                    # Try it again
                    packetSet.name = newPacketSetName
                    continue

            break

    # colValueIDList = [[(col1, value), (col2, value), ID], [(col1, value), ID]]
    # List of Lists -- Tuples with ID
    def updatePackets(self, rowList, packetSet, packetIDsToRemove):
        """
        Update the packets of a specific packet set

        :param rowList: A list containing raw packet data
               e.g.: ``[[("CANID", "232"), ("DATA", "BEEF"), packetID], [("DATA", "C0FFEE"), ("CANID", "137"), packetID]]``
        :param packetSet: The PacketSet object the data in rowList belongs to
        :param packetIDsToRemove: Database IDs of packets to remove
        """

        cursor = self.connection.cursor()

        # Process every sublist
        for row in rowList:

            # Extract  and remove the ID - it's the last element
            ID = row.pop()
            assert not isinstance(ID, list)

            # Check if it is a new created row --> create a new packet in the DB
            # and set the ID accordingly
            if ID == -1:
                for colValueTuple in row:
                    if colValueTuple[
                            0] == DatabaseStatements.packetTableCANIDColName:
                        CANID = colValueTuple[1]
                    elif colValueTuple[
                            0] == DatabaseStatements.packetTableDataColName:
                        data = colValueTuple[1]

                newPacket = Packet.Packet(packetSet.id, CANID, data)
                ID = self.savePacket(newPacket)

            cursor.execute(
                DatabaseStatements.getUpdateByIDStatement(
                    DatabaseStatements.packetTableName, row, ID))
        # Remove all deleted packets
        for packetIDToRemove in packetIDsToRemove:
            cursor.execute(
                DatabaseStatements.getDeleteByIDStatement(
                    DatabaseStatements.packetTableName, packetIDToRemove))

        # Everything worked --> commit
        self.connection.commit()

    def savePacketSetWithData(self,
                              packetSetName,
                              rawPackets=None,
                              project=None,
                              packets=None):
        """
        Save a packet set in the database with the given data.
        If no project is given, the global project will be used.
        You must specifiy ``rawPackets`` or ``packets``.

        :param packetSetName: The desired name of the PacketSet
        :param rawPackets: Optional: Raw Packet data (List of lists). You can also use ``packets``.
        :param project: Optional parameter to specify a project. If this is not specified, the selected project
                        will be used
        :param packets: Optional; List of packet objects to save to the packet set.
                        If this is specified, ``rawPackets`` will be ignored
        :return:
        """

        if project is None:
            project = Globals.project
        if Toolbox.Toolbox.checkProjectIsNone(project):
            return -1

        # Create and save PacketSet
        packetSet = PacketSet(None, project.id, packetSetName)
        packetSetID = self.savePacketSet(packetSet)

        if packets is None and rawPackets is not None:
            self.savePacketsBatch(packetSetID, rawPackets=rawPackets)
            self.logger.info(Strings.dataWritten + " " + str(len(rawPackets)))

        elif packets is not None:
            self.savePacketsBatch(packetSetID, packets=packets)
            self.logger.info(Strings.dataWritten + " " + str(len(packets)))

        return packetSetID

    def savePacket(self,
                   packet=None,
                   packetSetID=None,
                   CANID=None,
                   data=None,
                   timestamp="",
                   iface="",
                   commit=True):
        """
        Save a packet to the database: Either by object Oo by list-values --> Faster for many values
        If the value in packet is not None: The passed object will be used
        Else: The seperate values will be used

        :param packet: Optional parameter: Packet object to save
        :param packetSetID: PacketSet ID of the saved packet
        :param CANID: CAN ID
        :param data: Payload data
        :param timestamp: Timestamp
        :param iface: The interface the packet was captured from
        :param commit: If the operation will be commite to the database or not. Batch operations use commit=False

        :return: The database ID of the saved packet if commit is True. Else -1
        """

        listVals = [packetSetID, CANID, data, timestamp, iface]

        cursor = self.connection.cursor()

        if packet is not None:
            cursor.execute(
                DatabaseStatements.getInsertPacketStatement(
                    packet.packetSetID, packet.CANID, packet.data,
                    packet.timestamp, packet.iface))

        elif listVals is not None and len(listVals) != 0:
            cursor.execute(
                DatabaseStatements.getInsertPacketStatement(
                    listVals[0], listVals[1], listVals[2], listVals[3],
                    listVals[4]))

        if commit:
            self.connection.commit()
            # Return the ID of the created object
            return cursor.lastrowid

        return -1

    def savePacketsBatch(self, packetSetID, rawPackets=None, packets=None):
        """
        Save many packets as a batch to the database.
        Use this for improved speed: No objects, only 1 commit.

        :param packetSetID: The PacketSet ID the packets belong to
        :param rawPackets: Optional: Packet data as raw data list (List of lists)
        :param packets: Optional: List of packet objects to save. If this is not None, this will be used instead of
                        ``rawPackets``
        """

        cursor = self.connection.cursor()
        counter = 0

        # Try it with the packet object list first
        if packets is not None:
            for packet in packets:
                if counter % 10000 == 0:
                    counter = 0
                    QtCore.QCoreApplication.processEvents()
                    counter += 1

                cursor.execute(
                    DatabaseStatements.getInsertPacketStatement(
                        packetSetID, packet.CANID, packet.data,
                        packet.timestamp, packet.iface))

        # Use raw data as fallback
        else:
            for rawPacket in rawPackets:

                if counter % 10000 == 0:
                    counter = 0
                    QtCore.QCoreApplication.processEvents()
                    counter += 1

                cursor.execute(
                    DatabaseStatements.getInsertPacketStatement(
                        packetSetID, rawPacket[0], rawPacket[1], rawPacket[3],
                        ""))
        self.connection.commit()

    def saveKnownPacket(self, knownPacket):
        """
        Save a known packt to the database.

        :param knownPacket: The KnownPacket object to save
        :return: The database ID of the saved known packet
        """

        cursor = self.connection.cursor()
        cursor.execute(
            DatabaseStatements.getInsertKnownPacketStatement(
                knownPacket.projectID, knownPacket.CANID, knownPacket.data,
                knownPacket.description))
        self.connection.commit()
        # Return the ID of the created object
        return cursor.lastrowid
