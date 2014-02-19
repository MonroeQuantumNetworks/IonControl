import logging

from PyQt4 import QtCore, QtGui 
import PyQt4.uic

from mylogging.ExceptionLogButton import ExceptionLogButton
from mylogging.LoggerLevelsUi import LoggerLevelsUi
from mylogging import LoggingSetup  #@UnusedImport
from gui import ProjectSelection
from gui import ProjectSelectionUi
from digitalLock.controller.ControllerClient import Controller 
from gui import SettingsDialog
from modules import DataDirectory
from persist import configshelve
from uiModules import MagnitudeParameter #@UnusedImport
from digitalLock.ui import RepetitionRate_rc   #@UnusedImport

from trace import Traceui
from trace import pens

from digitalLock.LockControl import LockControl
from digitalLock.TraceControl import TraceControl
from digitalLock.LockStatus import LockStatus

from pyqtgraph.dockarea import DockArea, Dock
from pyqtgraph.graphicsItems.ViewBox import ViewBox
from uiModules.CoordinatePlotWidget import CoordinatePlotWidget

WidgetContainerForm, WidgetContainerBase = PyQt4.uic.loadUiType(r'digitalLock\ui\DigitalLockUi.ui')


class DigitalLockUi(WidgetContainerBase,WidgetContainerForm):
    levelNameList = ["debug", "info", "warning", "error", "critical"]
    levelValueList = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
    def __init__(self,config):
        self.config = config
        super(DigitalLockUi, self).__init__()
        self.settings = SettingsDialog.Settings()
        self.deviceSerial = config.get('Settings.deviceSerial')
        self.deviceDescription = config.get('Settings.deviceDescription')
        self.loggingLevel = config.get('Settings.loggingLevel',logging.INFO)
        self.consoleMaximumLines = config.get('Settings.consoleMaximumLines',0)
        self.dockWidgetList = list()
        if self.loggingLevel not in self.levelValueList: self.loggingLevel = logging.INFO
        
    def __enter__(self):
        self.pulser = Controller()
        return self
    
    def __exit__(self, excepttype, value, traceback):
        self.pulser.shutdown()
        return False
    
    def setupUi(self, parent):
        super(DigitalLockUi,self).setupUi(parent)
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
#        self.levelComboBox.currentIndexChanged[int].connect( self.setLoggingLevel )            
        self.levelComboBox.setCurrentIndex( self.levelValueList.index(self.loggingLevel) )
#        self.consoleClearButton.clicked.connect( self.onClearConsole )
#        self.linesSpinBox.valueChanged.connect( self.onConsoleMaximumLinesChanged )
        
        self.parent = parent
        self.tabList = list()
        self.tabDict = dict()
               
        # initialize FPGA settings
        self.settingsDialog = SettingsDialog.SettingsDialog(self.pulser, self.config, self.parent)
        self.settingsDialog.setupUi()
        self.settings = self.settingsDialog.settings

        self.setupPlots()       
        # Traceui
        self.penicons = pens.penicons().penicons()
        self.traceui = Traceui.Traceui(self.penicons,self.config,"Main",self.plotDict["Scope"]["view"])
        self.traceui.setupUi(self.traceui)
        self.setupAsDockWidget(self.traceui, "Traces", QtCore.Qt.LeftDockWidgetArea)

        # Lock oOntrol      
        self.lockControl = LockControl(self.pulser, self.config, self.parent)
        self.lockControl.setupUi() 
        self.setupAsDockWidget(self.lockControl, "Control", QtCore.Qt.RightDockWidgetArea)
        
        # Trace control
        self.traceControl = TraceControl(self.pulser, self.config, self.traceui, self.plotDict["History"]["view"], self.parent)
        self.traceControl.setupUi()
        self.setupAsDockWidget(self.traceControl, "Trace Control", QtCore.Qt.RightDockWidgetArea)
        
        # Trace control
        self.lockStatus = LockStatus(self.pulser, self.config, self.traceui, self.plotDict["History"]["view"], self.parent)
        self.lockStatus.setupUi()
        self.setupAsDockWidget(self.lockStatus, "Status", QtCore.Qt.RightDockWidgetArea)
        
#         self.actionClear.triggered.connect(self.onClear)
#         self.actionPause.triggered.connect(self.onPause)
        self.actionSave.triggered.connect(self.onSave)
