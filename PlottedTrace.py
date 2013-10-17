# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 18:40:30 2012

@author: pmaunz
"""
from modules import enum
import pens
import pyqtgraph
import numpy

class PlottedTrace(object):
    Styles = enum.enum('lines','points','linespoints')
    def __init__(self,Trace,graphicsView,penList,pen=0,style=None,parentTrace=None):
        self.penList = penList
        self.graphicsView = graphicsView
        if not hasattr(self.graphicsView,'penUsageDict'):
            if self.graphicsView != None:
                self.graphicsView.penUsageDict = [0]*len(pens.penList)
        self.penUsageDict = self.graphicsView.penUsageDict
        self.trace = Trace
        self.curve = None
        self.fitcurve = None
        self.errorBarItem = None
        self.style = self.Styles.lines if style is None else style
#Tree related data
        self.parentTrace = parentTrace
        self.childTraces = []
        
    def appendChild(self, child):
        """Append a child to the trace's list of children"""
        return self.childTraces.append(child)
    
    def child(self, row):
        """Return the child at the specified row, from the trace's list of children."""
        return self.childTraces[row]
        
    def childCount(self):
        """Return the number of children of the trace."""
        return len(self.childTraces)
        
    def parent(self):
        """Return the parent of the trace."""
        return self.parentTrace
    
    def row(self):
        """Return the row of the trace. This is determined by the index of the row in the parent's list of children."""
        if self.parentTrace != None:
            return self.parentTrace.childItems.index(self)
        else:
            return 0
        
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
            self.fitx = numpy.linspace(numpy.min(self.trace.x),numpy.max(self.trace.x),300)
            self.fity = self.trace.fitfunction.value(self.fitx)
            self.fitcurve = self.graphicsView.plot(self.fitx, self.fity, pen=self.penList[penindex][0])
 
    def plotErrorBars(self,penindex):
        if hasattr(self.trace,'height'):
            self.errorBarItem = pyqtgraph.ErrorBarItem(x=self.trace.x, y=self.trace.y, height=self.trace.height,
                                                       pen=self.penList[penindex][0])
            self.graphicsView.addItem(self.errorBarItem)
        elif hasattr(self.trace,'top') and hasattr(self.trace,'bottom'):
            self.errorBarItem = pyqtgraph.ErrorBarItem(x=self.trace.x, y=self.trace.y, top=self.trace.top, bottom=self.trace.bottom,
                                                       pen=self.penList[penindex][0])
            self.graphicsView.addItem(self.errorBarItem)
            

    def plotLines(self,penindex):
        self.curve = self.graphicsView.plot(self.trace.x, self.trace.y, pen=self.penList[penindex][0])
    
    def plotPoints(self,penindex):
        self.curve = self.graphicsView.plot(self.trace.x, self.trace.y, pen=None, symbol=self.penList[penindex][1],
                                            symbolPen=self.penList[penindex][2],symbolBrush=self.penList[penindex][3])
    
    def plotLinespoints(self,penindex):
        self.curve = self.graphicsView.plot(self.trace.x, self.trace.y, pen=self.penList[penindex][0], symbol=self.penList[penindex][1],
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
            self.curve.setData( self.trace.x, self.trace.y )
        if hasattr(self,'errorBarItem') and self.errorBarItem is not None:
            if hasattr(self.trace,'height'):
                self.errorBarItem.setData(x=self.trace.x, y=self.trace.y, height=self.trace.height)
            else:
                self.errorBarItem.setOpts(x=self.trace.x, y=self.trace.y, top=self.trace.top, bottom=self.trace.bottom)