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

from math import ceil, floor
from random import shuffle
from time import sleep
from PySide import QtGui
from PySide.QtGui import QMessageBox
from PySide import QtCore
import socket

from AbstractTab import AbstractTab
import Strings
from CANData import CANData
import Toolbox


class SearcherTab(AbstractTab):
    """
    This class handles the logic of the filter tab
    """

    def __init__(self, tabWidget):
        AbstractTab.__init__(self, tabWidget, Strings.searcherTabLoggerName,
                             [2, 3, 4], Strings.searcherTabPacketTableViewName,
                             Strings.searcherTabLabelInterfaceValueName)

        #: The currently smallest known set of packets that cause a specific action.
        #: Values are lists with raw data
        self.lastWorkingChunk = []

        # Packet gap
        self.sleepTime = 0

        #: We first search downwards in the binary search tree. If this doesn't
        #: succeed, we use randomization and begint to search upwards.
        self.downwardsSearch = True

        # Get all GUI elements
        self.buttonSearcherAddPacket = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonSearcherAddPacket")
        self.doubleSpinBoxSearcherPacketGap = self.tabWidget.findChild(
            QtGui.QDoubleSpinBox, "doubleSpinBoxSearcherPacketGap")
        self.buttonSearcherInterfaceSettings = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonSearcherInterfaceSettings")
        self.buttonSearcherStart = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonSearcherStart")
        self.buttonSearcherDataClear = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonSearcherDataClear")

        assert all(GUIElem is not None for GUIElem in [
            self.buttonSearcherAddPacket, self.doubleSpinBoxSearcherPacketGap,
            self.buttonSearcherInterfaceSettings, self.buttonSearcherStart,
            self.buttonSearcherDataClear
        ]), "GUI Elements not found"

        self.buttonSearcherInterfaceSettings.clicked.connect(
            self.handleInterfaceSettingsDialog)
        self.buttonSearcherStart.clicked.connect(self.searchPackets)
        self.buttonSearcherAddPacket.clicked.connect(self.manualAddPacket)
        self.buttonSearcherDataClear.clicked.connect(self.clear)

        self.prepareUI()

    def splitLists(self, lst, chunkAmount=2):
        """
        Split a list into a specific amount of chunks

        :param lst: The list to split
        :param chunkAmount: Desired amount of chunks
        :return: List of chunks (List of lists in this case)
        """

        # First copy the list to avoid side effects
        lstCopy = lst[:]

        if len(lstCopy) == 1:
            return [lstCopy]

        # Amount if elements per chunk
        chunkSize = int(floor((len(lstCopy) / chunkAmount)))
        chunks = []

        for chunkIdx in range(chunkAmount):
            curChunk = []
            for chunkElement in range(chunkSize):
                curChunk.append(lstCopy.pop(0))
            chunks.append(curChunk)

        # If there are still items remaining: append them to the last list
        if len(lstCopy) > 0:
            self.logger.debug("lstCopyLength: " + str(len(lstCopy)))
            chunks[-1] = chunks[-1] + lstCopy

        self.logger.debug("Listlength: " + str(len(lst)))
        self.logger.debug("chunkAmount: " + str(chunkAmount))
        self.logger.debug("chunkSize: " + str(chunkSize))
        self.logger.debug("chunkLength: " + str(len(chunks)))

        assert (len(chunks) == chunkAmount)
        # Check if we lost or added elements
        assert (sum(len(sublst) for sublst in chunks) == len(lst))
        return chunks

    def sendAndSearch(self, chunkAmount=2):
        """
        Use the remaining data to search for relevant packets:
         1. Setup a progress bar
         2. Split the raw packet list in the desired amount of chunks
         3. Test each chunk (Newest packets first) and ask the user if it worked
         4. If it worked: Set ``lastWorkingChunk`` to the last tested chunk and return True
         5. Else: Return False if all other chunks failed too.

        :param chunkAmount: The amount of chunks to generate from the given data list
        :return: True if a specific chunk worked, else False
        """
        # Setup the progress dialog for the user
        progressDialog = Toolbox.Toolbox.getWorkingDialog(
            Strings.dialogSending)
        progressDialog.open()

        try:
            self.logger.info(Strings.searcherTabAmountPackets + ": " +
                             str(len(self.rawData)))

            # Split the list
            # Take the minimum --> cant split list with 2 elements in 3 parts
            chunks = self.splitLists(
                self.rawData,
                max(
                    2,
                    min(chunkAmount,
                        int(ceil((len(self.rawData) / chunkAmount))))))

            # Reverse the chunk order --> newest packets first
            for chunkIdx in reversed(range(len(chunks))):

                # Build and send the packets
                counter = 1
                for idAndData in chunks[chunkIdx]:
                    id = idAndData[0]
                    data = idAndData[1]

                    if counter % 1000 == 0:
                        self.logger.info("Packet " + str(counter) + "/" +
                                         str(len(chunks[chunkIdx])))

                    if counter % 200 == 0:
                        QtCore.QCoreApplication.processEvents()

                    counter += 1

                    try:
                        packet = CANData.tryBuildPacket(id, data)
                    except Exception as e:
                        progressDialog.close()
                        return

                    if packet is not None:
                        try:
                            self.CANData.sendPacket(packet)
                        except socket.error as e:
                            progressDialog.close()
                            self.logger.debug(Strings.gotSocketError)
                            raise e

                        sleep(self.sleepTime)
                    else:
                        self.logger.info(
                            Strings.searcherTabDamagedPacketIgnore)

                progressDialog.close()
                # Sending finished --> play a sound and ask the user what do to next
                self.beep()

                actionPerformed = self.askActionPerformed()

                # The tested chunk worked, forget everything else and user it for further testing
                if actionPerformed:
                    self.lastWorkingChunk = chunks[chunkIdx]
                    self.logger.debug(Strings.searcherTabSplitCurrentChunk)

                    self.rawData = chunks[chunkIdx]
                    # No need to test the other chunks <:
                    progressDialog.close()
                    return True

                # It didn't work. Let's try some other chunk
                else:
                    self.logger.debug(Strings.searcherTabSplitOtherChunks)
                    # Remove the tested chunk
                    chunks.pop(chunkIdx)
                    # set the remaining chunks to one flat list of the remaining packets
                    self.rawData = [
                        tupleData for tupleDataList in chunks
                        for tupleData in tupleDataList
                    ]
                    progressDialog.open()
        finally:
            progressDialog.close()

        return False

    def searchPackets(self):
        """
        This starts the whole searching routine and sets up things first:
         1. Set a CANData instance
         2. Get user input values
         3. Walk down the binary search tree: Try to find a specific packet for an action
         4. If 1 packet has been found: output the packet
         5. If not: Get the last working chunk of packets that worked.
            Use shuffling and new values for the chunk amount to find a minimal set of packets
        """

        if self.CANData is None:
            return

        # Add a lock
        self.active = True
        self.CANData.active = True

        self.logger.debug("Arraylength: " + str(len(self.rawData)))
        # sleep time in ms
        self.sleepTime = self.doubleSpinBoxSearcherPacketGap.value() / 1000
        # Initialize the last working chunk with all packets
        self.lastWorkingChunk = self.rawData

        # First: all the way down in the search tree
        while len(self.rawData) > 1:
            self.sendAndSearch()

        # We have one or no packet remaining in ``lastWorkingChunk``
        # If we have 1 packet --> output
        # If we have no packet --> Try the last working chunk to find multiple packets
        self.rawData = self.lastWorkingChunk
        chunkAmount = 2

        # Used when re-testing the current ``lastWorkingChunk``
        skipSending = False

        while len(self.rawData) > 1:
            if not skipSending:
                # If a chunk worked: continue
                if self.sendAndSearch(chunkAmount):
                    chunkAmount += 1
                    self.rawData = self.lastWorkingChunk
                    self.logger.info(Strings.searcherTabMinimizingWorked)
                    continue

            self.rawData = self.lastWorkingChunk
            skipSending = False
            # No chunk worked --> What to do?
            self.beep()
            chosenAction = self.askWhichAction()

            # Choose an action
            # Didnt't work --> try again (Shuffle and decrease chunk amount)
            if chosenAction == 0:
                chunkAmount = 2
                # recover the last working chunk and shuffle it
                self.rawData = self.lastWorkingChunk
                shuffle(self.rawData)
                continue

            # Not sure if relevant packets still in scope --> Re-test
            elif chosenAction == 1:
                self.logger.debug(Strings.searcherTabTestLastWorkingChunk)
                packets = self.lastWorkingChunk
                counter = 1
                progressDialog = Toolbox.Toolbox.getWorkingDialog(
                    Strings.dialogSending)
                progressDialog.open()
                try:
                    for packet in packets:

                        if counter % 500 == 0:
                            self.logger.debug("Packet " + str(counter) + "/" +
                                              str(len(self.rawData)))

                        try:
                            builtPacket = CANData.tryBuildPacket(
                                packet[0], packet[1])

                        except:
                            progressDialog.close()
                            return

                        if builtPacket is not None:
                            try:
                                self.CANData.sendPacket(builtPacket)
                            except socket.error as e:
                                progressDialog.close()
                                self.logger.debug(Strings.gotSocketError)
                                raise e

                            sleep(self.sleepTime)
                        else:
                            self.logger.info(
                                Strings.searcherTabDamagedPacketIgnore)

                        if counter % 200 == 0:
                            QtCore.QCoreApplication.processEvents()

                        counter += 1
                    progressDialog.close()
                    skipSending = True
                    continue

                finally:
                    progressDialog.close()
            # Finished --> Cancel
            else:
                self.logger.debug(Strings.searcherTabStoppingAndDumping)
                break

        self.outputRemainingPackets(self.rawData)

        # Remove the lock
        self.CANData.active = False
        self.active = False

    # searchPacket helpers

    def askActionPerformed(self):
        """
        Ask the user if the action has been performed using a MessageBox

        :return: True if the user pressed yes, else False
        """

        answer = QMessageBox.question(
            self.tabWidget, Strings.searcherTabActionPerformedMessageBoxTitle,
            Strings.searcherTabActionPerformedMessageBoxText,
            QMessageBox.Yes | QMessageBox.No)
        return answer == QMessageBox.Yes

    def askWhichAction(self):
        """
        Ask the user what to do if no chunk worked:
         - Try again
         - Re-test the current last working chunk
         - Cancel

        :return: An integer value indicating the pressed button:
         - 0 if the user wants to try again
         - 1 if the user wants to re-test
         - 2 if the user wants to cancel
        """

        messageBox = QMessageBox()
        messageBox.setWindowTitle(Strings.searcherTabAskActionMessageBoxTitle)
        messageBox.setText(Strings.searcherTabAskActionMessageBoxText)

        tryAgainButton = messageBox.addButton(
            Strings.searcherTabAskActionMessageBoxButtonTryAgainText,
            QMessageBox.RejectRole)
        reTestButton = messageBox.addButton(
            Strings.searcherTabAskActionMessageBoxButtonReTestText,
            QMessageBox.NoRole)
        cancelButton = messageBox.addButton(
            Strings.searcherTabAskActionMessageBoxButtonCancelText,
            QMessageBox.YesRole)
        messageBox.exec_()

        if messageBox.clickedButton() == tryAgainButton:
            return 0
        elif messageBox.clickedButton() == reTestButton:
            return 1
        elif messageBox.clickedButton() == cancelButton:
            return 2

    def enterWhenReady(self):
        """
        Block the GUI thread until the user pressed the button on the MessageBox.
        """

        QMessageBox.information(
            self.tabWidget, Strings.searcherTabEnterWhenReadyMessageBoxTitle,
            Strings.searcherTabEnterWhenReadyMessageBoxText, QMessageBox.Ok)

    def clear(self, returnOldPackets=False):
        """
        Clear the GUI table and all associated data lists
        """
        AbstractTab.clear(self, returnOldPackets=returnOldPackets)
        self.lastWorkingChunk = []

    def outputRemainingPacket(self, packet):
        """
        Show the passed packet on the GUI table.

        :param packet: The raw packet to display
        """

        self.outputRemainingPackets([packet])

    def outputRemainingPackets(self, rawPackets):
        """
        Show all passed packets on the GUI table.
        Note: This also sets ``rawData`` to the passed set of packets.

        :param packet: List of raw packets to display
        """

        self.rawData = []
        self.clear()
        self.packetTableModel.appendRows(rawPackets)
        self.rawData = rawPackets

    def toggleGUIElements(self, state):
        """
        {En, Dis}able all GUI elements that are used to change searcher settings

        :param state: Boolean value to indicate whether to enable or disable elements
        """

        for GUIElement in [
                self.doubleSpinBoxSearcherPacketGap, self.buttonSearcherStart,
                self.buttonSearcherInterfaceSettings,
                self.buttonSearcherAddPacket, self.buttonSearcherDataClear,
                self.packetTableView
        ]:
            GUIElement.setEnabled(state)

    def beep(self):
        """
        To play a sound after sending has been finished.
        """
        Toolbox.Toolbox.playMP3(Strings.searcherTabSearcherFinishedMP3FilePath)
