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

from datetime import datetime
import Settings

# MainTab
mainTabLoggerName = "MainTab"
mainTabNoSU = "No superuser privileges found, asking"
mainTabProjectSet = "Switched project to"
mainTabVCANAdded = "Virtual CAN interface added:"
mainTabVCANRemoved = "Virtual CAN interface removed:"
mainTabMessageBoxNoSUHint = "This application was not run as root. You will be asked for your sudo password in a moment."
mainTabCANConfigUpdated = "CAN configuration updated"
mainTabLogLevelChanged = "Loglevel changed"

# Shared and misc
uncaughtExceptionLoggerName = "UncaughtException"
messageBoxErrorTitle = "Error"
messageBoxNoticeTitle = "Notice"
uncaughtExceptionLabel = "Uncaught exception"
confirmDeleteMessageBoxTitle = "Confirmation"
confirmDeleteMessageBoxText = "Are you sure you want to proceed?"
rowSelectionHint = "No packets selected! Please mark entire rows using the row number indicator"
packetBuildError = "Error building packet"
snifferProcessTerminated = "SnifferProcess terminated"
applyingKnownPackets = "Applying..."
packetSetSaveMessageBoxTitle = "Saving packets"
packetSetSaveMessageBoxText = "Please enter a name for the packet set"
noProjectSelectedMessageBoxTitle = "No active project"
noProjectSelectedMessageBoxText = "Please select a project first"
packetSetInvalidName = "Invalid PacketSet name"
knownPacketInvalidDescription = "Invalid description"
dataNotWritten = "Data not saved"
saveDialogTitle = "Save data"
openDialogTitle = "Open file"
objectCreated = "Object created"
itemAdderThreadTerminated = "ItemAdderThread terminated"
mainTabLoadingProjectData = "Loading project data..."
dataWritten = "Records saved:"
contextMenuSendToSender = "Send all packets to sender"
contextMenuSaveAsPacketSet = "Save all packets as new dump"
OSError = "Got OSError, retrying"
ignoringCANDataStillActive = "Ignoring CANData Instance: Interface is being used: "
errorNoAudioDevice = "No audio device present"
activeCANDataWontSave = "Active interface found, won't save: "
gotSocketError = "Socket error received"
dialogFiltering = "Filtering..."
dialogSending = "Sending...."
noRootshell = "No shell process with elevated privileges available."

# SnifferTab
snifferTabLoggerName = "SnifferTab"
snifferTemplatePath = "ui/SnifferTemplate.ui"
snifferPlaceHolderTemplatePath = "ui/SnifferPlaceholderTemplate.ui"
snifferTabElementAlreadyPresent = "SnifferTabElement already present, aborting"
snifferTabPlaceHolderTabText = "No interface"

# SnifferTabElement
snifferTabElementLoggerName = "SnifferTabElement"
snifferTabElementPacketTableViewName = "tableViewSnifferXData"
snifferTabElementLabelInterfaceValueName = "labelSnifferXInterfaceValue"
snifferTabElementSniffingStarted = "Started sniffing"
snifferTabElementSniffingStopped = "Stopped sniffing"
snifferTabElementSniffingProcessTerminated = "Sniffing process terminated"
snifferTabElementSniffingButtonDisabled = "Start"
snifferTabElementSniffingButtonEnabled = "Stop"
snifferTabElementSocketCANConvertOK = "Converted raw data to SocketCAN format"
snifferTabElementInterfaceMissingMessageBoxTitle = "No interface selected"
snifferTabElementInterfaceMissingMessageBoxText = "Please select an interface in the main tab"
snifferTabElementDisableAutoScroll = "Disabling autoscroll to prevent freezes"
snifferTabElementIgnoredPacketsUpdated = "Ignored packets updated"
snifferTabElementTooMuchData = "Too much data, will process when sniffing is stopped"
snifferTabElementDialogProcessing = "Processing..."

# SnifferProcess
snifferProcessLoggerName = "SnifferProcess"

# SenderTab
senderTabLoggerName = "SenderTab"
senderTabSenderTemplatePath = "ui/SenderTemplate.ui"
senderTabNewSenderMessageBoxTitle = "New sender"
senderTabNewSenderMessageBoxText = "Please enter a tab name"
senderTabSenderInvalidName = "Invalid sender name"
senderTabSendAll = "Send all"
senderTabStopSending = "Stop"
senderTabPacketsSentOK = "Packets sent successfully"

# SenderTabElement
senderTabElementLoggerName = "SenderTabElement"
senderTabElementPacketTableViewName = "tableViewSenderXData"
senderTabElementLabelInterfaceValueName = "labelSenderXInterfaceValue"
senderTabElementSenderThreadStarted = "Started sender thread"
senderTabElementSenderThreadStopped = "Stopped sender thread"

# SenderThread
senderThreadLoggerName = "SenderThread"

