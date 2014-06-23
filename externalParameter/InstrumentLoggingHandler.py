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

MaxRecordingInterval = 180
GlobalTimeOffset = time.time()

class SourceTracking:
    def __init__(self):
        self.stat = RunningStatHistogram()
        self.timeStat = RunningStat()
        self.trace = None
        self.plottedTrace = None
        self.lastRecordingTime = 0

class InstrumentLoggingHandler:
    def __init__(self, traceui, plotDict):
        self.traceui = traceui
        self.plotDict = plotDict
        self.sourceData = defaultdict( SourceTracking )
        
    def addData(self, source, data ):
        if data is None:
            if source in self.sourceData:
                self.sourceData.pop(source)
        else:
            takentime, value = data
            sourceData = self.sourceData[source]
            sourceData.stat.add( value )
            sourceData.timeStat.add( takentime )
            if takentime-sourceData.lastRecordingTime > MaxRecordingInterval or len(sourceData.stat.histogram)>2:
                self.addPoint(source, sourceData)
                sourceData.lastRecordingTime = takentime
                sourceData.stat.clear()
                sourceData.timeStat.clear()

    def addPoint(self, source, sourceData):
        if sourceData.trace is None:
            sourceData.trace = Trace(record_timestamps=True)
            sourceData.trace.name = source
            sourceData.trace.x = numpy.array( [sourceData.timeStat.mean - GlobalTimeOffset] )
            sourceData.trace.y = numpy.array( [sourceData.stat.mean] )
            sourceData.trace.top = numpy.array( [sourceData.stat.max-sourceData.stat.mean ])
            sourceData.trace.bottom = numpy.array( [sourceData.stat.mean-sourceData.stat.min ])
            sourceData.plottedTrace = PlottedTrace(sourceData.trace, self.plotDict["Scan"]["view"], pens.penList, xAxisUnit = "s", xAxisLabel = "time") 
            sourceData.plottedTrace.trace.filenameCallback = functools.partial( WeakMethod.ref(sourceData.plottedTrace.traceFilename), source )
            self.traceui.addTrace( sourceData.plottedTrace, pen=-1)
            self.traceui.resizeColumnsToContents()
        else:
            sourceData.trace.x = numpy.append( sourceData.trace.x, sourceData.timeStat.mean-GlobalTimeOffset )
            sourceData.trace.y = numpy.append( sourceData.trace.y, sourceData.stat.mean )
            sourceData.trace.top = numpy.append( sourceData.trace.top, sourceData.stat.max-sourceData.stat.mean )
            sourceData.trace.bottom = numpy.append( sourceData.trace.bottom, sourceData.stat.mean-sourceData.stat.min )
            sourceData.plottedTrace.replot()
                
                
                