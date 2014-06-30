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
    
class TraceTreeModel(QtCore.QAbstractItemModel):
    
    """
    This class is the data model used to displaying the traces in a tree.
    
    instance variables:
    penicons -- the list of icons available for the different traces
    rootTrace -- This is an empty PlottedTrace object. It is the parent of all the top level
                 traces. It contains a list of all its child traces, which in turn contain
                 a list of their child traces, etc. In this way, all the traces are stored
                 in the model.

    methods:
    __init__(self, TraceList, penicons, parent=None, *args): Construct the TraceTreeModel
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
    
    def __init__(self, traceList, penicons, parent=None, *args): 
        """
        Construct the TraceTreeModel.
        
        traceList: The initial list of traces (typically empty)
        penicons: The list of available icons for the different traces
        """
        super(TraceTreeModel, self).__init__(parent)
        self.rootTrace = PlottedTrace(None,None,None,isRootTrace=True) #rootTrace is an empty plotted trace
        self.penicons = penicons
        for trace in traceList: #set all top level traces to have rootTrace as parent
            if trace.parentTrace == None:
                trace.parentTrace = self.rootTrace
                self.rootTrace.appendChild(trace)

    def getTrace(self, traceIndex):
        """Return the trace at the given index. If the index is invalid, return the root trace."""
        if not traceIndex.isValid():
            return self.rootTrace
        return traceIndex.internalPointer()
        
    def index(self, row, column, parentIndex=QtCore.QModelIndex()):
        """Required. Return a model index for the specified row, column, and parent."""
        if not self.hasIndex(row, column, parentIndex):
            return QtCore.QModelIndex()
        parentTrace = self.getTrace(parentIndex)
        trace = parentTrace.child(row)
        if trace == None:
            return QtCore.QModelIndex()
        return self.createIndex(row, column, trace)

    def parent(self, traceIndex):
        """Required. Return a model index for the parent of the specified index."""
        trace = self.getTrace(traceIndex)
        if trace == self.rootTrace:
            return QtCore.QModelIndex()
        parentTrace = trace.parent()
        if parentTrace == self.rootTrace:
            return QtCore.QModelIndex()
        return self.createIndex(parentTrace.childNumber(), 0, parentTrace) #index created for column 0 of parent

    def rowCount(self, parentIndex=QtCore.QModelIndex()):
        """Required. Return the number of rows beneath the given parent."""
        parentTrace = self.getTrace(parentIndex)
        if parentIndex.column() > 0:
            return 0
        return parentTrace.childCount()

    def columnCount(self, parent=QtCore.QModelIndex()): 
        """Required. Return the number of columns."""
        return 5

    def data(self, traceIndex, role):
        """Required. Return the data at the given index for the given role."""
        trace = self.getTrace(traceIndex)
        if trace == self.rootTrace:
            return None
        col = traceIndex.column()
        return { (QtCore.Qt.DisplayRole,2): ", ".join([str(trace.trace.name), str(trace.name)]),
                 (QtCore.Qt.DisplayRole,3): trace.trace.description["comment"],
                 (QtCore.Qt.DisplayRole,4): getattr( trace.trace, 'fileleaf', None ),
                 (QtCore.Qt.CheckStateRole,0): QtCore.Qt.Checked if trace.curvePen > 0 else QtCore.Qt.Unchecked,
                 (QtCore.Qt.DecorationRole,1): QtGui.QIcon(self.penicons[trace.curvePen]) if hasattr(trace, 'curve') and trace.curve is not None else None,
                 (QtCore.Qt.BackgroundColorRole,1): QtGui.QColor(QtCore.Qt.white) if not (hasattr(trace, 'curve') and trace.curve is not None) else None,
                 (QtCore.Qt.EditRole,1): trace.curvePen,
                 (QtCore.Qt.EditRole,2): trace.trace.description["comment"],
                 (QtCore.Qt.EditRole,3): trace.trace.description["comment"]
                 }.get((role,col))

    def flags(self, index):
        """Required. Return the flags for the given index."""
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        col = index.column()
        return { 0: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled,
                 1: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
                 3: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
                 }.get(col, QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

    def headerData(self, section, orientation, role):
        """Required. Return the headers for each column."""
        if (role == QtCore.Qt.DisplayRole) and (orientation == QtCore.Qt.Horizontal): 
            return {
                1: 'Plot   ',
                2: 'Name',
                3: 'Comment',
                4: 'Filename'
                }.get(section)
        return None #QtCore.QVariant()

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
            if not comment == trace.trace.description["comment"]:
                trace.trace.description["comment"] = comment
                trace.trace.resave()
            return True
        
        else:
            return False
            
    def addTrace(self,trace,parentTrace=None):
        """Add a new trace to the list of traces. Return a persistent index to that trace."""
        if parentTrace == None:
            parentTrace = self.rootTrace
            parentIndex = QtCore.QModelIndex()
        else:
            parentIndex = self.createIndex(parentTrace.childNumber(), 0, parentTrace)
        position = parentTrace.childCount() #New trace is added at the end of the list
        self.beginInsertRows(parentIndex, position, position)
        parentTrace.appendChild(trace)
        trace.parentTrace = parentTrace
        #For the callback, we use a persistent index, so that when the trace "calls"
        #that its data is changed, the index it calls remains valid.
        persistentIndex = QtCore.QPersistentModelIndex(self.createIndex(position, 0, trace))
        trace.trace.dataChangedCallback = partial(self.updateTrace, persistentIndex)
        self.endInsertRows()
        return persistentIndex

    def dropTrace(self, parentTraceIndex, row):
        """Remove a trace from the list of traces."""
        self.beginRemoveRows(parentTraceIndex, row, row)
        parentTrace = self.getTrace(parentTraceIndex)
        del parentTrace.childTraces[row]
        self.endRemoveRows()

    def updateTrace(self, persistentIndex):
        """Emit the signal to update the trace."""
        #the index passed in is of type QPersistentModelIndex, it has to be recast as a QModelIndex
        traceIndex = QtCore.QModelIndex(persistentIndex)
        trace = self.getTrace(traceIndex)
        row = traceIndex.row()
        leftInd = self.createIndex(row, 0, trace)
        rightInd = self.createIndex(row, 4, trace)
        self.dataChanged.emit(leftInd, rightInd) #Update all 5 columns