# -*- coding: utf-8 -*-
"""
Created on Thu Feb 07 22:55:28 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtCore, QtGui
import PulseProgram
import VariableTableModel
import ShutterTableModel
import TriggerTableModel
import os

PulseProgramWidget, PulseProgramBase = PyQt4.uic.loadUiType('ui/PulseProgram.ui')

recentFiles = dict()

class PulseProgramUi(PulseProgramWidget,PulseProgramBase):
    def __init__(self):
        PulseProgramWidget.__init__(self)
        PulseProgramBase.__init__(self)
        self.pulseProgram = PulseProgram.PulseProgram()
        self.sourceCodeEdits = dict()
    
    def setupUi(self,experimentname,parent):
        super(PulseProgramUi,self).setupUi(parent)
        self.okButton.clicked.connect( self.onOk )
        self.loadButton.clicked.connect( self.onLoad )
        self.saveButton.clicked.connect( self.onSave )
        self.applyButton.clicked.connect( self.onApply )
        self.checkBoxParameter.stateChanged.connect( self.onVariableSelectionChanged )
        self.checkBoxAddress.stateChanged.connect( self.onVariableSelectionChanged )
        self.checkBoxOther.stateChanged.connect( self.onVariableSelectionChanged )
        self.experimentname = experimentname
        
    def onVariableSelectionChanged(self):
        visibledict = dict()
        for tag in [self.checkBoxParameter,self.checkBoxAddress,self.checkBoxOther]:
            visibledict[str(tag.text())] = tag.isChecked()
        self.variableTableModel.setVisible(visibledict)
        
    def onOk(self):
        pass
    
    def onLoad(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, 'Open Pulse Programmer file'))
        if path!="":
            self.pulseProgram.loadSource(path)
            self.updateDisplay()
            filename = os.path.basename(path)
            recentFiles[filename]=path
            self.filenameComboBox.clear()
            self.filenameComboBox.addItems([x for x in recentFiles])
            self.filenameComboBox.setCurrentIndex( self.filenameComboBox.findText(filename))
    
    def onSave(self):
        self.onApply()
        self.pulseProgram.saveSource()
    
    def onApply(self):
        for name, textEdit in self.sourceCodeEdits.iteritems():
            self.pulseProgram.source[name] = str(textEdit.toPlainText())
        self.pulseProgram.loadFromMemory()
        self.updateDisplay()
    
    def updateDisplay(self):
        self.sourceTabs.clear()
        for name, text in self.pulseProgram.source.iteritems():
            textEdit = QtGui.QTextEdit()
            textEdit.setPlainText(text)
            self.sourceCodeEdits[name] = textEdit
            self.sourceTabs.addTab( textEdit, name )
        self.variableTableModel = VariableTableModel.VariableTableModel( self.pulseProgram.variabledict )
        self.variableView.setModel(self.variableTableModel)
        self.shutterTableModel = ShutterTableModel.ShutterTableModel( self.pulseProgram.variabledict )
        self.shutterTableView.setModel(self.shutterTableModel)
        self.shutterTableView.resizeColumnsToContents()
        self.shutterTableView.clicked.connect(self.shutterTableModel.onClicked)
        self.triggerTableModel = TriggerTableModel.TriggerTableModel( self.pulseProgram.variabledict )
        self.triggerTableView.setModel(self.triggerTableModel)
        self.triggerTableView.resizeColumnsToContents()
        self.triggerTableView.clicked.connect(self.triggerTableModel.onClicked)
        
    def onActivated(self, index):
        if index==self.myindex:
            print "Activated", self.experimentname
            self.filenameComboBox.clear()
            self.filenameComboBox.addItems([x for x in recentFiles])
            self.filenameComboBox.setCurrentIndex( self.filenameComboBox.findText(filename))
        else:
            print "Deactivated", self.experimentname
    
class PulseProgramSetUi(QtGui.QDialog):
    def __init__(self):
        super(PulseProgramSetUi,self).__init__()
        self.pulseProgramSet = dict()
    
    def setupUi(self,parent):
        self.horizontalLayout = QtGui.QHBoxLayout(parent)
        self.tabWidget = QtGui.QTabWidget(parent)
        self.horizontalLayout.addWidget(self.tabWidget)

    def addExperiment(self, experiment):
        if not experiment in self.pulseProgramSet:
            programUi = PulseProgramUi()
            programUi.setupUi(experiment,programUi)
            programUi.myindex = self.tabWidget.addTab(programUi,experiment)
            self.pulseProgramSet[experiment] = programUi
            self.tabWidget.currentChanged.connect( programUi.onActivated )

            
    def getPulseProgram(self, experiment):
        return self.pulseProgramSet[experiment]
        
    def accept(self):
        print "accept"
        self.lastPos = self.pos()
        self.lastSize = self.size()
        self.hide()
        self.recipient.onSettingsApply()        
        
    def reject(self):
        print "reject"
        self.lastPos = self.pos()
        self.lastSize = self.size()
        self.hide()
        
    def show(self):
        print "show"
        if hasattr(self, 'lastPos'):
            self.move(self.lastPos)
        if hasattr(self,'lastSize'):
            self.resize( self.lastSize)
        QtGui.QDialog.show(self)

    
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = PulseProgramSetUi()
    ui.setupUi(ui)
    ui.addExperiment("Sequence")
    ui.addExperiment("Doppler Recooling")
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
