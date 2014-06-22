import logging

from PyQt4 import QtCore, QtGui 
import PyQt4.uic

from mylogging.ExceptionLogButton import ExceptionLogButton
from mylogging.LoggerLevelsUi import LoggerLevelsUi
from mylogging import LoggingSetup  #@UnusedImport
from gui import ProjectSelection
from gui import ProjectSelectionUi
from modules import DataDirectory
from persist import configshelve
from uiModules import MagnitudeParameter #@UnusedImport

from trace import Traceui
from trace import pens

from pyqtgraph.dockarea import DockArea, Dock
from uiModules.CoordinatePlotWidget import CoordinatePlotWidget
from externalParameter.InstrumentLogging import LoggingInstruments 
from externalParameter import ExternalParameterSelection 
from externalParameter.InstrumentLoggingHandler import InstrumentLoggingHandler

WidgetContainerForm, WidgetContainerBase = PyQt4.uic.loadUiType(r'ui\InstrumentLoggingUi.ui')


class InstrumentLoggingUi(WidgetContainerBase,WidgetContainerForm):
    levelNameList = ["debug", "info", "warning", "error", "critical"]
    levelValueList = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
    plotConfigurationChanged = QtCore.pyqtSignal( object )
    def __init__(self,config):
        self.config = config
        super(InstrumentLoggingUi, self).__init__()
        self.loggingLevel = config.get('Settings.loggingLevel',logging.INFO)
        self.consoleMaximumLines = config.get('Settings.consoleMaximumLines',0)
        self.dockWidgetList = list()
        if self.loggingLevel not in self.levelValueList: self.loggingLevel = logging.INFO
        self.plotDict = dict()
        self.instrument = ""
        
    def __enter__(self):
        return self
    
    def __exit__(self, excepttype, value, traceback):
        return False
    
    def setupUi(self, parent):
        super(InstrumentLoggingUi,self).setupUi(parent)
        self.dockWidgetConsole.hide()
        self.loggerUi = LoggerLevelsUi(self.config)
        self.loggerUi.setupUi(self.loggerUi)
        self.setupAsDockWidget(self.loggerUi, "Logging", QtCore.Qt.NoDockWidgetArea)
                
        logger = logging.getLogger()        
        self.toolBar.addWidget(ExceptionLogButton())
            
        self.parent = parent
        self.tabList = list()
        self.tabDict = dict()
               
        self.setupPlots()       
        # Traceui
        self.penicons = pens.penicons().penicons()
        self.traceui = Traceui.Traceui(self.penicons,self.config,"Main",self.plotDict[self.plotDict.keys()[0]]["view"])
        self.traceui.setupUi(self.traceui)
        self.setupAsDockWidget(self.traceui, "Traces", QtCore.Qt.LeftDockWidgetArea)

        self.instrumentLoggingHandler = InstrumentLoggingHandler(self.traceui, self.plotDict)

        self.ExternalParametersSelectionUi = ExternalParameterSelection.SelectionUi(self.config, classdict=LoggingInstruments,newDataSlot=self.instrumentLoggingHandler.addData)
        self.ExternalParametersSelectionUi.setupUi( self.ExternalParametersSelectionUi )
        self.ExternalParameterSelectionDock = QtGui.QDockWidget("Params Selection")
        self.ExternalParameterSelectionDock.setObjectName("_ExternalParameterSelectionDock")
        self.ExternalParameterSelectionDock.setWidget(self.ExternalParametersSelectionUi)
        self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.ExternalParameterSelectionDock)
    
        self.actionSave.triggered.connect(self.onSave)
        #self.actionSettings.triggered.connect(self.onSettings)
        self.actionExit.triggered.connect(self.onClose)
        self.actionProject.triggered.connect( self.onProjectSelection)
        
