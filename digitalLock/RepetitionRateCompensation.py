# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 17:37:41 2012

This is the main gui program for the ExperimentalUi

@author: pmaunz
"""

import LoggingSetup
import MagnitudeParameter
import SettingsDialog
from persist import configshelve
import PulserHardware
import os
from modules import DataDirectory
from ExceptionLogButton import ExceptionLogButton
from PulserHardwareClient import PulserHardware 
import ProjectSelection
from collections import OrderedDict

import PyQt4.uic
from PyQt4 import QtCore, QtGui 
import argparse
import logging
from ProjectSelectionUi import GetProjectSelection

import DigitalLockUi
from digitalLock import LockControl
from digitalLock import LockStatus

WidgetContainerForm, WidgetContainerBase = PyQt4.uic.loadUiType(r'ui\RepetitionRate.ui')


class WidgetContainerUi(WidgetContainerBase,WidgetContainerForm):
    levelNameList = ["debug", "info", "warning", "error", "critical"]
    levelValueList = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
    def __init__(self,config):
        self.config = config
        super(WidgetContainerUi, self).__init__()
        self.settings = SettingsDialog.Settings()
        self.deviceSerial = config.get('Settings.deviceSerial')
        self.deviceDescription = config.get('Settings.deviceDescription')
        self.loggingLevel = config.get('Settings.loggingLevel',logging.INFO)
        self.consoleMaximumLines = config.get('Settings.consoleMaximumLines',0)
        if self.loggingLevel not in self.levelValueList: self.loggingLevel = logging.INFO
        
    def __enter__(self):
        self.pulser = PulserHardware()
        return self
    
    def __exit__(self, type, value, traceback):
        self.pulser.shutdown()
        return False
    
    def setupUi(self, parent):
        logger = logging.getLogger("")
        super(WidgetContainerUi,self).setupUi(parent)
        self.toolBar.addWidget(ExceptionLogButton())
        
        # Setup Console Dockwidget
        self.levelComboBox.addItems(self.levelNameList)
        self.levelComboBox.currentIndexChanged[int].connect( self.setLoggingLevel )            
        self.levelComboBox.setCurrentIndex( self.levelValueList.index(self.loggingLevel) )
        self.consoleClearButton.clicked.connect( self.onClearConsole )
        self.linesSpinBox.valueChanged.connect( self.onConsoleMaximumLinesChanged )
        
        self.parent = parent
        self.tabList = list()
        self.tabDict = dict()
        
        self.settingsDialog = SettingsDialog.SettingsDialog(self.pulser, self.config, self.parent)
        self.settingsDialog.setupUi()

        self.settings = self.settingsDialog.settings
        
        repRateWidget = RepetitionRateWidget( self.settings, self.pulser, self.config )        
        repRateWidget.setupUi()
        self.tabWidget.addTab(repRateWidget, "Repetition Rate")
        self.tabList.append(repRateWidget)
        self.tabDict["Repetition Rate"] = repRateWidget
            
        self.repetitionRateTrace = LockStatus(self.pulser, self.config)
        self.repetitionRateTrace.setupUi()
        self.traceControl.setWidget( self.repetitionRateTrace )

        self.repetitionRateLock = RepetitionRateLock(self.pulser, self.config)
        self.repetitionRateLock.setupUi()
        self.lockControl.setWidget( self.repetitionRateLock )
              
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
        if 'MainWindow.State' in self.config:
            self.parent.restoreState(self.config['MainWindow.State'])
        self.initMenu()
        #if 'MainWindow.pos' in self.config:
        #    self.move(self.config['MainWindow.pos'])
        if 'MainWindow.size' in self.config:
            self.resize(self.config['MainWindow.size'])
            
        self.setWindowTitle("Repetition Rate Control ({0})".format(project) )
        
    def onClearConsole(self):
        self.textEditConsole.clear()
        
    def onConsoleMaximumLinesChanged(self, maxlines):
        self.consoleMaximumLines = maxlines
        
    def setLoggingLevel(self, index):
        self.loggingLevel = self.levelValueList[index]

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
#         for dock in [self.dockWidgetConsole, self.shutterDockWidget, self.triggerDockWidget, self.DDSDockWidget, 
#                      self.ExternalScannedParametersDock, self.ExternalScannedParametersSelectionDock, self.globalVariablesDock ]:
#             self.menuView.addAction(dock.toggleViewAction())
        
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
        
    def onMessageWrite(self,message,level=logging.DEBUG):
        if level>= self.loggingLevel:
            cursor = self.textEditConsole.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            if level < logging.ERROR:
                self.textEditConsole.setTextColor(QtCore.Qt.black)
            else:
                self.textEditConsole.setTextColor(QtCore.Qt.red)
            cursor.insertText(message)
            self.textEditConsole.setTextCursor(cursor)
            self.textEditConsole.ensureCursorVisible()
        
    def closeEvent(self,e):
        logger = logging.getLogger("")
        logger.debug( "Saving Configuration" )
        self.saveConfig()
        for tab in self.tabList:
            tab.onClose()
        self.saveConfig()
        self.currentTab.deactivate()
        self.settingsDialog.done(0)

    def saveConfig(self):
        self.config['MainWindow.State'] = self.parent.saveState()
        for tab in self.tabList:
            tab.saveConfig()
        self.config['Settings.deviceSerial'] = self.settings.deviceSerial
        self.config['Settings.deviceDescription'] = self.settings.deviceDescription
        self.config['MainWindow.currentIndex'] = self.tabWidget.currentIndex()
        self.config['MainWindow.pos'] = self.pos()
        self.config['MainWindow.size'] = self.size()
        self.config['Settings.loggingLevel'] = self.loggingLevel
        self.config['Settings.consoleMaximumLines'] = self.consoleMaximumLines
        self.settingsDialog.saveConfig()
        self.repetitionRateLock.saveConfig()
        self.repetitionRateTrace.saveConfig()
        
    def onProjectSelection(self):
        ProjectSelectionUi.GetProjectSelection()
        
        
if __name__ == "__main__":
    import sys
    #The next three lines make it so that the icon in the Windows taskbar matches the icon set in Qt Designer
    import ctypes
    myappid = 'TrappedIons.RepetitionRateControl' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    parser = argparse.ArgumentParser(description='Get a program and run it with input', version='%(prog)s 1.0')
    parser.add_argument('--project',type=str,default=None,help='project name')
    args = parser.parse_args()
    app = QtGui.QApplication(sys.argv)

    logger = logging.getLogger("")

    project, projectDir = GetProjectSelection(True)
    
    if project:
        DataDirectory.DefaultProject = project
        
        with configshelve.configshelve( os.path.join( ProjectSelection.guiConfigDir(), "repetitionratecontrol.db.config" )  ) as config:
            with WidgetContainerUi(config) as ui:
                ui.setupUi(ui)
                LoggingSetup.qtHandler.textWritten.connect(ui.onMessageWrite)
                ui.show()
                sys.exit(app.exec_())
    else:
        logger.warning( "No project selected. Nothing I can do about that ;)" )
