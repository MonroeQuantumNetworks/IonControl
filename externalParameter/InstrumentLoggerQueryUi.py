'''
Created on Aug 31, 2014

@author: pmaunz
'''

import PyQt4.uic
from PyQt4 import QtCore
from functools import partial
from persist.ValueHistory import ValueHistoryStore
from modules.PyqtUtility import updateComboBoxItems
from datetime import datetime, timedelta
from trace.Trace import Trace
from trace.PlottedTrace import PlottedTrace
import numpy
from collections import defaultdict
import logging
import pytz
from modules import WeakMethod 
import weakref

Form, Base = PyQt4.uic.loadUiType(r'ui\InstrumentLoggerQueryUi.ui')

class Parameters:
    def __init__(self):
        self.space = None
        self.parameter = None
        self.fromTime = datetime(2014,8,30)
        self.toTime = datetime.now()
        self.plotName = None 
        self.plotUnit = ""
        self.steps = False
        self.spaceParamCache = dict()
        self.updatePrevious = True
        
    def __setstate__(self, s):
        self.__dict__ = s
        self.__dict__.setdefault('updatePrevious', True)

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
        self.utcOffset = (datetime.utcnow()-datetime.now()).total_seconds()
        self.cache = dict()
    
    def setupUi(self,MainWindow):
        Form.setupUi(self,MainWindow)
        self.comboBoxSpace.currentIndexChanged[QtCore.QString].connect( self.onSpaceChanged  )
        self.comboBoxParam.currentIndexChanged[QtCore.QString].connect( partial(self.onValueChangedString, 'parameter') )      
        self.comboBoxPlotName.currentIndexChanged[QtCore.QString].connect( partial(self.onValueChangedString, 'plotName') )
        self.onRefresh()
        if self.parameters.space is not None:
            self.comboBoxSpace.setCurrentIndex( self.comboBoxSpace.findText(self.parameters.space ))
        if self.parameters.parameter is not None:
            self.comboBoxParam.setCurrentIndex( self.comboBoxParam.findText(self.parameters.parameter ))
        if self.parameters.fromTime is not None:
            self.dateTimeEditFrom.setDateTime( self.parameters.fromTime )
        self.dateTimeEditFrom.dateTimeChanged.connect( partial(self.onValueChangedDateTime, 'fromTime')  )
        if self.parameters.toTime is not None:
            self.dateTimeEditTo.setDateTime( self.parameters.toTime )
        self.dateTimeEditTo.dateTimeChanged.connect( partial(self.onValueChangedDateTime, 'toTime')  )
        if self.parameters.plotName is not None:
            self.comboBoxPlotName.setCurrentIndex( self.comboBoxPlotName.findText(self.parameters.plotName ))
        self.lineEditPlotUnit.setText( self.parameters.plotUnit )
        self.lineEditPlotUnit.textChanged.connect( partial(self.onValueChangedString, 'plotUnit') )
        self.pushButtonCreatePlot.clicked.connect( self.onCreatePlot )
        self.pushButtonUpdateAll.clicked.connect( self.onUpdateAll )
        self.pushButtonLast15Min.clicked.connect( partial(self.onLastTime, s=900) )
        self.pushButtonLastHour.clicked.connect( partial(self.onLastTime, s=3600) )
        self.pushButtonLastDay.clicked.connect( partial(self.onLastTime, d=1) )
        self.pushButtonLastWeek.clicked.connect( partial(self.onLastTime, d=7) )
        self.pushButtonLastCustom.clicked.connect( partial(self.onLastTime, custom=True) )
        self.toolButtonRefresh.clicked.connect( self.onRefresh )
        self.checkBoxSteps.setChecked( self.parameters.steps )
        self.checkBoxSteps.stateChanged.connect( partial(self.onStateChanged, 'steps') )
        self.checkBoxUpdatePrevious.setChecked( self.parameters.updatePrevious )
        self.checkBoxUpdatePrevious.stateChanged.connect( partial( self.onStateChanged, 'updatePrevious') )
        self.onSpaceChanged(self.parameters.space)

    def onLastTime(self, d=0, s=0, custom=False):
        now = datetime.now()
        if custom:
            d=self.spinBoxCustomDays.value()
            s=self.spinBoxCustomMinutes.value()*60.0 + self.spinBoxCustomHours.value()*3600.0
        shift = timedelta(days=d, seconds=s)
        self.dateTimeEditFrom.setDateTime( now-shift )
        self.dateTimeEditTo.setDateTime( now )
        
    def onStateChanged(self, attr, state):
        setattr( self.parameters, attr, state==QtCore.Qt.Checked )
        
    def onValueChangedString(self, param, value):
        setattr( self.parameters, param, str(value) )
        
    def onValueChangedDateTime(self, param, value):
        setattr( self.parameters, param, value.toPyDateTime() )

    def saveConfig(self):
        self.config["InstrumentLoggerQueryUi"] = self.parameters
        
    def onRefresh(self):
        self.parameterNames = defaultdict( list )
        for (space,source) in self.connection.refreshSourceDict().keys():
            self.parameterNames[space].append(source)
        updateComboBoxItems( self.comboBoxSpace, sorted(self.parameterNames.keys()) )
        updateComboBoxItems( self.comboBoxParam, sorted(self.parameterNames[self.parameters.space]) )
        updateComboBoxItems( self.comboBoxPlotName, sorted(self.plotDict.keys()) )        
        
    def onSpaceChanged(self, newSpace):
        newSpace = str(newSpace)
        if self.parameters.space is not None and self.parameters.parameter is not None:
            self.parameters.spaceParamCache[self.parameters.space] = self.parameters.parameter
        self.parameters.space = newSpace
        self.parameters.parameter = self.parameters.spaceParamCache.get( self.parameters.space, self.parameterNames[self.parameters.space][0] if len(self.parameterNames[self.parameters.space])>0 else None )
        updateComboBoxItems( self.comboBoxParam, sorted(self.parameterNames[self.parameters.space]) )
        if self.parameters.parameter is not None:
            self.comboBoxParam.setCurrentIndex( self.comboBoxParam.findText(self.parameters.parameter ))
        
       
    def onCreatePlot(self): 
        self.doCreatePlot(self.parameters.space, self.parameters.parameter, self.parameters.fromTime , self.parameters.toTime, self.parameters.plotName, self.parameters.steps)
        self.cacheGarbageCollect()
        
    def cacheGarbageCollect(self):
        for key, (ref,_) in self.cache.items():
            if ref() is None:
                self.cache.pop(key)
        
    def doCreatePlot(self, space, parameter, fromTime, toTime, plotName, steps, forceUpdate=False ):
        ref, _ = self.cache.get( ( space, parameter ), (lambda: None, None)) 
        plottedTrace = ref() if (self.parameters.updatePrevious or forceUpdate) else None # get plottedtrace from the weakref if exists           
        result = self.connection.getHistory( space, parameter, fromTime , toTime )
        if not result:
            logging.getLogger(__name__).error("Database query returned empty set")
        elif len(result)>0:
            epoch = datetime(1970, 1, 1) - timedelta(seconds=self.utcOffset) if result[0].upd_date.tzinfo is None else datetime(1970, 1, 1).replace(tzinfo=pytz.utc)
            time = [(e.upd_date - epoch).total_seconds() for e in result]
            value = [e.value for e in result]
            bottom = [e.value - e.bottom if e.bottom is not None else e.value for e in result]
            top = [e.top -e.value if e.top is not None else e.value for e in result]
            if plottedTrace is None:  # make a new plotted trace
                trace = Trace(record_timestamps=False)
                trace.name = parameter + " Query"
                trace.y = numpy.array( value )
                if plotName is None:
                    plotName = str(self.comboBoxPlotName.currentText()) 
                if steps:
                    trace.x = numpy.array( time+[time[-1]] )
                    plottedTrace = PlottedTrace( trace, self.plotDict[plotName]["view"], xAxisLabel = "local time", plotType=PlottedTrace.Types.steps, fill=False, windowName=plotName) #@UndefinedVariable
                else:
                    trace.x = numpy.array( time )
                    trace.top = numpy.array( top )
                    trace.bottom = numpy.array( bottom )
                    plottedTrace = PlottedTrace( trace, self.plotDict[plotName]["view"], xAxisLabel = "local time", windowName=plotName) 
                    plottedTrace.trace.filenameCallback = partial( WeakMethod.ref(plottedTrace.traceFilename), "" )
                self.traceui.addTrace( plottedTrace, pen=-1)
                self.traceui.resizeColumnsToContents()
                self.cache[(space, parameter)] = ( weakref.ref(plottedTrace), (space, parameter, fromTime, toTime, plotName, steps) )
            else:  # update the existing plotted trace
                trace = plottedTrace.trace
                trace.y = numpy.array( value )
                if steps:
                    trace.x = numpy.array( time+[time[-1]] )
                else:
                    trace.x = numpy.array( time )
                    trace.top = numpy.array( top )
                    trace.bottom = numpy.array( bottom )
                plottedTrace.replot()     
                
    def onUpdateAll(self):
        for ref, context in self.cache.values():
            if ref() is not None:
                self.doCreatePlot(*context, forceUpdate=True )
        self.cacheGarbageCollect()
            
