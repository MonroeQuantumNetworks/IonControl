# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 17:37:41 2012

This is the main gui program for the ExperimentalUi

@author: pmaunz
"""

#import sip
#sip.setapi("QString",2)
#sip.setapi("QVariant",2)
#sip.setapi("QDate",2)
#sip.setapi("QDateTime",2)
#sip.setapi("QTextStream",2)
#sip.setapi("QTime",2)
#sip.setapi("QUrl",2)

import LoggingSetup
import MagnitudeParameter
import ScanExperiment
import ExternalScanExperiment
import VoltageScanExperiment
import SettingsDialog
import testExperiment
from persist import configshelve
import PulseProgramUi
import ShutterUi
import DDSUi
import PulserHardware
import DedicatedCounters
import ExternalScannedParametersSelection
import ExternalScannedParametersUi
import ProjectSelectionUi
import os
from modules import DataDirectory
from ExceptionLogButton import ExceptionLogButton
import GlobalVariables 
from PulserHardwareClient import PulserHardware 
import ProjectSelection

import VoltageControl
    
import PyQt4.uic
from PyQt4 import QtCore, QtGui 
import argparse
import logging

WidgetContainerForm, WidgetContainerBase = PyQt4.uic.loadUiType(r'ui\Experiment.ui')


class WidgetContainerUi(WidgetContainerBase,WidgetContainerForm):
    def __init__(self,config):
        self.config = config
        super(WidgetContainerUi, self).__init__()
        self.settings = SettingsDialog.Settings()
        self.deviceSerial = config.get('Settings.deviceSerial')
        self.deviceDescription = config.get('Settings.deviceDescription')
        
    def __enter__(self):
        self.pulser = PulserHardware()
        return self
    
    def __exit__(self, type, value, traceback):
        self.pulser.shutdown()
        return False
    
    def setupUi(self, parent):
        logger = logging.getLogger(__name__)
        super(WidgetContainerUi,self).setupUi(parent)
        self.toolBar.addWidget(ExceptionLogButton())
        
        self.parent = parent
        self.tabList = list()
        self.tabDict = dict()
        # initialize PulseProgramUi
        self.pulseProgramDialog = PulseProgramUi.PulseProgramSetUi(self.config)
        self.pulseProgramDialog.setupUi(self.pulseProgramDialog)
        
        self.settingsDialog = SettingsDialog.SettingsDialog(self.pulser, self.config, self.parent)
        self.settingsDialog.setupUi()

        self.settings = self.settingsDialog.settings        

        # Global Variables
        self.globalVariablesUi = GlobalVariables.GlobalVariableUi(self.config)
        self.globalVariablesUi.setupUi(self.globalVariablesUi)
        self.globalVariablesDock = QtGui.QDockWidget("Global Variables")
        self.globalVariablesDock.setObjectName("Global Variables")
        self.globalVariablesDock.setWidget( self.globalVariablesUi )
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea , self.globalVariablesDock)

        for widget,name in [ (ScanExperiment.ScanExperiment(self.settings,self.pulser,"ScanExperiment"), "Scan"),
                             (ExternalScanExperiment.ExternalScanExperiment(self.settings,self.pulser,"ExternalScan"), "External Scan"),
                             (VoltageScanExperiment.VoltageScanExperiment(self.settings,self.pulser,"VoltageScan"), "Voltage Scan"),
                             (testExperiment.test(),"test"),
                             ]:
            widget.setupUi( widget, self.config )
            if hasattr(widget, 'setGlobalVariablesUi'):
                widget.setGlobalVariablesUi( self.globalVariablesUi )
            if hasattr(widget,'setPulseProgramUi'):
                widget.setPulseProgramUi( self.pulseProgramDialog )
            self.tabWidget.addTab(widget, name)
            self.tabList.append(widget)
            self.tabDict[name] = widget
            widget.ClearStatusMessage.connect( self.statusbar.clearMessage)
            widget.StatusMessage.connect( self.statusbar.showMessage)
            
        self.ExternalScanExperiment = self.tabDict["External Scan"]
        self.voltageScanExperiment = self.tabDict["Voltage Scan"]
        
        self.shutterUi = ShutterUi.ShutterUi(self.pulser, 'shutter', self.config)
        self.shutterUi.setupUi(self.shutterUi, True)
        self.shutterDockWidget.setWidget( self.shutterUi )
        logger.debug( "ShutterUi representation:" + repr(self.shutterUi) )

        self.triggerUi = ShutterUi.TriggerUi(self.pulser, 'trigger', self.config)
        self.triggerUi.offColor =  QtGui.QColor(QtCore.Qt.white)
        self.triggerUi.setupUi(self.triggerUi)
        self.triggerDockWidget.setWidget( self.triggerUi )

        self.DDSUi = DDSUi.DDSUi(self.config, self.pulser )
        self.DDSUi.setupUi(self.DDSUi)
        self.DDSDockWidget.setWidget( self.DDSUi )
        self.tabDict['Scan'].NeedsDDSRewrite.connect( self.DDSUi.onWriteAll )
                
        # tabify the dock widgets
        self.tabifyDockWidget( self.triggerDockWidget, self.shutterDockWidget)
        self.tabifyDockWidget( self.shutterDockWidget, self.DDSDockWidget )
        self.tabifyDockWidget( self.DDSDockWidget, self.globalVariablesDock )
        
        self.ExternalParametersSelectionUi = ExternalScannedParametersSelection.SelectionUi(self.config)
        self.ExternalParametersSelectionUi.setupUi( self.ExternalParametersSelectionUi )
        self.ExternalScannedParametersSelectionDock = QtGui.QDockWidget("Params Selection")
        self.ExternalScannedParametersSelectionDock.setObjectName("_ExternalScannedParametersSelectionDock")
        self.ExternalScannedParametersSelectionDock.setWidget(self.ExternalParametersSelectionUi)
        self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.ExternalScannedParametersSelectionDock)

        self.ExternalParametersUi = ExternalScannedParametersUi.ControlUi()
        self.ExternalParametersUi.setupUi( self.ExternalParametersSelectionUi.enabledParametersObjects, self.ExternalParametersUi )
        self.ExternalScannedParametersDock = QtGui.QDockWidget("Params Control")
        self.ExternalScannedParametersDock.setWidget(self.ExternalParametersUi)
        self.ExternalScannedParametersDock.setObjectName("_ExternalScannedParametersDock")
        self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.ExternalScannedParametersDock)
        self.ExternalParametersSelectionUi.selectionChanged.connect( self.ExternalParametersUi.setupParameters )
               
        self.ExternalParametersSelectionUi.selectionChanged.connect( self.ExternalScanExperiment.updateEnabledParameters )               
        self.ExternalScanExperiment.updateEnabledParameters( self.ExternalParametersSelectionUi.enabledParameters )
        #tabify 
        self.tabifyDockWidget( self.ExternalScannedParametersSelectionDock, self.ExternalScannedParametersDock)
        
        self.tabWidget.currentChanged.connect(self.onCurrentChanged)
        self.actionClear.triggered.connect(self.onClear)
        self.actionPause.triggered.connect(self.onPause)
        self.actionSave.triggered.connect(self.onSave)
        self.actionStart.triggered.connect(self.onStart)
        self.actionStop.triggered.connect(self.onStop)
        self.actionSettings.triggered.connect(self.onSettings)
        self.actionExit.triggered.connect(self.onClose)
        self.actionContinue.triggered.connect(self.onContinue)
        self.actionPulses.triggered.connect(self.onPulses)
        self.actionReload.triggered.connect(self.onReload)
        self.actionProject.triggered.connect( self.onProjectSelection)
        self.actionVoltageControl.triggered.connect(self.onVoltageControl)
        self.actionDedicatedCounters.triggered.connect(self.showDedicatedCounters)
        self.currentTab = self.tabList[self.config.get('MainWindow.currentIndex',0)]
        self.tabWidget.setCurrentIndex( self.config.get('MainWindow.currentIndex',0) )
        self.currentTab.activate()
        if 'MainWindow.State' in self.config:
            self.parent.restoreState(self.config['MainWindow.State'])
        self.initMenu()
        #if 'MainWindow.pos' in self.config:
        #    self.move(self.config['MainWindow.pos'])
        if 'MainWindow.size' in self.config:
            self.resize(self.config['MainWindow.size'])
            
        self.dedicatedCountersWindow = DedicatedCounters.DedicatedCounters(self.config, self.pulser)
        self.dedicatedCountersWindow.setupUi(self.dedicatedCountersWindow)
        
        self.voltageControlWindow = VoltageControl.VoltageControl(self.config)
        self.voltageControlWindow.setupUi(self.voltageControlWindow)
        self.setWindowTitle("Experimental Control ({0})".format(project) )

    def showDedicatedCounters(self):
        self.dedicatedCountersWindow.show()
        self.dedicatedCountersWindow.setWindowState(QtCore.Qt.WindowActive)
        self.dedicatedCountersWindow.raise_()
        self.dedicatedCountersWindow.onStart() #Start displaying data immediately

    def onVoltageControl(self):
        self.voltageControlWindow.show()
        self.voltageControlWindow.setWindowState(QtCore.Qt.WindowActive)
        self.voltageControlWindow.raise_()
        
    def onClear(self):
        self.currentTab.onClear()
    
    def onSave(self):
        logger = logging.getLogger(__name__)
        self.currentTab.onSave()
        logger.info( "Saving config" )
        filename, components = DataDirectory.DataDirectory().sequencefile("configuration.db")
        self.config.saveConfig(filename)
    
    def onStart(self):
        self.currentTab.onStart()
    
    def onPause(self):
        self.currentTab.onPause()
    
    def onStop(self):
        self.currentTab.onStop()
        
    def onContinue(self):
        if hasattr(self.currentTab,'onContinue'):
            self.currentTab.onStop()
        else:
            self.statusbar.showMessage("continue not implemented")    
            
    def onReload(self):
        logger = logging.getLogger(__name__)
        logger.debug( "OnReload" )
        self.currentTab.onReload()
    
    def onCurrentChanged(self, index):
        self.currentTab.deactivate()
        self.currentTab = self.tabList[index]
        self.currentTab.activate()
        self.initMenu()
        
    def initMenu(self):
        self.menuView.clear()
        if hasattr(self.currentTab,'viewActions'):
            self.menuView.addActions(self.currentTab.viewActions())
        for dock in [self.dockWidgetConsole, self.shutterDockWidget, self.triggerDockWidget, self.DDSDockWidget, 
                     self.ExternalScannedParametersDock, self.ExternalScannedParametersSelectionDock, self.globalVariablesDock ]:
            self.menuView.addAction(dock.toggleViewAction())
        
    def onSettings(self):
        self.settingsDialog.show()
        
    def onPulses(self):
        self.pulseProgramDialog.show()
        self.pulseProgramDialog.setWindowState(QtCore.Qt.WindowActive)
        self.pulseProgramDialog.raise_()
        if hasattr(self.currentTab,'experimentName'):
            self.pulseProgramDialog.setCurrentTab(self.currentTab.experimentName)
                  
    def onClose(self):
        self.parent.close()
        
    def onMessageWrite(self,message):
        cursor = self.textEditConsole.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(message)
        self.textEditConsole.setTextCursor(cursor)
        self.textEditConsole.ensureCursorVisible()
        
    def closeEvent(self,e):
        logger = logging.getLogger(__name__)
        logger.debug( "Saving Configuration" )
        self.saveConfig()
        for tab in self.tabList:
            tab.onClose()
        self.saveConfig()
        self.currentTab.deactivate()
        self.pulseProgramDialog.done(0)
        self.settingsDialog.done(0)
        self.ExternalParametersSelectionUi.onClose()
        self.voltageControlWindow.close()
        self.dedicatedCountersWindow.close()
        self.pulseProgramDialog.onClose()

    def saveConfig(self):
        self.config['MainWindow.State'] = self.parent.saveState()
        for tab in self.tabList:
            tab.saveConfig()
        self.config['Settings.deviceSerial'] = self.settings.deviceSerial
        self.config['Settings.deviceDescription'] = self.settings.deviceDescription
        self.config['MainWindow.currentIndex'] = self.tabWidget.currentIndex()
        self.config['MainWindow.pos'] = self.pos()
        self.config['MainWindow.size'] = self.size()
        self.pulseProgramDialog.saveConfig()
        self.settingsDialog.saveConfig()
        self.DDSUi.saveConfig()
        self.shutterUi.saveConfig()
        self.triggerUi.saveConfig()
        self.dedicatedCountersWindow.saveConfig()
        self.voltageControlWindow.saveConfig()
        self.ExternalParametersSelectionUi.saveConfig()
        self.globalVariablesUi.saveConfig()
        
    def onProjectSelection(self):
        ProjectSelectionUi.GetProjectSelection()
        
        
if __name__ == "__main__":
    import sys
    #The next three lines make it so that the icon in the Windows taskbar matches the icon set in Qt Designer
    import ctypes
    myappid = 'TrappedIons.FPGAControlProgram' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    parser = argparse.ArgumentParser(description='Get a program and run it with input', version='%(prog)s 1.0')
    parser.add_argument('--project',type=str,default=None,help='project name')
    args = parser.parse_args()
    app = QtGui.QApplication(sys.argv)

    logger = logging.getLogger("")
    # the next two lines migrate old pickle files to use the new magnitude module
    import modules.magnitude as magnitude
    sys.modules['magnitude'] = magnitude

    project, projectDir = ProjectSelectionUi.GetProjectSelection(True)
    
    if project:
        DataDirectory.DefaultProject = project
        
        with configshelve.configshelve( ProjectSelection.guiConfigFile() ) as config:
            with WidgetContainerUi(config) as ui:
                ui.setupUi(ui)
                LoggingSetup.qtHandler.textWritten.connect(ui.onMessageWrite)
                ui.show()
                sys.exit(app.exec_())
    else:
        logger.warning( "No project selected. Nothing I can do about that ;)" )
