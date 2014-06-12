'''
Created on Apr 6, 2014

@author: pmaunz
'''

from PyQt4 import uic, QtCore, QtGui
from modules.statemachine import Statemachine
from TodoListTableModel import TodoListTableModel
from uiModules.KeyboardFilter import KeyListFilter
from modules.Utility import unique
from functools import partial
from modules.ScanDefinition import ScanSegmentDefinition

Form, Base = uic.loadUiType(r'ui\TodoList.ui')


class TodoListEntry:
    def __init__(self, scan=None, measurement=None):
        self.parent = None
        self.children = list()
        self.scan = scan
        self.measurement = measurement
        self.scanParameter = None
        self.scanSegment = ScanSegmentDefinition()

class Settings:
    def __init__(self):
        self.todoList = list()
        self.currentIndex = 0
        self.repeat = False
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault( 'currentIndex', 0)
        self.__dict__.setdefault( 'repeat', False)

class TodoList(Form, Base):
    def __init__(self,scanModules,config,currentScan,setCurrentScan,parent=None):
        Base.__init__(self,parent)    
        Form.__init__(self)
        self.config = config
        self.settings = config.get('TodolistSettings', Settings())
        self.scanModules = scanModules
        self.scanModuleMeasurements = dict()
        self.currentMeasurementsDisplayedForScan = None
        self.currentScan = currentScan
        self.setCurrentScan = setCurrentScan

    def setupStatemachine(self):
        self.statemachine = Statemachine()        
        self.statemachine.addState( 'Idle', self.enterIdle  )
        self.statemachine.addState( 'MeasurementRunning', self.enterMeasurementRunning, self.exitMeasurementRunning )
        self.statemachine.addState( 'Check' )
        self.statemachine.addState( 'Paused', self.enterPaused )
        self.statemachine.initialize( 'Idle' )
        self.statemachine.addTransition('startCommand', 'Idle', 'MeasurementRunning', self.checkReadyToRun )
        self.statemachine.addTransitionList('stopCommand', ['Idle','MeasurementRunning', 'Paused'], 'Idle')
        self.statemachine.addTransition('measurementFinished','MeasurementRunning','Check', self.checkReadyToRun )
        self.statemachine.addTransition('docheck', 'Check', 'MeasurementRunning', lambda state: self.settings.currentIndex>0 or self.settings.repeat)
        self.statemachine.addTransition('docheck', 'Check', 'Idle', lambda state: self.settings.currentIndex==0 and not self.settings.repeat)
                
    def setupUi(self):
        super(TodoList,self).setupUi(self)
        self.setupStatemachine()
        self.populateMeasurements()
        self.scanSelectionBox.addItems( self.scanModuleMeasurements.keys() )
        self.scanSelectionBox.currentIndexChanged[QtCore.QString].connect( self.updateMeasurementSelectionBox )
        self.updateMeasurementSelectionBox( self.scanSelectionBox.currentText() )
        self.tableModel = TodoListTableModel( self.settings.todoList )
        self.tableView.setModel( self.tableModel )
        self.addMeasurementButton.clicked.connect( self.onAddMeasurement )
        self.removeMeasurementButton.clicked.connect( self.onDropMeasurement )
        self.runButton.clicked.connect( partial( self.statemachine.processEvent, 'startCommand' ) )
        self.stopButton.clicked.connect( partial( self.statemachine.processEvent, 'stopCommand' ) )
        self.repeatButton.clicked.connect( self.onRepeatChanged )
        self.filter = KeyListFilter( [QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown] )
        self.filter.keyPressed.connect( self.onReorder )
        self.tableView.installEventFilter(self.filter)
        self.tableModel.setActiveRow(self.settings.currentIndex, False)
        self.tableView.doubleClicked.connect( self.setCurrentIndex )
        
    def setCurrentIndex(self, index):
        self.settings.currentIndex = index.row()
        self.tableModel.setActiveRow(self.settings.currentIndex, self.statemachine.currentState=='MeasurementRunning')        
        
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
                self.populateMeasurementsItem( name, widget.scanControlWidget.settingsDict )
                
    def populateMeasurementsItem(self, name, settingsDict ):
        self.scanModuleMeasurements[name] = sorted(settingsDict.keys())
        if name == self.currentMeasurementsDisplayedForScan:
            self.measurementSelectionBox.clear()
            self.measurementSelectionBox.addItems( self.scanModuleMeasurements[name] )            

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
        for index in sorted(unique([ i.row() for i in self.tableView.selectedIndexes() ]),reverse=True):
            self.tableModel.dropMeasurement(index)
        numEntries = self.tableModel.rowCount()
        if self.settings.currentIndex >= numEntries:
            self.settings.currentIndex = 0

    def checkReadyToRun(self, state, _=True ):
        _, current = self.currentScan()
        return current.state()==0
    
    
    def onStateChanged(self, newstate ):
        if newstate=='idle':
            self.statemachine.processEvent('measurementFinished')
            self.statemachine.processEvent('docheck')
    
    def onRepeatChanged(self, enabled):
        self.settings.repeat = enabled

    def enterIdle(self):
        self.statusLabel.setText('Idle')
        
    def enterMeasurementRunning(self):
        self.statusLabel.setText('Measurement Running')
        currentname, currentwidget = self.currentScan()
        entry = self.settings.todoList[ self.settings.currentIndex ]
        # switch to the scan for the first line
        if entry.scan!=currentname:
            self.setCurrentScan(entry.scan)
        # load the correct measurement
        currentwidget.scanControlWidget.loadSetting( entry.measurement )        
        # start
        currentwidget.onStart()
        self.tableModel.setActiveRow(self.settings.currentIndex, True)
        
    def exitMeasurementRunning(self):
        self.settings.currentIndex = (self.settings.currentIndex+1) % len(self.settings.todoList)
        self.tableModel.setActiveRow(self.settings.currentIndex, False)
        
    def enterPaused(self):
        self.statusLabel.setText('Paused')
        
    def saveConfig(self):
        self.config['TodolistSettings'] = self.settings
       
        
        