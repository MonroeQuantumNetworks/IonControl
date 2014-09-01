'''
Created on Aug 31, 2014

@author: pmaunz
'''

import PyQt4.uic
from PyQt4 import QtCore
from functools import partial
from persist.ValueHistory import ValueHistoryStore
from modules.PyqtUtility import updateComboBoxItems
from datetime import datetime
from trace.Trace import Trace
from trace.PlottedTrace import PlottedTrace
import numpy
from trace import pens

Form, Base = PyQt4.uic.loadUiType(r'ui\InstrumentLoggerQueryUi.ui')

class Parameters:
    def __init__(self):
        self.parameter = None
        self.fromTime = datetime(2014,8,30)
        self.toTime = datetime.now()
        self.timeOrigin = datetime(2014,8,30)
        self.plotName = None 
        self.plotUnit = ""
        self.steps = False
        

class InstrumentLoggerQueryUi(Form,Base):
    def __init__(self, config, traceui, plotDict, parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        self.config = config
        self.parameters = self.config.get("InstrumentLoggerQueryUi",Parameters())
        self.traceui = traceui
        self.plotDict = plotDict
        self.connection = ValueHistoryStore("postgresql://python:yb171@localhost/ioncontrol")
        self.connection.open_session()
    
    def setupUi(self,MainWindow):
        Form.setupUi(self,MainWindow)
        self.comboBoxParam.currentIndexChanged[QtCore.QString].connect( partial(self.onValueChangedString, 'parameter') )
        self.comboBoxPlotName.currentIndexChanged[QtCore.QString].connect( partial(self.onValueChangedString, 'plotName') )
        self.onRefresh()
        if self.parameters.parameter is not None:
            self.comboBoxParam.setCurrentIndex( self.comboBoxParam.findText(self.parameters.parameter ))
        if self.parameters.fromTime is not None:
            self.dateTimeEditFrom.setDateTime( self.parameters.fromTime )
        self.dateTimeEditFrom.dateTimeChanged.connect( partial(self.onValueChangedDateTime, 'fromTime')  )
        if self.parameters.toTime is not None:
            self.dateTimeEditTo.setDateTime( self.parameters.toTime )
        self.dateTimeEditTo.dateTimeChanged.connect( partial(self.onValueChangedDateTime, 'toTime')  )
        if self.parameters.timeOrigin is not None:
            self.dateTimeEditOrigin.setDateTime( self.parameters.timeOrigin )
        self.dateTimeEditOrigin.dateTimeChanged.connect( partial(self.onValueChangedDateTime, 'timeOrigin')  )
        if self.parameters.plotName is not None:
            self.comboBoxPlotName.setCurrentIndex( self.comboBoxPlotName.findText(self.parameters.plotName ))
        self.lineEditPlotUnit.setText( self.parameters.plotUnit )
        self.lineEditPlotUnit.textChanged.connect( partial(self.onValueChangedString, 'plotUnit') )
        self.pushButtonCreatePlot.clicked.connect( self.onCreatePlot )
        self.toolButtonRefresh.clicked.connect( self.onRefresh )
        self.checkBoxSteps.setChecked( self.parameters.steps )
        self.checkBoxSteps.stateChanged.connect( self.onStateChanged )
        
    def onStateChanged(self, state):
        self.parameters.steps = state==QtCore.Qt.Checked
        
    def onValueChangedString(self, param, value):
        setattr( self.parameters, param, str(value) )
        
    def onValueChangedDateTime(self, param, value):
        setattr( self.parameters, param, value.toPyDateTime() )

    def saveConfig(self):
        self.config["InstrumentLoggerQueryUi"] = self.parameters
        
    def onRefresh(self):
        self.parameterNames = self.connection.refreshSourceDict().keys()
        updateComboBoxItems( self.comboBoxParam, self.parameterNames )
        updateComboBoxItems( self.comboBoxPlotName, self.plotDict.keys() )        
        
    def onCreatePlot(self):
        result = self.connection.getHistory( self.parameters.parameter, self.parameters.fromTime , self.parameters.toTime )
        time = [(e.upd_date-self.parameters.timeOrigin) for e in result]
        value = [e.value for e in result]
        bottom = [e.bottom if e.bottom is not None else e.value for e in result]
        top = [e.top if e.top is not None else e.value for e in result]
        trace = Trace(record_timestamps=False)
        trace.name = self.parameters.parameter
        trace.y = numpy.array( value )
        if self.parameters.plotName is None:
            self.parameters.plotName = str(self.comboBoxPlotName.currentText())
        if self.parameters.steps:
            trace.x = numpy.array( [t.days*86400 + t.seconds + t.microseconds*1e-6 for t in time+[time[-1]]] )
            plottedTrace = PlottedTrace( trace, self.plotDict[self.parameters.plotName]["view"], xAxisUnit = "s", xAxisLabel = "time", plotType=PlottedTrace.Types.steps, fill=False) #@UndefinedVariable
        else:
            trace.x = numpy.array( [t.days*86400 + t.seconds + t.microseconds*1e-6 for t in time] )
            trace.top = numpy.array( top )
            trace.bottom = numpy.array( bottom )
            plottedTrace = PlottedTrace( trace, self.plotDict[self.parameters.plotName]["view"], xAxisUnit = "s", xAxisLabel = "time") 
        self.traceui.addTrace( plottedTrace, pen=-1)
        self.traceui.resizeColumnsToContents()
