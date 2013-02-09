# -*- coding: utf-8 -*-
"""
Created on Thu Feb 07 22:55:28 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtCore, QtGui
import PulseProgram
import re

PulseProgramWidget, PulseProgramBase = PyQt4.uic.loadUiType('ui/PulseProgram.ui')

class PulseProgramUi(PulseProgramWidget,PulseProgramBase):
    def __init__(self):
        PulseProgramWidget.__init__(self)
        PulseProgramBase.__init__(self)
        self.pulseProgram = PulseProgram.PulseProgram()  
        self.sourceTextEdits = dict()
        
        
    def setupUi(self, parent):
        super(PulseProgramUi,self).setupUi(parent)
        self.loadButton.clicked.connect( self.onLoad )
        self.saveButton.clicked.connect( self.onSave )
        self.applyButton.clicked.connect( self.onApply )

    def onSave(self):
        print "onSave"
        pass
    
    def onLoad(self):
        print "onLoad"
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open Pulse Programmer file')
        print fname
        self.pulseProgram.loadSource(str(fname))
        self.showData()
   
    def onApply(self):
        print "onApply"
        pass

    def showData(self):
        # make the right number of tabs and show the source files
        self.sourceTabs.clear()
        self.sourceTextEdits = dict()
        for name, text in self.pulseProgram.source.iteritems():
            textEdit = QtGui.QTextEdit()
#            print text
#            text = re.sub( r"\r\n", r"\n", text)
#            print text
            textEdit.setPlainText(text)
            self.sourceTextEdits[name] = textEdit
            self.sourceTabs.addTab( textEdit, name )
  

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    widget = QtGui.QWidget()
    ui = PulseProgramUi()
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
