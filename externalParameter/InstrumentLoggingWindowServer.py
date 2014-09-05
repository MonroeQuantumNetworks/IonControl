'''
Created on Aug 28, 2014

@author: pmaunz
'''
import logging

from PyQt4 import QtCore, QtGui 
import PyQt4.uic

from mylogging import LoggingSetup  #@UnusedImport
from gui import ProjectSelection
from modules import DataDirectory
from persist import configshelve
from uiModules import MagnitudeParameter #@UnusedImport

from trace import Traceui
from trace import pens

from pyqtgraph.dockarea import DockArea, Dock
from uiModules.CoordinatePlotWidget import CoordinatePlotWidget
from externalParameter.InstrumentLogging import LoggingInstruments 
from externalParameter.InstrumentLoggingSelection import InstrumentLoggingSelection 
from externalParameter.InstrumentLoggingHandler import InstrumentLoggingHandler
from fit.FitUi import FitUi
from multiprocessing import Process
from mylogging.ServerLogging import configureServerLogging
from InstrumentLoggerQueryUi import InstrumentLoggerQueryUi

WidgetContainerForm, WidgetContainerBase = PyQt4.uic.loadUiType(r'ui\InstrumentLoggingWindow.ui')

class FinishException(Exception):
    pass

class InstrumentLoggingUi(WidgetContainerBase,WidgetContainerForm):
    plotConfigurationChanged = QtCore.pyqtSignal( object )
    def __init__(self,project,config):
        super(InstrumentLoggingUi, self).__init__()
        self.config = config
        self.project = project
        self.dockWidgetList = list()
        self.plotDict = dict()
        self.instrument = ""
        
    def __enter__(self):
        return self
    
    def __exit__(self, excepttype, value, traceback):
        return False
    
    def setupUi(self, parent):
        super(InstrumentLoggingUi,self).setupUi(parent)
                
        logger = logging.getLogger()        
            
        self.parent = parent
        self.tabList = list()
        self.tabDict = dict()
               
        self.setupPlots()       
        # Traceui
        self.penicons = pens.penicons().penicons()
        self.traceui = Traceui.Traceui(self.penicons,self.config,"Main",self.plotDict[self.plotDict.keys()[0]]["view"])
        self.traceui.setupUi(self.traceui)
        self.setupAsDockWidget(self.traceui, "Traces", QtCore.Qt.LeftDockWidgetArea)

        # new fit widget
        self.fitWidget = FitUi(self.traceui,self.config,"Main")
        self.fitWidget.setupUi(self.fitWidget)
        self.fitWidgetDock = self.setupAsDockWidget(self.fitWidget, "Fit", QtCore.Qt.LeftDockWidgetArea)

        self.instrumentLoggingHandler = InstrumentLoggingHandler(self.traceui, self.plotDict, self.config, 'externalInput')

        self.ExternalParametersSelectionUi = InstrumentLoggingSelection(self.config, classdict=LoggingInstruments,newDataSlot=self.instrumentLoggingHandler.addData, plotNames=self.plotDict.keys(),
                                                                        instrumentLoggingHandler=self.instrumentLoggingHandler )
        self.ExternalParametersSelectionUi.setupUi( self.ExternalParametersSelectionUi )
        self.ExternalParameterSelectionDock = QtGui.QDockWidget("Params Selection")
        self.ExternalParameterSelectionDock.setObjectName("_ExternalParameterSelectionDock")
        self.ExternalParameterSelectionDock.setWidget(self.ExternalParametersSelectionUi)
        self.addDockWidget( QtCore.Qt.RightDockWidgetArea, self.ExternalParameterSelectionDock)
        self.instrumentLoggingHandler.paramTreeChanged.connect( self.ExternalParametersSelectionUi.refreshParamTree)
    
        self.instrumentLoggingQueryUi = InstrumentLoggerQueryUi(self.config, self.traceui, self.plotDict )
        self.instrumentLoggingQueryUi.setupUi( self.instrumentLoggingQueryUi )
        self.instrumentLoggingQueryUiDock = self.setupAsDockWidget(self.instrumentLoggingQueryUi, "Query", QtCore.Qt.LeftDockWidgetArea)
    
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

        self.setWindowTitle("Instrument Logger ({0})".format(self.project) )
        if 'MainWindow.State' in self.config:
            self.parent.restoreState(self.config['MainWindow.State'])
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

    def onSave(self):
        logger = logging.getLogger(__name__)
        logger.info( "Saving config" )
        filename, _ = DataDirectory.DataDirectory().sequencefile("InstrumentLogger-configuration.db")
        self.saveConfig()
        self.config.saveConfig(filename)
    
    def onClose(self):
        self.parent.close()
        
    def closeEvent(self,e):
        logger = logging.getLogger(__name__)
        logger.info( "Close Event" )
        logger = logging.getLogger("")
        logger.debug( "Saving Configuration" )
        self.saveConfig()

    def saveConfig(self):
        self.config['MainWindow.State'] = self.parent.saveState()
        for tab in self.tabList:
            tab.saveConfig()
        self.config['MainWindow.pos'] = self.pos()
        self.config['MainWindow.size'] = self.size()
        self.config['PlotNames'] = self.plotDict.keys()
        self.config['pyqtgraph-dockareastate'] = self.area.saveState()
        self.ExternalParametersSelectionUi.saveConfig()
        self.instrumentLoggingHandler.saveConfig()
        self.instrumentLoggingQueryUi.saveConfig()

