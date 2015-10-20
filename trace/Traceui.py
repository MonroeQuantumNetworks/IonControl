# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 18:40:30 2012

@author: pmaunz
"""
import logging
import os.path
from trace import Trace
from trace import pens

from PyQt4 import QtGui, QtCore
import PyQt4.uic

from ProjectConfig.Project import getProject
from TraceModel import TraceComboDelegate
from TraceModel import TraceModel
from trace.PlottedTrace import PlottedTrace
from TraceDescriptionTableModel import TraceDescriptionTableModel
from uiModules.ComboBoxDelegate import ComboBoxDelegate
from uiModules.KeyboardFilter import KeyListFilter

uipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\Traceui.ui')
TraceuiForm, TraceuiBase = PyQt4.uic.loadUiType(uipath)

class Settings:
    """Class to hold Traceui settings"""
    def __init__(self, lastDir=None, plotstyle=0):
        """Construct settings. Used only if configuration file has no Traceui settings."""
        if lastDir == None:
            self.lastDir = getProject().projectDir
        else:
            self.lastDir = lastDir
        self.plotstyle = plotstyle
        self.unplotLastTrace = True
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault( 'unplotLastTrace', True)

class Traceui(TraceuiForm, TraceuiBase):
    def __init__(self, penicons, config, parentname, graphicsViewDict, parent=None, lastDir=None):
        TraceuiBase.__init__(self,parent)
        TraceuiForm.__init__(self)
        self.penicons = penicons
        self.config = config
        self.configname = "Traceui."+parentname
        self.settings = self.config.get(self.configname+".settings",Settings(lastDir=lastDir, plotstyle=0))
        self.graphicsViewDict = graphicsViewDict

    def setupUi(self,MainWindow):
        """Setup the UI. Create the model and the view. Connect all the buttons."""
        TraceuiForm.setupUi(self,MainWindow)
        self.model = TraceModel([], self.penicons, self.graphicsViewDict)
        self.traceView.setModel(self.model)
        self.delegate = TraceComboDelegate(self.penicons)
        self.graphicsViewDelegate = ComboBoxDelegate()
        self.traceView.setItemDelegateForColumn(1,self.delegate) #This is for selecting which pen to use in the plot
        self.traceView.setItemDelegateForColumn(5,self.graphicsViewDelegate) #This is for selecting which plot to use
        self.traceView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection) #allows selecting more than one element in the view
        self.filter = KeyListFilter( [QtCore.Qt.Key_Delete] )
        self.filter.keyPressed.connect( self.onKey )
        self.traceView.installEventFilter(self.filter)
        self.clearButton.clicked.connect(self.onClear)
        self.saveButton.clicked.connect(self.onSave)
        self.removeButton.clicked.connect(self.onRemove)
        self.traceView.clicked.connect(self.onViewClicked)
        self.comboBoxStyle.setCurrentIndex(self.settings.plotstyle)
        self.comboBoxStyle.currentIndexChanged[int].connect(self.setPlotStyle)
        self.pushButtonApplyStyle.clicked.connect(self.onApplyStyle)
        self.openFileButton.clicked.connect(self.onOpenFile)
        self.plotButton.clicked.connect(self.onPlot)
        self.showOnlyLastButton.clicked.connect(self.onShowOnlyLast)
        self.selectAllButton.clicked.connect(self.traceView.selectAll)
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.unplotSettingsAction = QtGui.QAction( "Unplot last trace", self )
        self.unplotSettingsAction.setCheckable(True)
        self.unplotSettingsAction.setChecked( self.settings.unplotLastTrace)
        self.unplotSettingsAction.triggered.connect( self.onUnplotSetting )
        self.addAction( self.unplotSettingsAction )
        self.descriptionModel = TraceDescriptionTableModel() 
        self.descriptionTableView.setModel( self.descriptionModel )
        self.traceView.clicked.connect( self.onActiveTraceChanged )
        self.descriptionTableView.horizontalHeader().setStretchLastSection(True)   

    def onKey(self, key):
        if key==QtCore.Qt.Key_Delete:
            self.onRemove()

    def onActiveTraceChanged(self, modelIndex ):
        trace = self.model.getTrace(modelIndex)
        self.descriptionModel.setDescription(trace.trace.description)

    def onUnplotSetting(self, checked):
        self.settings.unplotLastTrace = checked
        
    def unplotLastTrace(self):
        return self.settings.unplotLastTrace

    def uniqueSelectedIndexes(self, useLastIfNoSelection=True, allowUnplotted=True):
        """From the selected elements, return one index from each row.
        
        Using one index from each row prevents executing an action multiple times on the same row.
        If useLastifNoSelection is true, then an index to the last trace added is used if there is
        no selection.
        """
        uniqueIndexes = []
        selectedIndexes = self.traceView.selectedIndexes()
        if (len(selectedIndexes) != 0):
            for traceIndex in selectedIndexes:
                if traceIndex.column() == 0 and (allowUnplotted or self.model.getTrace(traceIndex).isPlotted):
                    uniqueIndexes.append(traceIndex)
        if (len(uniqueIndexes) == 0) and useLastIfNoSelection:
            if len(self.tracePersistentIndexes) != 0:
                #Find and return the most recently added trace that still has a valid index (i.e. has not been removed).
                for ind in range(-1, -len(self.tracePersistentIndexes)-1, -1): 
                    if self.tracePersistentIndexes[ind].isValid():
                        return [QtCore.QModelIndex(self.tracePersistentIndexes[ind])]
                return None #If the for loop failed to find a valid index, return None. This happens if all traces have been deleted.
            else:
                return None #If there were no traces added, return None. This happens if no trace was ever added.
        return uniqueIndexes

    def addTrace(self, trace, pen, parentTrace=None):
        """Add a trace to the model, plot it, and resize the view appropriately."""
        PersistentIndex = self.model.addTrace(trace, parentTrace)
        self.tracePersistentIndexes.append(PersistentIndex)
        if parentTrace != None:
            parentIndex = self.model.createIndex(parentTrace.childNumber(), 0, parentTrace)
            if not self.traceView.isExpanded(parentIndex):
                self.traceView.expand(parentIndex)
        trace.plot(pen,self.settings.plotstyle)
                
    def resizeColumnsToContents(self):
        for column in range(self.model.columnCount()):
            self.traceView.resizeColumnToContents(column)

    def setPlotStyle(self,value):
        """Set the plot style to 'value'."""
        self.settings.plotstyle = value
        self.onApplyStyle()
        
    def onViewClicked(self,index):
        """If one of the editable columns is clicked, begin to edit it."""
        if index.column() in [1,3]:
            self.traceView.edit(index)

    def onPlot(self):
        """Execute when the plot button is clicked. Plot the selected traces."""
        selectedIndexes = self.uniqueSelectedIndexes()
        if selectedIndexes:
            for traceIndex in selectedIndexes:
                trace = self.model.getTrace(traceIndex)
                trace.plot(-1,self.settings.plotstyle)
                self.model.updateTrace(QtCore.QPersistentModelIndex(traceIndex))

    def onClear(self):
        """Execute when the clear button is clicked. Remove the selected plots from the trace.
        
           This leaves the traces in the list of traces (i.e. in the model and view)."""
        selectedIndexes = self.uniqueSelectedIndexes()
        if selectedIndexes:
            for traceIndex in selectedIndexes:
                trace = self.model.getTrace(traceIndex)
                if trace.curvePen != 0:
                    trace.plot(0)
                self.model.updateTrace(QtCore.QPersistentModelIndex(traceIndex))

    def onApplyStyle(self):
        """Execute when the apply style button is clicked. Change the selected traces to the new style."""
        selectedIndexes = self.uniqueSelectedIndexes()
        if selectedIndexes:
            for traceIndex in selectedIndexes:
                trace = self.model.getTrace(traceIndex)
                trace.plot(-2, self.settings.plotstyle)           

    def onSave(self):
        """Execute when the save button is clicked. Save (or resave) the selected traces."""
        selectedIndexes = self.uniqueSelectedIndexes()
        if selectedIndexes:
            for traceIndex in selectedIndexes:
                trace = self.model.getTrace(traceIndex)
                trace.trace.resave()

    def onRemove(self):
        """Execute when the remove button is clicked. Remove the selected traces from the model and view (but don't delete files)."""
        selectedIndexes = self.uniqueSelectedIndexes()
        if selectedIndexes:
            for traceIndex in selectedIndexes: #Loop through each trace and remove it
                trace = self.model.getTrace(traceIndex)
                parentIndex = self.model.parent(traceIndex)
                row = trace.childNumber()
                if trace.childCount() != 0: #If the trace has children, remove them first
                    while trace.childCount() != 0:
                        if trace.child(0).curvePen != 0:
                            trace.child(0).plot(0)
                        self.model.dropTrace(traceIndex, 0) #Repeatedly remove row zero until there are no more child traces
                if trace.curvePen != 0:
                    trace.plot(0)
                self.model.dropTrace(parentIndex, row)
        # remove invalid indices to prevent memory leak
        for ind in reversed(range( len(self.tracePersistentIndexes) )): 
            if not self.tracePersistentIndexes[ind].isValid():
                self.tracePersistentIndexes.pop(ind)

    def onOpenFile(self):
        """Execute when the open button is clicked. Open an existing trace file from disk."""
        fnames = QtGui.QFileDialog.getOpenFileNames(self, 'Open files', self.settings.lastDir)
        for fname in fnames:
            self.openFile(fname)

    def openFile(self, fname):
        trace = Trace.Trace()
        trace.filename = str(fname)
        self.settings.lastDir, trace.name = os.path.split(str(fname))
        trace.loadTrace(str(fname))
        plottedTraceList = list()
        for plotting in trace.tracePlottingList:
            name = plotting.windowName if plotting.windowName in self.graphicsViewDict else self.graphicsViewDict.keys()[0]
            plottedTrace = PlottedTrace(trace,self.graphicsViewDict[name]['view'],pens.penList,-1,tracePlotting=plotting, windowName=name)
            plottedTraceList.append(plottedTrace)
            self.addTrace(plottedTrace,-1)
        return plottedTraceList

    def saveConfig(self):
        """Execute when the UI is closed. Save the settings to the config file."""
        self.config[self.configname+".settings"] = self.settings
        
    def selectedPlottedTraces(self, defaultToLastLine=False, allowUnplotted=True):
        """Return a list of the selected traces."""
        selectedIndexes = self.uniqueSelectedIndexes(allowUnplotted=allowUnplotted)
        traceList = []
        if selectedIndexes:
            for traceIndex in selectedIndexes:
                trace = self.model.getTrace(traceIndex)
                traceList.append(trace)
        return traceList
    
    def onShowOnlyLast(self):
        pass
        
#if __name__ == '__main__':
#    import sys
#    import pyqtgraph as pg
#    from CoordinatePlotWidget import CoordinatePlotWidget
#    pg.setConfigOption('background', 'w') #set background to white
#    pg.setConfigOption('foreground', 'k') #set foreground to black
#    app = QtGui.QApplication(sys.argv)
#    penicons = pens.penicons().penicons()
#    plot = CoordinatePlotWidget()
#    ui = Traceui(penicons, {}, '', plot, lastDir = ' ')
#    ui.setupUi(ui)
#    addPlotButton = QtGui.QPushButton()
#    addAvgPlotButton = QtGui.QPushButton()
#    trace = Trace.Trace()
#    plottedTrace = PlottedTrace(trace, plot, pens.penList)
#    addPlotButton.clicked.connect(ui.addTrace(plottedTrace, pens.penList[0]))
#    window = QtGui.QWidget()
#    layout = QtGui.QVBoxLayout()
#    layout.addWidget(ui)
#    layout.addWidget(addPlotButton)
#    layout.addWidget(addAvgPlotButton)
#    layout.addWidget(plot)
#    window.setLayout(layout)
#    window.show()
#    sys.exit(app.exec_())