# -*- coding: utf-8 -*-
"""
Created on Sun Dec 23 19:27:39 2012

@author: pmaunz
"""

import numpy
from datetime import datetime
import os.path

try:
    import FitFunctions
    FitFunctionsAvailable = True
except:
    FitFunctionsAvailable = False

class Empty:
    pass

class TraceException(Exception):
    pass

class Trace(object):
    """ Class to encapsulate one displayed trace. The data can be saved to and loaded
    from a file
    """
    def __init__(self):
        self._x_ = numpy.array([])
        self._y_ = numpy.array([])
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
        self.rawdata = None
        self.columnNames = ['height', 'top', 'bottom','raw']
        
    @property
    def x(self):
        return self._x_
        
    @x.setter
    def x(self, new):
        self._x_ = new
        
    @property
    def y(self):
        return self._y_
        
    @y.setter
    def y(self,new):
        self._y_ = new
        self.vars.lastDataAquired = datetime.now()
        
    @property
    def filename(self):
        """ getter for the full pathname of the file
        """
        return self._filename
        
    @filename.setter
    def filename(self, filename):
        """ setter for the full pathname of the file
        upon resave, the data gets saved into this file
        """
        self._filename = filename    
        if filename:
            self.filepath, self.fileleaf = os.path.split(filename)
        else:
            self.filepath, self.fileleaf = None, None
        print "Trace filename", self.filename, self.filepath, self.fileleaf
        if self.dataChangedCallback:
            self.dataChangedCallback()                            
        
    def resave(self, saveIfUnsaved=True):
        """ save the data to the filename set previously by writing to filename
        """
        if hasattr(self, 'filename' ) and self.filename and self.filename!='':
            self.saveTrace(self.filename)
        elif self.filenameCallback and saveIfUnsaved:
            self.saveTrace(self.filenameCallback())
    
    def deleteFile(self):
        """ delete the file from disk
        """
        if hasattr(self, 'filename' ) and self.filename and self.filename!='':
            os.remove(self.filename)
    
    def plot(self,penindex):
        """ plot the data, penindex >= 0 gives requests the style with this number,
        penindex = -1 uses the first available style, penindex = -2 uses the previous style
        """
        if hasattr( self, 'plotfunction' ):
            (self.plotfunction)(self,penindex)
    
    def varstr(self,name):
        """ return the variable value as a string
        """
        return str(self.vars.__dict__.get(name,""))
        
    def saveTraceHeader(self,outfile):
        """ save the header of the trace to outfile
        """
        self.vars.fileCreation = datetime.now()
        for var, value in sorted(self.vars.__dict__.iteritems()):
            print >>outfile, "# {0}\t{1}".format(var, value)
        if self.header is not None:
            print >>outfile, self.header

    def saveTrace(self,filename):
        if self.rawdata:
            self.vars.rawdata = self.rawdata.save()
        if hasattr(self,'fitfunction'):
            print 'fitfunction saved'
            self.vars.fitfunction = self.fitfunction
        if filename!='':
            of = open(filename,'w')
            columnlist = [self._x_,self._y_]
            columnspec = ['x', 'y']
            for column in self.columnNames:
                if hasattr(self, column):
                    columnlist.append( getattr(self,column) )
                    columnspec.append( column )
            self.vars.columnspec = ",".join(columnspec)
            self.saveTraceHeader(of)
            for l in zip(*columnlist):
                print >>of, "\t".join(map(repr,l))
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
                    line = line.lstrip('# \t\r\n')
                    if line.find('\t')<0:
                        a = line.split(None,1)
                    else:
                        a = line.split('\t',1)
                    if len(a)>1:
                        self.vars.__dict__[a[0]] = a[1]  
                else:
                    data.append( map(float,line.split()) )
        columnspec =  self.vars.columnspec.split(',')
        for attr,d in zip( columnspec, zip(*data) ):
            setattr( self, attr, numpy.array(d) )
        self.filename = filename
        if hasattr(self.vars,'fitfunction') and FitFunctionsAvailable:
            self.fitfunction = FitFunctions.fitFunctionFactory(self.vars.fitfunction)
            
    def addColumn(self, name):
        """ adds a column with the given name, the column is saved in the file in the order added
        """
        if hasattr( self, name):
            raise TraceException("cannot add column '{0}' trace already has attribute with this name.".format(name))
        self.columnNames.append(name)
        setattr( self, name, numpy.array([]))
            
    
    def setPlotfunction(self, callback):
        self.plotfunction = callback
