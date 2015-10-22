# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 18:40:30 2012

@author: pmaunz
"""
import logging
import os.path
from trace import TraceCollection
from trace import pens

from PyQt4 import QtGui, QtCore
import PyQt4.uic

from ProjectConfig.Project import getProject
from TraceModel import TraceComboDelegate
from TraceModel import TraceModel
from uiModules.CategoryTree import nodeTypes
from trace.PlottedTrace import PlottedTrace
from TraceDescriptionTableModel import TraceDescriptionTableModel
from uiModules.ComboBoxDelegate import ComboBoxDelegate
from uiModules.KeyboardFilter import KeyListFilter
from functools import partial

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
        self.collapseLastTrace = True
        self.expandNew = True
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault('unplotLastTrace', True)
        self.__dict__.setdefault('collapseLastTrace', True)
        self.__dict__.setdefault('expandNew', True)

class Traceui(TraceuiForm, TraceuiBase):
    """
    Class for the trace interface.
    Attributes:
        penicons (list[QtGui.QIcon]): icons to display available trace pens
        config (configshelve): configuration dictionary
        experimentName (str): name of experiment with which this Traceui is associated
        graphicsViewDict (dict): dict of available plot windows
    """
    def __init__(self, penicons, config, experimentName, graphicsViewDict, parent=None, lastDir=None):
        TraceuiBase.__init__(self,parent)
        TraceuiForm.__init__(self)
        self.penicons = penicons
        self.config = config
        self.configname = "Traceui."+experimentName
        self.settings = self.config.get(self.configname+".settings",Settings(lastDir=lastDir, plotstyle=0))
        self.graphicsViewDict = graphicsViewDict

    def setupUi(self,MainWindow):
        """Setup the UI. Create the model and the view. Connect all the buttons."""
        TraceuiForm.setupUi(self,MainWindow)
        self.model = TraceModel([], self.penicons, self.graphicsViewDict)
        self.traceView.setModel(self.model)
        self.delegate = TraceComboDelegate(self.penicons)
        self.graphicsViewDelegate = ComboBoxDelegate()
        self.traceView.setItemDelegateForColumn(self.model.column.plot, self.delegate) #This is for selecting which pen to use in the plot
        self.traceView.setItemDelegateForColumn(self.model.column.window, self.graphicsViewDelegate) #This is for selecting which plot to use
        self.traceView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection) #allows selecting more than one element in the view

        self.clearButton.clicked.connect(partial(self.onButton, self.clear))
        self.pushButtonApplyStyle.clicked.connect(partial(self.onButton, self.applyStyle))
        self.plotButton.clicked.connect(partial(self.onButton, self.plot))

        self.saveButton.clicked.connect(self.onSave)
        self.removeButton.clicked.connect(self.onRemove)

        self.openFileButton.clicked.connect(self.onOpenFile)
        self.comboBoxStyle.currentIndexChanged[int].connect(self.setPlotStyle)
        self.traceView.clicked.connect(self.onViewClicked)
        self.comboBoxStyle.setCurrentIndex(self.settings.plotstyle)

        self.showOnlyLastButton.clicked.connect(self.onShowOnlyLast)
        self.selectAllButton.clicked.connect(self.traceView.selectAll)
        self.collapseAllButton.clicked.connect(self.traceView.collapseAll)
        self.expandAllButton.clicked.connect(self.traceView.expandAll)

        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )

        self.unplotSettingsAction = QtGui.QAction( "Unplot last trace set", self )
        self.unplotSettingsAction.setCheckable(True)
        self.unplotSettingsAction.setChecked( self.settings.unplotLastTrace)
        self.unplotSettingsAction.triggered.connect( self.onUnplotSetting )
        self.addAction( self.unplotSettingsAction )

        self.collapseLastTraceAction = QtGui.QAction( "Collapse last trace set", self )
        self.collapseLastTraceAction.setCheckable(True)
        self.collapseLastTraceAction.setChecked( self.settings.collapseLastTrace)
        self.collapseLastTraceAction.triggered.connect(self.onCollapseLastTrace)
        self.addAction( self.collapseLastTraceAction )

        self.expandNewAction = QtGui.QAction( "Expand new traces", self )
        self.expandNewAction.setCheckable(True)
        self.expandNewAction.setChecked( self.settings.expandNew)
        self.expandNewAction.triggered.connect(self.onExpandNew)
        self.addAction( self.expandNewAction )

        self.descriptionModel = TraceDescriptionTableModel()
        self.descriptionTableView.setModel( self.descriptionModel )
        self.traceView.clicked.connect( self.onActiveTraceChanged )
        self.descriptionTableView.horizontalHeader().setStretchLastSection(True)

    def onButton(self, func):
        """Execute when a trace action button is clicked. Execute its function on the selected traces."""
        selectedIndexes = self.selectedRows()
        if selectedIndexes:
            for index in selectedIndexes:
                node = self.model.nodeFromIndex(index)
                if node.nodeType == nodeTypes.data:
                    trace = node.content
                    dataChanged = func(trace)
                    if dataChanged: self.model.modelChange(index)
                elif node.nodeType == nodeTypes.category:
                    dataChangedList=[]
                    for child in node.children:
                        trace = child.content
                        childIndex = self.model.indexFromNode(child)
                        dataChanged = func(trace)
                        dataChangedList.append(dataChanged)
                        if dataChanged: self.model.modelChange(childIndex)
                    if any(dataChangedList): self.model.modelChange(index)

    def selectedUniqueFilenames(self):
        """Get selected data nodes which have unique filenames"""
        selectedIndexes = self.selectedRows()
        nodesWithUniqueFilenames = []
        uniqueTraceCollections = []
        if selectedIndexes:
            for index in selectedIndexes:
                node = self.model.nodeFromIndex(index)
                if node.nodeType == nodeTypes.data:
                    if node.content.traceCollection not in uniqueTraceCollections:
                        uniqueTraceCollections.append(node.content.traceCollection)
                        nodesWithUniqueFilenames.append(node)
                elif node.nodeType == nodeTypes.category:
                    if node.children and node.children[0].content.traceCollection not in uniqueTraceCollections:
                        uniqueTraceCollections.append(node.children[0].content.traceCollection)
                        nodesWithUniqueFilenames.append(node.children[0])
        return nodesWithUniqueFilenames

    def onSave(self):
        """Save button is clicked. Save selected traces. If a trace has never been saved before, update model."""
        nodeList = self.selectedUniqueFilenames()
        for node in nodeList:
            alreadySaved = node.content.traceCollection.saved
            node.content.traceCollection.save()
            if not alreadySaved:
                self.model.onSaveUnsavedTrace(node)
                parentIndex = self.model.indexFromNode(node.parent)
                self.model.modelChange(parentIndex)

    def clear(self, trace):
        """Unplot trace."""
        if trace.curvePen != 0:
            trace.plot(0)
            return True

    def applyStyle(self, trace):
        """Apply style to trace."""
        trace.plot(-2, self.settings.plotstyle)
        return False

    def plot(self, trace):
        """plot trace"""
        trace.plot(-1,self.settings.plotstyle)
        return True

    def onRemove(self):
        """Execute when remove button is clicked. Remove selected traces from list (but don't delete files).."""
        self.traceView.onDelete()

    def onActiveTraceChanged(self, index):
        """Display trace description when a trace is clicked"""
        node = self.model.nodeFromIndex(index)
        if node.nodeType==nodeTypes.data:
            self.descriptionModel.setDescription(node.content.traceCollection.description)
        elif node.nodeType==nodeTypes.category:
            if node.children:
                self.descriptionModel.setDescription(node.children[0].content.traceCollection.description)

    def onUnplotSetting(self, checked):
        self.settings.unplotLastTrace = checked

    def onCollapseLastTrace(self, checked):
        self.settings.collapseLastTrace = checked

    def onExpandNew(self, checked):
        self.settings.expandNew = checked

    @QtCore.pyqtProperty(bool)
    def unplotLastTrace(self):
        return self.settings.unplotLastTrace

    @QtCore.pyqtProperty(bool)
    def collapseLastTrace(self):
        return self.settings.collapseLastTrace

    @QtCore.pyqtProperty(bool)
    def expandNew(self):
        return self.settings.expandNew

    def collapse(self, trace):
        """collapse node associated with trace"""
        node = self.model.nodeFromContent(trace)
        if node:
            index = self.model.indexFromNode(node.parent)
            self.traceView.collapse(index)

    def expand(self, trace):
        """expand node associated with trace"""
        node = self.model.nodeFromContent(trace)
        if node:
            index = self.model.indexFromNode(node.parent)
            self.traceView.expand(index)

    def selectedRows(self, useLastIfNoSelection=True, allowUnplotted=True):
        inputIndexes = self.traceView.selectionModel().selectedRows(0)
        outputIndexes = []
        for index in inputIndexes:
            trace = self.model.contentFromIndex(index)
            if allowUnplotted or trace.isPlotted:
                outputIndexes.append(index)
        if not outputIndexes and useLastIfNoSelection:
            if self.model.traceList != []:
                trace = self.model.traceList[-1]
                node = self.model.nodeFromContent(trace)
                index = self.model.indexFromNode(node)
                outputIndexes.append(index)
        return outputIndexes

    def selectedTraces(self, useLastIfNoSelection=False, allowUnplotted=True):
        """Return a list of the selected traces."""
        selectedIndexes = self.selectedRows(useLastIfNoSelection, allowUnplotted)
        return [self.model.contentFromIndex(index) for index in selectedIndexes]

    def addTrace(self, trace, pen):
        """Add a trace to the model and plot it."""
        self.model.addTrace(trace)
        trace.plot(pen,self.settings.plotstyle)
                
    def resizeColumnsToContents(self):
        for column in range(self.model.numColumns):
            self.traceView.resizeColumnToContents(column)

    def setPlotStyle(self,value):
        """Set the plot style to 'value'."""
        self.settings.plotstyle = value
        self.onApplyStyle()
        
    def onViewClicked(self,index):
        """If one of the editable columns is clicked, begin to edit it."""
        if self.model.isDataNode(index):
            if index.column() in [self.model.column.plot, self.model.column.window, self.model.column.comment]:
                self.traceView.edit(index)
        elif index.column()==self.model.column.comment:
            self.traceView.edit(index)

    def onOpenFile(self):
        """Execute when the open button is clicked. Open an existing trace file from disk."""
        fnames = QtGui.QFileDialog.getOpenFileNames(self, 'Open files', self.settings.lastDir)
        for fname in fnames:
            self.openFile(fname)

    def openFile(self, fname):
        trace = TraceCollection.TraceCollection()
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