#         self.actionStart.triggered.connect(self.meterControl.onScan)
#         self.actionStop.triggered.connect(self.meterControl.onStop)

        self.addPlot = QtGui.QAction( QtGui.QIcon(":/openicon/icons/add-plot.png"), "Add new plot", self)
        self.addPlot.setToolTip("Add new plot")
        self.addPlot.triggered.connect(self.onAddPlot)
        self.toolBar.addAction(self.addPlot)
        
        self.removePlot = QtGui.QAction( QtGui.QIcon(":/openicon/icons/remove-plot.png"), "Remove a plot", self)
        self.removePlot.setToolTip("Remove a plot")
        self.removePlot.triggered.connect(self.onRemovePlot)
        self.toolBar.addAction(self.removePlot)

        self.renamePlot = QtGui.QAction( QtGui.QIcon(":/openicon/icons/rename-plot.png"), "Rename a plot", self)
        self.renamePlot.setToolTip("Rename a plot")
        self.renamePlot.triggered.connect(self.onRenamePlot)
        self.toolBar.addAction(self.renamePlot)

        self.setWindowTitle("Instrument Logger ({0})".format(project) )
        if 'MainWindow.State' in self.config:
            self.parent.restoreState(self.config['MainWindow.State'])
        self.initMenu()
        try:
            if 'pyqtgraph-dockareastate' in self.config:
                self.area.restoreState(self.config['pyqtgraph-dockareastate'])
        except Exception as e:
            logger.error("Cannot restore dock state in experiment {0}. Exception occurred: ".format(self.experimentName) + str(e))
                    
    def setupPlots(self):
        self.area = DockArea()
        self.setCentralWidget(self.area)
        self.plotDict = dict()
        # initialize all the plot windows we want
        plotNames = self.config.get( 'PlotNames', ['Scan'] )
        if len(plotNames)<1:
            plotNames.append('Scan')
        for name in plotNames:
            dock = Dock(name)
            widget = CoordinatePlotWidget(self)
            view = widget.graphicsView
            self.area.addDock(dock, "bottom")
            dock.addWidget(widget)
            self.plotDict[name] = {"dock":dock, "widget":widget, "view":view}
        
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

    def onAddPlot(self):
        name, ok = QtGui.QInputDialog.getText(self, 'Plot Name', 'Please enter a plot name: ')
        if ok:
            name = str(name)
            dock = Dock(name)
            widget = CoordinatePlotWidget(self)
            view = widget.graphicsView
            self.area.addDock(dock, "bottom")
            dock.addWidget(widget)
            self.plotDict[name] = {"dock":dock, "widget":widget, "view":view}
            self.plotConfigurationChanged.emit( self.plotDict )
            
    def onRemovePlot(self):
        logger = logging.getLogger(__name__)
        if len(self.plotDict) > 0:
            name, ok = QtGui.QInputDialog.getItem(self, "Select Plot", "Please select which plot to remove: ", self.plotDict.keys(), editable=False)
            if ok:
                name = str(name)
                self.plotDict[name]["dock"].close()
                del self.plotDict[name]
                self.plotConfigurationChanged.emit( self.plotDict )
        else:
            logger.info("There are no plots which can be removed")
                
    def onRenamePlot(self):
        logger = logging.getLogger(__name__)
        if len(self.plotDict) > 0:
            name, ok = QtGui.QInputDialog.getItem(self, "Select Plot", "Please select which plot to rename: ", self.plotDict.keys(), editable=False)
            if ok:
                newName, newOk = QtGui.QInputDialog.getText(self, 'New Plot Name', 'Please enter a new plot name: ')
                if newOk:
                    name = str(name)
                    newName = str(newName)
                    self.plotDict[name]["dock"].label.setText(QtCore.QString(newName))
                    self.plotDict[newName] = self.plotDict[name]
                    del self.plotDict[name]
                    self.plotConfigurationChanged.emit( self.plotDict )
        else:
            logger.info("There are no plots which can be renamed")

    def onProjectSelection(self):
        ProjectSelectionUi.GetProjectSelection()

    def onSettings(self):
        self.settingsDialog.show()
        
    def onSave(self):
        logger = logging.getLogger(__name__)
        logger.info( "Saving config" )
        filename, _ = DataDirectory.DataDirectory().sequencefile("InstrumentLogger-configuration.db")
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

    def initMenu(self):
        self.menuView.clear()
        for dock in self.dockWidgetList:
            self.menuView.addAction(dock.toggleViewAction())

    def saveConfig(self):
        self.config['MainWindow.State'] = self.parent.saveState()
        for tab in self.tabList:
            tab.saveConfig()
        self.config['MainWindow.pos'] = self.pos()
        self.config['MainWindow.size'] = self.size()
        self.config['Settings.loggingLevel'] = self.loggingLevel
        self.config['Settings.consoleMaximumLines'] = self.consoleMaximumLines
        self.config['PlotNames'] = self.plotDict.keys()
        self.config['pyqtgraph-dockareastate'] = self.area.saveState()
        self.loggerUi.saveConfig()
        self.ExternalParametersSelectionUi.saveConfig()

if __name__ == "__main__":
    #The next three lines make it so that the icon in the Windows taskbar matches the icon set in Qt Designer
    import ctypes, sys
    myappid = 'TrappedIons.InstrumentLogging' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    app = QtGui.QApplication(sys.argv)

    logger = logging.getLogger("")

    project, projectDir = ProjectSelectionUi.GetProjectSelection(True)
    
    if project:
        DataDirectory.DefaultProject = project
        
        with configshelve.configshelve( ProjectSelection.guiConfigFile() ) as config:
            with InstrumentLoggingUi(config) as ui:
                ui.setupUi(ui)
                LoggingSetup.qtHandler.textWritten.connect(ui.onMessageWrite)
                ui.show()
                sys.exit(app.exec_())
    else:
        logger.warning( "No project selected. Nothing I can do about that ;)" )
