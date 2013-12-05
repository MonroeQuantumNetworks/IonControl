# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 18:40:30 2012

@author: pmaunz
"""
from modules import enum
import pens
import pyqtgraph
import numpy
from modules import DataDirectory 
import os.path
from PyQt4 import QtGui
from Trace import TracePlotting

class PlottedTrace(object):
    Styles = enum.enum('lines','points','linespoints')
    def __init__(self,Trace,graphicsView,penList,pen=0,style=None,isRootTrace=False,
                 xColumn='x',yColumn='y',topColumn='top',bottomColumn='bottom',heightColumn='height',
                 rawColumn='raw', tracePlotting=None, name=""):
        self.penList = penList
        self.graphicsView = graphicsView
        if self.graphicsView != None:
            if not hasattr(self.graphicsView,'penUsageDict'):
                self.graphicsView.penUsageDict = [0]*len(pens.penList)
            self.penUsageDict = self.graphicsView.penUsageDict
        self.trace = Trace
        self.curve = None
        self.fitcurve = None
        self.errorBarItem = None
        self.style = self.Styles.lines if style is None else style
#Tree related data. Parent and children are set in the model's addTrace method, but declared here
        self.isRootTrace = isRootTrace
        self.parentTrace = None
        self.childTraces = []
        self.curvePen = 0
        self.name = name
        # we use pointers to the relevant columns in trace
        if tracePlotting is not None:
            self.tracePlotting = tracePlotting
            self._xColumn = tracePlotting.xColumn
            self._yColumn = tracePlotting.yColumn
            self._topColumn = tracePlotting.topColumn
            self._bottomColumn = tracePlotting.bottomColumn
            self._heightColumn = tracePlotting.heightColumn
            self._rawColumn = tracePlotting.rawColumn
        elif self.trace:
            self._xColumn = xColumn
            self._yColumn = yColumn
            self._topColumn = topColumn
            self._bottomColumn = bottomColumn
            self._heightColumn = heightColumn
            self._rawColumn = rawColumn
            self.tracePlotting = TracePlotting(xColumn=self._xColumn, yColumn=self._yColumn, topColumn=self._topColumn, bottomColumn=self._bottomColumn,
                                               heightColumn=self._heightColumn, rawColumn=self._rawColumn, name=name)
            self.trace.addTracePlotting( self.tracePlotting )
            if not hasattr(self.trace,xColumn):
                self.trace.addColumn( xColumn )
            if not hasattr(self.trace,yColumn):
                self.trace.addColumn( yColumn )
          
    @property
    def hasTopColumn(self):
        return hasattr(self.trace, self._topColumn)

    @property
    def hasBottomColumn(self):
        return hasattr(self.trace, self._bottomColumn)

    @property
    def hasHeightColumn(self):
        return hasattr(self.trace, self._heightColumn)

    @property
    def hasRawColumn(self):
        return hasattr(self.trace, self._rawColumn)
        
    @property
    def x(self):
        return getattr(self.trace, self._xColumn)
    
    @x.setter
    def x(self, column):
        setattr(self.trace, self._xColumn, column)

    @property
    def y(self):
        return getattr(self.trace, self._yColumn)
    
    @y.setter
    def y(self, column):
        setattr(self.trace, self._yColumn, column)

    @property
    def top(self):
        return getattr(self.trace, self._topColumn)
    
    @top.setter
    def top(self, column):
        setattr(self.trace, self._topColumn, column)

    @property
    def bottom(self):
        return getattr(self.trace, self._bottomColumn)
    
    @bottom.setter
    def bottom(self, column):
        setattr(self.trace, self._bottomColumn, column)

    @property
    def height(self):
        return getattr(self.trace, self._heightColumn)
    
    @height.setter
    def height(self, column):
        setattr(self.trace, self._heightColumn, column)

    @property
    def raw(self):
        return getattr(self.trace, self._rawColumn)
    
    @raw.setter
    def raw(self, column):
       setattr(self.trace, self._rawColumn, column)

    def child(self, number):
        """Return the child at the specified number, from the trace's list of children."""
        return self.childTraces[number]

    def childCount(self):
        """Return the number of children of the trace."""
        return len(self.childTraces)

    def childNumber(self):
        """Return the row of this trace in its parent's list of traces."""
        if self.parentTrace != None:
            return self.parentTrace.childTraces.index(self)
        else:
            return 0

    def parent(self):
        """Return the parent of the trace."""
        return self.parentTrace
    
    def appendChild(self, trace):
        """Append a child to the trace."""
        self.childTraces.append(trace)
        return True
        
    def averageChildren(self):
        """Set the trace data to the average of its children's data."""
        self.x = self.childTraces[0].x #All child traces should have the same x data!
        childTraceYvalues = numpy.array([childTrace.y for childTrace in self.childTraces]) #2D array of children's y data
        self.y = numpy.mean(childTraceYvalues, axis=0) #set parent y to mean of children's y

    def removePlots(self):
        if self.curve is not None:
            self.graphicsView.removeItem(self.curve)
            self.curve = None
            self.penUsageDict[self.curvePen] -= 1
            if self.errorBarItem is not None:
                self.graphicsView.removeItem(self.errorBarItem)  
                self.errorBarItem = None
            if self.fitcurve is not None:
                self.graphicsView.removeItem(self.fitcurve)
                self.fitcurve = None
                
    def plotFitfunction(self,penindex):
        if self.fitFunction:
            self.fitx = numpy.linspace(numpy.min(self.x),numpy.max(self.x),300)
            self.fity = self.fitFunction.value(self.fitx)
            self.fitcurve = self.graphicsView.plot(self.fitx, self.fity, pen=self.penList[penindex][0])
 
    def plotErrorBars(self,penindex):
        if self.hasHeightColumn:
            self.errorBarItem = pyqtgraph.ErrorBarItem(x=self.x, y=self.y, height=self.height,
                                                       pen=self.penList[penindex][0])
            self.graphicsView.addItem(self.errorBarItem)
        elif self.hasTopColumn and self.hasBottomColumn:
            self.errorBarItem = pyqtgraph.ErrorBarItem(x=self.x, y=self.y, top=self.top, bottom=self.bottom,
                                                       pen=self.penList[penindex][0])
            self.graphicsView.addItem(self.errorBarItem)
            

    def plotLines(self,penindex):
        self.curve = self.graphicsView.plot(self.x, self.y, pen=self.penList[penindex][0])
    
    def plotPoints(self,penindex):
        self.curve = self.graphicsView.plot(self.x, self.y, pen=None, symbol=self.penList[penindex][1],
                                            symbolPen=self.penList[penindex][2],symbolBrush=self.penList[penindex][3])
    
    def plotLinespoints(self,penindex):
        self.curve = self.graphicsView.plot(self.x, self.y, pen=self.penList[penindex][0], symbol=self.penList[penindex][1],
                                            symbolPen=self.penList[penindex][2],symbolBrush=self.penList[penindex][3])                
    
    def plot(self,penindex,style=None):
        self.style = self.style if style is None else style
        self.removePlots()
        penindex = { -2: self.__dict__.get('curvePen',0),
                     -1: sorted(zip(self.penUsageDict, range(len(self.penUsageDict))))[1][1] }.get(penindex, penindex)
        if penindex>0:
            self.plotFitfunction(penindex)
            self.plotErrorBars(penindex)
            { self.Styles.lines: self.plotLines,
              self.Styles.points: self.plotPoints,
              self.Styles.linespoints: self.plotLinespoints }.get(self.style,self.plotLines)(penindex)
            self.penUsageDict[penindex] += 1
        self.curvePen = penindex
        
    def replot(self):
        if hasattr(self,'curve') and self.curve is not None:
            self.curve.setData( self.x, self.y )
        if hasattr(self,'errorBarItem') and self.errorBarItem is not None:
            if self.hasHeightColumn:
                self.errorBarItem.setData(x=self.x, y=self.y, height=self.trace.height)
            else:
                self.errorBarItem.setOpts(x=self.x, y=self.y, top=self.top, bottom=self.bottom)

    def traceFilename(self, pattern):
        directory = DataDirectory.DataDirectory()
        if self.parent().isRootTrace: 
            if pattern and pattern!='':
                filename, components = directory.sequencefile(pattern)
                return filename
            else:
                path = str(QtGui.QFileDialog.getSaveFileName(None, 'Save file',directory.path()))
                return path
        else:
            parentFilename = self.parent().trace.getFilename() 
            filename, components = directory.sequencefile( os.path.split(parentFilename)[1] )
            return filename
            
    @property
    def fitFunction(self):
        return self.tracePlotting.fitFunction if self.tracePlotting else None
    
    @fitFunction.setter
    def fitFunction(self, fitfunction):
        self.tracePlotting.fitFunction = fitfunction
        

                