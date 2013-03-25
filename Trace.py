# -*- coding: utf-8 -*-
"""
Created on Sun Dec 23 19:27:39 2012

@author: pmaunz
"""

import numpy
import datetime
import os.path

class Empty:
    pass

class Trace(object):
    def __init__(self):
        self.x = numpy.array([])
        self.y = numpy.array([])
        self.name = "noname"
        self.curve = None
        self.vars = Empty()
        self.vars.comment = ""
        self.header = None
        self.curvePen = 0
        self._filename = None
        self.filenameCallback = None   # function to result in filename for save
        
    @property
    def filename(self):        
        return self._filename
        
    @filename.setter
    def filename(self, filename):
        self._filename = filename    
        if filename:
            self.filepath, self.fileleaf = os.path.split(filename)
        else:
            self.filepath, self.fileleaf = None, None
        print "Trace filename", self.filename, self.filepath, self.fileleaf                               
        
    def resave(self):
        if hasattr(self, 'filename' ) and self.filename and self.filename!='':
            self.saveTrace(self.filename)
        elif self.filenameCallback:
            self.saveTrace(self.filenameCallback())
    
    def plot(self,penindex):
        if hasattr( self, 'plotfunction' ):
            (self.plotfunction)(self,penindex)
    
    def varstr(self,name):
        return str(self.vars.__dict__.get(name,""))
        
    def saveTraceHeader(self,outfile):
        print >>outfile, "#", datetime.datetime.now()
        for var in self.vars.__dict__.keys():
            print >>outfile, "#", var, self.vars.__dict__[var]
        if self.header is not None:
            print >>outfile, self.header

    def saveTrace(self,filename):
        if filename!='':
            of = open(filename,'w')
            self.saveTraceHeader(of)
            if hasattr(self, 'height'):
                print >>of, "# x y error"
                for x,db,error in zip(self.x, self.y, self.height):
                    print >>of, x, db, error
            else:
                print >>of, "# x y "
                for x,db in zip(self.x, self.y):
                    print >>of, x, db
            self.filename = filename
            of.close()
    
    def loadTrace(self,filename):
        infile = open(filename,'r')
        self.x = []
        self.y = []
        with infile:
            for line in infile:
                line = line.lstrip()
                if line[0]=='#':
                    a = line.split(None,2)
                    if len(a)>2:
                        self.vars.__dict__[a[1]] = a[2]  
                else:
                    a = line.split(None,2)
                    if len(a)>1:
                        self.x.append(float(a[0]))
                        self.y.append(float(a[1]))
        self.filename = filename
    
    def setPlotfunction(self, callback):
        self.plotfunction = callback
