'''
Created on Jun 21, 2014

@author: pmaunz
'''
import numpy
from trace.Trace import Trace
from trace.PlottedTrace import PlottedTrace
from trace import pens
from modules.RunningStat import RunningStatHistogram, RunningStat
from collections import defaultdict
import time 
import functools
from modules import WeakMethod
from modules.magnitude import mg

MaxRecordingInterval = 180
GlobalTimeOffset = time.time()

class DynamicDecimation:
    def __init__(self):
        self.stat = RunningStatHistogram()
        self.timeStat = RunningStat()
        self.lastRecordingTime = 0
        self.MaxRecordingInterval = 300
        
    def decimate(self, takentime, value):
        self.stat.add( value )
        self.timeStat.add( takentime )
        if takentime-self.lastRecordingTime > MaxRecordingInterval or len(self.stat.histogram)>2:
            self.lastRecordingTime = takentime
            meanVal, minVal, maxVal = self.stat.mean, self.stat.min, self.stat.max
            timeVal = self.timeStat.mean 
            self.stat.clear()
            self.timeStat.clear()
            return True, (timeVal, meanVal, minVal, maxVal)
        return False, None
        
class NoCalibration:
    def __init__(self):
        pass
    
    def convert(self, value):
        return value
    
    def convertMagnitude(self, value):
        return mg(value)
        

class DataHandling:
    def __init__(self):
        self.calibration = NoCalibration()
        self.decimation = DynamicDecimation()
        self.plotName = None
        self.persistence = None
        self.calibrationCache = dict()
        self.decimationCache = dict()
        self.persistenceCache = dict()
        self.trace = None
        self.plottedTrace = None
        self.filename = None
        
    def finishTrace(self):
        self.trace = None
        
    def decimate(self, takentime, value):
        return self.decimation.decimate( takentime, value )
    
    def convert(self, data ):
        takentime, value, minVal, maxVal = data
        calMin = self.calibration.convert(minVal)
        calMax = self.calibration.convert(maxVal)
        calValue = self.calibration.convert(value)
        calMagnitude = self.calibration.convertMagnitude(value)
        return (takentime, calValue, calMin, calMax)
        
    def addPoint(self, traceui, plot, data ):
        takentime, value, minval, maxval = data
        if self.trace is None:
            self.trace = Trace(record_timestamps=True)
            #self.trace.name = self.source
            self.trace.x = numpy.array( [takentime - GlobalTimeOffset] )
            self.trace.y = numpy.array( [value] )
            self.trace.timestamp = takentime
            self.trace.top = numpy.array( [maxval - value])
            self.trace.bottom = numpy.array( [value - minval])
            self.plottedTrace = PlottedTrace(self.trace, plot, pens.penList, xAxisUnit = "s", xAxisLabel = "time") 
            self.plottedTrace.trace.filenameCallback = functools.partial( WeakMethod.ref(self.plottedTrace.traceFilename), self )
            traceui.addTrace( self.plottedTrace, pen=-1)
            traceui.resizeColumnsToContents()
        else:
            self.trace.x = numpy.append( self.trace.x, takentime-GlobalTimeOffset )
            self.trace.y = numpy.append( self.trace.y, value )
            self.trace.top = numpy.append( self.trace.top, maxval - value )
            self.trace.bottom = numpy.append( self.trace.bottom, value - minval )
            self.plottedTrace.replot()


class InstrumentLoggingHandler:
    def __init__(self, traceui, plotDict, config):
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
            plot = self.plotDict.get( handler.plotName, None ) 
            if plot is None:
                plot = self.plotDict.values()[0]
            handler.addPoint( self.traceui, plot["view"], data )
            
    def saveConfig(self):
        self.config["InstrumentLogging.HandlerDict"] = self.handlerDict

                
                