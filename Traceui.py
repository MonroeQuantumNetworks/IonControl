# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 18:40:30 2012

@author: pmaunz
"""
import PyQt4.uic
from TraceTreeModel import TraceComboDelegate, TraceTreeModel
import pens
from PyQt4 import QtGui
import Trace
import os.path
import ProjectSelection
from PlottedTrace import PlottedTrace

TraceuiForm, TraceuiBase = PyQt4.uic.loadUiType(r'ui\TraceTreeui.ui')

def unique(seq):
#    seen = set()
#    return [ x for x in seq if x not in seen and not seen.add(x)]
    return list(set(seq))

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
        self.model = TraceTreeModel(self.TraceList,self.penicons)    
        self.traceTreeView.setModel(self.model)
        self.traceTreeView.setItemDelegateForColumn(1,TraceComboDelegate(self.penicons))

    def addTrace(self,trace,pen):
        self.model.addTrace(trace)
        trace.plot(pen,self.settings.plotstyle)
#        for column in range(5):
#            self.traceTreeView.resizeColumnToContents(column)
        
#        self.clearButton.clicked.connect(self.onClear )
#        self.saveButton.clicked.connect(self.onSave )
#        self.removeButton.clicked.connect(self.onRemove)
#        self.traceTreeView.clicked.connect(self.onClicked)
#        self.comboBoxStyle.setCurrentIndex( self.settings.plotstyle )
#        self.comboBoxStyle.currentIndexChanged[int].connect( self.setPlotStyle )
#        self.pushButtonApplyStyle.clicked.connect(self.onApplyStyle)
#        self.openFileButton.clicked.connect(self.onOpenFile)
#        self.plotButton.clicked.connect(self.onPlot)
#        self.shredderButton.clicked.connect(self.onShredder)
#
#    def setPlotStyle(self,value):
#        self.settings.plotstyle = value
#        
#    def onClicked(self,index):
#        if index.column() in [1,3]:
#            self.traceTreeView.edit(index)
####
#    def onPlot(self):
#        for index in unique([ i.row() for i in self.traceTreeView.selectedIndexes() ]):
#            self.TraceList[index].plot(-1,self.settings.plotstyle)
####
#    def onShredder(self):
#        for index in sorted(unique([ i.row() for i in self.traceTreeView.selectedIndexes() ]),reverse=True):
#            if self.TraceList[index].curvePen!=0:
#                self.TraceList[index].plot(0)
#            self.TraceList[index].trace.deleteFile()
#            self.model.dropTrace(index)
#        
#    def onClear(self):
#        for index in unique([ i.row() for i in self.traceTreeView.selectedIndexes() ]):
#            if self.TraceList[index].curvePen!=0:
#                self.TraceList[index].plot(0)
#                self.model.updateTrace(index)
#        
#    def onApplyStyle(self):
#        for index in unique([ i.row() for i in self.traceTreeView.selectedIndexes() ]):
#            self.TraceList[index].plot(-2,self.settings.plotstyle)
#    
#    def onRemove(self):
#        for index in sorted(unique([ i.row() for i in self.traceTreeView.selectedIndexes() ]),reverse=True):
#            if self.TraceList[index].curvePen!=0:
#                self.TraceList[index].plot(0)
#            self.model.dropTrace(index)
#    
#    def onSave(self):
#        for index in unique([ i.row() for i in self.traceTreeView.selectedIndexes() ]):
#            self.TraceList[index].trace.resave()
#
#        
#    def selectedTraces(self):
#        return [self.TraceList[index].trace for index in sorted(unique([ i.row() for i in self.traceTreeView.selectedIndexes() ]))]
#
#    def selectedPlottedTraces(self, defaultToLastLine=False):
#        traceList = [self.TraceList[index] for index in sorted(unique([ i.row() for i in self.traceTreeView.selectedIndexes() ]))]
#        if defaultToLastLine and len(traceList)==0 and len(self.model.TraceList)>0:
#            traceList = [self.model.TraceList[-1]]
#        return traceList
#
#    def onOpenFile(self):
#        fnames = QtGui.QFileDialog.getOpenFileNames(self, 'Open files', self.settings.lastDir)
#        for fname in fnames:
#            trace = Trace.Trace()
#            trace.filename = str(fname)
#            self.settings.lastDir, trace.name = os.path.split(str(fname))
#            trace.loadTrace(str(fname))
#            self.addTrace(PlottedTrace(trace,self.graphicsView,pens.penList,-1),-1)
#
#    def onClose(self):
#        #print "{0}.settings".format(self.configname), self.settings
#        self.config[self.configname+".settings"] = self.settings
#        