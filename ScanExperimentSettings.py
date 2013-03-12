# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
       
ScanExperimentSettingsForm, ScanExperimentSettingsBase = PyQt4.uic.loadUiType(r'ui\ScanExperimentSettings.ui')


class Scan:
    pass

class Settings:
    project = ""
    histogramBins = 50
    filename = "Data.dat"
    integrate = False
    counter = 0

class ScanExperimentSettings(ScanExperimentSettingsForm, ScanExperimentSettingsBase ):
    def __init__(self,config,parentname,parent=0):
        ScanExperimentSettingsForm.__init__(self,parent)
        ScanExperimentSettingsBase.__init__(self)
        self.config = config
        self.configname = 'ScanExperimentSettings.'+parentname
        self.settings = self.config.get(self.configname,Settings())

    def setupUi(self, parent):
        ScanExperimentSettingsForm.setupUi(self,parent)
        self.projectEdit.setText(self.settings.project)
        self.projectEdit.editingFinished.connect(self.onProjectEditingFinished)
        self.histogramBinsBox.setValue(self.settings.histogramBins)
        self.histogramBinsBox.valueChanged.connect(self.onHistogramBinsChanged)
        self.filenameEdit.setText( self.settings.filename )
        self.filenameEdit.editingFinished.connect(self.onFilenameEditingFinished)
        self.integrateHistogramButton.setChecked( self.settings.integrate )
        self.integrateHistogramButton.clicked.connect( self.onIntegrateHistogramClicked )
        self.counterSpinBox.setValue( self.settings.counter )
        self.counterSpinBox.valueChanged.connect( self.onCounterChanged )

    def onIntegrateHistogramClicked(self):
        self.settings.integrate = self.integrateHistogramButton.isChecked()

    def onFilenameEditingFinished(self):
        self.settings.filename = str(self.filenameEdit.text())

    def onProjectEditingFinished(self):
        self.settings.project = str(self.projectEdit.text())
        
    def onHistogramBinsChanged(self, bins):
        self.settings.histogramBins = bins
        
    def onCounterChanged(self, value):
        self.settings.counter = value
    
    def onClose(self):
        self.config[self.configname] = self.settings
        