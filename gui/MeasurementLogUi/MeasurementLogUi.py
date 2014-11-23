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

Form, Base = PyQt4.uic.loadUiType(r'ui\MeasurementLog.ui')

class Settings:
    def __init__(self):
        self.timespan = 0
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault( 'timespan', 0)

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

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        # measurement Table
        self.measurementModel = MeasurementTableModel(self.container.measurements)
        self.measurementTableView.setModel( self.measurementModel )
        # result Table
        self.resultModel = ResultTableModel( list() )
        self.resultTableView.setModel( self.resultModel )
        # study table
        self.studyModel = StudyTableModel( list() )
        self.studyTableView.setModel( self.studyModel )
        # parameter table
        self.parameterModel = ParameterTableModel( list() )
        self.parameterTableView.setModel( self.parameterModel )
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
        self.measurementTableView.selectionModel().currentChanged.connect( self.onActiveInstrumentChanged )

    def onChangeTimespan(self, index):
        isCustom = self.timespans[index] == 'Custom'
        self.toDateTimeEdit.setEnabled( isCustom )
        self.fromDateTimeEdit.setEnabled( isCustom )

    def saveConfig(self):
        for splitter in self.mySplitters:
            self.config[self.configname+"."+splitter] = getattr(self, splitter).saveState()
        self.config[self.configname] = self.settings
        
    def onActiveInstrumentChanged(self, modelIndex, modelIndex2 ):
        measurement = self.container.measurements[modelIndex.row()]
        self.parameterModel.setParameters( measurement.parameters )
        self.resultModel.setResults( measurement.results )
        