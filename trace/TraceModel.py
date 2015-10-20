# -*- coding: utf-8 -*-
"""
Created on Wed Jan 02 09:53:48 2013

@author: Jonathan Mizrahi

This is the model used with TraceTreeView to view the list of traces in a tree.
"""

from functools import partial

from PyQt4 import QtCore, QtGui
import sip

from PlottedTrace import PlottedTrace


api2 = sip.getapi("QVariant")==2

class TraceComboDelegate(QtGui.QItemDelegate):
    
    """
    This class is a delegate of the trace tree view, responsible for the combo box editor in the trace tree.
    
    The combo box editor is used to select which pen to use in drawing the
    trace on the plot. The available pen icons to use are in the array penicons,
    which is determined when the delegate is constructed.
    
    methods:
    __init__: constructor for TraceComboDelegate. Construct the parent, and set the penicons array.
    createEditor: create the combo box editor, and add in all the icons.
    
    The following methods are required reimplementations if QItemDelegate methods:
    createEditor(self,parent, option, index): Create the combo box editor used to select the pen icon.
    setEditorData(self,editor, index): Supply data to the editor from the model.
    setModelData(self,editor, model, index): Supply data to the model from the editor.
    updateEditorGeometry(self,editor, option, index): Set the size of the combo box appropriately.
    """    
    
    def __init__(self, penicons):
        """Construct the TraceComboDelegate object, and set the penicons array."""
        QtGui.QItemDelegate.__init__(self)
        self.penicons = penicons        
        
    def createEditor(self,parent, option, index ):
        """Required. Create the combo box editor used to select pen icon.
        
           The for loop adds each pen icon into the combo box."""
        editor = QtGui.QComboBox(parent);
        #for icon, string in zip(self.penicons, ["{0}".format(i) for i in range(0,len(self.penicons))] ):
        for icon, string in zip(self.penicons, ['']*len(self.penicons) ):
            editor.addItem( icon, string )
        return editor

    def setEditorData(self,editor, index):
        """Required. Supply data to the editor from the model."""
        value = index.model().data(index, QtCore.Qt.EditRole) 
        editor.setCurrentIndex(value)
        
    def setModelData(self,editor, model, index):
        """Required. Supply data to the model from the editor."""
        value = editor.currentIndex()
        model.setData(index, value, QtCore.Qt.EditRole)
         
    def updateEditorGeometry(self,editor, option, index ):
        """Required. Set the size of the combo box appropriately."""
        editor.setGeometry(option.rect)
    