class CommandReader(QtCore.QThread):
    quitProcess = QtCore.pyqtSignal()
    saveConfig = QtCore.pyqtSignal()
    def __init__(self, commandPipe, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.running = True
        self.commandPipe = commandPipe
        
    def run(self):
        logger = logging.getLogger(__name__)
        logger.debug("CommandReader Thread running")
        while (self.running):
            if self.commandPipe.poll(0.1):
                try:
                    commandstring, argument = self.commandPipe.recv()
                    command = getattr(self, commandstring)
                    logger.debug( "InstrumentLoggingServer {0}".format(commandstring) )
                    self.commandPipe.send(command(*argument))
                except Exception as e:
                    self.commandPipe.send(e)

    def finish(self):
        logging.getLogger(__name__).info("Shutdown Logger Process")
        self.saveConfig.emit()
        self.quitProcess.emit()
        self.running = False

class InstrumentLoggingProcess(Process):
    def __init__(self, project=None, dataQueue=None, commandPipe=None, loggingQueue=None, sharedMemoryArray=None):
        self.project = project
        super(InstrumentLoggingProcess,self).__init__()
        self.dataQueue = dataQueue
        self.commandPipe = commandPipe
        self.running = True
        self.openModule = None
        self.xem = None
        self.loggingQueue = loggingQueue
        self.sharedMemoryArray = sharedMemoryArray
        
    def run(self):
        ProjectSelection.setProject(self.project)
        ProjectSelection.setDefaultProject(self.project)
        configureServerLogging(self.loggingQueue)
        
        self.commandReader = CommandReader(self.commandPipe)

        #The next three lines make it so that the icon in the Windows taskbar matches the icon set in Qt Designer
        import ctypes, sys
        myappid = 'TrappedIons.FPGAControlProgram' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
        app = QtGui.QApplication(["LoggingWindow"])    
        logger = logging.getLogger("")
        self.commandReader.quitProcess.connect( app.quit )
        self.commandReader.start()
               
               
        with configshelve.configshelve( ProjectSelection.guiConfigFile("LoggingWindow") ) as config:
            with InstrumentLoggingUi(self.project,config) as ui:
                ui.setupUi(ui)
                ui.show()
                self.commandReader.saveConfig.connect( ui.saveConfig )
                sys.exit(app.exec_())
        
        self.dataQueue.put(FinishException())
        logger.info( "Pulser Hardware Server Process finished." )
        self.dataQueue.close()
        self.loggingQueue.put(None)
        self.loggingQueue.close()
        self.commandReader.quit()
        
    

