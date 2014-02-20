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

import argparse
import logging

from PyQt4 import QtCore, QtGui 
import PyQt4.uic

from pulser import DDSUi
from mylogging.ExceptionLogButton import ExceptionLogButton
from gui import ExternalScanExperiment
from gui import GlobalVariables
from mylogging.LoggerLevelsUi import LoggerLevelsUi
from mylogging import LoggingSetup  #@UnusedImport
from gui import ProjectSelection
from gui import ProjectSelectionUi
from pulser.PulserHardwareClient import PulserHardware 
from gui import ScanExperiment
from gui import SettingsDialog
from gui import VoltageScanExperiment
from dedicatedCounters.DedicatedCounters import DedicatedCounters
from externalParameter import ExternalParameterSelection
from externalParameter import ExternalParameterUi 
from logicAnalyzer.LogicAnalyzer import LogicAnalyzer
from modules import DataDirectory
from modules.DataChanged import DataChanged
from modules.bidict import ChannelNameMap
from persist import configshelve
from pulseProgram import PulseProgramUi
from pulser import ShutterUi
from gui import testExperiment
from uiModules import MagnitudeParameter #@UnusedImport


WidgetContainerForm, WidgetContainerBase = PyQt4.uic.loadUiType(r'ui\Experiment.ui')


