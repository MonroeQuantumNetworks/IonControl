# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import copy

from PyQt4 import QtGui
import PyQt4.uic


ComboBoxTestForm, ComboBoxTestBase = PyQt4.uic.loadUiType(r'ComboBoxTest.ui')


class Settings:
    def __init__(self):
        self.text = ''
        
    def __eq__(self, other):
        return self.text == other.text

class ComboBoxTest(ComboBoxTestForm, ComboBoxTestBase ):    
    def __init__(self,parent=0):
        ComboBoxTestForm.__init__(self,parent)
        ComboBoxTestBase.__init__(self)
        self.settingsDict = dict()
        self.settingsHistory = list()
        self.settingsHistoryPointer = None
        self.currentSettings = Settings()
        self.historyFinalState = None

    def setupUi(self, parent):
        ComboBoxTestForm.setupUi(self,parent)
        self.saveButton.clicked.connect( self.onSave )
        self.undoButton.clicked.connect( self.onUndo )
        self.redoButton.clicked.connect( self.onRedo )
        self.comboBox.currentIndexChanged['QString'].connect( self.onLoad )
        self.commitButton.clicked.connect( self.onCommit )
        self.lineEdit.editingFinished.connect( self.onEditingFinished )
        
    def setSettings(self, settings):
        self.currentSettings = copy.copy(settings)
        self.lineEdit.setText( self.currentSettings.text )
        
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
                self.historyFinalState = copy.copy( self.currentSettings )
            self.settingsHistoryPointer -= 1
            self.setSettings( self.settingsHistory[self.settingsHistoryPointer] )
    
    def onSave(self):
        name = str(self.comboBox.currentText())
        print "onSave", name, self.currentSettings.text
        if name != '':
            if name not in self.settingsDict:
                if self.comboBox.findText(name)==-1:
                    self.comboBox.addItem(name)
                print "adding to combo", name
            self.settingsDict[name] = copy.copy(self.currentSettings)
    
    def onLoad(self,name):
        name = str(name)
        print "onLoad", name
        if name !='' and name in self.settingsDict:
            self.setSettings(self.settingsDict[name])
            print "restore", self.settingsDict[name].text
        else:
            print self.settingsDict

    def onEditingFinished(self):
        self.currentSettings.text = str(self.lineEdit.text())
    
    def onCommit(self):
        if len(self.settingsHistory)==0 or self.currentSettings!=self.settingsHistory[-1]:
            self.settingsHistory.append(copy.copy(self.currentSettings))
            self.settingsHistoryPointer = len(self.settingsHistory)
            print "adding setting to stack", self.currentSettings.text, self.settingsHistoryPointer
        
  
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = ComboBoxTest()
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())


        