# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 18:40:30 2012

@author: pmaunz
"""
import logging
import os.path
from trace.TraceCollection import TraceCollection
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
from dateutil.tz import tzlocal

uipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\Traceui.ui')
TraceuiForm, TraceuiBase = PyQt4.uic.loadUiType(uipath)

class Settings:
    """
    Class to hold Traceui settings

    Attributes:
        lastDir (str): last directory from which traces were opened
        plotStyle (int): style to use for plotting new traces (i.e. lines, points, etc.)
        unplotLastTrace (bool): whether last trace should be unplotted when new trace is created
        collapseLastTrace (bool): whether last set of traces should be collapsed in tree when new trace set is created
        expandNew (bool): whether new trace sets should be expanded when they are created
    """
    def __init__(self, lastDir=None, plotstyle=0):
        if lastDir == None:
            self.lastDir = getProject().projectDir
        else:
            self.lastDir = lastDir
        self.plotstyle = plotstyle
        self.unplotLastTrace = True
        self.collapseLastTrace = False
        self.expandNew = True
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault('unplotLastTrace', True)
        self.__dict__.setdefault('collapseLastTrace', False)
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
    openMeasurementLog = QtCore.pyqtSignal(list) #list of strings with trace creation dates
    def __init__(self, penicons, config, experimentName, graphicsViewDict, parent=None, lastDir=None, hasMeasurementLog=False, highlightUnsaved=False):
        TraceuiBase.__init__(self,parent)
        TraceuiForm.__init__(self)
        self.penicons = penicons
        self.config = config
        self.configname = "Traceui."+experimentName
        self.settings = self.config.get(self.configname+".settings",Settings(lastDir=lastDir, plotstyle=0))
        self.graphicsViewDict = graphicsViewDict
        self.hasMeasurementLog = hasMeasurementLog
        self.highlightUnsaved = highlightUnsaved

    def setupUi(self,MainWindow):
        """Setup the UI. Create the model and the view. Connect all the buttons."""
        TraceuiForm.setupUi(self,MainWindow)
        self.model = TraceModel([], self.penicons, self.graphicsViewDict, highlightUnsaved=self.highlightUnsaved)
        self.traceView.setModel(self.model)
        self.delegate = TraceComboDelegate(self.penicons)
        self.graphicsViewDelegate = ComboBoxDelegate()
        self.traceView.setItemDelegateForColumn(self.model.column.pen, self.delegate) #This is for selecting which pen to use in the plot
        self.traceView.setItemDelegateForColumn(self.model.column.window, self.graphicsViewDelegate) #This is for selecting which plot to use
        self.traceView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection) #allows selecting more than one element in the view

        self.clearButton.clicked.connect(partial(self.onClearOrPlot, 'clear'))
        self.plotButton.clicked.connect(partial(self.onClearOrPlot, 'plot'))
        self.pushButtonApplyStyle.clicked.connect(self.onApplyStyle)
        self.saveButton.clicked.connect(self.onSave)
        self.removeButton.clicked.connect(self.traceView.onDelete)
        self.openFileButton.clicked.connect(self.onOpenFile)
        self.comboBoxStyle.currentIndexChanged[int].connect(self.setPlotStyle)
        self.traceView.clicked.connect(self.onViewClicked)
        self.comboBoxStyle.setCurrentIndex(self.settings.plotstyle)

        self.showOnlyLastButton.clicked.connect(self.onShowOnlyLast)
        self.selectAllButton.clicked.connect(self.traceView.selectAll)
        self.collapseAllButton.clicked.connect(self.traceView.collapseAll)
        self.expandAllButton.clicked.connect(self.traceView.expandAll)
        self.traceView.selectionModel().selectionChanged.connect(self.onActiveTraceChanged)
        self.measurementLogButton.clicked.connect(self.onMeasurementLog)

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
        self.measurementLogButton.setVisible(self.hasMeasurementLog)

    def onMeasurementLog(self):
        """Execute when open measurement log is clicked. Emit signal containing list of trace creation keys selected."""
        selectedTopNodes = self.traceView.selectedTopNodes()
        traceCreationList = []
        for topNode in selectedTopNodes:
            dataNode = self.model.getFirstDataNode(topNode)
            if dataNode:
                traceCreation = str(dataNode.content.traceCollection.traceCreation)
                traceCreationList.append(traceCreation)
        self.openMeasurementLog.emit(traceCreationList)

    def onClearOrPlot(self, changeType):
        """Execute when clear or plot action buttons are clicked."""
        leftCol=self.model.column.name
        rightCol=self.model.column.pen
        selectedNodes = self.traceView.selectedNodes()
        uniqueSelectedNodes = [node for node in selectedNodes if node.parent not in selectedNodes]
        for node in uniqueSelectedNodes:
            dataNodes = self.model.getDataNodes(node)
            for dataNode in dataNodes:
                plottedTrace = dataNode.content
                changed=False
                if changeType=='clear' and plottedTrace.curvePen!=0:
                    plottedTrace.plot(0)
                    changed=True
                elif changeType=='plot' and plottedTrace.curvePen==0:
                    plottedTrace.plot(-1,self.settings.plotstyle)
                    changed=True
                if changed:
                    self.model.traceModelDataChanged.emit(str(plottedTrace.traceCollection.traceCreation), 'isPlotted', '')
                    leftInd = self.model.indexFromNode(dataNode, col=leftCol)
                    rightInd = self.model.indexFromNode(dataNode, col=rightCol)
                    self.model.dataChanged.emit(leftInd, rightInd)
                    self.model.emitParentDataChanged(dataNode, leftCol, rightCol)

    def onApplyStyle(self):
        """Execute when apply style button is clicked. Changed style of selected traces."""
        selectedNodes = self.traceView.selectedNodes()
        uniqueSelectedNodes = [node for node in selectedNodes if node.parent not in selectedNodes]
        for node in uniqueSelectedNodes:
            dataNodes = self.model.getDataNodes(node)
            for dataNode in dataNodes:
                trace = dataNode.content
                trace.plot(-2, self.settings.plotstyle)

    def onSave(self):
        """Save button is clicked. Save selected traces. If a trace has never been saved before, update model."""
        leftCol = 0
        rightCol = self.model.numColumns-1
        selectedTopNodes = self.traceView.selectedTopNodes()
        for node in selectedTopNodes:
            dataNode=self.model.getFirstDataNode(node)
            if dataNode:
                traceCollection = dataNode.content.traceCollection
                alreadySaved = traceCollection.saved
                traceCollection.save()
                if not alreadySaved:
                    self.model.onSaveUnsavedTrace(dataNode)
                    self.model.traceModelDataChanged.emit(str(traceCollection.traceCreation), 'filename', traceCollection.filename)
                    if dataNode is node:
                        topLeftInd = self.model.indexFromNode(dataNode, leftCol)
                        bottomRightInd = self.model.indexFromNode(dataNode, rightCol)
                    else:
                        topLeftInd = self.model.indexFromNode(dataNode.parent.children[0], leftCol)
                        bottomRightInd = self.model.indexFromNode(dataNode.parent.children[-1], rightCol)
                    self.model.dataChanged.emit(topLeftInd, bottomRightInd)
                    self.model.emitParentDataChanged(dataNode, leftCol, rightCol)

    def onActiveTraceChanged(self):
        """Display trace creation/finalized date/time when a trace is selected"""
        nodes=self.traceView.selectedNodes()
        dataNode=self.model.getFirstDataNode(nodes[0]) if nodes else None
        if dataNode:
            description = dataNode.content.traceCollection.description
            traceCreation = description.get("traceCreation")
            traceFinalized = description.get("traceFinalized")
            if traceCreation:
                traceCreationLocal = traceCreation.astimezone(tzlocal()) #use local time
                self.createdDateLabel.setText(traceCreationLocal.strftime('%Y-%m-%d'))
                self.createdTimeLabel.setText(traceCreationLocal.strftime('%H:%M:%S'))
            else:
                self.createdDateLabel.setText('')
                self.createdTimeLabel.setText('')
            if traceFinalized:
                traceFinalizedLocal = traceFinalized.astimezone(tzlocal()) #use local time
                self.finalizedDateLabel.setText(traceFinalizedLocal.strftime('%Y-%m-%d'))
                self.finalizedTimeLabel.setText(traceFinalizedLocal.strftime('%H:%M:%S'))
            else:
                self.finalizedDateLabel.setText('')
                self.finalizedTimeLabel.setText('')
        else:
                self.createdDateLabel.setText('')
                self.createdTimeLabel.setText('')
                self.finalizedDateLabel.setText('')
                self.finalizedTimeLabel.setText('')

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

    def selectedRowIndexes(self, useLastIfNoSelection=True, allowUnplotted=True):
        """Return selected row indexes, modified according to the boolean controls"""
        inputIndexes = self.traceView.selectedRowIndexes()
        outputIndexes = []
        for index in inputIndexes:
            trace = self.model.contentFromIndex(index)
            if allowUnplotted or trace.isPlotted:
                outputIndexes.append(index)
        if not outputIndexes and useLastIfNoSelection:
            node = self.model.getLastDataNode(self.model.root)
            if node:
                index = self.model.indexFromNode(node)
                outputIndexes.append(index)
        return outputIndexes

    def selectedTraces(self, useLastIfNoSelection=False, allowUnplotted=True):
        """Return a list of the selected traces."""
        selectedIndexes = self.selectedRowIndexes(useLastIfNoSelection, allowUnplotted)
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
            if index.column() in [self.model.column.pen, self.model.column.window, self.model.column.comment]:
                self.traceView.edit(index)
        elif index.column()==self.model.column.comment:
            self.traceView.edit(index)

    def onOpenFile(self):
        """Execute when the open button is clicked. Open an existing trace file from disk."""
        fnames = QtGui.QFileDialog.getOpenFileNames(self, 'Open files', self.settings.lastDir)
        for fname in fnames:
            self.openFile(fname)

    def openFile(self, filename):
        filename = str(filename)
        traceCollection = TraceCollection()
        traceCollection.filename = filename
        traceCollection.filepath, traceCollection.fileleaf = os.path.split(filename)
        self.settings.lastDir = traceCollection.filepath
        traceCollection.name = traceCollection.fileleaf
        traceCollection.saved = True
        traceCollection.loadTrace(filename)
        plottedTraceList = list()
        for plotting in traceCollection.tracePlottingList:
            windowName = plotting.windowName if plotting.windowName in self.graphicsViewDict else self.graphicsViewDict.keys()[0]
            name = plotting.name
            plottedTrace = PlottedTrace(traceCollection, self.graphicsViewDict[windowName]['view'], pens.penList, -1, tracePlotting=plotting, windowName=windowName, name=name)
            plottedTrace.category = traceCollection.fileleaf
            plottedTraceList.append(plottedTrace)
            self.addTrace(plottedTrace,-1)
        if self.expandNew:
            self.expand(plottedTraceList[0])
        self.resizeColumnsToContents()
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