# FuzzerTab
fuzzerTabLoggerName = "FuzzerTab"
fuzzerTabPacketTableViewName = "tableViewFuzzerData"
fuzzerTabLabelInterfaceValueName = "labelFuzzerInterfaceValue"
fuzzerTabInvalidIDMaskLength = "CAN IDs must consist of 3 or 8 hex chars"
fuzzerTabInvalidExtendedIDMaskValue = "Extended CAN IDs have a maximal value of 0x1FFFFFFF"
fuzzerTabInvalidDataMaskLength = "CAN data must consinst of up to 8 hex chars"
fuzzerTabFuzzerThreadStarted = "Started fuzzer thread"
fuzzerTabFuzzerThreadStopped = "Stopped fuzzer thread"
fuzzerTabFuzzerButtonEnabled = "Stop"
fuzzerTabFuzzerButtonDisabled = "Start"
fuzzerTabExtendedDataMask = "Extended data mask to: "
fuzzerTabBuildPacketValueError = "Error building packet, ignoring"

# FuzzerThread
fuzzSenderThreadLoggerName = "FuzzerThread"

# ComparerTab
comparerTabLoggerName = "ComparerTab"
comparerTabPacketViewName = "tableViewComparerData"

# ManagerTab
managerTabLoggerName = "ManagerTab"
managerTabPacketTableViewName = "tableViewManagerDumpsData"
managerTabKnownPacketAdded = "Added known packet"
managerTabKnownPacketRemoved = "Removed known packet"
managerTabKnownPacketNotAdded = "No known packet added, please use all fields"
managerTabKnownPacketNotEdited = "Not edited, please use all fields"
managerTabAddAsKnownPacketMessageBoxTitle = "Add known packet"
managerTabAddAsKnownPacketMessageBoxText = "You have saved a dump with 1 packet.\nDo you want to add it as a known packet too?"
managerTabAskKnownPacketDescriptionMessageBoxTitle = "New known packet"
managerTabAskKnownPacketDescriptionMessageBoxText = "Please enter a description for the new known packet"
managerTabProjectExported = "Project exported"
managerTabProjectNoFileGiven = "No import file specified"
managerTabObjectsImported = "Objects created, writing to DB"
managerTabObjectsWritten = "Objects written to the DB, finished"
managerTabDBIntegrityNewProjectNameMessageBoxTitle = "New project name"
managerTabDBIntegrityNewProjectNameMessageBoxText = "There's already a project in the DB with the same name\nPlease enter a new name"
managerTabInvalidProjectName = "Invalid project name"
managerTabDBIntegrityNewPacketSetNameMessageBoxTitle = "New dump name"
managerTabDBIntegrityNewPacketSetNameMessageBoxText = "There's already a dump in the DB with the same name\nPlease enter a new name\nExisting name: "
managerTabInvalidPacketSetName = "Invalid dump name"
managerTabNoDataToImport = "No data to import, stopping"
managerTabNoProjectFound = "No project data found"
managerTabDumpsTableDisabledNoProject = "Please select a project before adding packets"
managerTabLoadingDumpDataStart = "Loading dump data..."
managerTabLoadingDumpDataFinished = "Finished loading dump data"
managerTabDumpUpdated = "Dump updated"
managerTabWarningKnownPacketOverwritten = "Duplicate known packet values for: "
managerTabKnownPacketUpdated = "Known packet updated"
managerTabNoActionLoadingData = "No action performed, currently loading data"
managerTabNoPacketsFromPacketSet = "No packets present in packet set"
managerTabGettingPacketData = "Getting packet data..."
managerTabSavingPackets = "Saving packets..."
managerTabExportingProject = "Exporting project data..."
managerTabImportingProject = "Importing project data..."
managerTabDebuggingDumpsRowIDsIndexError = "Index error for: "

# FilterTab
filterTabLoggerName = "FilterTab"
filterTabPacketTableViewName = "tableViewFilterData"
filterTabLabelInterfaceValueName = "labelFilterInterfaceValue"
filterTabSniffingMessageBoxTitle = "Sniffing..."
filterTabSniffingMessageBoxText = "Press OK to capture the next sample"
filterTabSniffingLastSampleMessageBoxText = "Press OK to stop and analyze"
filterTabNewRunStarted = "Started sample run"
filterTabCollectingNoiseLog = "Collecting noise started"
filterTabCollectingNoiseMessageBoxText = "Collected packets: 0"
filterTabDataAdderThreadTerminated = "DataAdderThread terminated"
filterTabStartAnalyzing = "Starting to analyze samples"
filterTabFinishAnalyzing = "Finished analyzing"
filterTabDialogAnalyzing = "Analyzing..."

