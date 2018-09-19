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
Created on Jun 02, 2017

@author: pschmied
"""

from multiprocessing import Pipe, Value
from operator import itemgetter
import time

from AbstractTab import AbstractTab
from PySide.QtGui import QMessageBox, QProgressDialog
from PySide import QtCore, QtGui
import Globals
import Strings
import Toolbox
from SnifferProcess import SnifferProcess
from Packet import Packet


class FilterTab(AbstractTab):

    """
    This class handles the logic of the filter tab
    """

    def __init__(self, tabWidget):
        AbstractTab.__init__(self,
                             tabWidget,
                             Strings.filterTabLoggerName,
                             [0, 1, 2, 3, 4],
                             Strings.filterTabPacketTableViewName,
                             Strings.filterTabLabelInterfaceValueName,
                             allowTablePaste=False)

        #: Noise that will be substracted from the collected data
        self.noiseData = []

        self.snifferProcess = None
        self.dataAdderThread = None

        #: Shared process independent flag to terminate the sniffer process
        self.sharedSnifferEnabledFlag = Value("i", 1)
        #: Shared process independent flag to terminate the data adder
        self.sharedDataAdderEnabledFlag = Value("i", 1)

        # Get all GUI elements
        self.spinBoxFilterTimeCollectNoise = self.tabWidget.findChild(
            QtGui.QSpinBox, "spinBoxFilterTimeCollectNoise")
        self.spinBoxFilterSampleAmount = self.tabWidget.findChild(
            QtGui.QSpinBox, "spinBoxFilterSampleAmount")
        self.buttonFilterInterfaceSettings = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonFilterInterfaceSettings")
        self.buttonFilterStart = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonFilterStart")
        self.buttonFilterDataClear = self.tabWidget.findChild(
            QtGui.QPushButton, "buttonFilterDataClear")

        assert all(GUIElem is not None for GUIElem in [self.spinBoxFilterTimeCollectNoise,
                                                       self.spinBoxFilterSampleAmount,
                                                       self.buttonFilterInterfaceSettings,
                                                       self.buttonFilterStart,
                                                       self.buttonFilterDataClear]), "GUI Elements not found"

        self.buttonFilterInterfaceSettings.clicked.connect(
            self.handleInterfaceSettingsDialog)
        self.buttonFilterStart.clicked.connect(self.startFilter)
        self.buttonFilterDataClear.clicked.connect(self.clear)

        self.prepareUI()

    def startFilter(self):
        """
        Handle the filtering process:
         1. Collect noise
         2. Record sample data
         3. Analyze captured data
        """

        if self.CANData is None:
            return

        self.active = True

        self.clear()

        sampleAmount = self.spinBoxFilterSampleAmount.value()
        noiseCollectSeconds = self.spinBoxFilterTimeCollectNoise.value()

        noiseCaptureOK = True
        self.CANData.active = True
        if noiseCollectSeconds > 0:
            noiseCaptureOK = self.collectNoise(noiseCollectSeconds)

        if noiseCaptureOK:
            # Reset the captured data
            self.rawData = []
            for curSampleIndex in range(sampleAmount):
                self.getSampleData(sampleAmount, curSampleIndex)

            # Analyze it
            self.analyze()

        self.CANData.active = False
        self.active = False

    def analyze(self, removeNoiseWithIDAndData=True):
        """
        Analyze captured data:
         1. Remove sorted noise data (if collected):
            For each sample:
             - Sort the sample to increase filtering speed
             - Remove noise
         2. Find relevant packets:
             - Sort each sample to increase filtering speed
             - Assume that all packets of the first sample occurred in every other sample
             - Take every other sample and compare

        Depending on ``removeNoiseWithIDAndData`` noise will be filtered by
        ID and data (default) or ID only

        :param removeNoiseWithIDAndData: Optional value: Filter data by ID and Data or ID only
        """

        # Setup the progress dialog for the user
        progressDialog = Toolbox.Toolbox.getWorkingDialog(
            Strings.filterTabDialogAnalyzing)
        progressDialog.open()
        try:
            QtCore.QCoreApplication.processEvents()

            # Do the actual computing
            sortedSamplesWithoutNoise = []

            # Remove noise (if collected)

            if len(self.noiseData) > 0:
                # Sort by CAN ID first
                noiseDataSorted = sorted(self.noiseData, key=itemgetter(0))

                # For each sample
                for curSampleIndex in range(len(self.rawData)):
                    curSample = self.rawData[curSampleIndex]

                    # Sort the sample list and noise data by ID to increase filtering speed
                    curSampleSorted = sorted(curSample, key=itemgetter(0))
                    self.logger.debug("Sample size: " + str(len(curSample)))

                    # Compare noise and sample data
                    for noisePacket in noiseDataSorted:
                        # Update the progress bar
                        QtCore.QCoreApplication.processEvents()
                        for sniffedPacket in curSampleSorted:

                            # We sorted the lists previously because of this
                            # This allows us to break the loop earlier because no
                            # equal ID will be reached anymore (it's sorted!)
                            if sniffedPacket[0] > noisePacket[0]:
                                break

                            if removeNoiseWithIDAndData:

                                if sniffedPacket[0] == noisePacket[0] and sniffedPacket[1] == noisePacket[1]:
                                    curSampleSorted.remove(sniffedPacket)

                            # Filter it by ID only
                            else:
                                if sniffedPacket[0] == noisePacket[0]:
                                    curSampleSorted.remove(sniffedPacket)

                    sortedSamplesWithoutNoise.append(curSampleSorted)

            # No noise to remove, just sort
            else:
                for curSample in self.rawData:
                    sortedSamplesWithoutNoise.append(
                        sorted(curSample, key=itemgetter(0))
                    )

            # Noise has been removed --> find relevant packets now
            self.logger.info(Strings.filterTabStartAnalyzing)
            # Find packets with ID and data that occurred in all samples

            # First just assume that all packets of the first sample occurred in every other sample
            # --> Copy the list using the slicing operator
            packetsInAllSamples = sortedSamplesWithoutNoise[0][:]
            remainingPackets = []

            # Now take every other sample and compare
            for sampleIndex in range(1, len(sortedSamplesWithoutNoise)):

                # Every potential packet has been removed --> don't continue
                if len(packetsInAllSamples) == 0:
                    break

                for samplePacket in sortedSamplesWithoutNoise[sampleIndex]:

                    # Update the progress bar
                    QtCore.QCoreApplication.processEvents()

                    for packetInAllSamples in packetsInAllSamples:
                        # Don't continue searching if a greater element has been found
                        # because they will all be greater anyway
                        if samplePacket[0] < packetInAllSamples[0]:
                            break

                    # Check if ID and data are equal
                        if samplePacket[0] == packetInAllSamples[0] and samplePacket[1] == packetInAllSamples[1]:
                            # The packet exists in both lists --> break the inner loop because all following
                            # packets would have greater IDs
                            remainingPackets.append(packetInAllSamples)
                        else:
                            pass

            self.logger.info(Strings.filterTabFinishAnalyzing)

            # Analyzing done, show the remaining packets
            self.outputRemainingPackets(remainingPackets)

        finally:
            progressDialog.close()

    def collectNoise(self, seconds):
        """
        Collect noise data and update ``noiseData``.
        Uses the processes/threads started in :func:`startSnifferAndAdder`.

        :param seconds: Amount of seconds to capture noise

        :return: True if noise was captured. False if the user pressed "Cancel"
        """

        self.noiseData = []
        # Setup the ProgressDialog
        progressDialog = QProgressDialog(Strings.filterTabCollectingNoiseMessageBoxText,
                                         "Cancel",
                                         0,
                                         seconds)

        progressDialog.setMinimumDuration(0)
        progressDialog.setMinimum(0)
        progressDialog.setMaximum(seconds)
        progressDialog.adjustSize()
        progressDialog.setFixedSize(progressDialog.width()+40,
                                    progressDialog.height())

        # Users still can click on the "X"
        progressDialog.setCancelButton(None)

        # Start collecting
        self.startSnifferAndAdder(adderMethod=self.addSniffedNoise)

        progressDialog.open()

        secondsToCollect = seconds
        while secondsToCollect > 0 and not progressDialog.wasCanceled():
            time.sleep(0.5)
            secondsToCollect -= 0.5
            self.updateNoiseCollectProgress(
                progressDialog, seconds - secondsToCollect)

        self.stopSnifferAndAdder()
        return not progressDialog.wasCanceled()

    def updateNoiseCollectProgress(self, progressDialog, value):
        """
        Update the text and progressbar value displayed while collecting noise.

        :param progressDialog: The QProgressDialog to update
        :param value: The value to set the progressbar to
        """

        labelText = Strings.filterTabCollectingNoiseMessageBoxText.replace(
            "0", str(len(self.noiseData)))
        progressDialog.setLabelText(labelText)
        progressDialog.setValue(value)

        progressDialog.adjustSize()
        progressDialog.setFixedSize(progressDialog.width(),
                                    progressDialog.height())

    def getSampleData(self, sampleAmount, curSampleIndex):
        """
        Collect sample data and add the sniffed data to ``rawData[curSampleIndex]``.
        Uses the processes/threads started using :func:`startSnifferAndAdder`.

        :param sampleAmount: Amount of samples to collect
        :param curSampleIndex: Index of the currently captured sample in ``rawData``
        """

        # Append a new list for the current sample run
        self.rawData.append([])

        # Display another text in the last round
        if curSampleIndex == range(sampleAmount)[-1]:
            messageBoxText = Strings.filterTabSniffingLastSampleMessageBoxText
        else:
            messageBoxText = Strings.filterTabSniffingMessageBoxText

        self.startSnifferAndAdder(
            self.addSniffedPacketToSample, curSampleIndex)

        # Sniff and wait for the user to do an action
        QMessageBox.information(Globals.ui.tableViewFilterData,
                                Strings.filterTabSniffingMessageBoxTitle +
                                " (" + str(curSampleIndex + 1) +
                                "/" + str(sampleAmount) + ")",
                                messageBoxText,
                                QMessageBox.Ok)

        self.stopSnifferAndAdder()

    def startSnifferAndAdder(self, adderMethod, curSampleIndex=-1):
        """
        Start a DataAdderThread and a SnifferProcess to collect data. They will communicate using a
        multiprocess pipe to collect data without interrupting the GUI thread.

        :param adderMethod: The DataAdderThread will call this method to handle the received data
        :param curSampleIndex: The index of the currently captured sample (-1 as default)
        """

        # Reset the flags
        self.sharedSnifferEnabledFlag = Value("i", 1)
        self.sharedDataAdderEnabledFlag = Value("i", 1)

        # Start the sniffer process and append
        # the sniffed data to the current list using the adder thread
        snifferReceivePipe, snifferSendPipe = Pipe()

        # First start the DataAdderThread...
        self.dataAdderThread = DataAdderThread(snifferReceivePipe,
                                               self.sharedDataAdderEnabledFlag,
                                               curSampleIndex)

        self.dataAdderThread.signalSniffedPacket.connect(adderMethod)
        self.dataAdderThread.start()

        # ... then start the SnifferProcess
        self.snifferProcess = SnifferProcess(snifferSendPipe,
                                             self.sharedSnifferEnabledFlag,
                                             Strings.filterTabLoggerName,
                                             self.CANData)
        self.snifferProcess.start()

        if curSampleIndex == -1:
            self.logger.info(Strings.filterTabCollectingNoiseLog)
        else:
            self.logger.info(Strings.filterTabNewRunStarted +
                             " " + str(curSampleIndex))

    def stopSnifferAndAdder(self):
        """
        Stop the DataAdderThread and SnifferProcess using the shared integer variable.
        """

        # Stop SnifferProcess and DataAdderThread
        # Stop the Sniffer
        with self.sharedSnifferEnabledFlag.get_lock():
            self.sharedSnifferEnabledFlag.value = 0
        self.snifferProcess.join()
        self.logger.debug(Strings.snifferProcessTerminated)

        # Stop the DataAdder
        with self.sharedDataAdderEnabledFlag.get_lock():
            self.sharedDataAdderEnabledFlag.value = 0
        self.dataAdderThread.wait()
        self.logger.debug(Strings.filterTabDataAdderThreadTerminated)

    def clear(self, returnOldPackets=False):
        """
        Clear the currently displayed data on the GUI and in the lists.
        """
        AbstractTab.clear(self)
        self.noiseData = []

    def outputRemainingPackets(self, remainingPackets):
        """
        Output all remaining packets after filtering to the table view.
        Note: This also clears previous data

        :param remainingPackets: Raw packet list to display
        """
        self.clear()
        for rawPacket in remainingPackets:
            self.addPacket(rawPacket)

    def addSniffedNoise(self, dummyIndex, packet):
        """
        Adds the passed packet data to ``noiseData``.
        This method gets called by a DataAdderThread.

        :param dummyIndex: Not used, only exists to match the signature defined in the signal of the DataAdderThread
        :param packet: The packet object to extract and add data from
        """

        assert packet is not None
        # Use a list of values because it's much faster than creating "Packet" objects
        self.noiseData.append([packet.CANID,
                               packet.data,
                               packet.length,
                               packet.timestamp])

    def addSniffedPacketToSample(self, curSampleIndex, packet):
        """
        Adds a sniffed packet to the sample defined by ``curSampleIndex``.
        Gets called by a DataAdderThread.

        :param curSampleIndex: The sample index to get a list from ``rawData[curSampleIndex]``
        :param packet: Packet data to add
        :return:
        """

        assert packet is not None

        # Use a list of values because it's much faster than creating "Packet" objects
        self.rawData[curSampleIndex].append([packet.CANID,
                                             packet.data,
                                             packet.length,
                                             packet.timestamp])

    def toggleGUIElements(self, state):
        """
        {En, Dis}able all GUI elements that are used to change filter settings

        :param state: Boolean value to indicate whether to enable or disable elements
        """

        for GUIElement in [self.spinBoxFilterTimeCollectNoise,
                           self.spinBoxFilterSampleAmount,
                           self.buttonFilterStart,
                           self.buttonFilterInterfaceSettings,
                           self.buttonFilterDataClear,
                           self.packetTableView]:
            GUIElement.setEnabled(state)


####

class DataAdderThread(QtCore.QThread):

    """
    This thread receives data from the sniffer process and
    emits a signal which causes the main thread to add the packets.
    """

    #: Emit a signal to the main thread when items are ready to be added
    #: This emits the packet and the current sample index
    signalSniffedPacket = QtCore.Signal(int, object)

    def __init__(self, snifferReceivePipe, sharedEnabledFlag, curSampleIndex):
        # Call the superclass constructor
        QtCore.QThread.__init__(self)
        self.curSampleIndex = curSampleIndex
        # Attributes to manage the sniffer process
        self.sharedEnabledFlag = sharedEnabledFlag
        self.snifferReceivePipe = snifferReceivePipe

    def frameToList(self, frame):
        """
        Converts a received pyvit frame to raw list data.
        After that, the data is emitted using ``signalSniffedPacket``

        :param frame: pyvit CAN frame
        """

        # Extract the data to be displayed
        id = str(hex(frame.arb_id)).replace("0x", "").upper()
        # cut "0x" and always use an additional leading zero if needed
        data = "".join(hex(value)[2:].zfill(2) for value in frame.data).upper()
        length = frame.dlc
        timestamp = str(frame.timestamp)

        packet = Packet(None, id, data, timestamp, "", length=length)

        self.signalSniffedPacket.emit(self.curSampleIndex,
                                      packet)

    def run(self):
        """
        As long as ``sharedEnabledFlag`` is not set to ``0`` data will be
        received using the pipe and processed using :func:`frameToList`.
        """

        while self.sharedEnabledFlag.value == 1:
            frame = None
            try:
                # Receive data from the SnifferProcess via a pipe
                if self.snifferReceivePipe.poll(1):
                    frame = self.snifferReceivePipe.recv()
            except EOFError:
                break
            else:
                if frame is not None:
                    self.frameToList(frame)
