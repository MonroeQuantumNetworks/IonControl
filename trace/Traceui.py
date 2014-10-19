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

from gui import ProjectSelection
from TraceTreeModel import TraceComboDelegate
from TraceTreeModel import TraceTreeModel
from trace.PlottedTrace import PlottedTrace
from TraceDescriptionTableModel import TraceDescriptionTableModel
from uiModules.ComboBoxDelegate import ComboBoxDelegate

TraceuiForm, TraceuiBase = PyQt4.uic.loadUiType(r'ui\TraceTreeui.ui')

class Settings:
    """Class to hold Traceui settings"""
    def __init__(self, lastDir=None, plotstyle=0):
        """Construct settings. Used only if configuration file has no Traceui settings."""
        if lastDir == None:
            self.lastDir = ProjectSelection.configDir()
        else:
            self.lastDir = lastDir
        self.plotstyle = plotstyle
        self.unplotLastTrace = True
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault( 'unplotLastTrace', True)

class Traceui(TraceuiForm, TraceuiBase):

    """
    Class for the trace interface. It displays the plotted traces (using a tree
    view, and the model in TraceTreeModel), and allows for selecting which are 
    plotted, in addition to deleting them, adding them, saving them, etc.
    
    instance variables:
    penicons -- the list of icons available for the different traces
    config -- configuration data, saved in pickled form to file
    configname -- the name to use in the config file
    settings -- the plot settings: plot style and last used directory
    graphicsView -- the actual plot window, only used for opened files, otherwise the graphics view in the plotted trace is used
    
    methods:
    __init__(self, penicons, config, parentname, graphicsView, parent=None, lastDir=None):
        construct the Traceui and set instance variables. It inherits from a Qt Designer file.
    setupUi(self, MainWindow): setup the UI.
    uniqueSelectedIndexes(self): return from the selected elements of the tree one index for each row.
    addTrace(self, trace, pen): add 'trace' to the plot and the model, using the specified pen
    setPlotStyle(self,value): Set the plot style to 'value'
    onViewClicked(self, index): Execute when view is clicked
    onPlot(self): Execute when 'plot' is clicked
    onClear(self): Execute when 'clear' is clicked
    onApplyStyle(self): Execute when 'apply style' is clicked
    onSave(self): Execute when 'save' is clicked
    onOpenFile(self): Execute when 'open file' is clicked
    onShredder(self): Execute when 'shredder' is clicked
    onRemove(self): Execute when 'remove' is clicked
    warningMessage(self): Pop up a warning message to confirm deletion
    onCLose(self): Execute when UI is closed
    """

    def __init__(self, penicons, config, parentname, graphicsViewDict, parent=None, lastDir=None):
        """Construct the trace user interface, and set instance variables. Inherits from Qt Designer file."""
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
        self.model = TraceTreeModel([], self.penicons, self.graphicsViewDict)
        self.tracePersistentIndexes = []
        self.traceTreeView.setModel(self.model)
        self.delegate = TraceComboDelegate(self.penicons)
        self.graphicsViewDelegate = ComboBoxDelegate()
        self.traceTreeView.setItemDelegateForColumn(1,self.delegate) #This is for selecting which pen to use in the plot
        self.traceTreeView.setItemDelegateForColumn(5,self.graphicsViewDelegate) #This is for selecting which pen to use in the plot
        self.traceTreeView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection) #allows selecting more than one element in the view
        self.clearButton.clicked.connect(self.onClear)
        self.saveButton.clicked.connect(self.onSave)
        self.removeButton.clicked.connect(self.onRemove)
        self.traceTreeView.clicked.connect(self.onViewClicked)
        self.comboBoxStyle.setCurrentIndex(self.settings.plotstyle)
        self.comboBoxStyle.currentIndexChanged[int].connect(self.setPlotStyle)
        self.pushButtonApplyStyle.clicked.connect(self.onApplyStyle)
        self.openFileButton.clicked.connect(self.onOpenFile)
        self.plotButton.clicked.connect(self.onPlot)
        self.shredderButton.clicked.connect(self.onShredder)
        self.selectAllButton.clicked.connect(self.traceTreeView.selectAll)
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.unplotSettingsAction = QtGui.QAction( "Unplot last trace", self )
        self.unplotSettingsAction.setCheckable(True)
        self.unplotSettingsAction.setChecked( self.settings.unplotLastTrace)
        self.unplotSettingsAction.triggered.connect( self.onUnplotSetting )
        self.addAction( self.unplotSettingsAction )
        self.descriptionModel = TraceDescriptionTableModel() 
        self.descriptionTableView.setModel( self.descriptionModel )
        self.traceTreeView.clicked.connect( self.onActiveTraceChanged )
        self.descriptionTableView.horizontalHeader().setStretchLastSection(True)   

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
        selectedIndexes = self.traceTreeView.selectedIndexes()
        if (len(selectedIndexes) != 0):
            for traceIndex in selectedIndexes:
                if traceIndex.column() == 0 and (allowUnplotted or self.model.getTrace(traceIndex).isPlotted()):
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
            if not self.traceTreeView.isExpanded(parentIndex):
                self.traceTreeView.expand(parentIndex)
        trace.plot(pen,self.settings.plotstyle)
                
    def resizeColumnsToContents(self):
        for column in range(self.model.columnCount()):
            self.traceTreeView.resizeColumnToContents(column)

    def setPlotStyle(self,value):
        """Set the plot style to 'value'."""
        self.settings.plotstyle = value
        self.onApplyStyle()
        
    def onViewClicked(self,index):
        """If one of the editable columns is clicked, begin to edit it."""
        if index.column() in [1,3]:
            self.traceTreeView.edit(index)

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

    def onShredder(self):
        """Execute when the shredder button is clicked. Remove the selected plots, and delete the files from disk.
        
           A warning message appears first, asking to confirm deletion. Traces with children cannot be deleted from disk until their children are deleted."""
        logger = logging.getLogger(__name__)
        selectedIndexes = self.uniqueSelectedIndexes()
        if selectedIndexes:
            warningResponse = self.warningMessage("Are you sure you want to delete the selected trace file(s) from disk?", "Press OK to continue with deletion.")
            if warningResponse == QtGui.QMessageBox.Ok:
                for traceIndex in selectedIndexes:
                    trace = self.model.getTrace(traceIndex)
                    parentIndex = self.model.parent(traceIndex)
                    row = trace.childNumber()
                    if trace.childCount() == 0:
                        if trace.curvePen != 0:
                            trace.plot(0)
                        try:
                            trace.trace.deleteFile()
                        except WindowsError:
                            pass   # we ignore if the file cannot be found
                        self.model.dropTrace(parentIndex, row)
                    else:
                        logger.error( "trace has children, please delete them first." )

    def warningMessage(self, warningText, informativeText):
        """Pop up a warning message. Return the response."""
        warningMessage = QtGui.QMessageBox()
        warningMessage.setText(warningText)
        warningMessage.setInformativeText(informativeText)
        warningMessage.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
        return warningMessage.exec_()        

    def onRemove(self):
        """Execute when the remove button is clicked. Remove the selected traces from the model and view (but don't delete files)."""
        selectedIndexes = self.uniqueSelectedIndexes()
        if selectedIndexes:
            thereAreParents = False
            for traceIndex in selectedIndexes: #Loop through selection and find out if any of the traces have children
                if self.model.getTrace(traceIndex).childCount() != 0:
                    thereAreParents = True
                    warningResponse = self.warningMessage("Some of the selected traces have child traces. Removal will also remove the child traces.", "Press OK to proceed with removal.")
                    break
            if (not thereAreParents) or (warningResponse == QtGui.QMessageBox.Ok):
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
            trace = Trace.Trace()
            trace.filename = str(fname)
            self.settings.lastDir, trace.name = os.path.split(str(fname))
            trace.loadTrace(str(fname))
            for plotting in trace.tracePlottingList:
                name = plotting.windowName if plotting.windowName in self.graphicsViewDict else self.graphicsViewDict.keys()[0]
                self.addTrace(PlottedTrace(trace,self.graphicsViewDict[name]['view'],pens.penList,-1,tracePlotting=plotting, windowName=name),-1)

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