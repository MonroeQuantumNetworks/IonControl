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

class PlottedTrace(object):
    Styles = enum.enum('lines','points','linespoints')
    def __init__(self,Trace,graphicsView,penList,pen=0,style=None,isRootTrace=False,
                 xColumnName='x',yColumnName='y',topColumnName='top',bottomColumnName='bottom',heightColumnName='height'):
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
        # we use pointers to the relevant columns in trace
        self.xColumn = getattr(self.trace,xColumnName)
        self.yColumn = getattr(self.trace,yColumnName)
        if hasattr(self.trace, topColumnName):
            self.topColumn = getattr(self.trace,topColumnName)
        if hasattr(self.trace, bottomColumnName):
            self.bottomColumn = getattr(self.trace,bottomColumnName)
        if hasattr(self.trace, heightColumnName):
            self.heightColumn = getattr(self.trace,heightColumnName)

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
        self.xColumn = self.childTraces[0].xColumn #All child traces should have the same x data!
        childTraceYvalues = numpy.array([childTrace.yColumn for childTrace in self.childTraces]) #2D array of children's y data
        self.yColumn = numpy.mean(childTraceYvalues, axis=0) #set parent y to mean of children's y

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
        if hasattr(self.trace,'fitfunction'):
            self.fitx = numpy.linspace(numpy.min(self.xColumn),numpy.max(self.xColumn),300)
            self.fity = self.trace.fitfunction.value(self.fitx)
            self.fitcurve = self.graphicsView.plot(self.fitx, self.fity, pen=self.penList[penindex][0])
 
    def plotErrorBars(self,penindex):
        if hasattr(self,'heightColumn'):
            self.errorBarItem = pyqtgraph.ErrorBarItem(x=self.xColumn, y=self.yColumn, height=self.heightColumn,
                                                       pen=self.penList[penindex][0])
            self.graphicsView.addItem(self.errorBarItem)
        elif hasattr(self,'topColumn') and hasattr(self,'bottomColumn'):
            self.errorBarItem = pyqtgraph.ErrorBarItem(x=self.xColumn, y=self.yColumn, top=self.topColumn, bottom=self.bottomColumn,
                                                       pen=self.penList[penindex][0])
            self.graphicsView.addItem(self.errorBarItem)
            

    def plotLines(self,penindex):
        self.curve = self.graphicsView.plot(self.xColumn, self.yColumn, pen=self.penList[penindex][0])
    
    def plotPoints(self,penindex):
        self.curve = self.graphicsView.plot(self.xColumn, self.yColumn, pen=None, symbol=self.penList[penindex][1],
                                            symbolPen=self.penList[penindex][2],symbolBrush=self.penList[penindex][3])
    
    def plotLinespoints(self,penindex):
        self.curve = self.graphicsView.plot(self.xColumn, self.yColumn, pen=self.penList[penindex][0], symbol=self.penList[penindex][1],
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
            self.curve.setData( self.xColumn, self.yColumn )
        if hasattr(self,'errorBarItem') and self.errorBarItem is not None:
            if hasattr(self.trace,'height'):
                self.errorBarItem.setData(x=self.xColumn, y=self.yColumn, height=self.trace.height)
            else:
                self.errorBarItem.setOpts(x=self.xColumn, y=self.yColumn, top=self.topColumn, bottom=self.bottomColumn)

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
            
            
                