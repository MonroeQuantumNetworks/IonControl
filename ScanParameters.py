# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
import copy
       
ScanExperimentForm, ScanExperimentBase = PyQt4.uic.loadUiType(r'ui\ScanParameters.ui')

import ScanList
from modules import enum

class Scan:
    pass

class Settings:
    def __init__(self):
        self.parameter = None
        self.minimum = "0 ms"
        self.maximum = "10 ms"
        self.steps = 10
        self.scantype = 0
        self.scanMode = 0
        self.rewriteDDS = False
        
    def __eq__(self, other):
        return ( self.parameter == other.parameter and
                self.minimum == other.minimum and
                self.maximum == other.maximum and
                self.steps == other.steps and
                self.scantype == other.scantype and
                self.scanMode == other.scanMode and 
                self.rewriteDDS == other.rewriteDDS)

class ScanParameters(ScanExperimentForm, ScanExperimentBase ):
    ScanModes = enum.enum('SingleScan','RepeatedScan','StepInPlace')
    def __init__(self,config,parentname,parent=0):
        ScanExperimentForm.__init__(self,parent)
        ScanExperimentBase.__init__(self)
        self.config = config
        self.configname = 'ScanParameters.'+parentname
        # History and Dictionary
        self.settingsDict = dict()
        self.settingsHistory = list()
        self.settingsHistoryPointer = None
        self.historyFinalState = None

    def setupUi(self, parent):
        ScanExperimentForm.setupUi(self,parent)
        # History and Dictionary
        self.saveButton.clicked.connect( self.onSave )
        self.undoButton.clicked.connect( self.onUndo )
        self.redoButton.clicked.connect( self.onRedo )
        self.comboBox.currentIndexChanged['QString'].connect( self.onLoad )
        self.setSettings( self.config.get(self.configname,Settings()) )
        #self.commitButton.clicked.connect( self.onCommit )
        #self.lineEdit.editingFinished.connect( self.onEditingFinished )

    def setVariables(self, variabledict):
        self.variabledict = variabledict
        for name, var in variabledict.iteritems():
            if var.type == "parameter":
                self.comboBoxParameter.addItem(var.name)
        if self.settings.parameter is not None:
            self.comboBoxParameter.setCurrentIndex(self.comboBoxParameter.findText(self.settings.parameter) )
            
    def setScanNames(self, scannames):
        for name in scannames:
            self.comboBoxParameter.addItem(name)
                
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
        self.settings.rewriteDDS = self.rewriteDDSCheckBox.isChecked()
        self.settings.scanMode = self.scanModeComboBox.currentIndex()
        Scan.rewriteDDS = self.settings.rewriteDDS
        Scan.scanMode = self.settings.scanMode
        self.onCommit()
        return Scan
        
    def onClose(self):
        self.config[self.configname] = self.settings
               
    # History stuff
    def setSettings(self, settings):
        self.settings = copy.copy(settings)
        self.minimumBox.setValue(self.settings.minimum)
        self.maximumBox.setValue(self.settings.maximum)
        self.stepsBox.setValue(self.settings.steps)
        self.scanTypeCombo.setCurrentIndex(self.settings.scantype )
        self.rewriteDDSCheckBox.setChecked( self.settings.rewriteDDS )
        self.progressBar.setVisible( False )
        self.scanModeComboBox.setCurrentIndex( self.settings.scanMode )
    
    def onRedo(self):
        if self.settingsHistoryPointer<len(self.settingsHistory):
            self.settingsHistoryPointer += 1
            if self.settingsHistoryPointer<len(self.settingsHistory):
                self.setSettings( self.settingsHistory[self.settingsHistoryPointer])
            elif self.historyFinalState:
                self.setSettings( self.historyFinalState )
                self.historyFinalState = None
     
    def onUndo(self):
        if self.settingsHistoryPointer>0:
            if self.settingsHistoryPointer==len(self.settingsHistory):
                self.historyFinalState = copy.copy( self.settings )
            self.settingsHistoryPointer -= 1
            self.setSettings( self.settingsHistory[self.settingsHistoryPointer] )
    
    def onSave(self):
        name = str(self.comboBox.currentText())
        if name != '':
            if name not in self.settingsDict:
                if self.comboBox.findText(name)==-1:
                    self.comboBox.addItem(name)
                print "adding to combo", name
            self.settingsDict[name] = copy.copy(self.settings)
    
    def onLoad(self,name):
        name = str(name)
        print "onLoad", name
        if name !='' and name in self.settingsDict:
            self.setSettings(self.settingsDict[name])
            print "restore", self.settingsDict[name].text
        else:
            print self.settingsDict

   
    def onCommit(self):
        if len(self.settingsHistory)==0 or self.settings!=self.settingsHistory[-1]:
            self.settingsHistory.append(copy.copy(self.settings))
            self.settingsHistoryPointer = len(self.settingsHistory)

        