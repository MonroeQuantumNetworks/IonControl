'''
Created on Jun 21, 2014

@author: pmaunz
'''
import numpy
from trace.Trace import Trace
from trace.PlottedTrace import PlottedTrace
from trace import pens
from collections import defaultdict
import time 
import functools
from modules import WeakMethod
from pyqtgraph.parametertree import Parameter
from PyQt4 import QtCore
from decimation import decimationDict
from calibration import calibrationDict
from persistence import persistenceDict
from dedicatedCounters.AnalogInputCalibration import AnalogInputCalibrationMap

GlobalTimeOffset = time.time()    
        
class DataHandling(object):
    def __init__(self):
        self.calibration = None
        self.decimation = None
        self.plotName = None
        self.persistence = None
        self.calibrationCache = dict()
        self.decimationCache = dict()
        self.persistenceCache = dict()
        self.trace = None
        self.plottedTrace = None
        self.filename = None
        self.maximumPoints = 0
        
    @property
    def decimationClass(self):
        return self.decimation.name if self.decimation else 'None'
    
    @decimationClass.setter
    def decimationClass(self, name):
        if self.decimation is not None:
            self.decimationCache[self.decimation.name] = self.decimation 
        self.decimation = self.decimationCache.get(name, decimationDict[name]() ) if name != 'None' else None
        
    @property
    def calibrationClass(self):
        return self.decimation.name if self.calibration else 'None'
    
    @calibrationClass.setter
    def calibrationClass(self, name):
        if self.calibration is not None:
            self.calibrationCache[self.calibration.name] = self.calibration 
        self.calibration = self.calibrationCache.get(name, calibrationDict[name]() ) if name != 'None' else None
        
    @property
    def persistenceClass(self):
        return self.persistence.name if self.persistence else 'None'
    
    @persistenceClass.setter
    def persistenceClass(self, name):
        if self.persistence is not None:
            self.persistenceCache[self.persistence.name] = self.persistence 
        self.persistence = self.persistenceCache.get(name, persistenceDict[name]() ) if name != 'None' else None
        
    def __getstate__(self):
        odict = self.__dict__.copy()
        del odict['trace']
        del odict['plottedTrace']
        return odict
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.trace = None
        self.plottedTrace = None

    def finishTrace(self):
        self.trace = None
        
    def decimate(self, takentime, value):
        if self.decimation is None:
            return True, (takentime, value, None, None)
        return self.decimation.decimate( takentime, value )
    
    def persist(self, source, data):
        if self.persistence is not None:
            self.persistence.persist(source, data)
    
    def convert(self, data ):
        takentime, value, minVal, maxVal = data
        if self.calibration is None:
            return data
        calMin = self.calibration.convert(minVal)
        calMax = self.calibration.convert(maxVal)
        calValue = self.calibration.convert(value)
        calMagnitude = self.calibration.convertMagnitude(value)
        return (takentime, calValue, calMin, calMax)
        
    def addPoint(self, traceui, plot, data, source ):
        takentime, value, minval, maxval = data
        if self.trace is None:
            self.trace = Trace(record_timestamps=True)
            self.trace.name = source
            self.trace.x = numpy.array( [takentime - GlobalTimeOffset] )
            self.trace.y = numpy.array( [value] )
            self.trace.timestamp = takentime
            if maxval is not None:
                self.trace.top = numpy.array( [maxval - value])
            if minval is not None:
                self.trace.bottom = numpy.array( [value - minval])
            self.plottedTrace = PlottedTrace(self.trace, plot, pens.penList, xAxisUnit = "s", xAxisLabel = "time") 
            self.plottedTrace.trace.filenameCallback = functools.partial( WeakMethod.ref(self.plottedTrace.traceFilename), self.filename )
            traceui.addTrace( self.plottedTrace, pen=-1)
            traceui.resizeColumnsToContents()
        else:
            if self.maximumPoints==0 or len(self.trace.x)<self.maximumPoints:
                self.trace.x = numpy.append( self.trace.x, takentime-GlobalTimeOffset )
                self.trace.y = numpy.append( self.trace.y, value )
                if maxval is not None:
                    self.trace.top = numpy.append( self.trace.top, maxval - value )
                if minval is not None:
                    self.trace.bottom = numpy.append( self.trace.bottom, value - minval )
            else:
                self.trace.x = numpy.append( self.trace.x[1:], takentime-GlobalTimeOffset )
                self.trace.y = numpy.append( self.trace.y[1:], value )
                if maxval is not None:
                    self.trace.top = numpy.append( self.trace.top[1:], maxval - value )
                if minval is not None:
                    self.trace.bottom = numpy.append( self.trace.bottom[1:], value - minval )                
            self.plottedTrace.replot()            


