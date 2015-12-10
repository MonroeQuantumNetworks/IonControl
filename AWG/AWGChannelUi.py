"""
Created on 08 Dec 2015 at 4:11 PM

author: jmizrahi
"""

import logging
import os

import PyQt4.uic
from PyQt4 import QtCore

from AWG.AWGWaveform import AWGWaveform
from AWG.AWGSegmentTableModel import AWGSegmentTableModel
from trace.pens import solidBluePen

AWGChanneluipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\AWGChannel.ui')
AWGChannelForm, AWGChannelBase = PyQt4.uic.loadUiType(AWGChanneluipath)

class AWGChannelUi(AWGChannelForm, AWGChannelBase):
    """interface for one channel of the AWG.

    Args:
       settings (Settings): AWG settings
       channel (int): channel number for this AWGChannel
    """
    dependenciesChanged = QtCore.pyqtSignal(int)
    def __init__(self, channel, settings, globalDict, parent=None):
        AWGChannelBase.__init__(self, parent)
        AWGChannelForm.__init__(self)
        self.settings = settings
        self.channel = channel
        self.globalDict = globalDict
        self.waveform = AWGWaveform(channel, settings)
        self.waveform.updateDependencies()

    @property
    def plotEnabled(self):
        return self.settings.channelSettingsList[self.channel]['plotEnabled']

    @plotEnabled.setter
    def plotEnabled(self, val):
        self.settings.channelSettingsList[self.channel]['plotEnabled'] = val
        self.settings.saveIfNecessary()

    @property
    def equation(self):
        return self.settings.channelSettingsList[self.channel]['equation']

    @equation.setter
    def equation(self, val):
        self.settings.channelSettingsList[self.channel]['equation'] = val
        self.waveform.updateDependencies()
        self.dependenciesChanged.emit(self.channel)

    def setupUi(self, parent):
        AWGChannelForm.setupUi(self, parent)
        #equation
        self.equationEdit.setText(self.equation)
        self.evalButton.clicked.connect(self.onEquation)
        self.equationEdit.returnPressed.connect(self.onEquation)
        self.equationEdit.setToolTip("use 't' for time variable")

        #segment table
        self.segmentModel = AWGSegmentTableModel(self.channel, self.settings, self.globalDict)
        self.segmentView.setModel(self.segmentModel)
        self.segmentModel.segmentChanged.connect(self.onSegmentChanged)
        self.addSegmentButton.clicked.connect(self.onAddSegment)
        self.removeSegmentButton.clicked.connect(self.onRemoveSegment)

        #plot
        self.plot.setTimeAxis(False)
        self.plotCheckbox.setChecked(self.plotEnabled)
        self.plot.setVisible(self.plotEnabled)
        self.plotCheckbox.stateChanged.connect(self.onPlotCheckbox)
        self.replot()

    def onPlotCheckbox(self, checked):
        self.plotEnabled = checked
        if not checked:
            self.plot.getItem(0,0).clear()
        elif checked:
            self.replot()
        self.plot.setVisible(checked)

    def replot(self):
        logger = logging.getLogger(__name__)
        if self.plotEnabled:
            try:
                points = self.waveform.evaluate()
                self.plot.getItem(0,0).clear()
                self.plot.getItem(0,0).plot(points, pen=solidBluePen)
            except Exception as e:
                logger.warning(e.__class__.__name__ + ": " + str(e))

    def onEquation(self):
        self.equation = str(self.equationEdit.text())

    def onSegmentChanged(self, channel=None, row=None, column=None, value=None):
        self.waveform.updateDependencies()
        self.dependenciesChanged.emit(self.channel)
        self.settings.saveIfNecessary()

    def onAddSegment(self):
        self.segmentModel.addSegment()
        self.onSegmentChanged()

    def onRemoveSegment(self):
        selectedIndexes = self.segmentView.selectedIndexes()
        selectedRows = list({index.row() for index in selectedIndexes})
        selectedRows.sort(reverse=True) #go backwards so the earlier rows don't change their row number
        for row in selectedRows:
            self.segmentModel.removeSegment(row)
        self.onSegmentChanged()