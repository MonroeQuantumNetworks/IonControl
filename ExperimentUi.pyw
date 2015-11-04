# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 17:37:41 2012

This is the main gui program for the ExperimentalUi

@author: pmaunz
"""
import webbrowser

from PyQt4 import QtCore, QtGui
import PyQt4.uic
from ProjectConfig.Project import Project, ProjectInfoUi
import sys
import logging
import os
from modules.XmlUtilit import prettify
from modules.SequenceDict import SequenceDict
from functools import partial
import xml.etree.ElementTree as ElementTree
from gui import GlobalVariables
from gui import ScanExperiment
from dedicatedCounters.DedicatedCounters import DedicatedCounters
from externalParameter import ExternalParameterSelection
from externalParameter import ExternalParameterUi
from externalParameter.InstrumentLoggingDisplay import InstrumentLoggingDisplay
from logicAnalyzer.LogicAnalyzer import LogicAnalyzer
from modules import DataDirectory, MyException
from modules.DataChanged import DataChanged
from persist import configshelve
from pulseProgram import PulseProgramUi
from uiModules.ImportErrorPopup import importErrorPopup
from gui.TodoList import TodoList
from gui.Preferences import PreferencesUi
from gui.MeasurementLogUi.MeasurementLogUi import MeasurementLogUi
from gui.ValueHistoryUi import ValueHistoryUi
from scripting.ScriptingUi import ScriptingUi
from pulser import DDSUi
from pulser.DACUi import DACUi
from pulser.DACController import DACController    #@UnresolvedImport
from pulser.PulserHardwareClient import PulserHardware
from pulser.ChannelNameDict import ChannelNameDict
from pulser import ShutterUi
from pulser.OKBase import OKBase
from pulser.PulserParameterUi import PulserParameterUi
from gui.FPGASettings import FPGASettings
import ctypes
import locket
import scan.EvaluationAlgorithms #@UnusedImport

setID = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
if __name__=='__main__': #imports that aren't just definitions
    from uiModules import MagnitudeParameter #@UnusedImport
    from mylogging.ExceptionLogButton import ExceptionLogButton, LogButton
    from mylogging import LoggingSetup  #@UnusedImport #This runs the logging setup code
    from mylogging.LoggingSetup import qtWarningButtonHandler
    from mylogging.LoggerLevelsUi import LoggerLevelsUi

WidgetContainerForm, WidgetContainerBase = PyQt4.uic.loadUiType(r'ui\Experiment.ui')


class ConfigException(Exception):
    pass


def checkFileValid( filename, typeName, FPGAName ):
    if not filename:
        raise ConfigException("No {0} specified".format(typeName))
    elif not isinstance(filename, str):
        raise ConfigException("{0} '{1}' specified in '{2}' config is not a string".format(typeName, filename, FPGAName))
    elif not os.path.exists(filename):
        raise ConfigException("Unable to open {0} '{1}' specified in '{2}' config: Invalid {0} path".format(typeName, filename, FPGAName))


class ExperimentUi(WidgetContainerBase,WidgetContainerForm):
    levelNameList = ["debug", "info", "warning", "error", "critical"]
    levelValueList = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]

    def __init__(self, config, project):
        self.config = config
        self.project = project
        super(ExperimentUi, self).__init__()
        self.settings = FPGASettings()
        self.loggingLevel = config.get('Settings.loggingLevel',logging.INFO)
        self.consoleMaximumLines = config.get('Settings.consoleMaximumLinesNew',100)
        self.consoleEnable = config.get('Settings.consoleEnable',False)
        self.shutterNameDict = config.get('Settings.ShutterNameDict', ChannelNameDict())
        if self.shutterNameDict.__class__.__name__ == 'ChannelNameMap':
            self.shutterNameDict = ChannelNameDict( self.shutterNameDict.names )
        self.shutterNameSignal = DataChanged()
        self.triggerNameDict = config.get('Settings.TriggerNameDict', ChannelNameDict())
        if self.triggerNameDict.__class__.__name__ == 'ChannelNameMap':
            self.triggerNameDict = ChannelNameDict( self.triggerNameDict.names )
        self.triggerNameSignal = DataChanged()
        if self.loggingLevel not in self.levelValueList: self.loggingLevel = logging.INFO
        self.dbConnection = project.dbConnection

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

        self.warningLogButton = LogButton(messageIcon=":/petersIcons/icons/Warning.png", messageName="warnings")
        self.toolBar.addWidget(self.warningLogButton)
        qtWarningButtonHandler.textWritten.connect(self.warningLogButton.addMessage)

        # Setup Console Dockwidget
        self.levelComboBox.addItems(self.levelNameList)
        self.levelComboBox.currentIndexChanged[int].connect( self.setLoggingLevel )
        self.levelComboBox.setCurrentIndex( self.levelValueList.index(self.loggingLevel) )
        self.consoleClearButton.clicked.connect( self.onClearConsole )
        self.linesSpinBox.valueChanged.connect( self.onConsoleMaximumLinesChanged )
        self.linesSpinBox.setValue( self.consoleMaximumLines )
        self.checkBoxEnableConsole.stateChanged.connect( self.onEnableConsole )
        self.checkBoxEnableConsole.setChecked( self.consoleEnable )

        self.parent = parent
        self.tabDict = SequenceDict()

        #determine if AWG software is enabled and import class if it is
        self.AWGEnabled = self.project.isEnabled('software', 'AWG')
        if self.AWGEnabled:
            from AWG.AWGUi import AWGUi

        #determine if Voltages software is enabled and import class if it is
        softwareVoltages = self.project.software.get('Voltages')
        self.voltagesEnabled = self.project.isEnabled('software', 'Voltages')
        hardwareVoltagesName = softwareVoltages.get('hardware') if softwareVoltages else None
        hardwareVoltagesEnabled = self.project.isEnabled('hardware', hardwareVoltagesName)
        if self.voltagesEnabled:
            from voltageControl.VoltageControl import VoltageControl

        #setup external parameters; import specific libraries if they are needed, popup warnings if selected hardware import fail
        import externalParameter.StandardExternalParameter
        import externalParameter.InterProcessParameters
        if self.project.isEnabled('hardware', 'Conex Motion'):
            try:
                import externalParameter.MotionParameter #@UnusedImport
            except ImportError: #popup on failed import
                importErrorPopup('Conex Motion')
        if self.project.isEnabled('hardware', 'APT Motion'):
            try:
                import externalParameter.APTInstruments #@UnusedImport
            except ImportError: #popup on failed import
                importErrorPopup('APT Motion')
        from externalParameter.ExternalParameterBase import InstrumentDict

        #setup FPGAs
        self.setupFPGAs()

        # initialize PulseProgramUi
        pulserConfig = self.pulser.pulserConfiguration()
        self.shutterNameDict.defaultDict = pulserConfig.shutterBits if pulserConfig else dict()
        self.triggerNameDict.defaultDict = pulserConfig.triggerBits if pulserConfig else dict()
        self.counterNameDict = pulserConfig.counterBits if pulserConfig else dict()
        self.channelNameData = (self.shutterNameDict, self.shutterNameSignal, self.triggerNameDict, self.triggerNameSignal, self.counterNameDict )
        self.pulseProgramDialog = PulseProgramUi.PulseProgramSetUi(self.config,  self.channelNameData )
        self.pulseProgramDialog.setupUi(self.pulseProgramDialog)

        # Global Variables
        self.globalVariablesUi = GlobalVariables.GlobalVariableUi(self.config)
        self.globalVariablesUi.setupUi(self.globalVariablesUi)
        self.globalVariablesDock = QtGui.QDockWidget("Global Variables")
        self.globalVariablesDock.setObjectName("Global Variables")
        self.globalVariablesDock.setWidget( self.globalVariablesUi )
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea , self.globalVariablesDock)

        self.measurementLog = MeasurementLogUi(self.config, self.dbConnection)
        self.measurementLog.setupUi(self.measurementLog)
        #self.measurementLogDock = QtGui.QDockWidget("Measurement Log")
        #self.measurementLogDock.setWidget( self.measurementLog )
        #self.measurementLogDock.setObjectName('_MeasurementLog')
        #self.addDockWidget( QtCore.Qt.BottomDockWidgetArea, self.measurementLogDock )
        
        for widget,name in [ (ScanExperiment.ScanExperiment(self.settings,self.pulser,self.globalVariablesUi,"ScanExperiment", toolBar=self.experimentToolBar, 
                                                            measurementLog=self.measurementLog, callWhenDoneAdjusting=self.callWhenDoneAdjusting), "Scan")
                             ]:
            widget.setupUi( widget, self.config )
            if hasattr(widget,'setPulseProgramUi'):
                widget.setPulseProgramUi( self.pulseProgramDialog )
            if hasattr(widget, 'plotsChanged'):
                widget.plotsChanged.connect( self.initMenu )
            self.tabWidget.addTab(widget, name)
            self.tabDict[name] = widget
            widget.ClearStatusMessage.connect( self.statusbar.clearMessage)
            widget.StatusMessage.connect( self.statusbar.showMessage)
                    
        self.scanExperiment = self.tabDict["Scan"]
                    
        self.shutterUi = ShutterUi.ShutterUi(self.pulser, 'shutter', self.config, (self.shutterNameDict, self.shutterNameSignal), size=49 )
        self.shutterUi.setupUi(self.shutterUi, True)
        self.shutterDockWidget.setWidget( self.shutterUi )
        self.pulser.ppActiveChanged.connect( self.shutterUi.setDisabled )
        logger.debug( "ShutterUi representation:" + repr(self.shutterUi) )

        self.triggerUi = ShutterUi.TriggerUi(self.pulser, 'trigger', self.config, (self.triggerNameDict, self.triggerNameSignal) )
        self.triggerUi.offColor =  QtGui.QColor(QtCore.Qt.white)
        self.triggerUi.setupUi(self.triggerUi)
        self.pulser.ppActiveChanged.connect( self.triggerUi.setDisabled )
        self.triggerDockWidget.setWidget( self.triggerUi )

        self.preferencesUi = PreferencesUi(config, self)
        self.preferencesUi.setupUi(self.preferencesUi)
        self.preferencesUiDock = QtGui.QDockWidget("Print Preferences")
        self.preferencesUiDock.setWidget(self.preferencesUi)
        self.preferencesUiDock.setObjectName("_preferencesUi")
        self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.preferencesUiDock)

        if self.AWGEnabled:
            self.AWGUi = AWGUi(self.pulser, self.config, self.globalVariablesUi.variables)
            self.AWGUi.setupUi(self.AWGUi)
            self.AWGUiDock = QtGui.QDockWidget("AWG")
            self.AWGUiDock.setWidget(self.AWGUi)
            self.AWGUiDock.setObjectName("_AWGUi")
            self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.AWGUiDock)
            self.AWGUi.outputChannelsChanged.connect( partial(self.scanExperiment.updateScanTarget, 'AWG') )
            self.scanExperiment.updateScanTarget( 'AWG', self.AWGUi.outputChannels() )
            self.globalVariablesUi.valueChanged.connect( self.AWGUi.evaluate )

        self.pulserParameterUi = PulserParameterUi(self.pulser, self.config, self.globalVariablesUi.variables)
        self.pulserParameterUi.setupUi()
        self.pulserParameterUiDock = QtGui.QDockWidget("Pulser Parameters")
        self.pulserParameterUiDock.setWidget(self.pulserParameterUi)
        self.pulserParameterUiDock.setObjectName("_pulserParameterUi")
        self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.pulserParameterUiDock)
        self.tabDict['Scan'].NeedsDDSRewrite.connect( self.pulserParameterUi.onWriteAll )

        self.DDSUi = DDSUi.DDSUi(self.config, self.pulser, self.globalVariablesUi.variables )
        self.DDSUi.setupUi(self.DDSUi)
        self.DDSDockWidget.setWidget( self.DDSUi )
        self.globalVariablesUi.valueChanged.connect( self.DDSUi.evaluate )
        self.pulser.ppActiveChanged.connect( self.DDSUi.setDisabled )
        self.tabDict['Scan'].NeedsDDSRewrite.connect( self.DDSUi.onWriteAll )
        
        self.DACUi = DACUi(self.config, self.pulser, self.globalVariablesUi.variables )
        self.DACUi.setupUi(self.DACUi)
        self.DACDockWidget = QtGui.QDockWidget("DAC")
        self.DACDockWidget.setObjectName("_DAC_")
        self.DACDockWidget.setWidget( self.DACUi )
        self.pulser.ppActiveChanged.connect( self.DACUi.setDisabled )
        self.tabDict['Scan'].NeedsDDSRewrite.connect( self.DACUi.onWriteAll )
        self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.DACDockWidget )

#         self.DDSUi9910 = DDSUi9910.DDSUi(self.config, self.pulser )
#         self.DDSUi9910.setupUi(self.DDSUi9910)
#         self.DDS9910DockWidget.setWidget( self.DDSUi9910 )
#        self.pulser.ppActiveChanged.connect( self.DDSUi9910.setDisabled )
        #self.tabDict['Scan'].NeedsDDSRewrite.connect( self.DDSUi9910.onWriteAll )

        self.valueHistoryUi = ValueHistoryUi(self.config, self.dbConnection)
        self.valueHistoryUi.setupUi( self.valueHistoryUi )
        self.valueHistoryDock = QtGui.QDockWidget("Value History")
        self.valueHistoryDock.setWidget( self.valueHistoryUi )
        self.valueHistoryDock.setObjectName("_valueHistory")
        self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.valueHistoryDock )
        
        # tabify the dock widgets
        self.tabifyDockWidget( self.pulserParameterUiDock, self.preferencesUiDock)
        self.tabifyDockWidget( self.preferencesUiDock, self.triggerDockWidget )
        self.tabifyDockWidget( self.triggerDockWidget, self.shutterDockWidget)
        self.tabifyDockWidget( self.shutterDockWidget, self.DDSDockWidget )
        self.tabifyDockWidget( self.DDSDockWidget, self.DACDockWidget )
#        self.tabifyDockWidget( self.DDSDockWidget, self.DDS9910DockWidget )
#        self.tabifyDockWidget( self.DDS9910DockWidget, self.globalVariablesDock )
        self.tabifyDockWidget( self.DACDockWidget, self.globalVariablesDock )
        self.tabifyDockWidget( self.globalVariablesDock, self.valueHistoryDock )
        if self.AWGEnabled:
            self.tabifyDockWidget( self.valueHistoryDock, self.AWGUiDock )
        self.triggerDockWidget.hide()
        self.preferencesUiDock.hide()

        self.ExternalParametersSelectionUi = ExternalParameterSelection.SelectionUi(self.config, self.globalVariablesUi.variables, classdict=InstrumentDict)
        self.ExternalParametersSelectionUi.setupUi( self.ExternalParametersSelectionUi )
        self.ExternalParameterSelectionDock = QtGui.QDockWidget("Params Selection")
        self.ExternalParameterSelectionDock.setObjectName("_ExternalParameterSelectionDock")
        self.ExternalParameterSelectionDock.setWidget(self.ExternalParametersSelectionUi)
        self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.ExternalParameterSelectionDock)

        self.ExternalParametersUi = ExternalParameterUi.ControlUi(self.config, self.globalVariablesUi.variables)
        self.ExternalParametersUi.setupUi(self.ExternalParametersSelectionUi.outputChannels())

        self.ExternalParameterDock = QtGui.QDockWidget("Params Control")
        self.ExternalParameterDock.setWidget(self.ExternalParametersUi)
        self.ExternalParameterDock.setObjectName("_ExternalParameterDock")
        self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.ExternalParameterDock)
        self.ExternalParametersSelectionUi.outputChannelsChanged.connect( self.ExternalParametersUi.setupParameters )

        self.instrumentLoggingDisplay = InstrumentLoggingDisplay(self.config)
        self.instrumentLoggingDisplay.setupUi( self.ExternalParametersSelectionUi.inputChannels(), self.instrumentLoggingDisplay )
        self.instrumentLoggingDisplayDock = QtGui.QDockWidget("Params Reading")
        self.instrumentLoggingDisplayDock.setObjectName("_ExternalParameterDisplayDock")
        self.instrumentLoggingDisplayDock.setWidget(self.instrumentLoggingDisplay)
        self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.instrumentLoggingDisplayDock)
        self.ExternalParametersSelectionUi.inputChannelsChanged.connect( self.instrumentLoggingDisplay.setupParameters )
               
        self.ExternalParametersSelectionUi.outputChannelsChanged.connect( partial(self.scanExperiment.updateScanTarget, 'External') )               
        self.scanExperiment.updateScanTarget( 'External', self.ExternalParametersSelectionUi.outputChannels() )
        
        self.todoList = TodoList( self.tabDict, self.config, self.getCurrentTab, self.switchTab, self.globalVariablesUi )
        self.todoList.setupUi()
        self.todoListDock = QtGui.QDockWidget("Todo List")
        self.todoListDock.setWidget(self.todoList)
        self.todoListDock.setObjectName("_todoList")
        self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.todoListDock)
        if self.AWGEnabled: self.tabifyDockWidget(self.AWGUiDock, self.todoListDock)
        else: self.tabifyDockWidget(self.valueHistoryDock, self.todoListDock)

        for name, widget in self.tabDict.iteritems():
            if hasattr( widget, 'scanConfigurationListChanged' ) and widget.scanConfigurationListChanged is not None:
                widget.scanConfigurationListChanged.connect( partial( self.todoList.populateMeasurementsItem, name)  )
            if hasattr( widget, 'evaluationConfigurationChanged' ) and widget.evaluationConfigurationChanged is not None:
                widget.evaluationConfigurationChanged.connect( partial( self.todoList.populateEvaluationItem, name)  )
            if hasattr( widget, 'analysisConfigurationChanged' ) and widget.analysisConfigurationChanged is not None:
                widget.analysisConfigurationChanged.connect( partial( self.todoList.populateAnalysisItem, name)  )
       
        #tabify external parameters controls
        self.tabifyDockWidget(self.ExternalParameterSelectionDock, self.ExternalParameterDock)
        self.tabifyDockWidget(self.ExternalParameterDock, self.instrumentLoggingDisplayDock)
        
        self.tabWidget.currentChanged.connect(self.onCurrentChanged)
        self.actionClear.triggered.connect(self.onClear)
        self.actionPause.triggered.connect(self.onPause)

        #Save and load actions
        self.actionSave_GUI.triggered.connect(self.onSaveGUI)
        settingsCategories = ('All Settings', 'Scan Settings', 'Evaluation Settings', 'Analysis Settings', 'Pulse Program Settings', 'Global Variables')
        importModes = ('Replace', 'Update', 'Add')
        self.actionSave_Settings.triggered.connect(self.onSaveSettings)
        for category in settingsCategories:
            loadMenu = QtGui.QMenu(category, self)
            self.menuLoad_Settings.addMenu(loadMenu)
            for mode in importModes:
                loadAction = QtGui.QAction(mode, self)
                loadMenu.addAction(loadAction)
                loadAction.triggered.connect(partial(self.onLoadSettings, category, mode))

        self.actionStart.triggered.connect(self.onStart)
        self.actionStop.triggered.connect(self.onStop)
        self.actionAbort.triggered.connect(self.onAbort)
        self.actionExit.triggered.connect(self.onClose)
        self.actionContinue.triggered.connect(self.onContinue)
        self.actionPulses.triggered.connect(self.onPulses)
        self.actionReload.triggered.connect(self.onReload)
        self.actionProject.triggered.connect( self.onProjectSelection)
        self.actionDocumentation.triggered.connect(self.onShowDocumentation)
        if self.voltagesEnabled:
            self.actionVoltageControl.triggered.connect(self.onVoltageControl)
        else:
            self.actionVoltageControl.setDisabled(True)
            self.actionVoltageControl.setVisible(False)
        self.actionScripting.triggered.connect(self.onScripting)
        self.actionMeasurementLog.triggered.connect(self.onMeasurementLog)
        self.actionDedicatedCounters.triggered.connect(self.showDedicatedCounters)
        self.actionLogic.triggered.connect(self.showLogicAnalyzer)
        self.currentTab = self.tabDict.at( min(len(self.tabDict)-1, self.config.get('MainWindow.currentIndex',0) ) )
        self.tabWidget.setCurrentIndex( self.config.get('MainWindow.currentIndex',0) )
        self.currentTab.activate()
        if hasattr( self.currentTab, 'stateChanged' ):
            self.currentTab.stateChanged.connect( self.todoList.onStateChanged )
        if 'MainWindow.State' in self.config:
            self.parent.restoreState(self.config['MainWindow.State'])
        self.initMenu()
        if 'MainWindow.pos' in self.config:
            self.move(self.config['MainWindow.pos'])
        if 'MainWindow.size' in self.config:
            self.resize(self.config['MainWindow.size'])
        if 'MainWindow.isMaximized' in self.config:
            if self.config['MainWindow.isMaximized']:
                self.showMaximized()
        else:
            self.showMaximized()
            
        self.dedicatedCountersWindow = DedicatedCounters(self.config, self.dbConnection, self.pulser, self.globalVariablesUi, self.ExternalParametersUi.callWhenDoneAdjusting )
        self.dedicatedCountersWindow.setupUi(self.dedicatedCountersWindow)
        
        self.logicAnalyzerWindow = LogicAnalyzer(self.config, self.pulser, self.channelNameData )
        self.logicAnalyzerWindow.setupUi(self.logicAnalyzerWindow)

        if self.voltagesEnabled:
            try:
                self.voltageControlWindow = VoltageControl(self.config, self.globalVariablesUi.variables, self.dac)
                self.voltageControlWindow.setupUi(self.voltageControlWindow)
                self.voltageControlWindow.globalAdjustUi.outputChannelsChanged.connect( partial(self.scanExperiment.updateScanTarget, 'Voltage') )
                #self.voltageControlWindow.localAdjustUi.outputChannelsChanged.connect( partial(self.scanExperiment.updateScanTarget, 'Voltage Local Adjust') )
                self.scanExperiment.updateScanTarget( 'Voltage', self.voltageControlWindow.globalAdjustUi.outputChannels() )
                #self.scanExperiment.updateScanTarget( 'Voltage Local Adjust', self.voltageControlWindow.localAdjustUi.outputChannels() )
            except MyException.MissingFile as e:
                self.voltageControlWindow = None
                self.actionVoltageControl.setDisabled( True )
                logger.warning("Missing file - voltage subsystem disabled: {0}".format(str(e)))
            if self.voltageControlWindow:
                self.tabDict["Scan"].ppStartSignal.connect( self.voltageControlWindow.synchronize )   # upload shuttling data before running pule program
                self.dedicatedCountersWindow.autoLoad.setVoltageControl( self.voltageControlWindow )

        self.setWindowTitle("Experimental Control ({0})".format(self.project) )

        
        QtCore.QTimer.singleShot(60000, self.onCommitConfig )
        traceFilename, _ = DataDirectory.DataDirectory().sequencefile("Trace.log")
        LoggingSetup.setTraceFilename( traceFilename )
        errorFilename, _ = DataDirectory.DataDirectory().sequencefile("Error.log")
        LoggingSetup.setErrorFilename( errorFilename )
        
        # connect signals and slots for todolist and auto resume
        for name, widget in self.tabDict.iteritems():
            if hasattr(widget,'onContinue'):
                self.dedicatedCountersWindow.autoLoad.ionReappeared.connect( widget.onContinue )
                
        # add PushDestinations
        for widget in self.tabDict.values():
            if hasattr(widget, 'addPushDestination'):
                widget.addPushDestination( 'External', self.ExternalParametersUi )
                
        # initialize ScriptingUi
        self.scriptingWindow = ScriptingUi(self)
        self.scriptingWindow.setupUi(self.scriptingWindow)

    def callWhenDoneAdjusting(self, callback):
        self.ExternalParametersUi.callWhenDoneAdjusting(callback)

    def onEnableConsole(self, state):
        self.consoleEnable = state==QtCore.Qt.Checked

    def onClearConsole(self):
        self.textEditConsole.clear()
        
    def onConsoleMaximumLinesChanged(self, maxlines):
        self.consoleMaximumLines = maxlines
        self.textEditConsole.document().setMaximumBlockCount(maxlines)
        
    def setLoggingLevel(self, index):
        self.loggingLevel = self.levelValueList[index]

    def showDedicatedCounters(self):
        self.dedicatedCountersWindow.show()
        self.dedicatedCountersWindow.setWindowState(QtCore.Qt.WindowActive)
        self.dedicatedCountersWindow.raise_()
        self.dedicatedCountersWindow.onStart() #Start displaying data immediately
        self.dedicatedCountersWindow._graphicsView.onHoldZero() #Set the plot to "hold zero" autorange mode

    def showLogicAnalyzer(self):
        self.logicAnalyzerWindow.show()
        self.logicAnalyzerWindow.setWindowState(QtCore.Qt.WindowActive)
        self.logicAnalyzerWindow.raise_()

    def onVoltageControl(self):
        self.voltageControlWindow.show()
        self.voltageControlWindow.setWindowState(QtCore.Qt.WindowActive)
        self.voltageControlWindow.raise_()

    def onScripting(self):
        self.scriptingWindow.show()
        self.scriptingWindow.setWindowState(QtCore.Qt.WindowActive)
        self.scriptingWindow.raise_()
        
    def onMeasurementLog(self):
        self.measurementLog.show()
        self.measurementLog.setWindowState(QtCore.Qt.WindowActive)
        self.measurementLog.raise_()
        
    def onClear(self):
        self.currentTab.onClear()
    
    def onSaveGUI(self, _):
        logger = logging.getLogger(__name__)
        self.currentTab.onSave()
        logger.info( "Saving config" )
        filename, _ = DataDirectory.DataDirectory().sequencefile("configuration.db")
        self.saveConfig()
        self.config.saveConfig(filename)
        
    def onSaveSettings(self):
        """Save settings associated with given category"""
        #Not looking at category yet
        root = ElementTree.Element('IonControlSettings')
        self.globalVariablesUi.onExportXml(root, writeToFile=False)
        self.todoList.onExportXml(root, writeToFile=False)
        if hasattr(self.currentTab,'exportXml'):
            self.currentTab.exportXml(root)   
        filename = DataDirectory.DataDirectory().sequencefile("IonControlSettings.xml")[0]
        with open(filename,'w') as f:
            f.write(prettify(root))
            
    def onLoadSettings(self, category, mode):
        """Load settings associated with given category, with given mode"""
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Import XML file', filter="*.xml" )
        if filename:
            tree = ElementTree.parse(filename)
            root = tree.getroot()
            if category in ['All Settings', 'Global Variables']:
                self.globalVariablesUi.importXml(root, mode=mode)
            if category in ['All Settings']:
                self.todoList.importXml(root, mode=mode)
            if hasattr(self.currentTab,'importXml'):
                self.currentTab.importXml(root, category, mode)
         
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
        
    def onAbort(self):
        self.currentTab.onStop(reason='aborted')
        
    def onContinue(self):
        if hasattr(self.currentTab,'onContinue'):
            self.currentTab.onStop()
        else:
            self.statusbar.showMessage("continue not implemented")    
            
    def onReload(self):
        logger = logging.getLogger(__name__)
        logger.debug( "OnReload" )
        self.currentTab.onReload()
    
    def switchTab(self, name):
        self.tabWidget.setCurrentWidget( self.tabDict[name] )
        self.onCurrentChanged(self.tabDict.index(name))  # this gets called later, but we need it to run now in order to switch scans from the todolist
    
    def onCurrentChanged(self, index):
        if self.tabDict.at(index)!=self.currentTab:
            self.currentTab.deactivate()
            if hasattr( self.currentTab, 'stateChanged' ):
                try:
                    self.currentTab.stateChanged.disconnect()
                except TypeError:
                    pass
            self.currentTab = self.tabDict.at(index)
            self.currentTab.activate()
            if hasattr( self.currentTab, 'stateChanged' ):
                self.currentTab.stateChanged.connect( self.todoList.onStateChanged )
            self.initMenu()
        
    def initMenu(self):
        """setup print and view menus"""
        #view menu
        self.menuView.clear()
        if hasattr(self.currentTab,'viewActions'):
            self.menuView.addActions(self.currentTab.viewActions())
        dockList = self.findChildren(QtGui.QDockWidget)
        for dock in dockList:
            self.menuView.addAction(dock.toggleViewAction())

        #print menu
        self.menuPrint.clear()
        if hasattr(self.currentTab,'printTargets'):
            for plot in self.currentTab.printTargets():
                action = self.menuPrint.addAction( plot )
                action.triggered.connect( partial(self.onPrint, plot ))
        self.menuPrint.addSeparator()
        action = self.menuPrint.addAction("Print Preferences")
        action.triggered.connect(self.preferencesUiDock.show)
        action.triggered.connect(self.preferencesUiDock.raise_)

    def onPulses(self):
        self.pulseProgramDialog.show()
        self.pulseProgramDialog.setWindowState(QtCore.Qt.WindowActive)
        self.pulseProgramDialog.raise_()
        if hasattr(self.currentTab,'experimentName'):
            self.pulseProgramDialog.setCurrentTab(self.currentTab.experimentName)
                  
    def onClose(self):
        self.parent.close()
        
    def onMessageWrite(self,message,level=logging.DEBUG):
        if self.consoleEnable and level>= self.loggingLevel:
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
        self.config.saveConfig() 
        for tab in self.tabDict.values():
            tab.onClose()
        self.currentTab.deactivate()
        self.pulseProgramDialog.done(0)
        self.ExternalParametersSelectionUi.onClose()
        self.dedicatedCountersWindow.close()
        self.pulseProgramDialog.onClose()
        self.scriptingWindow.onClose()
        self.logicAnalyzerWindow.close()
        self.measurementLog.close()
        if self.voltagesEnabled:
            self.voltageControlWindow.close()
        numTempAreas = len(self.scanExperiment.area.tempAreas)
        for i in range(numTempAreas):
            if len(self.scanExperiment.area.tempAreas) > 0:
                self.scanExperiment.area.tempAreas[0].win.close()

    def saveConfig(self):
        self.config['MainWindow.State'] = self.parent.saveState()
        for tab in self.tabDict.values():
            tab.saveConfig()
        self.config['MainWindow.currentIndex'] = self.tabWidget.currentIndex()
        self.config['MainWindow.pos'] = self.pos()
        self.config['MainWindow.size'] = self.size()
        self.config['MainWindow.isMaximized'] = self.isMaximized()
        self.config['Settings.loggingLevel'] = self.loggingLevel
        self.config['Settings.consoleMaximumLinesNew'] = self.consoleMaximumLines
        self.config['Settings.ShutterNameDict'] = self.shutterNameDict 
        self.config['SettingsTriggerNameDict'] = self.triggerNameDict 
        self.config['Settings.consoleEnable'] = self.consoleEnable 
        self.pulseProgramDialog.saveConfig()
        self.scriptingWindow.saveConfig()
        self.DDSUi.saveConfig()
        self.DACUi.saveConfig()
        #self.DDSUi9910.saveConfig()
        self.shutterUi.saveConfig()
        self.triggerUi.saveConfig()
        self.dedicatedCountersWindow.saveConfig()
        self.logicAnalyzerWindow.saveConfig()
        if self.voltagesEnabled:
            if self.voltageControlWindow:
                self.voltageControlWindow.saveConfig()
        self.ExternalParametersSelectionUi.saveConfig()
        self.globalVariablesUi.saveConfig()
        self.loggerUi.saveConfig()
        self.todoList.saveConfig()
        self.preferencesUi.saveConfig()
        self.measurementLog.saveConfig()
        self.valueHistoryUi.saveConfig()
        self.ExternalParametersUi.saveConfig()
        self.pulserParameterUi.saveConfig()
        if self.AWGEnabled:
            self.AWGUi.saveConfig()
        
    def onProjectSelection(self):
        ui = ProjectInfoUi(self.project)
        ui.show()
        ui.exec_()
        
    def getCurrentTab(self):
        index = self.tabWidget.currentIndex()
        return self.tabDict.keyAt(index), self.tabDict.at(index)
    
    def setCurrentTab(self, name):
        self.onCurrentChanged(self.tabDict.index(name))

    def onPrint(self, target):
        """Print action is triggered on 'target', which is a plot name"""
        if hasattr( self.currentTab, 'onPrint' ):
            printer = QtGui.QPrinter(mode=QtGui.QPrinter.ScreenResolution)
            if self.preferencesUi.preferences().printPreferences.doPrint:
                dialog = QtGui.QPrintDialog(printer, self)
                dialog.setWindowTitle("Print Document")
                if dialog.exec_() != QtGui.QDialog.Accepted:
                    return
            printer.setResolution(self.preferencesUi.preferences().printPreferences.printResolution)
    
            pdfPrinter = QtGui.QPrinter()
            pdfPrinter.setOutputFormat(QtGui.QPrinter.PdfFormat)
            pdfPrinter.setOutputFileName(DataDirectory.DataDirectory().sequencefile(target+".pdf")[0])
            self.currentTab.onPrint(target, printer, pdfPrinter, self.preferencesUi.preferences().printPreferences)

    def onShowDocumentation(self):
        url = "file://" + os.path.join(os.path.dirname(os.path.abspath(__file__)),"docs\\_build\\html\\index.html")
        webbrowser.open(url, new=2)

    def show(self):
        """show ExperimentUi, and any of the other main windows which were previously visible"""
        super(ExperimentUi, self).show()

        # restore dock state of ScanExperiment. Because ScanExperiment is a child QMainWindow of ExperimentUi
        # (rather than an independent window), restoreState must be called after show() is called on the parent
        # widget in order to work properly.
        for tab in self.tabDict.values():
            tabStateName = tab.experimentName+'.MainWindow.State'
            if tabStateName in self.config:
                tab.restoreState(self.config[tabStateName])

        pulseProgramVisible = self.config.get(self.pulseProgramDialog.configname+'.isVisible', True) #pulse program defaults to visible
        if pulseProgramVisible: self.pulseProgramDialog.show()
        else: self.pulseProgramDialog.hide()

        scriptingWindowVisible = self.config.get(self.scriptingWindow.configname+'.isVisible', False)
        if scriptingWindowVisible: self.scriptingWindow.show()
        else: self.scriptingWindow.hide()

        if self.voltagesEnabled:
            voltageControlWindowVisible = getattr(self.voltageControlWindow.settings, 'isVisible', False)
            if voltageControlWindowVisible: self.voltageControlWindow.show()
            else: self.voltageControlWindow.hide()

        self.raise_()

    def setupFPGAs(self):
        """Setup all Opal Kelly FPGAs"""
        self.pmt32 = OKBase() #32 channel PMT
        self.dac = DACController() #100 channel DAC board

        #Determine what's enabled
        softwarePulserConfig = self.project.software.get('Pulser')
        softwarePulserEnabled = softwarePulserConfig.get('enabled') if softwarePulserConfig else False
        hardwarePulserName = softwarePulserConfig.get('hardware') if softwarePulserConfig else None
        hardwarePulserConfig = self.project.hardware.get(hardwarePulserName)
        hardwarePulserEnabled = hardwarePulserConfig.get('enabled') if hardwarePulserConfig else False
        self.pulserEnabled = softwarePulserEnabled and hardwarePulserEnabled

        pmt32Name = "Opal Kelly FPGA: 32 Channel PMT"
        pmt32Config = self.project.hardware.get(pmt32Name)
        self.pmt32Enabled = pmt32Config.get('enabled') if pmt32Config else False

        dacName = "Opal Kelly FPGA: DAC"
        dacConfig = self.project.hardware.get(dacName)
        self.dacEnabled = dacConfig.get('enabled') if dacConfig else False

        self.settings = FPGASettings() #settings for pulser specifically
        if not any([self.pulserEnabled, self.pmt32Enabled, self.dacEnabled]): #if nothing is enabled, no need to do anything
            return

        self.OK_FPGA_Dict = self.pulser.listBoards() #all connected Opal Kelly FPGA boards
        logger.info( "Opal Kelly Devices found: {0}".format({k:v.modelName for k,v in self.OK_FPGA_Dict.iteritems()}) )

        for FPGA, FPGAName, FPGAConfig, FPGAEnabled, hasConfig in [(self.pulser, hardwarePulserName, hardwarePulserConfig, self.pulserEnabled, True),
                                                                   (self.dac, dacName, dacConfig, self.dacEnabled, False),
                                                                   (self.pmt32, pmt32Name, pmt32Config, self.pmt32Enabled, False)]:
            if FPGAEnabled:
                deviceName=FPGAConfig.get('device') #The 'device' field of an FPGA should be the identifier of the FPGA.
                if not deviceName:
                    logger.error("No FPGA specified: 'device' field missing in '{0}' config".format(FPGAName))
                elif deviceName not in self.OK_FPGA_Dict:
                    logger.error("FPGA device {0} specified in '{1}' config cannot be found".format(deviceName, FPGAName))
                else:
                    device=self.OK_FPGA_Dict[deviceName]
                    FPGA.openBySerial(device.serial)
                    bitFile=FPGAConfig.get('bitFile')
                    checkFileValid(bitFile, 'bitfile', FPGAName)
                    if hasConfig:
                        configFile = os.path.splitext(bitFile)[0] + '.xml'
                        checkFileValid(configFile, 'config file', FPGAName)
                    if FPGAConfig.get('uploadOnStartup'):
                        FPGA.uploadBitfile(bitFile)
                        logger.info("Uploaded file '{0}' to {1} (model {2}) in '{3}' config".format(bitFile, deviceName, device.modelName, FPGAName))
                    if hasConfig:   # check and make sure corrct hardware is loaded
                        FPGA.pulserConfiguration(configFile)
                    if FPGA==self.pulser:
                        self.settings.deviceSerial = device.serial
                        self.settings.deviceDescription = device.identifier
                        self.settings.deviceInfo = device
        pulserHardwareId = self.pulser.hardwareConfigurationId()
        if pulserHardwareId:
            logger.info("Pulser Configuration {0:x}".format(pulserHardwareId))
        else:
            logger.error("No pulser available")



if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    project = Project() #loads in the project through the config files/config GUIs
    logger = logging.getLogger("")
    setID('TrappedIons.FPGAControlProgram') #Makes the icon in the Windows taskbar match the icon set in Qt Designer

    lockfile = project.guiConfigFile+".lock"
    try:
        with locket.lock_file(lockfile, timeout=0):
            with configshelve.configshelve(project.guiConfigFile) as config:
                 with ExperimentUi(config, project) as ui:
                    ui.setupUi(ui)
                    LoggingSetup.qtHandler.textWritten.connect(ui.onMessageWrite)
                    ui.show()
                    sys.exit(app.exec_())
    except locket.LockError:
        messageBox = QtGui.QMessageBox()
        response = messageBox.warning(messageBox,
                                  'Configuration file is locked',
                                  'Please make sure no other process is using the same project. If no other process is runnung delete lock file \n"{0}"\nand restart the program.'.format(lockfile),
                                  QtGui.QMessageBox.Abort )
