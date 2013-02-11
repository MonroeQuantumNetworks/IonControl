# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 22:34:06 2012

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore
import fpgaUtilit
import sys, os.path
sys.path.append(os.path.abspath(r'ui'))

class Settings:
    def __init__(self):
        self.deviceSerial = None
        self.deviceDescription = None

SettingsDialogForm, SettingsDialogBase = PyQt4.uic.loadUiType(r'ui\SettingsDialog.ui')

class SettingsDialogConfig:
    autoUpload = False
    lastInstrument = None

class SettingsDialog(SettingsDialogForm, SettingsDialogBase):
    def __init__(self,config,parent=0):
        SettingsDialogBase.__init__(self,parent)    
        SettingsDialogForm.__init__(self)
        self.config = config
        self.deviceMap = dict()
        self.settings = Settings()
        self.fpga = fpgaUtilit.FPGAUtilit()
        
    def setupUi(self,recipient):
        super(SettingsDialog,self).setupUi(self)
        self.recipient = recipient
        self.pushButtonScan.clicked.connect( self.scanInstruments )
        self.comboBoxInstruments.currentIndexChanged[str].connect( self.onIndexChanged )
        self.renameButton.clicked.connect( self.onBoardRename )
        self.uploadButton.clicked.connect( self.onUploadBitfile )
        self.toolButtonOpenBitfile.clicked.connect( self.onLoadBitfile )
        self.scanInstruments()
        self.configSettings = self.config.get('SettingsDialog.Config',SettingsDialogConfig() )
        self.bitfileCache = self.config.get('SettingsDialog.bitfileCache',dict())
        self.checkBoxAutoUpload.setChecked( self.configSettings.autoUpload )
        if self.configSettings.lastInstrument in self.deviceMap:
            self.comboBoxInstruments.setCurrentIndex( self.comboBoxInstruments.findText(self.configSettings.lastInstrument) )
                
        
    def onBoardRename(self):
        newIdentifier = str(self.identifierEdit.text())
        self.fpga.renameBoard(self.settings.deviceSerial, newIdentifier )
        self.scanInstruments()
        self.comboBoxInstruments.setCurrentIndex( self.comboBoxInstruments.findText(newIdentifier) )
        
    def scanInstruments(self):
        self.comboBoxInstruments.clear()
        self.deviceMap = self.fpga.listBoards()
        self.comboBoxInstruments.addItems( self.deviceMap.keys() )
        print self.deviceMap
        
    def onIndexChanged(self,description):
        print "New instrument", description, self.deviceMap[str(description)]
        self.settings.deviceSerial = self.deviceMap[str(description)].serial
        self.settings.deviceDescription = str(description)
        self.settings.deviceInfo = self.deviceMap[str(description)]
        self.identifierEdit.setText( description )
        
    def accept(self):
        print "accept"
        self.lastPos = self.pos()
        self.hide()
        self.recipient.onSettingsApply()        
        
    def reject(self):
        print "reject"
        self.lastPos = self.pos()
        self.hide()
        
    def show(self):
        if hasattr(self, 'lastPos'):
            self.move(self.lastPos)
        QtGui.QDialog.show(self)
        
    def apply(self,button):
        print button.text(), "button pressed"
        if str(button.text())=="Apply":
            self.recipient.onSettingsApply()
            
    def close(self):
        self.config['SettingsDialog.Config'] = self.configSettings
        
    def onLoadBitfile(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, 'Open bitfile'))
        if path!="":
            if path not in self.bitfileCache:
                self.bitfileCache[path]=path
                self.comboBoxBitfiles.addItem(path)
            self.comboBoxBitfiles.setCurrentIndex(self.comboBoxBitfiles.findText(path))
            
    def onUploadBitfile(self):
        bitfile = str(self.comboBoxBitfiles.currentText())
        if bitfile!="":
            self.fpga.uploadBitfile(self.settings.deviceSerial,self.bitfileCache[bitfile])

    def progressCallback(length,count,arg):
        print length, count
            
if __name__ == "__main__":
    import sys
    class Recipient:
        def onSettingsApply():
            pass
        
    recipient = Recipient()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = SettingsDialog(MainWindow)
    ui.setupUi(recipient)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
