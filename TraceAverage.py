# -*- coding: utf-8 -*-
"""
Created on Tue Feb 26 21:57:31 2013

@author: pmaunz
"""

import Trace
import numpy

class TraceAverage(Trace):
    def __init__(self):
        self.traceList = list()
        self.x = None
        
    def addTraces(self, iterable):
        for trace in iterable:
            self.addTrace(trace)
    
    def addTrace(self, trace):
        if self.x is None:
            self.x = trace.x
            self.tracelist.append(trace)
        else:
            if numpy.array_equal( trace.x, self.x ):
                self.tracelist.append(trace)
        
    def calculateAverage(self):
        m = numpy.matrix( [trace.x for trace in self.tracelist] )
        w = numpy.matrix( [trace.height for trace in self.tracelist if hasattr(trace,'height') else [1]])
        numpy.mean(m, axis=0, weight=w)
        
        
if __name__=="__main__":
    t1 = Trace.Trace()
    t1.x = [1,2,3,4,5]
    t1.y = [4,5,6,7,8]
    t2 = Trace.Trace()
    t2.x = t1.x
    t2.y = [5,6,7,8,9]
    
    ta = TraceAverage()
    ta.addTraces([t1, t2])
    ta.calculateAverage()