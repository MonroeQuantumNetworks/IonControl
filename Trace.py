# -*- coding: utf-8 -*-
"""
Created on Sun Dec 23 19:27:39 2012

@author: pmaunz
"""

import numpy
from datetime import datetime
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
        self.vars.traceCreation = datetime.now()
        self.header = None
        self.curvePen = 0
        self._filename = None
        self.filenameCallback = None   # function to result in filename for save
        self.dataChangedCallback = None # used to update the gui table
        
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
        if self.dataChangedCallback:
            self.dataChangedCallback()                            
        
    def resave(self, saveIfUnsaved=True):
        if hasattr(self, 'filename' ) and self.filename and self.filename!='':
            self.saveTrace(self.filename)
        elif self.filenameCallback and saveIfUnsaved:
            self.saveTrace(self.filenameCallback())
    
    def plot(self,penindex):
        if hasattr( self, 'plotfunction' ):
            (self.plotfunction)(self,penindex)
    
    def varstr(self,name):
        return str(self.vars.__dict__.get(name,""))
        
    def saveTraceHeader(self,outfile):
        self.vars.fileCreation = datetime.now()
        for var, value in self.vars.__dict__.iteritems():
            print >>outfile, "#", var, value
        if self.header is not None:
            print >>outfile, self.header

    def saveTrace(self,filename):
        if hasattr(self,'fitfunction'):
            print 'fitfunction saved'
            self.vars.fitfunction = self.fitfunction
        if filename!='':
            of = open(filename,'w')
            columnlist = [self.x,self.y]
            columnspec = ['x', 'y']
            for column in ['height', 'top', 'bottom']:
                if hasattr(self, column):
                    columnlist.append( getattr(self,column) )
                    columnspec.append( column )
            self.vars.columnspec = ",".join(columnspec)
            self.saveTraceHeader(of)
            for l in zip(*columnlist):
                print >>of, " ".join(map(str,l))
            self.filename = filename
            of.close()
    
    def loadTrace(self,filename):
        infile = open(filename,'r')
        data = []
        self.vars.columnspec = "x,y"
        with infile:
            for line in infile:
                line = line.strip()
                if line[0]=='#':
                    a = line.split(None,2)
                    if len(a)>2:
                        self.vars.__dict__[a[1]] = a[2]  
                else:
                    data.append( map(float,line.split()) )
        columnspec =  self.vars.columnspec.split(',')
        for attr,d in zip( columnspec, zip(*data) ):
            setattr( self, attr, numpy.array(d) )
        self.filename = filename
    
    def setPlotfunction(self, callback):
        self.plotfunction = callback