class InstrumentLoggingHandler(QtCore.QObject):
    paramTreeChanged = QtCore.pyqtSignal()
    def __init__(self, traceui, plotDict, config):
        super(InstrumentLoggingHandler, self).__init__()
        self.traceui = traceui
        self.plotDict = plotDict
        self.config = config
        self.handlerDict = self.config.get("InstrumentLogging.HandlerDict", defaultdict( DataHandling ) )
        
        
    def addData(self, source, data ):
        handler = self.handlerDict[source]
        if data is None:
            handler.finishTrace()
        else:
            keep, data = handler.decimate( *data )
            if not keep:
                return
            data = handler.convert( data )
            handler.persist( source, data )
            plot = self.plotDict.get( handler.plotName, None ) 
            if plot is None:
                plot = self.plotDict.values()[0]
            handler.addPoint( self.traceui, plot["view"], data, source )
            
    def saveConfig(self):
        self.config["InstrumentLogging.HandlerDict"] = self.handlerDict

    def paramDef(self, source):
        handler = self.handlerDict[source]
        param = [{'name': 'filename', 'type': 'str', 'object': handler, 'field': 'filename', 'value': handler.filename, 'tip': "Filename to be saved"},
                {'name': 'plot window', 'type': 'list', 'object': handler,'field': 'plotName', 'value': handler.plotName, 'values': self.plotDict.keys() },
                {'name': 'max points', 'type': 'int', 'object': handler,'field': 'maximumPoints', 'value': handler.maximumPoints },
                {'name': 'decimation', 'type': 'list', 'object': handler, 'field': 'decimationClass', 
                 'value': handler.decimation.name if handler.decimation else 'None', 'values': ['None'] + decimationDict.keys(), 'reload': True }]
        if handler.decimation is not None:
            param.append( {'name': 'Decimation parameters', 'type': 'group', 'children': handler.decimation.paramDef()} )
        param.append( {'name': 'calibration', 'type': 'list', 'object': handler, 'field': 'calibrationClass', 
                       'value': handler.calibration.name if handler.calibration else 'None', 'values': ['None'] + calibrationDict.keys(), 'reload': True } )
        if handler.calibration is not None:
            param.append( {'name': 'Calibration parameters', 'type': 'group', 'children': handler.calibration.paramDef()} )
        param.append( {'name': 'persistence', 'type': 'list', 'object': handler, 'field': 'persistenceClass', 
                       'value': handler.persistence.name if handler.persistence else 'None', 'values': ['None'] + persistenceDict.keys() , 'reload': True} )
        if handler.persistence is not None:
            param.append( {'name': 'Persistence parameters', 'type': 'group', 'children': handler.persistence.paramDef()} ) 
        return param

    def parameter(self, source):
        # re-create the parameters each time to prevent a exception that says the signal is not connected
        self._parameter = Parameter.create(name=source, type='group',children=self.paramDef(source))     
        self._parameter.sigTreeStateChanged.connect( self.update , QtCore.Qt.UniqueConnection)
        return self._parameter
    
    def update(self, param, changes):
        """
        update the parameter, called by the signal of pyqtgraph parametertree
        """
        for param, change, data in changes:
            if change=='value':
                setattr( param.opts.get('object',self), param.opts.get('field',param.name()), data)
                if param.opts.get('reload',False):
                    self.paramTreeChanged.emit()
                    
        
                
                