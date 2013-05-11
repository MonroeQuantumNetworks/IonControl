# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
import copy
import functools
from PyQt4 import QtCore
       
ScanExperimentForm, ScanExperimentBase = PyQt4.uic.loadUiType(r'ui\ScanParameters.ui')

import ScanList
from modules import enum

class Scan:
    def __init__(self):
        self.name = None
        self.start = None
        self.stop = None
        self.steps = None
        self.type = None
        self.rewriteDDS = None
        self.scanMode = None
        self.filename = None
        self.autoSave = None
        
    def __repr__(self):
        r = "Scanning parameter: {0}\nScanning From: {1}\nScanning To: {2}\n".format(self.name,self.start,self.stop)
        r+= "Scanning Steps: {0}\nScanning type: {1}\nScanning rewriteDDS: {2}\n".format(self.steps,self.type,self.rewriteDDS)
        r+= "Scanning mode: {0}".format(self.scanMode)
        return r

class Settings:
    def __init__(self):
        self.parameter = None
        self.minimum = "0 ms"
        self.maximum = "10 ms"
        self.steps = 10
        self.scantype = 0
        self.scanMode = 0
        self.rewriteDDS = False
        self.filename = ''
        self.autoSave = False
        
    def __eq__(self, other):
        return ( self.parameter == other.parameter and
                self.minimum == other.minimum and
                self.maximum == other.maximum and
                self.steps == other.steps and
                self.scantype == other.scantype and
                self.scanMode == other.scanMode and 
                self.rewriteDDS == other.rewriteDDS and
                self.filename == other.filename and
                self.autoSave == other.autoSave )

class ScanParameters(ScanExperimentForm, ScanExperimentBase ):
    ScanModes = enum.enum('SingleScan','RepeatedScan','StepInPlace')
    def __init__(self,config,parentname,parent=0):
        ScanExperimentForm.__init__(self,parent)
        ScanExperimentBase.__init__(self)
        self.config = config
        self.configname = 'ScanParameters.'+parentname
        # History and Dictionary
        self.settingsDict = self.config.get(self.configname+'.dict',dict())
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
        try:
            self.setSettings( self.config.get(self.configname,Settings()) )
        except AttributeError as e:
            print "Ignoring exception",e
        for name in self.settingsDict:
            self.comboBox.addItem(name)
        # update connections
        self.comboBoxParameter.currentIndexChanged['QString'].connect( self.onCurrentTextChanged )        
        self.minimumBox.valueChanged.connect( functools.partial(self.onValueChanged,'minimum') )
        self.maximumBox.valueChanged.connect( functools.partial(self.onValueChanged,'maximum') )
        self.stepsBox.valueChanged.connect( functools.partial(self.onValueChanged,'steps') )
        self.scanTypeCombo.currentIndexChanged[int].connect( functools.partial(self.onCurrentIndexChanged,'scantype') )
        self.rewriteDDSCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'rewriteDDS') )
        self.autoSaveCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'autoSave') )
        self.scanModeComboBox.currentIndexChanged[int].connect( functools.partial(self.onCurrentIndexChanged,'scanMode') )
        self.filenameEdit.editingFinished.connect( self.onNewFilename )
        
    def onNewFilename(self):
        self.settings.filename = str(self.filenameEdit.text())
        
    def beginChange(self):
        self.tempSettings = copy.copy( self.settings )

    def commitChange(self): 
        pass
        #if self.tempSettings!=self.settings:
        #    self.comboBox.setEditText('')
        
    def onStateChanged(self, attribute, state):
        self.beginChange()
        setattr( self.settings, attribute, (state == QtCore.Qt.Checked)  )
        self.commitChange()
        
    def onCurrentTextChanged(self, text):
        self.beginChange()
        self.settings.parameter = str(text)
        self.commitChange()
    
    def onCurrentIndexChanged(self, attribute, index):
        self.beginChange()
        setattr( self.settings, attribute, index )
        self.commitChange()
    
    def onValueChanged(self, attribute, value):
        self.beginChange()
        setattr( self.settings, attribute, value )
        self.commitChange()
        
    def setVariables(self, variabledict):
        self.variabledict = variabledict
        oldParameterName = self.comboBoxParameter.currentText()
        self.comboBoxParameter.clear()
        for name, var in iter(sorted(variabledict.iteritems())):
            if var.type == "parameter":
                self.comboBoxParameter.addItem(var.name)
        if oldParameterName and oldParameterName!="":
            self.comboBoxParameter.setCurrentIndex(self.comboBoxParameter.findText(oldParameterName) )
            
    def setScanNames(self, scannames):
        self.comboBoxParameter.clear()
        for name in scannames:
            self.comboBoxParameter.addItem(name)
        self.comboBoxParameter.setCurrentIndex( self.comboBoxParameter.findText(self.settings.parameter))
        print self.configname,"activating", self.settings.parameter
                
    def getScan(self):
        scan = Scan()
        scan.name = self.settings.parameter
        scan.start = self.settings.minimum
        scan.stop = self.settings.maximum
        scan.steps = self.settings.steps
        scan.type = [ ScanList.ScanType.LinearUp, ScanList.ScanType.LinearDown, ScanList.ScanType.Randomized][self.settings.scantype]
        scan.list = ScanList.scanList( scan.start, scan.stop, scan.steps, scan.type )
        scan.rewriteDDS = self.settings.rewriteDDS
        scan.scanMode = self.settings.scanMode
        scan.filename = getattr(self.settings,'filename','')
        scan.autoSave = getattr(self.settings,'autoSave',False)
        self.onCommit()
        return scan
        
    def onClose(self):
        self.config[self.configname] = self.settings
        self.config[self.configname+'.dict'] = self.settingsDict
               
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
        if settings.parameter: self.comboBoxParameter.setCurrentIndex( self.comboBoxParameter.findText(settings.parameter))
        self.filenameEdit.setText( getattr(self.settings,'filename','') )
    
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
                print self.configname, "adding to combo", name
            self.settingsDict[name] = copy.copy(self.settings)
    
    def onLoad(self,name):
        name = str(name)
        print self.configname, "onLoad", name
        if name !='' and name in self.settingsDict:
            self.setSettings(self.settingsDict[name])
        else:
            print self.configname, self.settingsDict

   
    def onCommit(self):
        if len(self.settingsHistory)==0 or self.settings!=self.settingsHistory[-1]:
            self.settingsHistory.append(copy.copy(self.settings))
            self.settingsHistoryPointer = len(self.settingsHistory)

        