# SearcherTab
searcherTabLoggerName = "SearcherTab"
searcherTabPacketTableViewName = "tableViewSearcherData"
searcherTabLabelInterfaceValueName = "labelSearcherInterfaceValue"
searcherTabAmountPackets = "# packets"
searcherTabDamagedPacketIgnore = "Ignoring damaged packet"
searcherTabSplitCurrentChunk = "Splitting current chunk"
searcherTabSplitOtherChunks = "Splitting other chunk(s)"
searcherTabMinimizingWorked = "Minimizing worked, trying once again!"
searcherTabTestLastWorkingChunk = "Testing the last working chunk"
searcherTabStoppingAndDumping = "Stopping, remaining packets:"
searcherTabActionPerformedMessageBoxTitle = "Packets sent"
searcherTabActionPerformedMessageBoxText = "Action performed?"
searcherTabAskActionMessageBoxTitle = "No chunk worked"
searcherTabAskActionMessageBoxText = "Please choose an action"
searcherTabAskActionMessageBoxButtonTryAgainText = "Shuffle and decrease chunk amount"
searcherTabAskActionMessageBoxButtonReTestText = "Re-test last working chunk"
searcherTabAskActionMessageBoxButtonCancelText = "Cancel"
searcherTabEnterWhenReadyMessageBoxTitle = ""
searcherTabEnterWhenReadyMessageBoxText = "Press ENTER when ready"
searcherTabSendingDone = "Sending done"
searcherTabSearcherFinishedMP3FilePath = "../sounds/searcherFinished.mp3"

# CANData
CANDataLoggerName = "CANData"
CANDataInvalidSocketCANLine = "Invalid SocketCAN line found"
CANDataParseSocketCANEmptyLine = "Empty line"
CANDataCantExecuteNoSuchInterface = "Can't execute, no such interface: "
CANDataCantExecuteInterfaceActive = "The interface is still being used, can't delete"
CANDataDetectedVirtualInterface = "Detected virtual interface for: "
CANDataNoInstanceAvailable = "No CANData instance available"
CANDataNewInterfaceAdded = "New CAN interface added: "

# Database
databaseLoggerName = "Database"
databaseConnectionOK = "Database connection OK"
databaseConnectionFailed = "Database connection failed, check the path in Settings.py"
databaseCreatingTablesStart = "Preparing database"
databaseCreatingTablesOK = "Database prepared"
databaseCorruptMessageBoxTitle = "Database error"
databaseCorruptMessageBoxText = "The database seems to be corrupted. Do you want to truncate it?"
databaseCorruptNoAction = "No action required, exiting"
databaseCorruptAction = "Creating a new database"
databaseSetupOK = "Database object created"
databaseFirstRunMessageBoxTitle = "First run"
databaseFirstRunMessageBoxText = "Welcome to " + \
    Settings.APP_NAME + "!\n Please create a project first."
databaseLogDeleteStatement = "Deleting row(s) with:"
databaseLogInsertStatement = "Inserting with:"
databaseInvalidPacketCantSave = "Invalid packet - can't save"
databaseProjectUpdated = "Project updated"
databaseProjectSaved = "Project saved"
databaseProjectDeleted = "Project deleted"

# Toolbox
toolboxLoggerName = "Toolbox"
toolboxInvalidLength = "INVALID"
toolboxImportingPastedData = "Importing..."
toolboxNewInterfaceSettingsDialogUIPath = "ui/newInterfaceSettingsDialog.ui"

# PacketsDialog
packetsDialogLoggerName = "IgnoredPacketsDialog"
packetsDialogUIPath = "ui/newManagePacketsDialog.ui"
packetsDialogTableViewName = "tableViewManagePacketsDialogData"

# Statusbar
statusBarSelectGlobalInterface = "No global interface selected"
statusBarReady = "Ready"
statusBarNoProject = "No project selected"
statusBarProjectWasDeleted = "Project was deleted"
statusBarSniffing = "sniffing"
statusBarFuzzing = "fuzzing"
statusBarSending = "sending"

# Project import/export file structuring
projectExportEndSectionMarker = "\n=============\n"
projectExportEndElementMarker = "\n-------------\n"
projectExportHeader = Settings.APP_NAME + " " + Settings.APP_VERSION + \
    " project export (" + str(datetime.now()) + ")"
projectExportProjectHeader = "Project:"
projectExportPacketSetHeader = "PacketSets:"
projectExportPacketHeader = "Packets:"
projectExportKnownPacketHeader = "KnownPackets:"

musicFilePath = "../sounds/music.mp3"
banner = """
   _________    _   __      __                  __  ____
  / ____/   |  / | / /___ _/ /_  ______  ____ _/ /_/ __ \_____
 / /   / /| | /  |/ / __ `/ / / / /_  / / __ `/ __/ / / / ___/
/ /___/ ___ |/ /|  / /_/ / / /_/ / / /_/ /_/ / /_/ /_/ / /
\____/_/  |_/_/ |_/\__,_/_/\__, / /___/\__,_/\__/\____/_/
                          /____/
"""
