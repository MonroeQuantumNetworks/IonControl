# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
       
ScanExperimentForm, ScanExperimentBase = PyQt4.uic.loadUiType(r'ui\ScanParameters.ui')

import ScanList

class Scan:
    pass

class Settings:
    parameter = None
    minimum = "0 ms"
    maximum = "10 ms"
    steps = 10
    scantype = 0
    repeat = False
    stepInPlace = False

class ScanParameters(ScanExperimentForm, ScanExperimentBase ):
    def __init__(self,config,parentname,parent=0):
        ScanExperimentForm.__init__(self,parent)
        ScanExperimentBase.__init__(self)
        self.config = config
        self.configname = 'ScanParameters.'+parentname
        self.settings = self.config.get(self.configname,Settings())

    def setupUi(self, parent):
        ScanExperimentForm.setupUi(self,parent)
        self.minimumBox.setValue(self.settings.minimum)
        self.maximumBox.setValue(self.settings.maximum)
        self.stepsBox.setValue(self.settings.steps)
        self.scanTypeCombo.setCurrentIndex(self.settings.scantype )
        self.repeatCheckBox.setChecked( self.settings.repeat )
        self.stepInPlaceCheckBox.setCheck( self.settings.stepInPlace )

    def setVariables(self, variabledict):
        self.variabledict = variabledict
        for name, var in variabledict.iteritems():
            if var.type == "parameter":
                self.comboBoxParameter.addItem(var.name)
        if self.settings.parameter is not None:
            self.comboBoxParameter.setCurrentIndex(self.comboBoxParameter.findText(self.settings.parameter) )
                
    def getScan(self):
        Scan.name = str(self.comboBoxParameter.currentText())
        Scan.start = self.minimumBox.value()
        Scan.stop = self.maximumBox.value()
        Scan.steps = self.stepsBox.value()
        Scan.type = [ ScanList.ScanType.LinearUp, ScanList.ScanType.LinearDown, ScanList.ScanType.Randomized][self.scanTypeCombo.currentIndex()]
        Scan.list = ScanList.scanList( Scan.start, Scan.stop, Scan.steps, Scan.type )
        self.settings.parameter = Scan.name
        self.settings.minimum = self.minimumBox.value()
        self.settings.maximum = self.maximumBox.value()
        self.settings.steps = self.stepsBox.value()
        self.settings.scantype = self.scanTypeCombo.currentIndex()
        self.settings.repeat = self.repeatCheckBox.isChecked()
        self.settings.stepInPlace = self.stepInPlaceCeckBox.isChecked()
        Scan.repeat = self.settings.repeat
        Scan.stepInPlace = self.settings.stepInPlace
        return Scan
        
    def onClose(self):
        self.config[self.configname] = self.settings
        