class ExperimentUi(WidgetContainerBase,WidgetContainerForm):
    levelNameList = ["debug", "info", "warning", "error", "critical"]
    levelValueList = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
    def __init__(self,config):
        self.config = config
        super(ExperimentUi, self).__init__()
        self.settings = SettingsDialog.Settings()
        self.deviceSerial = config.get('Settings.deviceSerial')
        self.deviceDescription = config.get('Settings.deviceDescription')
        self.loggingLevel = config.get('Settings.loggingLevel',logging.INFO)
        self.consoleMaximumLines = config.get('Settings.consoleMaximumLines',0)
        self.shutterNameDict = config.get('Settings.ShutterNameDict', ChannelNameMap())
        self.shutterNameSignal = DataChanged()
        self.triggerNameDict = config.get('Settings.TriggerNameDict', ChannelNameMap())
        self.triggerNameSignal = DataChanged()
        if self.loggingLevel not in self.levelValueList: self.loggingLevel = logging.INFO
        
    def __enter__(self):
        self.pulser = PulserHardware()
        return self
    
    def __exit__(self, excepttype, value, traceback):
        self.pulser.shutdown()
        return False
    
    def setupUi(self, parent):
        super(ExperimentUi,self).setupUi(parent)
        self.dockWidgetConsole.hide()
        self.loggerUi = LoggerLevelsUi(self.config)
        self.loggerUi.setupUi(self.loggerUi)
        self.loggerDock = QtGui.QDockWidget("Logging")
        self.loggerDock.setWidget(self.loggerUi)
        self.loggerDock.setObjectName("_LoggerDock")
        self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.loggerDock)
        self.loggerDock.hide()
                
        logger = logging.getLogger()        
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
        
        
        # initialize PulseProgramUi
        self.channelNameData = (self.shutterNameDict, self.shutterNameSignal, self.triggerNameDict, self.triggerNameSignal)
        self.pulseProgramDialog = PulseProgramUi.PulseProgramSetUi(self.config,  self.channelNameData )
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

        for widget,name in [ (ScanExperiment.ScanExperiment(self.settings,self.pulser,"ScanExperiment", toolBar=self.experimentToolBar), "Scan"),
                             (ExternalScanExperiment.ExternalScanExperiment(self.settings,self.pulser,"ExternalScan", toolBar=self.experimentToolBar), "External Scan"),
                             (VoltageScanExperiment.VoltageScanExperiment(self.settings,self.pulser,"VoltageScan", toolBar=self.experimentToolBar), "Voltage Scan"),
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
        
        self.shutterUi = ShutterUi.ShutterUi(self.pulser, 'shutter', self.config, (self.shutterNameDict, self.shutterNameSignal) )
        self.shutterUi.setupUi(self.shutterUi, True)
        self.shutterDockWidget.setWidget( self.shutterUi )
        self.pulser.ppActiveChanged.connect( self.shutterUi.setDisabled )
        logger.debug( "ShutterUi representation:" + repr(self.shutterUi) )

        self.triggerUi = ShutterUi.TriggerUi(self.pulser, 'trigger', self.config, (self.triggerNameDict, self.triggerNameSignal) )
        self.triggerUi.offColor =  QtGui.QColor(QtCore.Qt.white)
        self.triggerUi.setupUi(self.triggerUi)
        self.pulser.ppActiveChanged.connect( self.triggerUi.setDisabled )
        self.triggerDockWidget.setWidget( self.triggerUi )

        self.DDSUi = DDSUi.DDSUi(self.config, self.pulser )
        self.DDSUi.setupUi(self.DDSUi)
        self.DDSDockWidget.setWidget( self.DDSUi )
        self.pulser.ppActiveChanged.connect( self.DDSUi.setDisabled )
        self.tabDict['Scan'].NeedsDDSRewrite.connect( self.DDSUi.onWriteAll )
        
        # tabify the dock widgets
        self.tabifyDockWidget( self.triggerDockWidget, self.shutterDockWidget)
        self.tabifyDockWidget( self.shutterDockWidget, self.DDSDockWidget )
        self.tabifyDockWidget( self.DDSDockWidget, self.globalVariablesDock )
        
        self.ExternalParametersSelectionUi = ExternalParameterSelection.SelectionUi(self.config)
        self.ExternalParametersSelectionUi.setupUi( self.ExternalParametersSelectionUi )
        self.ExternalParameterSelectionDock = QtGui.QDockWidget("Params Selection")
        self.ExternalParameterSelectionDock.setObjectName("_ExternalParameterSelectionDock")
        self.ExternalParameterSelectionDock.setWidget(self.ExternalParametersSelectionUi)
        self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.ExternalParameterSelectionDock)

        self.ExternalParametersUi = ExternalParameterUi.ControlUi()
        self.ExternalParametersUi.setupUi( self.ExternalParametersSelectionUi.enabledParametersObjects, self.ExternalParametersUi )
        self.ExternalParameterDock = QtGui.QDockWidget("Params Control")
        self.ExternalParameterDock.setWidget(self.ExternalParametersUi)
        self.ExternalParameterDock.setObjectName("_ExternalParameterDock")
        self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.ExternalParameterDock)
        self.ExternalParametersSelectionUi.selectionChanged.connect( self.ExternalParametersUi.setupParameters )
               
        self.ExternalParametersSelectionUi.selectionChanged.connect( self.ExternalScanExperiment.updateEnabledParameters )               
        self.ExternalScanExperiment.updateEnabledParameters( self.ExternalParametersSelectionUi.enabledParametersObjects )
        #tabify 
        self.tabifyDockWidget( self.ExternalParameterSelectionDock, self.ExternalParameterDock)
        
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
        self.actionLogic.triggered.connect(self.showLogicAnalyzer)
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
            
        self.dedicatedCountersWindow = DedicatedCounters(self.config, self.pulser)
        self.dedicatedCountersWindow.setupUi(self.dedicatedCountersWindow)
        
        self.logicAnalyzerWindow = LogicAnalyzer(self.config, self.pulser, self.channelNameData )
        self.logicAnalyzerWindow.setupUi(self.logicAnalyzerWindow)
        
        self.voltageControlWindow = VoltageControl(self.config)
        self.voltageControlWindow.setupUi(self.voltageControlWindow)
        self.setWindowTitle("Experimental Control ({0})".format(project) )
        
        QtCore.QTimer.singleShot(60000, self.onCommitConfig )
        
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
        self.dedicatedCountersWindow.graphicsView.onHoldZero() #Set the plot to "hold zero" autorange mode

    def showLogicAnalyzer(self):
        self.logicAnalyzerWindow.show()
        self.logicAnalyzerWindow.setWindowState(QtCore.Qt.WindowActive)
        self.logicAnalyzerWindow.raise_()

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
        filename, _ = DataDirectory.DataDirectory().sequencefile("configuration.db")
        self.saveConfig()
        self.config.saveConfig(filename)
        
    def onCommitConfig(self):
        logger = logging.getLogger(__name__)
        self.currentTab.onSave()
        logger.debug( "Committing config" )
        self.saveConfig()
        self.config.saveConfig() 
        QtCore.QTimer.singleShot(60000, self.onCommitConfig )      
            
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
                     self.ExternalParameterDock, self.ExternalParameterSelectionDock, self.globalVariablesDock,
                     self.loggerDock ]:
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
        self.currentTab.deactivate()
        self.pulseProgramDialog.done(0)
        self.settingsDialog.done(0)
        self.ExternalParametersSelectionUi.onClose()
        self.voltageControlWindow.close()
        self.dedicatedCountersWindow.close()
        self.pulseProgramDialog.onClose()
        self.logicAnalyzerWindow.close()

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
        self.config['Settings.ShutterNameDict'] = self.shutterNameDict 
        self.config['SettingsTriggerNameDict'] = self.triggerNameDict 
        self.pulseProgramDialog.saveConfig()
        self.settingsDialog.saveConfig()
        self.DDSUi.saveConfig()
        self.shutterUi.saveConfig()
        self.triggerUi.saveConfig()
        self.dedicatedCountersWindow.saveConfig()
        self.logicAnalyzerWindow.saveConfig()
        self.voltageControlWindow.saveConfig()
        self.ExternalParametersSelectionUi.saveConfig()
        self.globalVariablesUi.saveConfig()
        self.loggerUi.saveConfig()
        
    def onProjectSelection(self):
        ProjectSelectionUi.GetProjectSelection()
        
        
if __name__ == "__main__":
    import sys
    from voltageControl.VoltageControl import VoltageControl

    #The next three lines make it so that the icon in the Windows taskbar matches the icon set in Qt Designer
    import ctypes
    myappid = 'TrappedIons.FPGAControlProgram' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    parser = argparse.ArgumentParser(description='Get a program and run it with input', version='%(prog)s 1.0')
    parser.add_argument('--project',type=str,default=None,help='project name')
    args = parser.parse_args()
    app = QtGui.QApplication(sys.argv)

    logger = logging.getLogger("")

    project, projectDir = ProjectSelectionUi.GetProjectSelection(True)
    
    if project:
        DataDirectory.DefaultProject = project
        
        with configshelve.configshelve( ProjectSelection.guiConfigFile() ) as config:
            with ExperimentUi(config) as ui:
                ui.setupUi(ui)
                LoggingSetup.qtHandler.textWritten.connect(ui.onMessageWrite)
                ui.show()
                sys.exit(app.exec_())
    else:
        logger.warning( "No project selected. Nothing I can do about that ;)" )
