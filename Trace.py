# -*- coding: utf-8 -*-
"""
Created on Sun Dec 23 19:27:39 2012

@author: pmaunz
"""

import numpy
import datetime

class Empty:
    pass

class Trace:
    def __init__(self):
        self.x = numpy.array([])
        self.y = numpy.array([])
        self.name = "noname"
        self.curve = None
        self.vars = Empty()
        self.vars.comment = ""
        self.curvePen = 0
        
    def resave(self):
        if hasattr(self, 'filename' ):
            self.saveTrace(self.filename)
    
    def plot(self,penindex):
        if hasattr( self, 'plotfunction' ):
            (self.plotfunction)(self,penindex)
    
    def varstr(self,name):
        return str(self.vars.__dict__.get(name,""))
        
    def saveTraceHeader(self,outfile):
        print >>outfile, "#", datetime.datetime.now()
        for var in self.vars.__dict__.keys():
            print >>outfile, "#", var, self.vars.__dict__[var]

    def saveTrace(self,filename):
        of = open(filename,'w')
        self.saveTraceHeader(of)
        print >>of, "# x y error"
        for x,db in zip(self.x, self.y):
            print >>of, x, db
        of.close()
    
    def setPlotfunction(self, callback):
        self.plotfunction = callback
