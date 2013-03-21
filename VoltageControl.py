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
import VoltageBlender
import VoltageTableModel
       
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
        self.voltageBlender = VoltageBlender.VoltageBlender()

    def setupUi(self, parent):
        VoltageControlForm.setupUi(self,parent)
        self.voltageFilesUi = VoltageFiles(self.config)
        self.voltageFilesUi.loadDefinition.connect( self.voltageBlender.loadVoltage )
        self.voltageFilesUi.loadMapping.connect( self.voltageBlender.loadMapping )
        self.voltageFilesUi.setupUi( self.voltageFilesUi )
        self.voltageFilesDock.setWidget( self.voltageFilesUi )
        self.adjustUi = VoltageAdjust(self.config)
        self.adjustUi.updateOutput.connect( self.onUpdate )
        self.adjustUi.setupUi( self.adjustUi )
        self.adjustDock.setWidget( self.adjustUi )
        self.globalAdjustUi = VoltageGlobalAdjust(self.config)
        self.globalAdjustUi.setupUi( self.globalAdjustUi )
        self.globalAdjustUi.updateOutput.connect( self.voltageBlender.setAdjust )
        self.globalAdjustDock.setWidget( self.globalAdjustUi )
        self.voltageFilesUi.loadGlobalAdjust.connect( self.onLoadGlobalAdjust )
        if hasattr(self.settings,'state'):
            self.restoreState( self.settings.state )
        self.voltageTableModel = VoltageTableModel.VoltageTableModel(self.voltageBlender)
        self.tableView.setModel( self.voltageTableModel )
        self.tableView.resizeColumnsToContents()
        self.tableView.resizeRowsToContents()
        self.voltageBlender.dataChanged.connect( self.voltageTableModel.onDataChanged )
        self.tableView.setSortingEnabled(True)
    
    def onUpdate(self, adjust):
        self.voltageBlender.applyLine(adjust.line, adjust.lineGain, adjust.globalGain )
    
    def onLoadGlobalAdjust(self, path):
        print "onLoadGlobalAdjust", path
        self.voltageBlender.loadGlobalAdjust(str(path) )
        self.globalAdjustUi.setupGlobalAdjust( self.voltageBlender.adjustDict )
    
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
    from modules import configshelve
    with configshelve.configshelve("VoltageControl-test") as config:
        app = QtGui.QApplication(sys.argv)
        MainWindow = QtGui.QMainWindow()
        ui = VoltageControl(config)
        ui.setupUi(ui)
        MainWindow.setCentralWidget(ui)
        MainWindow.show()
        sys.exit(app.exec_())


        