'''
Created on Apr 6, 2014

@author: pmaunz
'''

from PyQt4 import uic, QtCore, QtGui
from modules.statemachine import Statemachine
from TodoListTableModel import TodoListTableModel
from uiModules.KeyboardFilter import KeyListFilter
from modules.Utility import unique

Form, Base = uic.loadUiType(r'ui\TodoList.ui')


class TodoListEntry:
    def __init__(self, scan, measurement):
        self.scan = scan
        self.measurement = measurement

class Settings:
    def __init__(self):
        self.todoList = list()

class TodoList(Form, Base):
    def __init__(self,scanModules,config,currentScan,parent=None):
        Base.__init__(self,parent)    
        Form.__init__(self)
        self.config = config
        self.settings = config.get('TodolistSettings', Settings())
        self.scanModules = scanModules
        self.scanModuleMeasurements = dict()
        self.currentMeasurementsDisplayedForScan = None
        self.currentScan = currentScan

    def setupStatemachine(self):
        self.statemachine = Statemachine()        
        self.statemachine.addState( 'Idle', self.enterIdle  )
        self.statemachine.addState( 'MeasurementRunning', self.enterMeasurementRunning )
        self.statemachine.addState( 'Paused', self.enterPaused )
        self.statemachine.initialize( 'Idle' )
        self.statemachine.addTransition('startCommand', 'Idle', 'MeasurementRunning', self.checkReadyToRun )
        self.statemachine.addTransitionList('stopCommand', ['Idle','MeasurementRunning', 'Paused'], 'Idle')
        self.statemachine.addTransition('measurementFinished','MeasurementRunning','MeasurementRunning', self.checkReadyToRun )
                
    def setupUi(self):
        super(TodoList,self).setupUi(self)
        self.populateMeasurements()
        self.scanSelectionBox.addItems( self.scanModuleMeasurements.keys() )
        self.scanSelectionBox.currentIndexChanged[QtCore.QString].connect( self.updateMeasurementSelectionBox )
        self.updateMeasurementSelectionBox( self.scanSelectionBox.currentText() )
        self.tableModel = TodoListTableModel( self.settings.todoList )
        self.tableView.setModel( self.tableModel )
        self.addMeasurementButton.clicked.connect( self.onAddMeasurement )
        self.removeMeasurementButton.clicked.connect( self.onDropMeasurement )
        self.runButton.clicked.connect( self.onRun )
        self.stopButton.clicked.connect( self.onStop )
        self.repeatButton.clicked.connect( self.onRepeatChanged )
        self.filter = KeyListFilter( [QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown] )
        self.filter.keyPressed.connect( self.onReorder )
        self.tableView.installEventFilter(self.filter)
        self.setupStatemachine()
        
    def updateMeasurementSelectionBox(self, newscan ):
        newscan = str(newscan)
        if self.currentMeasurementsDisplayedForScan != newscan:
            self.currentMeasurementsDisplayedForScan = newscan
            self.measurementSelectionBox.clear()
            self.measurementSelectionBox.addItems( self.scanModuleMeasurements[newscan] )
        
    def populateMeasurements(self):
        self.scanModuleMeasurements = dict()
        for name, widget in self.scanModules.iteritems():
            if hasattr(widget, 'scanControlWidget' ):
                self.scanModuleMeasurements[name] = sorted(widget.scanControlWidget.settingsDict.keys())

    def onReorder(self, key):
        if key in [QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown]:
            indexes = self.tableView.selectedIndexes()
            up = key==QtCore.Qt.Key_PageUp
            delta = -1 if up else 1
            rows = sorted(unique([ i.row() for i in indexes ]),reverse=not up)
            if self.tableModel.moveRow( rows, up=up ):
                selectionModel = self.tableView.selectionModel()
                selectionModel.clearSelection()
                for index in indexes:
                    selectionModel.select( self.tableModel.createIndex(index.row()+delta,index.column()), QtGui.QItemSelectionModel.Select )
#            self.selectionChanged.emit( self.enabledParametersObjects )

    def onAddMeasurement(self):
        if self.currentMeasurementsDisplayedForScan and self.measurementSelectionBox.currentText():
            self.tableModel.addMeasurement( TodoListEntry(self.currentMeasurementsDisplayedForScan, str(self.measurementSelectionBox.currentText())))
    
    def onDropMeasurement(self):
        pass

    def onRun(self):
        pass
    
    def checkReadyToRun(self):
        pass
    
    def onStartMeasurement(self):
        pass
        # make sure the current tab is idle
        
        # switch to the scan for the first line
        
        # load the correct measurement
        
        # start
    
    def onStop(self):
        pass
    
    def onStateChanged(self, newstate ):
        pass
    
    def onRepeatChanged(self):
        pass

    def enterIdle(self):
        self.statusLabel.setText('Idle')
        
    def enterMeasurementRunning(self):
        self.statusLabel.setText('Measurement Running')
        
    def enterPaused(self):
        self.statusLabel.setText('Paused')
        
    def saveConfig(self):
        self.config['TodolistSettings'] = self.settings
       
        
        