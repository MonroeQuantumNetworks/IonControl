# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 18:40:30 2012

@author: pmaunz
"""
from modules import enum
import PyQt4.uic
import TraceTableModel
import pens
import pyqtgraph
import numpy
from PyQt4 import QtGui
import Trace
import os.path
import ProjectSelection

class PlottedTrace(object):
    Styles = enum.enum('lines','points','linespoints')
    def __init__(self,Trace,graphicsView,penList,pen=0,style=None):
        self.penList = penList
        self.graphicsView = graphicsView
        if not hasattr(self.graphicsView,'penUsageDict'):
            self.graphicsView.penUsageDict = [0]*len(pens.penList)
        self.penUsageDict = self.graphicsView.penUsageDict
        self.trace = Trace
        self.curve = None
        self.fitcurve = None
        self.errorBarItem = None
        self.style = self.Styles.lines if style is None else style
        #self.plot(pen)
        
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
            self.errorBarItem.setData(x=self.trace.x, y=self.trace.y, height=self.trace.height)


TraceuiForm, TraceuiBase = PyQt4.uic.loadUiType(r'ui\Traceui.ui')


def unique(seq):
    seen = set()
    return [ x for x in seq if x not in seen and not seen.add(x)]

class Settings:
    def __init__(self):
        self.lastDir = ProjectSelection.configDir()
        self.plotstyle = 0

class Traceui(TraceuiForm, TraceuiBase):
    def __init__(self, penicons, config, parentname, graphicsView, parent=None):
        TraceuiBase.__init__(self,parent)
        TraceuiForm.__init__(self)
        self.penicons = penicons
        self.config = config
        self.configname = "Traceui."+parentname
        self.settings = self.config.get(self.configname+".settings",Settings())
        self.graphicsView = graphicsView

    def setupUi(self,MainWindow):
        TraceuiForm.setupUi(self,MainWindow)
        self.TraceList = list()
        self.model = TraceTableModel.TraceTableModel(self.TraceList,self.penicons)    
        self.traceTableView.setModel(self.model)
        self.traceTableView.setItemDelegateForColumn(1,TraceTableModel.TraceComboDelegate(self.penicons))
        
        self.clearButton.clicked.connect(self.onClear )
        self.saveButton.clicked.connect(self.onSave )
        self.removeButton.clicked.connect(self.onRemove)
        self.traceTableView.clicked.connect(self.onClicked)
        self.comboBoxStyle.currentIndexChanged[int].connect( self.setPlotStyle )
        self.pushButtonApplyStyle.clicked.connect(self.onApplyStyle)
        self.openFileButton.clicked.connect(self.onOpenFile)
        self.plotButton.clicked.connect(self.onPlot)
        self.shredderButton.clicked.connect(self.onShredder)

    def setPlotStyle(self,value):
        self.settings.plotstyle = value
        
    def onClicked(self,index):
        if index.column() in [1,3]:
            self.traceTableView.edit(index)
        
    def onPlot(self):
        for index in unique([ i.row() for i in self.traceTableView.selectedIndexes() ]):
            self.TraceList[index].plot(-1,self.settings.plotstyle)

    def onShredder(self):
        for index in sorted(unique([ i.row() for i in self.traceTableView.selectedIndexes() ]),reverse=True):
            if self.TraceList[index].curvePen!=0:
                self.TraceList[index].plot(0)
            self.TraceList[index].trace.deleteFile()
            self.model.dropTrace(index)
        
    def onClear(self):
        for index in unique([ i.row() for i in self.traceTableView.selectedIndexes() ]):
            if self.TraceList[index].curvePen!=0:
                self.TraceList[index].plot(0)
                self.model.updateTrace(index)
        
    def onApplyStyle(self):
        for index in unique([ i.row() for i in self.traceTableView.selectedIndexes() ]):
            self.TraceList[index].plot(-2,self.settings.plotstyle)
    
    def onRemove(self):
        for index in sorted(unique([ i.row() for i in self.traceTableView.selectedIndexes() ]),reverse=True):
            if self.TraceList[index].curvePen!=0:
                self.TraceList[index].plot(0)
            self.model.dropTrace(index)
    
    def onSave(self):
        for index in unique([ i.row() for i in self.traceTableView.selectedIndexes() ]):
            self.TraceList[index].trace.resave()

    def addTrace(self,trace,pen):
        self.model.addTrace(trace)
        trace.plot(pen,self.settings.plotstyle)
        self.traceTableView.resizeColumnsToContents()
        
    def selectedTraces(self):
        return [self.TraceList[index].trace for index in sorted(unique([ i.row() for i in self.traceTableView.selectedIndexes() ]))]

    def selectedPlottedTraces(self):
        return [self.TraceList[index] for index in sorted(unique([ i.row() for i in self.traceTableView.selectedIndexes() ]))]

    def onOpenFile(self):
        fnames = QtGui.QFileDialog.getOpenFileNames(self, 'Open files', self.settings.lastDir)
        for fname in fnames:
            trace = Trace.Trace()
            trace.filename = str(fname)
            self.settings.lastDir, trace.name = os.path.split(str(fname))
            trace.loadTrace(str(fname))
            self.addTrace(PlottedTrace(trace,self.graphicsView,pens.penList,-1),-1)

    def onClose(self):
        #print "{0}.settings".format(self.configname), self.settings
        self.config[self.configname+".settings"] = self.settings