'''
Created on Nov 21, 2014

@author: pmaunz
'''

from PyQt4 import QtCore, QtGui
import PyQt4.uic
from persist.MeasurementLog import MeasurementContainer
from gui.MeasurementLogUi.MeasurementTableModel import MeasurementTableModel
from gui.MeasurementLogUi.ResultTableModel import ResultTableModel 
from gui.MeasurementLogUi.StudyTableModel import StudyTableModel
from gui.MeasurementLogUi.ParameterTableModel import ParameterTableModel
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from datetime import datetime, time, timedelta
from _functools import partial

Form, Base = PyQt4.uic.loadUiType(r'ui\MeasurementLog.ui')



class Settings:
    def __init__(self):
        self.timespan = 0
        self.fromDateTimeEdit = datetime.combine(datetime.now().date(), time())
        self.toDateTimeEdit = datetime.combine((datetime.now()+timedelta(days=1)).date(), time())
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault( 'timespan', 0)
        self.__dict__.setdefault( 'fromDateTimeEdit', datetime.combine(datetime.now().date(), time()))
        self.__dict__.setdefault( 'toDateTimeEdit', datetime.combine((datetime.now()+timedelta(days=1)).date(), time()))

class MeasurementLogUi(Form, Base ):
    timespans = ['Today','Three days','One week','One month', 'Three month', 'One year', 'All', 'Custom']
    mySplitters = ['splitterHorizontal', "splitterVertical", "splitterHorizontalParam" ]
    def __init__(self,config,parent=None):
        Form.__init__(self)
        Base.__init__(self,parent)
        self.config = config
        self.configname = 'MeasurementLog'
        self.settings = self.config.get(self.configname,Settings())
        self.container = MeasurementContainer("postgresql://python:yb171@localhost/ioncontrol")
        self.container.open()
        self.fromToTimeLookup = [ lambda now: (datetime.combine(now.date(), time()), datetime.combine(now + timedelta(days=1), time())),              # today
                           lambda now: (datetime.combine(now - timedelta(days=3), time()),  datetime.combine(now + timedelta(days=1), time())),  # three days ago
                           lambda now: (datetime.combine(now - timedelta(days=7), time()),  datetime.combine(now + timedelta(days=1), time())),  # one week
                           lambda now: (datetime.combine(now - timedelta(days=30), time()), datetime.combine(now + timedelta(days=1), time())),   # 30 days
                           lambda now: (datetime.combine(now - timedelta(days=90), time()), datetime.combine(now + timedelta(days=1), time())),   # 90 days
                           lambda now: (datetime.combine(now - timedelta(years=1), time()), datetime.combine(now + timedelta(days=1), time())),   # 1 year
                           lambda now: (datetime(2014,11,1,0,0),  datetime.combine(now + timedelta(days=1), time())),  # all
                           lambda now: (self.settings.fromDateTimeEdit, self.settings.toDateTimeEdit)
                           ]

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        # measurement Table
        self.measurementModel = MeasurementTableModel(self.container.measurements, self.container)
        self.measurementTableView.setModel( self.measurementModel )
        # result Table
        self.resultModel = ResultTableModel( list(), self.container )
        self.resultTableView.setModel( self.resultModel )
        # study table
        self.studyModel = StudyTableModel( list(), self.container )
        self.studyTableView.setModel( self.studyModel )
        # parameter table
        self.parameterModel = ParameterTableModel( list(), self.container )
        self.parameterTableView.setModel( self.parameterModel )
        magnitudeDelegate = MagnitudeSpinBoxDelegate()
        self.parameterTableView.setItemDelegateForColumn( 2, magnitudeDelegate )
        # Context Menu for ResultsTable
        self.resultTableView.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.addToMeasurementAction = QtGui.QAction( "add as column to measurement" , self)
        #self.addToMeasurementAction.triggered.connect( self.model.restoreCustomOrder  )
        self.resultTableView.addAction( self.addToMeasurementAction )
        # Context Menu for Measurements Table
        self.measurementTableView.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.removeColumnAction = QtGui.QAction( "remove selected column" , self)
        #self.removeColumnAction.triggered.connect( self.model.restoreCustomOrder  )
        self.measurementTableView.addAction( self.removeColumnAction )
        # Context Menu for Parameters Table
        self.parameterTableView.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.addManualParameterAction = QtGui.QAction( "add manual parameter" , self)
        self.addManualParameterAction.triggered.connect( self.parameterModel.addManualParameter  )
        self.parameterTableView.addAction( self.addManualParameterAction )
        # restore splitter positions
        for splitter in self.mySplitters:
            name = self.configname+"."+splitter
            if name in self.config:
                getattr(self, splitter).restoreState( self.config[name] )
        self.timespanComboBox.addItems( self.timespans )
        self.timespanComboBox.setCurrentIndex( self.settings.timespan )
        self.timespanComboBox.currentIndexChanged[int].connect( self.onChangeTimespan )
        self.container.beginInsertMeasurement.subscribe( self.measurementModel.beginInsertRows )
        self.container.endInsertMeasurement.subscribe( self.measurementModel.endInsertRows )  
        self.container.measurementsUpdated.subscribe( self.measurementModel.setMeasurements  )
        self.measurementTableView.selectionModel().currentChanged.connect( self.onActiveInstrumentChanged )
        self.refreshButton.clicked.connect( self.onFilterRefresh )
        # DateTimeEdit
        self.fromDateTimeEdit.setDateTime( self.settings.fromDateTimeEdit )
        self.toDateTimeEdit.setDateTime( self.settings.toDateTimeEdit )
        self.fromDateTimeEdit.dateTimeChanged.connect( partial( self.setDateTimeEdit, 'fromDateTimeEdit') )
        self.toDateTimeEdit.dateTimeChanged.connect( partial( self.setDateTimeEdit, 'toDateTimeEdit') )
        self.onFilterRefresh()

    def setDateTimeEdit(self, attr, value):
        setattr( self.settings, attr, datetime(value) )

    def onChangeTimespan(self, index):
        self.settings.timespan = index
        isCustom = self.timespans[index] == 'Custom'
        self.toDateTimeEdit.setEnabled( isCustom )
        self.fromDateTimeEdit.setEnabled( isCustom )
        self.onFilterRefresh()

    def saveConfig(self):
        for splitter in self.mySplitters:
            self.config[self.configname+"."+splitter] = getattr(self, splitter).saveState()
        self.config[self.configname] = self.settings
        
    def onActiveInstrumentChanged(self, modelIndex, modelIndex2 ):
        measurement = self.container.measurements[modelIndex.row()]
        self.parameterModel.setParameters( measurement.parameters )
        self.resultModel.setResults( measurement.results )
        
    def onFilterRefresh(self):
        self.container.query( *self.fromToTimeLookup[self.settings.timespan](datetime.now()) )
        