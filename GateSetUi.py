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
        if self.settings.gateDefinition:
            self.loadGateDefinition( self.settings.gateDefinition )
    
        self.gateSetContainer = GateSetContainer(self.gatedef)
        if self.settings.gateSet:
            self.loadGateSetList(self.settings.gateSet)
            
        self.gateSetCompiler = GateSetCompiler(pulseProgram)

    
    def setupUi(self,parent):
        super(GateSetUi,self).setupUi(parent)
        self.GateSetEnableCheckBox.setChecked( self.settings.enabled )
        self.GateSetFrame.setEnabled( self.settings.enabled )
        self.GateSetEnableCheckBox.stateChanged.connect( self.onEnableChanged )
        self.GateDefinitionButton.clicked.connect( self.onLoadGateDefinition )
        self.GateSetButton.clicked.connect( self.onLoadGateSetList )
        self.FullListRadioButton.toggled.connect( self.onRadioButtonToggled )
        self.GateEdit.editingFinished.connect( self.onGateEditChanged )
        self.GateEdit.setText( ", ".join(self.settings.gate ))
        self.StartAddressBox.currentIndexChanged['QString'].connect( self.onStartAddressParam )
        
    def onStartAddressParam(self,name):
        self.settings.startAddressParam = str(name)       
        
    def onEnableChanged(self, state):
        self.settings.enabled = state == QtCore.Qt.Checked
        self.GateSetFrame.setEnabled( self.settings.enabled )
        
    def close(self):
        self.config[self.configname] = self.settings
                
    def onLoadGateDefinition(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open Gate definition file:", self.settings.lastDir))
        if path!="":
            filedir, filename = os.path.split(path)
            self.settings.lastDir = filedir
            self.loadGateDefinition(path)
            self.GateDefinitionEdit.setText(filename)

    def loadGateDefinition(self, path):
        self.gatedef.loadGateDefinition(path)    
        self.settings.gateDefinition = path
        self.gatedef.printGates()
    
    def onLoadGateSetList(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open Gate Set file:", self.settings.lastDir))
        if path!="":
            filedir, filename = os.path.split(path)
            self.settings.lastDir = filedir
            self.GateSetEdit.setText(filename)
            self.loadGateSetList(path)
            
    def loadGateSetList(self, path):
        self.gateSetContainer.loadXml(path)
        print "loaded {0} gateSets.".format(len(self.gateSetContainer.GateSetDict))
        self.settings.gateSet = path
    
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
            data = self.gateSetCompiler.gateSetCompile( self.settings.gate )
            address = [0]
        return address, data, self.settings.startAddressParam
        
    def setVariables(self, variabledict):
        self.variabledict = variabledict
        oldParameterName = self.StartAddressBox.currentText()
        self.StartAddressBox.clear()
        for name, var in iter(sorted(variabledict.iteritems())):
            if var.type == "address":
                self.StartAddressBox.addItem(var.name)
        if oldParameterName and oldParameterName!="":
            self.StartAddressBox.setCurrentIndex(self.StartAddressBox.findText(oldParameterName) )


if __name__ == "__main__":
    from PulseProgram import PulseProgram   
    pp = PulseProgram()
    pp.debug = False
    pp.loadSource(r"C:\Users\Public\Documents\experiments\QGA\config\PulsePrograms\YbGateSetTomography.pp")
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = GateSetUi("test",config,pp)
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
    print config
