# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import logging

from PyQt4 import QtGui
import PyQt4.uic

from VoltageAdjust import VoltageAdjust
import VoltageBlender
from VoltageFiles import VoltageFiles
from VoltageGlobalAdjust import VoltageGlobalAdjust
import VoltageTableModel


VoltageControlForm, VoltageControlBase = PyQt4.uic.loadUiType(r'ui\VoltageControl.ui')


class Settings:
    pass

class VoltageControl(VoltageControlForm, VoltageControlBase ):    
    def __init__(self, config, globalDict=None, dacController=None, parent=None):
        VoltageControlForm.__init__(self)
        VoltageControlBase.__init__(self,parent)
        self.config = config
        self.configname = 'VoltageControl.Settings'
        self.settings = self.config.get(self.configname,Settings())
        self.dacController = dacController
        self.voltageBlender = VoltageBlender.VoltageBlender(globalDict, dacController)
        self.globalDict = globalDict

    def setupUi(self, parent):
        logger = logging.getLogger(__name__)
        VoltageControlForm.setupUi(self,parent)
        self.voltageFilesUi = VoltageFiles(self.config)
        self.voltageFilesUi.setupUi( self.voltageFilesUi )
        self.voltageFilesDock.setWidget( self.voltageFilesUi )
        self.adjustUi = VoltageAdjust(self.config)
        self.adjustUi.updateOutput.connect( self.onUpdate )
        self.adjustUi.setupUi( self.adjustUi )
        self.adjustDock.setWidget( self.adjustUi )
        self.globalAdjustUi = VoltageGlobalAdjust(self.config, self.globalDict)
        self.globalAdjustUi.setupUi( self.globalAdjustUi )
        self.globalAdjustUi.updateOutput.connect( self.voltageBlender.setAdjust )
        self.globalAdjustDock.setWidget( self.globalAdjustUi )
        if hasattr(self.settings,'state'):
            self.restoreState( self.settings.state )
        self.voltageFilesUi.loadMapping.connect( self.voltageBlender.loadMapping )
        self.voltageFilesUi.loadDefinition.connect( self.voltageBlender.loadVoltage )
        self.voltageFilesUi.loadGlobalAdjust.connect( self.onLoadGlobalAdjust )
        self.voltageTableModel = VoltageTableModel.VoltageTableModel(self.voltageBlender)
        self.tableView.setModel( self.voltageTableModel )
        self.tableView.resizeColumnsToContents()
        self.tableView.resizeRowsToContents()
        self.voltageBlender.dataChanged.connect( self.voltageTableModel.onDataChanged )
        self.voltageBlender.dataError.connect( self.voltageTableModel.onDataError )
        self.tableView.setSortingEnabled(True)
        self.voltageFilesUi.reloadAll()
        adjust = self.adjustUi.adjust
        try:
            self.voltageBlender.applyLine(adjust.line, adjust.lineGain, adjust.globalGain )
        except Exception:
            logger.error("cannot apply voltages. Ignored for now.")
        self.adjustUi.shuttleOutput.connect( self.voltageBlender.shuttle )
        self.voltageBlender.shuttlingOnLine.connect( self.adjustUi.onShuttlingDone )
    
    def onUpdate(self, adjust):
        self.voltageBlender.applyLine(adjust.line, adjust.lineGain, adjust.globalGain )
                     
    def onLoadGlobalAdjust(self, path):
        self.voltageBlender.loadGlobalAdjust(str(path) )
        self.globalAdjustUi.setupGlobalAdjust( str(path), self.voltageBlender.adjustDict )
    
    def saveConfig(self):
        self.settings.state = self.saveState()
        self.config[self.configname] = self.settings
        self.adjustUi.saveConfig()
        self.globalAdjustUi.saveConfig()
        self.voltageFilesUi.saveConfig()
    
    def onClose(self):
        pass
        
    def closeEvent(self,e):
        self.onClose()
        
    def onShuttleSequence(self, cont=False):
        self.adjustUi.onShuttleEdge(0)
  
if __name__ == "__main__":
    class MyMainWindow(QtGui.QMainWindow):
        def setCentralWidget(self, widget):
            self.myCentralWidget = widget
            super(MyMainWindow,self).setCentralWidget(widget)  
            
        def closeEvent(self,e):
            self.myCentralWidget.onClose()
            super(MyMainWindow,self).closeEvent(e)   
    
    import sys
    from persist import configshelve
    with configshelve.configshelve("VoltageControl-test") as config:
        app = QtGui.QApplication(sys.argv)
        MainWindow = MyMainWindow()
        ui = VoltageControl(config)
        ui.setupUi(ui)
        MainWindow.setCentralWidget(ui)
        MainWindow.show()
        sys.exit(app.exec_())


        