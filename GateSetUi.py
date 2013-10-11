# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 14:28:08 2013

@author: wolverine
"""

import PyQt4.uic
from PyQt4 import QtCore, QtGui
import operator
from modules.enum import enum
import os.path

from GateDefinition import GateDefinition
from GateSetContainer import GateSetContainer
from GateSetCompiler import GateSetCompiler

Form, Base = PyQt4.uic.loadUiType('ui/GateSet.ui')


class Settings(object):
    def __init__(self):
        self.enabled = False
        self.gate = []
        self.gateDefinition = None
        self.gateSet = None
        self.active = 0
        self.lastDir = ""
        self.startAddressParam = ""
        self.gateSetCache = dict()
        self.gateDefinitionCache = dict()
        self.thisSequenceRepetition = 10
        self.debug = False
        
    def __setstate__(self,d):
        self.__dict__ = d
        self.__dict__.setdefault( "gateSetCache", dict() )
        self.__dict__.setdefault( "gateDefinitionCache", dict() )
        self.__dict__.setdefault( "thisSequenceRepetition", 10 )
        self.__dict__.setdefault( "debug", False )
        
    def __repr__(self):
        m = list()
        m.append( "GateSet {0}".format( {True:'enabled',False:'disabled'}[self.enabled]) )
        m.append( "Gate Definition: {0}".format(self.gateDefinition))
        m.append( "GateSet StartAddressParam {0}".format(self.startAddressParam))
        if self.active==0: # Full list scan
            m.append( "GateSet: {0}".format(self.gateSet))
        else:
            m.append( "Gate {0}".format(self.gate))
        return "\n".join(m)

    documentationList = [ 'gateDefinition', 'gateSet', 'startAddressParam' ]
    
    def documentationString(self):
        r = "\r\n".join( [ "{0}\t{1}".format(field,getattr(self,field)) for field in self.documentationList] )
        return r
        

class GateSetUi(Form,Base):    
    Mode = enum('FullList', 'Gate')
    def __init__(self,parent=None):
        Form.__init__(self)
        Base.__init__(self,parent)
        
        
    def postInit(self,name,config,pulseProgram):
        self.config = config
        self.configname = "GateSetUi."+name
        self.settings = self.config.get(self.configname,Settings())

        self.gatedef = GateDefinition()
#        if self.settings.gateDefinition:
#            self.loadGateDefinition( self.settings.gateDefinition )
    
        self.gateSetContainer = GateSetContainer(self.gatedef)
#        if self.settings.gateSet:
#            self.loadGateSetList(self.settings.gateSet)
            
        self.gateSetCompiler = GateSetCompiler(pulseProgram)

    
    def setupUi(self,parent):
        super(GateSetUi,self).setupUi(parent)
        self.setSettings( self.settings )
        self.GateSetEnableCheckBox.stateChanged.connect( self.onEnableChanged )
        self.GateDefinitionButton.clicked.connect( self.onLoadGateDefinition )
        self.GateSetButton.clicked.connect( self.onLoadGateSetList )
        self.FullListRadioButton.toggled.connect( self.onRadioButtonToggled )
        self.GateEdit.editingFinished.connect( self.onGateEditChanged )
        self.StartAddressBox.currentIndexChanged['QString'].connect( self.onStartAddressParam )
        self.repetitionSpinBox.valueChanged.connect( self.onRepetitionChanged )
        self.GateSetBox.currentIndexChanged[str].connect( self.onGateSetChanged )
        self.GateDefinitionBox.currentIndexChanged[str].connect( self.onGateDefinitionChanged )
        self.debugCheckBox.stateChanged.connect( self.onDebugChanged )
        
    def getSettings(self):
        if self.settings.debug:
            print "GateSetUi GetSettings", self.settings.__dict__
        return self.settings
        
    def setSettings(self,settings):
        if self.settings.debug:
            print settings
            print "GateSetUi SetSettings", settings.__dict__
        self.settings = settings
        self.GateSetEnableCheckBox.setChecked( self.settings.enabled )
        self.GateSetFrame.setEnabled( self.settings.enabled )
        self.GateSetFrame.setEnabled( self.settings.enabled )
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
            oldState = self.GateSetBox.blockSignals(True);
            self.GateSetBox.clear()
            self.GateSetBox.addItems( self.settings.gateSetCache.keys() )
            self.GateSetBox.blockSignals(oldState);
            if self.settings.gateDefinition and self.settings.gateDefinition in self.settings.gateDefinitionCache:
                self.loadGateDefinition( self.settings.gateDefinitionCache[self.settings.gateDefinition] )
                self.GateDefinitionBox.setCurrentIndex(self.GateDefinitionBox.findText(self.settings.gateDefinition))
            if self.settings.gateSet and self.settings.gateSet in self.settings.gateSetCache:
                self.loadGateSetList( self.settings.gateSetCache[self.settings.gateSet] )
                self.GateSetBox.setCurrentIndex(self.GateSetBox.findText(self.settings.gateSet))
        except IOError as err:
            print err, "during loading of GateSet Files, ignored."

    def documentationString(self):
        return repr(self.settings)        
            
    def onGateDefinitionChanged(self, name):
        name = str(name)
        if name in self.settings.gateDefinitionCache:
            self.loadGateDefinition( self.settings.gateDefinitionCache[name] )            
            
    def onGateSetChanged(self, name):
        name = str(name)
        if name in self.settings.gateSetCache:
            self.loadGateSetList( self.settings.gateSetCache[name] )
            
    def onRepetitionChanged(self, value):
        self.settings.thisSequenceRepetition = value
        
    def onStartAddressParam(self,name):
        self.settings.startAddressParam = str(name)       
        
    def onEnableChanged(self, state):
        self.settings.enabled = state == QtCore.Qt.Checked
        self.GateSetFrame.setEnabled( self.settings.enabled )
        
    def onDebugChanged(self, state):
        self.settings.debug = state == QtCore.Qt.Checked        
        
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

    def loadGateDefinition(self, path):
        self.gatedef.loadGateDefinition(path)    
        filedir, filename = os.path.split(path)
        self.settings.gateDefinition = filename
        self.GateDefinitionBox.setCurrentIndex(self.GateDefinitionBox.findText(filename))
        self.gatedef.printGates()
    
    def onLoadGateSetList(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open Gate Set file:", self.settings.lastDir))
        if path!="":
            filedir, filename = os.path.split(path)
            self.settings.lastDir = filedir
            self.loadGateSetList(path)
            if filename not in self.settings.gateSetCache:
                self.settings.gateSetCache[filename] = path
                self.GateSetBox.addItem(filename)
                self.GateSetBox.setCurrentIndex( self.GateSetBox.findText(filename))
            
    def loadGateSetList(self, path):
        self.gateSetContainer.loadXml(path)
        if self.settings.debug:
            print "loaded {0} gateSets from {1}.".format(len(self.gateSetContainer.GateSetDict), path)
        filedir, filename = os.path.split(path)
        self.settings.gateSet = filename
        self.GateSetBox.setCurrentIndex(self.GateSetBox.findText(filename))
    
    def onGateEditChanged(self):
        self.settings.gate = map(operator.methodcaller('strip'),str(self.GateEdit.text()).split(','))
        self.GateEdit.setText( ", ".join(self.settings.gate ))
    
    def onRadioButtonToggled(self):
        if self.FullListRadioButton.isChecked():
            self.settings.active = self.Mode.FullList 
        else:
            self.settings.active = self.Mode.Gate   
            
    def gateSetScanData(self):
        if self.settings.active == self.Mode.FullList:
            address, data = self.gateSetCompiler.gateSetsCompile( self.gateSetContainer )
        else:
            self.gateSetCompiler.gateCompile( self.gateSetContainer.gateDefinition )
            data = self.gateSetCompiler.gateSetCompile( self.settings.gate )
            address = [0]*self.settings.thisSequenceRepetition
        if self.settings.debug:
            with open("GateSetData.debug","w") as of:
                print >>of, data
        return address, data, self.settings
        
    def setVariables(self, variabledict):
        self.variabledict = variabledict
        #oldParameterName = self.StartAddressBox.currentText()
        self.StartAddressBox.clear()
        for name, var in iter(sorted(variabledict.iteritems())):
            if var.type == "address":
                self.StartAddressBox.addItem(var.name)
        if self.settings.startAddressParam:
            self.StartAddressBox.setCurrentIndex(self.StartAddressBox.findText(self.settings.startAddressParam) )
        else:
            self.settings.startAddressParam = self.StartAddressBox.currentText()


if __name__ == "__main__":
    from PulseProgram import PulseProgram   
    pp = PulseProgram()
    pp.debug = False
    pp.loadSource(r"C:\Users\Public\Documents\experiments\test3\config\PulsePrograms\YbGateSetTomography.pp")
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = GateSetUi()
    ui.postInit("test",config,pp)
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    app.exec_()
    address, data, parameter = ui.gateSetScanData()
    a = address[541]
    l = data[ a/4 ]
    print a, l
    print data[ a/4 : a/4+3*l+1 ]
    address, data, parameter = ui.gateSetScanData()
    a = address[36]
    l = data[ a/4 ]
    print a, l
    print data[ a/4 : a/4+3*l+1 ]
    print config
    print "done"
