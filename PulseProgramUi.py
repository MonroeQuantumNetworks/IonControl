# -*- coding: utf-8 -*-
"""
Created on Thu Feb 07 22:55:28 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtCore, QtGui
import PulseProgram
import VariableTableModel

PulseProgramWidget, PulseProgramBase = PyQt4.uic.loadUiType('ui/PulseProgram.ui')

class PulseProgramUi(PulseProgramWidget,PulseProgramBase):
    def __init__(self):
        PulseProgramWidget.__init__(self)
        PulseProgramBase.__init__(self)
        self.pulseProgram = PulseProgram.PulseProgram()
        self.sourceCodeEdits = dict()
    
    def setupUi(self,parent):
        super(PulseProgramUi,self).setupUi(parent)
        self.okButton.clicked.connect( self.onOk )
        self.loadButton.clicked.connect( self.onLoad )
        self.saveButton.clicked.connect( self.onSave )
        self.applyButton.clicked.connect( self.onApply )
        self.checkBoxParameter.stateChanged.connect( self.onVariableSelectionChanged )
        self.checkBoxAddress.stateChanged.connect( self.onVariableSelectionChanged )
        self.checkBoxOther.stateChanged.connect( self.onVariableSelectionChanged )
        
    def onVariableSelectionChanged(self):
        visibledict = dict()
        for tag in [self.checkBoxParameter,self.checkBoxAddress,self.checkBoxOther]:
            visibledict[str(tag.text())] = tag.isChecked()
        self.variableTableModel.setVisible(visibledict)
        
    def onOk(self):
        pass
    
    def onLoad(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open Pulse Programmer file')
        if fname!="":
            self.pulseProgram.loadSource(str(fname))
            self.updateDisplay()
    
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
    

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    widget = QtGui.QWidget()
    ui = PulseProgramUi()
    ui.setupUi(widget)
    MainWindow.setCentralWidget(widget)
    MainWindow.show()
    sys.exit(app.exec_())