#         self.actionStart.triggered.connect(self.onStart)
#         self.actionStop.triggered.connect(self.onStop)
        self.actionSettings.triggered.connect(self.onSettings)
        self.actionExit.triggered.connect(self.onClose)
#         self.actionContinue.triggered.connect(self.onContinue)
#         self.actionPulses.triggered.connect(self.onPulses)
#         self.actionReload.triggered.connect(self.onReload)
        self.actionProject.triggered.connect( self.onProjectSelection)
#         self.actionVoltageControl.triggered.connect(self.onVoltageControl)
#         self.actionDedicatedCounters.triggered.connect(self.showDedicatedCounters)
#         self.actionLogic.triggered.connect(self.showLogicAnalyzer)
        self.setWindowTitle("Digital Lock ({0})".format(project) )
        if 'MainWindow.State' in self.config:
            self.parent.restoreState(self.config['MainWindow.State'])
        self.initMenu()
        
        
    def setupPlots(self):
        self.area = DockArea()
        self.setCentralWidget(self.area)
        self.plotDict = dict()
        plotNames = {"Scope", "History"}
        # initialize all the plot windows we want
        for name in plotNames:
            dock = Dock(name)
            widget = CoordinatePlotWidget(self)
            view = widget.graphicsView
            self.area.addDock(dock, "bottom")
            dock.addWidget(widget)
            self.plotDict[name] = {"dock":dock, "widget":widget, "view":view}
            del dock, widget, view #This is probably unnecessary, but can't hurt
        del plotNames #I don't want to leave this list around, as it is not updated and may cause confusion.

        
    def setupAsDockWidget(self, widget, name, area=QtCore.Qt.RightDockWidgetArea, stackAbove=None, stackBelow=None ):
        dock = QtGui.QDockWidget(name)
        dock.setObjectName(name)
        dock.setWidget( widget )
        self.addDockWidget(area , dock )
        self.dockWidgetList.append( dock )
        if stackAbove is not None:
            self.tabifyDockWidget( stackAbove, dock )
        elif stackBelow is not None:
            self.tabifyDockWidget( dock, stackBelow )
        return dock           

    def onProjectSelection(self):
        ProjectSelectionUi.GetProjectSelection()

    def onSettings(self):
        self.settingsDialog.show()
        
    def onSave(self):
        logger = logging.getLogger(__name__)
        logger.info( "Saving config" )
        filename, _ = DataDirectory.DataDirectory().sequencefile("digitalLock-configuration.db")
        self.saveConfig()
        self.config.saveConfig(filename)
    
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

    def onClose(self):
        self.parent.close()
        
    def closeEvent(self,e):
        logger = logging.getLogger("")
        logger.debug( "Saving Configuration" )
        self.saveConfig()
        self.settingsDialog.done(0)

    def initMenu(self):
        self.menuView.clear()
        for dock in self.dockWidgetList:
            self.menuView.addAction(dock.toggleViewAction())

    def saveConfig(self):
        self.config['MainWindow.State'] = self.parent.saveState()
        for tab in self.tabList:
            tab.saveConfig()
        self.config['Settings.deviceSerial'] = self.settings.deviceSerial
        self.config['Settings.deviceDescription'] = self.settings.deviceDescription
        self.config['MainWindow.pos'] = self.pos()
        self.config['MainWindow.size'] = self.size()
        self.config['Settings.loggingLevel'] = self.loggingLevel
        self.config['Settings.consoleMaximumLines'] = self.consoleMaximumLines
        self.settingsDialog.saveConfig()
        self.loggerUi.saveConfig()
        self.lockControl.saveConfig()
        self.lockStatus.saveConfig()
        self.traceControl.saveConfig()

if __name__ == "__main__":
    #The next three lines make it so that the icon in the Windows taskbar matches the icon set in Qt Designer
    import ctypes, sys
    myappid = 'TrappedIons.DigitalLockUi' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    app = QtGui.QApplication(sys.argv)

    logger = logging.getLogger("")

    project, projectDir = ProjectSelectionUi.GetProjectSelection(True)
    
    if project:
        DataDirectory.DefaultProject = project
        
        with configshelve.configshelve( ProjectSelection.guiConfigFile() ) as config:
            with DigitalLockUi(config) as ui:
                ui.setupUi(ui)
                LoggingSetup.qtHandler.textWritten.connect(ui.onMessageWrite)
                ui.show()
                sys.exit(app.exec_())
    else:
        logger.warning( "No project selected. Nothing I can do about that ;)" )