class TraceModel(QtCore.QAbstractTableModel):
    
    """
    This class is the data model used to displaying the traces in a tree.
    
    instance variables:
    penicons -- the list of icons available for the different traces
    rootTrace -- This is an empty PlottedTrace object. It is the parent of all the top level
                 traces. It contains a list of all its child traces, which in turn contain
                 a list of their child traces, etc. In this way, all the traces are stored
                 in the model.

    methods:
    __init__(self, TraceList, penicons, parent=None, *args): Construct the TraceModel
    getTrace(self, traceIndex): Return the trace at the given index.
    addTrace(self,trace,parentIndex=QtCore.QModelIndex()): Add a new trace to the list of traces.
    dropTrace(self, parentTraceIndex, row): Remove a trace from the list of traces.
    updateTrace(self, traceIndex): Emit the signal to update the trace.
    
    The following methods are required reimplementations of QAbstractItemModel methods (they are used by
    the view to display the data):
    index(self, row, column, parentIndex=QtCore.QModelIndex()): Return the index at the row, column, and parentIndex.
    parent(self, traceIndex): Return the index of the parent of traceIndex.
    rowCount(self, parentIndex=QtCore.QModelIndex()): Return the number of rows beneath the given parent.
    columnCount(self, parent=QtCore.QModelIndex()): Return the number of columns.
    data(self, traceIndex, role): Return the data from the model to the view at the given index for the given role.
    setData(self, traceIndex, value, role): Set the data in the model from the value set in the view.
    flags(self, index): Return the flags for the given index.
    headerData(self, section, orientation, role): Return the headers for each column.
    setData(self, traceIndex, value, role): Set the data in the model from the value set in the view.
    """
    
    def __init__(self, traceList, penicons, graphicsViewDict, parent=None, *args): 
        """
        Construct the TraceModel.
        
        traceList: The initial list of traces (typically empty)
        penicons: The list of available icons for the different traces
        """
        super(TraceModel, self).__init__(parent)
        self.penicons = penicons
        self.traceList = traceList
        self.graphicsViewDict = graphicsViewDict
        self.flagsLookup = { 0: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled,
                 1: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
                 3: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
                 5: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
                 }
        self.dataLookup =  { (QtCore.Qt.DisplayRole,2): lambda trace: ", ".join([str(trace.trace.name), str(trace.name)]),
                 (QtCore.Qt.DisplayRole,3): lambda trace: trace.trace.comment,
                 (QtCore.Qt.DisplayRole,4): lambda trace: getattr( trace.trace, 'fileleaf', None ),
                 (QtCore.Qt.DisplayRole,5): lambda trace: trace.windowName,
                 (QtCore.Qt.EditRole,5): lambda trace: trace.windowName,
                 (QtCore.Qt.CheckStateRole,0): lambda trace: QtCore.Qt.Checked if trace.curvePen > 0 else QtCore.Qt.Unchecked,
                 (QtCore.Qt.DecorationRole,1): lambda trace: QtGui.QIcon(self.penicons[trace.curvePen]) if hasattr(trace, 'curve') and trace.curve is not None else None,
                 (QtCore.Qt.BackgroundColorRole,1): lambda trace: QtGui.QColor(QtCore.Qt.white) if not (hasattr(trace, 'curve') and trace.curve is not None) else None,
                 (QtCore.Qt.EditRole,1): lambda trace: trace.curvePen,
                 (QtCore.Qt.EditRole,3): lambda trace: trace.trace.comment
                 }
                
    def choice(self, index):
        if index.column()==5:
            return self.graphicsViewDict.keys()
        return []

    def getTrace(self, traceIndex):
        """Return the trace at the given index. If the index is invalid, return the root trace."""
        if not traceIndex.isValid():
            return self.rootTrace
        return traceIndex.internalPointer()

    def rowCount(self, parentIndex=QtCore.QModelIndex()):
        """Required. Return the number of rows beneath the given parent."""
        parentTrace = self.getTrace(parentIndex)
        if parentIndex.column() > 0:
            return 0
        return parentTrace.childCount()

    def columnCount(self, parent=QtCore.QModelIndex()): 
        """Required. Return the number of columns."""
        return 6

    def data(self, traceIndex, role):
        """Required. Return the data at the given index for the given role."""
        trace = self.getTrace(traceIndex)
        if trace == self.rootTrace:
            return None
        col = traceIndex.column()
        return self.dataLookup.get((role,col), lambda trace: None)(trace)

    def flags(self, index):
        """Required. Return the flags for the given index."""
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        col = index.column()
        return self.flagsLookup.get(col, QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

    headerLookup = [None, 'Plot   ', 'Name', 'Comment', 'Filename','Window']
    def headerData(self, section, orientation, role):
        """Required. Return the headers for each column."""
        if (role == QtCore.Qt.DisplayRole) and (orientation == QtCore.Qt.Horizontal): 
            return self.headerLookup[section]
        return None #QtCore.QVariant()

    def setValue(self, index, value):
        self.setData(index, value, QtCore.Qt.EditRole )

    def setData(self, traceIndex, value, role):
        """Required. Set the data in the model from the value set in the view."""
        row = traceIndex.row()
        col = traceIndex.column()
        trace = self.getTrace(traceIndex)
        
        if (role == QtCore.Qt.CheckStateRole) and (col == 0):
            #If the checkbox is checked, replot.
            if (value == QtCore.Qt.Unchecked) and (trace.curvePen > 0):
                trace.plot(0)
            elif len(trace.trace.x) != 0: #Make sure the x array isn't empty before trying to plot
                trace.plot(-1)
            leftInd = self.createIndex(row, 0, trace)
            rightInd = self.createIndex(row, 4, trace)
            self.dataChanged.emit(leftInd, rightInd)
            return True      

        elif (role == QtCore.Qt.EditRole) and (col == 1):
            if len(trace.trace.x) != 0: #Make sure the x array isn't empty before trying to plot
                trace.plot(value)
            return True

        elif (role == QtCore.Qt.EditRole) and (col == 3):
            #If the comment changes, change it and resave the file.
            comment = value if api2 else str(value.toString())
            if not comment == trace.trace.comment:
                trace.trace.comment = comment
                trace.trace.resave()
            return True
        
        elif (role == QtCore.Qt.EditRole) and (col==5):
            name = str(value)
            if name in self.graphicsViewDict:
                trace.setGraphicsView( self.graphicsViewDict[name]['view'], name )
        
        else:
            return False
            
    def addTrace(self,trace):
        """Add a new trace to the list of traces."""
        self.beginInsertRows(QtCore.QModelIndex, self.rowCount(), self.rowCount())
        self.traceList.append(trace)
        #For the callback, we use a persistent index, so that when the trace "calls"
        #that its data is changed, the index it calls remains valid.
        trace.trace.filenameChanged.subscribe( partial(self.updateTrace, persistentIndex) )
        self.endInsertRows()
        return persistentIndex

    def dropTrace(self, parentTraceIndex, row):
        """Remove a trace from the list of traces."""
        self.beginRemoveRows(parentTraceIndex, row, row)
        parentTrace = self.getTrace(parentTraceIndex)
        del parentTrace.childTraces[row]
        self.endRemoveRows()

    def updateTrace(self, persistentIndex, event=None):
        """Emit the signal to update the trace."""
        #the index passed in is of type QPersistentModelIndex, it has to be recast as a QModelIndex
        traceIndex = QtCore.QModelIndex(persistentIndex)
        trace = self.getTrace(traceIndex)
        row = traceIndex.row()
        leftInd = self.createIndex(row, 0, trace)
        rightInd = self.createIndex(row, 4, trace)
        self.dataChanged.emit(leftInd, rightInd) #Update all 5 columns
        
    def removeRows(self, row, count, parent):
        print "removeRows"
        return False