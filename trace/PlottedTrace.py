# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 18:40:30 2012

@author: pmaunz
"""
import os.path
from trace import pens

from PyQt4 import QtGui, QtCore
import numpy
from pyqtgraph.graphicsItems.ErrorBarItem import ErrorBarItem
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem

from modules import DataDirectory 
from modules import enum
from trace.Trace import TracePlotting
from functools import partial
import time 
import logging
from weakref import WeakValueDictionary

class PlottedTrace(object):
    Styles = enum.enum('lines','points','linespoints','lines_with_errorbars','points_with_errorbars','linepoints_with_errorbars')
    Types = enum.enum('default','steps')
    def __init__(self,Trace,graphicsView,penList=None,pen=0,style=None,plotType=None, isRootTrace=False,
                 xColumn='x',yColumn='y',topColumn='top',bottomColumn='bottom',heightColumn='height',
                 rawColumn='raw', tracePlotting=None, name="", xAxisLabel = None, xAxisUnit = None,
                 yAxisLabel = None, yAxisUnit = None):
        if penList is None:
            penList = pens.penList
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
        self.type = self.Types.default if plotType is None else plotType
        #Tree related data. Parent and children are set in the model's addTrace method, but declared here
        self.isRootTrace = isRootTrace
        self.parentTrace = None
        self.childTraces = []
        self.curvePen = 0
        self.name = name
        self.xAxisLabel = xAxisLabel
        self.xAxisUnit = xAxisUnit
        self.yAxisLabel = yAxisLabel
        self.yAxisUnit = yAxisUnit
        self.lastPlotTime = time.time()
        self.needsReplot = False
        # we use pointers to the relevant columns in trace
        if tracePlotting is not None:
            self.tracePlotting = tracePlotting
            self._xColumn = tracePlotting.xColumn
            self._yColumn = tracePlotting.yColumn
            self._topColumn = tracePlotting.topColumn
            self._bottomColumn = tracePlotting.bottomColumn
            self._heightColumn = tracePlotting.heightColumn
            self._rawColumn = tracePlotting.rawColumn
            self.type = tracePlotting.type
        elif self.trace:
            self._xColumn = xColumn
            self._yColumn = yColumn
            self._topColumn = topColumn
            self._bottomColumn = bottomColumn
            self._heightColumn = heightColumn
            self._rawColumn = rawColumn
            self.tracePlotting = TracePlotting(xColumn=self._xColumn, yColumn=self._yColumn, topColumn=self._topColumn, bottomColumn=self._bottomColumn,
                                               heightColumn=self._heightColumn, rawColumn=self._rawColumn, name=name, type_=self.type)
            self.trace.addTracePlotting( self.tracePlotting )
            if not hasattr(self.trace,xColumn):
                self.trace.addColumn( xColumn )
            if not hasattr(self.trace,yColumn):
                self.trace.addColumn( yColumn )
        self.stylesLookup = WeakValueDictionary( { self.Styles.lines: partial(self.plotLines, errorbars=False),
                         self.Styles.points: partial(self.plotPoints, errorbars=False),
                         self.Styles.linespoints: partial(self.plotLinespoints, errorbars=False), 
                         self.Styles.lines_with_errorbars: partial(self.plotLines, errorbars=True),
                         self.Styles.points_with_errorbars: partial(self.plotPoints, errorbars=True),
                         self.Styles.linepoints_with_errorbars: partial(self.plotLinespoints, errorbars=True)} )

    @property
    def hasTopColumn(self):
        return self._topColumn and hasattr(self.trace, self._topColumn)

    @property
    def hasBottomColumn(self):
        return self._bottomColumn and hasattr(self.trace, self._bottomColumn)

    @property
    def hasHeightColumn(self):
        return self._heightColumn and hasattr(self.trace, self._heightColumn)

    @property
    def hasRawColumn(self):
        return self._rawColumn and hasattr(self.trace, self._rawColumn)
        
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
            self.errorBarItem = ErrorBarItem(x=(self.x), y=(self.y), height=(self.height),
                                                       pen=self.penList[penindex][0])
        elif self.hasTopColumn and self.hasBottomColumn:
            self.errorBarItem = ErrorBarItem(x=(self.x), y=(self.y), top=(self.top), bottom=(self.bottom),
                                                       pen=self.penList[penindex][0])
            self.graphicsView.addItem(self.errorBarItem)
            

    def plotLines(self,penindex, errorbars=True ):
        if errorbars:
            self.plotErrorBars(penindex)
        self.curve = self.graphicsView.plot((self.x), (self.y), pen=self.penList[penindex][0])            
        if self.xAxisLabel:
            if self.xAxisUnit:
                self.graphicsView.setLabel('bottom', text = "{0} ({1})".format(self.xAxisLabel, self.xAxisUnit))
            else:
                self.graphicsView.setLabel('bottom', text = "{0}".format(self.xAxisLabel))
    
    def plotPoints(self,penindex, errorbars=True ):
        if errorbars:
            self.plotErrorBars(penindex)
        self.curve = self.graphicsView.plot((self.x), (self.y), pen=None, symbol=self.penList[penindex][1],
                                            symbolPen=self.penList[penindex][2],symbolBrush=self.penList[penindex][3])
        if self.xAxisLabel:
            if self.xAxisUnit:
                self.graphicsView.setLabel('bottom', text = "{0} ({1})".format(self.xAxisLabel, self.xAxisUnit))
            else:
                self.graphicsView.setLabel('bottom', text = "{0}".format(self.xAxisLabel))

    
    def plotLinespoints(self,penindex, errorbars=True ):
        if errorbars:
            self.plotErrorBars(penindex)
        self.curve = self.graphicsView.plot((self.x), (self.y), pen=self.penList[penindex][0], symbol=self.penList[penindex][1],
                                            symbolPen=self.penList[penindex][2],symbolBrush=self.penList[penindex][3])
        if self.xAxisLabel:
            if self.xAxisUnit:
                self.graphicsView.setLabel('bottom', text = "{0} ({1})".format(self.xAxisLabel, self.xAxisUnit))
            else:
                self.graphicsView.setLabel('bottom', text = "{0}".format(self.xAxisLabel))
                
    
    def plotSteps(self,penindex):
        mycolor = list(self.penList[penindex][4])
        mycolor[3] = 80
        self.curve = PlotCurveItem(self.x, self.y, stepMode=True, fillLevel=0, brush=mycolor, pen=self.penList[penindex][0])
        if self.xAxisLabel:
            if self.xAxisUnit:
                self.graphicsView.setLabel('bottom', text = "{0} ({1})".format(self.xAxisLabel, self.xAxisUnit))
            else:
                self.graphicsView.setLabel('bottom', text = "{0}".format(self.xAxisLabel))
        self.graphicsView.addItem( self.curve )
    
    def plot(self,penindex=-1,style=None):
        self.style = self.style if style is None else style
        self.removePlots()
        penindex = { -2: self.__dict__.get('curvePen',0),
                     -1: sorted(zip(self.penUsageDict, range(len(self.penUsageDict))))[1][1] }.get(penindex, penindex)
        if penindex>0:
            if self.type==self.Types.default:
                self.plotFitfunction(penindex)
                self.stylesLookup.get(self.style,self.plotLines)(penindex)
            elif self.type ==self.Types.steps:
                self.plotSteps(penindex)
            self.penUsageDict[penindex] += 1
        self.curvePen = penindex
        
    def replot(self):
        if len(self.x)>500 and time.time()-self.lastPlotTime<len(self.x)/500.:
            if not self.needsReplot:
                self.needsReplot = True
                QtCore.QTimer.singleShot(len(self.x)*2,self._replot) 
        else:
            self._replot()
            
    def _replot(self):
        if hasattr(self,'curve') and self.curve is not None:
            self.curve.setData( (self.x), (self.y) )
        if hasattr(self,'errorBarItem') and self.errorBarItem is not None:
            if self.hasHeightColumn:
                self.errorBarItem.setData(x=(self.x), y=(self.y), height=(self.trace.height))
            else:
                self.errorBarItem.setOpts(x=(self.x), y=(self.y), top=(self.top), bottom=(self.bottom))
        self.lastPlotTime = time.time()
        self.needsReplot = False

    def traceFilename(self, pattern):
        directory = DataDirectory.DataDirectory()
        if self.parent().isRootTrace: 
            if pattern and pattern!='':
                filename, _ = directory.sequencefile(pattern)
                return filename
            else:
                path = str(QtGui.QFileDialog.getSaveFileName(None, 'Save file',directory.path()))
                return path
        else:
            parentFilename = self.parent().trace.getFilename() 
            filename, _ = directory.sequencefile( os.path.split(parentFilename)[1] )
            return filename
        
    def setView(self, graphicsView ):
        self.removePlots()
        self.graphicsView = graphicsView
        self.plot(-1)
            
    @property
    def fitFunction(self):
        return self.tracePlotting.fitFunction if self.tracePlotting else None
    
    @fitFunction.setter
    def fitFunction(self, fitfunction):
        self.tracePlotting.fitFunction = fitfunction
        
#     def __del__(self):
#         logging.getLogger(__name__).debug("Delete PlottedTrace")
#         print "Delete PlottedTrace"
        
        
if __name__=="__main__":
    from trace.Trace import Trace
    import gc
    import sys
    plottedTrace = PlottedTrace(Trace(),None,pens.penList)
    print sys.getrefcount(plottedTrace)
    plottedTrace = None
    del plottedTrace
    gc.collect()
                
