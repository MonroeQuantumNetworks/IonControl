# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 18:40:30 2012

@author: pmaunz
"""
import PyQt4.uic
from TraceTreeModel import TraceComboDelegate, TraceTreeModel
import pens
from PyQt4 import QtGui, QtCore
import Trace
import os.path
import ProjectSelection
from PlottedTrace import PlottedTrace

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
    graphicsView -- the actual plot window
    
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

    def __init__(self, penicons, config, parentname, graphicsView, parent=None, lastDir=None):
        """Construct the trace user interface, and set instance variables. Inherits from Qt Designer file."""
        TraceuiBase.__init__(self,parent)
        TraceuiForm.__init__(self)
        self.penicons = penicons
        self.config = config
        self.configname = "Traceui."+parentname
        self.settings = self.config.get(self.configname+".settings",Settings(lastDir=lastDir, plotstyle=0))
        self.graphicsView = graphicsView

    def setupUi(self,MainWindow):
        """Setup the UI. Create the model and the view. Connect all the buttons."""
        TraceuiForm.setupUi(self,MainWindow)
        self.model = TraceTreeModel([], self.penicons)    
        self.traceTreeView.setModel(self.model)
        self.traceTreeView.setItemDelegateForColumn(1,TraceComboDelegate(self.penicons)) #This is for selecting which pen to use in the plot
        self.traceTreeView.setSelectionMode(QtGui.QAbstractItemView.MultiSelection) #allows selecting more than one element in the view
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

    def uniqueSelectedIndexes(self):
        """From the selected elements, return one index from each row.
        
        This prevents executing an action multiple times on the same row."""
        uniqueRowIndexes = []
        uniqueRows = []
        for traceIndex in self.traceTreeView.selectedIndexes():
            row = traceIndex.row()
            if row not in uniqueRows:
                uniqueRows.append(row)
                uniqueRowIndexes.append(traceIndex)
        return uniqueRowIndexes

    def addTrace(self,trace,pen):
        """Add a trace to the model, plot it, and resize the view appropriately."""
        self.model.addTrace(trace)
        trace.plot(pen,self.settings.plotstyle)
        numcols = self.model.columnCount()
        for column in range(numcols):
            self.traceTreeView.resizeColumnToContents(column)

    def setPlotStyle(self,value):
        """Set the plot style to 'value'."""
        self.settings.plotstyle = value
        
    def onViewClicked(self,index):
        """If one of the editable columns is clicked, begin to edit it."""
        if index.column() in [1,3]:
            self.traceTreeView.edit(index)

    def onPlot(self):
        """Execute when the plot button is clicked. Plot the selected traces."""
        selectedIndexes = self.uniqueSelectedIndexes()
        for traceIndex in selectedIndexes:
            trace = self.model.getTrace(traceIndex)
            trace.plot(-1,self.settings.plotstyle)
            self.model.updateTrace(QtCore.QPersistentModelIndex(traceIndex))

    def onClear(self):
        """Execute when the clear button is clicked. Remove the selected plots from the trace.
        
           This leaves the traces in the list of traces (i.e. in the model and view)."""
        selectedIndexes = self.uniqueSelectedIndexes()
        for traceIndex in selectedIndexes:
            trace = self.model.getTrace(traceIndex)
            if trace.curvePen != 0:
                trace.plot(0)
            self.model.updateTrace(QtCore.QPersistentModelIndex(traceIndex))

    def onApplyStyle(self):
        """Execute when the apply style button is clicked. Change the selected traces to the new style."""
        selectedIndexes = self.uniqueSelectedIndexes()
        for traceIndex in selectedIndexes:
            trace = self.model.getTrace(traceIndex)
            trace.plot(-2, self.settings.plotstyle)           

    def onSave(self):
        """Execute when the save button is clicked. Save (or resave) the selected traces."""
        selectedIndexes = self.uniqueSelectedIndexes()
        for traceIndex in selectedIndexes:
            trace = self.model.getTrace(traceIndex)
            trace.trace.resave()

    def onShredder(self):
        """Execute when the shredder button is clicked. Remove the selected plots, and delete the files from disk.
        
           A warning message appears first, asking to confirm deletion. Traces with children cannot be deleted
           unless their children are deleted first."""
        warningResponse = self.warningMessage()
        if warningResponse == QtGui.QMessageBox.Ok:
            selectedIndexes = self.uniqueSelectedIndexes()
            for traceIndex in selectedIndexes:
                trace = self.model.getTrace(traceIndex)
                parentIndex = self.model.parent(traceIndex)
                row = trace.childNumber()
                if trace.childCount() == 0:
                    if trace.curvePen != 0:
                        trace.plot(0)
                    trace.trace.deleteFile()
                    self.model.dropTrace(parentIndex, row)
                else:
                    print "trace has children, please delete them first."

    def warningMessage(self):
        """Pop up a warning message asking to confirm deletion. Return the response."""
        warningMessage = QtGui.QMessageBox()
        warningMessage.setText("Are you sure you want to delete the selected trace file(s) from disk?")
        warningMessage.setInformativeText("Press OK to continue with deletion.")
        warningMessage.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
        return warningMessage.exec_()        

    def onRemove(self):
        """Execute when the remove button is clicked. Remove the selected traces from the model and view (but don't delete files)."""
        selectedIndexes = self.uniqueSelectedIndexes()
        for traceIndex in selectedIndexes:
            trace = self.model.getTrace(traceIndex)
            parentIndex = self.model.parent(traceIndex)
            row = trace.childNumber()
            if trace.curvePen != 0:
                trace.plot(0)
            self.model.dropTrace(parentIndex, row)

    def onOpenFile(self):
        """Execute when the open button is clicked. Open an existing trace file from disk."""
        fnames = QtGui.QFileDialog.getOpenFileNames(self, 'Open files', self.settings.lastDir)
        for fname in fnames:
            trace = Trace.Trace()
            trace.filename = str(fname)
            self.settings.lastDir, trace.name = os.path.split(str(fname))
            trace.loadTrace(str(fname))
            self.addTrace(PlottedTrace(trace,self.graphicsView,pens.penList,-1),-1)

    def onClose(self):
        """Execute when the UI is closed. Save the settings to the config file."""
        self.config[self.configname+".settings"] = self.settings

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