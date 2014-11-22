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

Form, Base = PyQt4.uic.loadUiType(r'ui\MeasurementLog.ui')

class Settings:
    def __init__(self):
        pass

class MeasurementLogUi(Form, Base ):
    def __init__(self,config,parent=None):
        Form.__init__(self)
        Base.__init__(self,parent)
        self.config = config
        self.configname = 'MeasurementLog'
        self.settings = self.config.get(self.configname,Settings())
        self.container = MeasurementContainer("postgresql://python:yb171@localhost/ioncontrol")
        

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        self.measurementModel = MeasurementTableModel(self.container.measurements)
        self.measurementTableView.setModel( self.measurementModel )
        self.resultModel = ResultTableModel( list() )
        self.resultTableView.setModel( self.resultModel )
        self.studyModel = StudyTableModel( list() )
        self.studyTableView.setModel( self.studyModel )
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
        if self.configname+".splitterHorizontal" in self.config:
            self.splitterHorizontal.restoreState( self.config[self.configname+".splitterHorizontal"] )
        if self.configname+".splitterVertical" in self.config:
            self.splitterVertical.restoreState( self.config[self.configname+".splitterVertical"] )

    def saveConfig(self):
        self.config[self.configname+".splitterHorizontal"] = self.splitterHorizontal.saveState()
        self.config[self.configname+".splitterVertical"] = self.splitterVertical.saveState()

