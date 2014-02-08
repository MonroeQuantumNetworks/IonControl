# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 14:28:08 2013

@author: wolverine
"""

import logging
import operator
import os.path

from PyQt4 import QtCore, QtGui
import PyQt4.uic

from GateDefinition import GateDefinition
from GateSequenceCompiler import GateSequenceCompiler
from GateSequenceContainer import GateSequenceContainer
from modules.enum import enum


Form, Base = PyQt4.uic.loadUiType('ui/GateSequence.ui')


class Settings:
    stateFields = [ 'enabled', 'gate', 'gateDefinition', 'gateSequence', 'active', 'startAddressParam', 'thisSequenceRepetition', 'debug' ]
    def __init__(self):
        self.enabled = False
        self.gate = []
        self.gateDefinition = None
        self.gateSequence = None
        self.active = 0
        self.lastDir = ""
        self.startAddressParam = ""
        self.gateSequenceCache = dict()
        self.gateDefinitionCache = dict()
        self.thisSequenceRepetition = 10
        self.debug = False
        
    def __setstate__(self,d):
        self.__dict__ = d

    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self,other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))
        
    def __repr__(self):
        m = list()
        m.append( "GateSequence {0}".format( {True:'enabled',False:'disabled'}[self.enabled]) )
        m.append( "Gate Definition: {0}".format(self.gateDefinition))
        m.append( "GateSequence StartAddressParam {0}".format(self.startAddressParam))
        if self.active==0: # Full list scan
            m.append( "GateSequence: {0}".format(self.gateSequence))
        else:
            m.append( "Gate {0}".format(self.gate))
        return "\n".join(m)

    documentationList = [ 'gateDefinition', 'gateSequence', 'startAddressParam' ]
    
    def documentationString(self):
        r = "\r\n".join( [ "{0}\t{1}".format(field,getattr(self,field)) for field in self.documentationList] )
        return r
        

class GateSequenceUi(Form,Base):    
    Mode = enum('FullList', 'Gate')
    valueChanged = QtCore.pyqtSignal()
    def __init__(self,parent=None):
        Form.__init__(self)
        Base.__init__(self,parent)
        
        
    def postInit(self,name,config,pulseProgram):
        self.config = config
        self.configname = "GateSequenceUi."+name
        self.settings = self.config.get(self.configname,Settings())

        self.gatedef = GateDefinition()
#        if self.settings.gateDefinition:
#            self.loadGateDefinition( self.settings.gateDefinition )
    
        self.gateSequenceContainer = GateSequenceContainer(self.gatedef)
#        if self.settings.gateSequence:
#            self.loadGateSequenceList(self.settings.gateSequence)
            
        self.gateSequenceCompiler = GateSequenceCompiler(pulseProgram)

    
    def setupUi(self,parent):
        super(GateSequenceUi,self).setupUi(parent)
        self.setSettings( self.settings )
        self.GateSequenceEnableCheckBox.stateChanged.connect( self.onEnableChanged )
        self.GateDefinitionButton.clicked.connect( self.onLoadGateDefinition )
        self.GateSequenceButton.clicked.connect( self.onLoadGateSequenceList )
        self.FullListRadioButton.toggled.connect( self.onRadioButtonToggled )
        self.GateEdit.editingFinished.connect( self.onGateEditChanged )
        self.StartAddressBox.currentIndexChanged['QString'].connect( self.onStartAddressParam )
        self.repetitionSpinBox.valueChanged.connect( self.onRepetitionChanged )
        self.GateSequenceBox.currentIndexChanged[str].connect( self.onGateSequenceChanged )
        self.GateDefinitionBox.currentIndexChanged[str].connect( self.onGateDefinitionChanged )
        self.debugCheckBox.stateChanged.connect( self.onDebugChanged )
        
    def getSettings(self):
        logger = logging.getLogger(__name__)
        logger.debug( "GateSequenceUi GetSettings {0}".format(self.settings.__dict__) )
        return self.settings
        
    def setSettings(self,settings):
        logger = logging.getLogger(__name__)
        logger.debug( str( settings) )
        logger.debug( "GateSequenceUi SetSettings {0}".format( settings.__dict__ ) )
        self.settings = settings
        self.GateSequenceEnableCheckBox.setChecked( self.settings.enabled )
        self.GateSequenceFrame.setEnabled( self.settings.enabled )
        self.GateSequenceFrame.setEnabled( self.settings.enabled )
        self.GateEdit.setText( ", ".join(self.settings.gate ))
        self.repetitionSpinBox.setValue( self.settings.thisSequenceRepetition )
        if self.settings.startAddressParam:
            self.StartAddressBox.setCurrentIndex(self.StartAddressBox.findText(self.settings.startAddressParam) )
        else:
            self.settings.startAddressParam = str(self.StartAddressBox.currentText())
        self.settings.startAddressParam = str(self.settings.startAddressParam)
        try:
            oldState = self.GateDefinitionBox.blockSignals(True);
            self.GateDefinitionBox.clear()
            self.GateDefinitionBox.addItems( self.settings.gateDefinitionCache.keys() )
            self.GateDefinitionBox.blockSignals(oldState);
            oldState = self.GateSequenceBox.blockSignals(True);
            self.GateSequenceBox.clear()
            self.GateSequenceBox.addItems( self.settings.gateSequenceCache.keys() )
            self.GateSequenceBox.blockSignals(oldState);
            if self.settings.gateDefinition and self.settings.gateDefinition in self.settings.gateDefinitionCache:
                self.loadGateDefinition( self.settings.gateDefinitionCache[self.settings.gateDefinition] )
                self.GateDefinitionBox.setCurrentIndex(self.GateDefinitionBox.findText(self.settings.gateDefinition))
            if self.settings.gateSequence and self.settings.gateSequence in self.settings.gateSequenceCache:
                self.loadGateSequenceList( self.settings.gateSequenceCache[self.settings.gateSequence] )
                self.GateSequenceBox.setCurrentIndex(self.GateSequenceBox.findText(self.settings.gateSequence))
        except IOError as err:
            logger.error( "{0} during loading of GateSequence Files, ignored.".format(err) )

    def documentationString(self):
        return repr(self.settings)        
            
    def onGateDefinitionChanged(self, name):
        name = str(name)
        if name in self.settings.gateDefinitionCache:
            self.loadGateDefinition( self.settings.gateDefinitionCache[name] )  
        self.valueChanged.emit()          
            
    def onGateSequenceChanged(self, name):
        name = str(name)
        if name in self.settings.gateSequenceCache:
            self.loadGateSequenceList( self.settings.gateSequenceCache[name] )
        self.valueChanged.emit()          
            
    def onRepetitionChanged(self, value):
        self.settings.thisSequenceRepetition = value
        self.valueChanged.emit()          
        
    def onStartAddressParam(self,name):
        self.settings.startAddressParam = str(name)       
        self.valueChanged.emit()          
        
    def onEnableChanged(self, state):
        self.settings.enabled = state == QtCore.Qt.Checked
        self.GateSequenceFrame.setEnabled( self.settings.enabled )
        self.valueChanged.emit()          
        
    def onDebugChanged(self, state):
        self.settings.debug = state == QtCore.Qt.Checked        
        self.valueChanged.emit()          
        
    def close(self):
        self.config[self.configname] = self.settings
                
    def onLoadGateDefinition(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open Gate definition file:", self.settings.lastDir))
        if path!="":
            filedir, filename = os.path.split(path)
            self.settings.lastDir = filedir
            self.loadGateDefinition(path)
            if filename not in self.settings.gateDefinitionCache:
                self.settings.gateDefinitionCache[filename] = path
                self.GateDefinitionBox.addItem(filename)
                self.GateDefinitionBox.setCurrentIndex( self.GateDefinitionBox.findText(filename))
        self.valueChanged.emit()          

    def loadGateDefinition(self, path):
        self.gatedef.loadGateDefinition(path)    
        _, filename = os.path.split(path)
        self.settings.gateDefinition = filename
        self.GateDefinitionBox.setCurrentIndex(self.GateDefinitionBox.findText(filename))
        self.gatedef.printGates()
        self.valueChanged.emit()          
    
    def onLoadGateSequenceList(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open Gate Set file:", self.settings.lastDir))
        if path!="":
            filedir, filename = os.path.split(path)
            self.settings.lastDir = filedir
            self.loadGateSequenceList(path)
            if filename not in self.settings.gateSequenceCache:
                self.settings.gateSequenceCache[filename] = path
                self.GateSequenceBox.addItem(filename)
                self.GateSequenceBox.setCurrentIndex( self.GateSequenceBox.findText(filename))
        self.valueChanged.emit()          
            
    def loadGateSequenceList(self, path):
        logger = logging.getLogger(__name__)
        self.gateSequenceContainer.loadXml(path)
        logger.debug( "loaded {0} gateSequences from {1}.".format(len(self.gateSequenceContainer.GateSequenceDict), path) )
        _, filename = os.path.split(path)
        self.settings.gateSequence = filename
        self.GateSequenceBox.setCurrentIndex(self.GateSequenceBox.findText(filename))
    
    def onGateEditChanged(self):
        self.settings.gate = map(operator.methodcaller('strip'),str(self.GateEdit.text()).split(','))
        self.GateEdit.setText( ", ".join(self.settings.gate ))
        self.valueChanged.emit()          
    
    def onRadioButtonToggled(self):
        if self.FullListRadioButton.isChecked():
            self.settings.active = self.Mode.FullList 
        else:
            self.settings.active = self.Mode.Gate   
        self.valueChanged.emit()          
            
    def gateSequenceScanData(self):
        if self.settings.active == self.Mode.FullList:
            address, data = self.gateSequenceCompiler.gateSequencesCompile( self.gateSequenceContainer )
        else:
            self.gateSequenceCompiler.gateCompile( self.gateSequenceContainer.gateDefinition )
            data = self.gateSequenceCompiler.gateSequenceCompile( self.settings.gate )
            address = [0]*self.settings.thisSequenceRepetition
        return address, data, self.settings
        
    def setVariables(self, variabledict):
        self.variabledict = variabledict
        #oldParameterName = self.StartAddressBox.currentText()
        self.StartAddressBox.clear()
        for _, var in iter(sorted(variabledict.iteritems())):
            if var.type == "address":
                self.StartAddressBox.addItem(var.name)
        if self.settings.startAddressParam:
            self.StartAddressBox.setCurrentIndex(self.StartAddressBox.findText(self.settings.startAddressParam) )
        else:
            self.settings.startAddressParam = self.StartAddressBox.currentText()


if __name__ == "__main__":
    from pulseProgram.PulseProgram import PulseProgram
    pp = PulseProgram()
    pp.debug = False
    pp.loadSource(r"C:\Users\Public\Documents\experiments\test3\config\PulsePrograms\YbGateSequenceTomography.pp")
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = GateSequenceUi()
    ui.postInit("test",config,pp)
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    app.exec_()
    address, data, parameter = ui.gateSequenceScanData()
    a = address[541]
    l = data[ a/4 ]
    print a, l
    print data[ a/4 : a/4+3*l+1 ]
    address, data, parameter = ui.gateSequenceScanData()
    a = address[36]
    l = data[ a/4 ]
    print a, l
    print data[ a/4 : a/4+3*l+1 ]
    print config
    print "done"
