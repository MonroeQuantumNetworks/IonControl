# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtGui, QtCore
import os.path
       
from VoltageFiles import VoltageFiles
from VoltageAdjust import VoltageAdjust
from VoltageGlobalAdjust import VoltageGlobalAdjust
       
VoltageControlForm, VoltageControlBase = PyQt4.uic.loadUiType(r'ui\VoltageControl.ui')


class Settings:
    pass

class VoltageControl(VoltageControlForm, VoltageControlBase ):    
    def __init__(self,config,parent=0):
        VoltageControlForm.__init__(self,parent)
        VoltageControlBase.__init__(self)
        self.config = config
        self.configname = 'VoltageControl.Settings'
        self.settings = self.config.get(self.configname,Settings())

    def setupUi(self, parent):
        VoltageControlForm.setupUi(self,parent)
        self.voltageFilesUi = VoltageFiles(self.config)
        self.voltageFilesUi.setupUi( self.voltageFilesUi )
        self.voltageFilesDock.setWidget( self.voltageFilesUi )
        self.adjustUi = VoltageAdjust(self.config)
        self.adjustUi.setupUi( self.adjustUi )
        self.adjustDock.setWidget( self.adjustUi )
        self.globalAdjustUi = VoltageGlobalAdjust(self.config)
        self.globalAdjustUi.setupUi( self.globalAdjustUi )
        self.globalAdjustDock.setWidget( self.globalAdjustUi )
        if hasattr(self.settings,'state'):
            self.restoreState( self.settings.state )
    
    def onClose(self):
        self.settings.state = self.saveState()
        self.config[self.configname] = self.settings
        self.voltageFilesUi.onClose()
        self.adjustUi.onClose()
        self.globalAdjustUi.onClose()
        
    def closeEvent(self,e):
        self.onClose()
  
if __name__ == "__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = VoltageControl(config)
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
    print config

        