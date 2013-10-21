# -*- coding: utf-8 -*-
"""
Created on Wed Jan 02 09:53:48 2013

@author: Jonathan Mizrahi

This is the model used with TraceTreeView to view the list of traces in a tree.
"""

from PyQt4 import QtCore, QtGui
import sip
from functools import partial
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
    setEditorData: 
    """    
    
    def __init__(self, penicons):
        """Construct the TraceComboDelegate object, and set the penicons array."""
        QtGui.QItemDelegate.__init__(self)
        self.penicons = penicons        
        
    def createEditor(self,parent, option, index ):
        """Required reimplementation of parent method. Create the combo box editor used to select pen icon.
        
           The for loop adds each pen icon into the combo box."""
        editor = QtGui.QComboBox(parent);
        #for icon, string in zip(self.penicons, ["{0}".format(i) for i in range(0,len(self.penicons))] ):
        for icon, string in zip(self.penicons, ['']*len(self.penicons) ):
            editor.addItem( icon, string )
        return editor

    def setEditorData(self,editor, index):
        """Required reimplementation of parent method. Supply data to the editor from the model."""
        value = index.model().data(index, QtCore.Qt.EditRole) 
        editor.setCurrentIndex(value)
        
    def setModelData(self,editor, model, index):
        """Required reimplementation of parent method. Supply data to the model from the editor."""
        value = editor.currentIndex()
        model.setData(index, value, QtCore.Qt.EditRole)
         
    def updateEditorGeometry(self,editor, option, index ):
        """Required reimplementation of parent method. Set the size of the combo box appropriately."""
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
    __init__(self, TraceList, penicons, parent=None, *args):  Construct the TraceTreeModel
    getTrace(self, traceIndex): Return the trace at the given index.
    index: 
    """
    
    def __init__(self, TraceList, penicons, parent=None, *args): 
        """
        Construct the TraceTreeModel.
        
        TraceList: The initial list of traces (typically empty)
        penicons: The list of available icons for the different traces
        """
        super(TraceTreeModel, self).__init__(parent)
        self.rootTrace = PlottedTrace(None,None,None) #rootTrace is an empty plotted trace
        self.penicons = penicons
        for trace in TraceList: #set all top level traces to have rootTrace as parent
            if trace.parentTrace == None:
                trace.parentTrace = self.rootTrace
                self.rootTrace.appendChild(trace)

    def getTrace(self, traceIndex):
        """Return the trace at the given index. If the index is invalid, return the root trace."""
        if not traceIndex.isValid():
            return self.rootTrace
        else:
            return traceIndex.internalPointer()
        
    def index(self, row, column, parentIndex=QtCore.QModelIndex()):
        """
        Required reimplementation of parent method. Return a model index for the specified row, column, and parent.
        
        This method is used by the view to extract indices for each element in the tree.        
        """
        if not self.hasIndex(row, column, parentIndex):
            return QtCore.QModelIndex()
        if not parentIndex.isValid():
            parentTrace = self.rootTrace
        else:
            parentTrace = parentIndex.internalPointer()
        childTrace = parentTrace.child(row)
        if childTrace:
            return self.createIndex(row, column, childTrace)
        return QtCore.QModelIndex()

    def parent(self, traceIndex):
        if not traceIndex.isValid():
            return QtCore.QModelIndex()
        trace = traceIndex.internalPointer()
        parentTrace = trace.parent()
        if parentTrace == self.rootTrace:
            return QtCore.QModelIndex()
        return self.createIndex(parentTrace.childNumber(), 0, parentTrace)

    def rowCount(self, parentIndex=QtCore.QModelIndex()):
        if not parentIndex.isValid():
            parentTrace = self.rootTrace
        else:
            parentTrace = parentIndex.internalPointer()
        if parentIndex.column() > 0:
            return 0
        return parentTrace.childCount()

    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 5

    def data(self, traceIndex, role): 
        if not traceIndex.isValid():
            return None
        col = traceIndex.column()
        trace = traceIndex.internalPointer()
        return { (QtCore.Qt.DisplayRole,2): trace.trace.name,
                 (QtCore.Qt.DisplayRole,3): trace.trace.vars.comment,
                 (QtCore.Qt.DisplayRole,4): getattr( trace.trace, 'fileleaf', None ),
                 (QtCore.Qt.CheckStateRole,0): trace.curvePen>0,
                 (QtCore.Qt.DecorationRole,1): QtGui.QIcon(self.penicons[trace.curvePen]) if hasattr(trace, 'curve') and trace.curve is not None else None,
                 (QtCore.Qt.BackgroundColorRole,1): QtGui.QColor(QtCore.Qt.white) if not (hasattr(trace, 'curve') and trace.curve is not None) else None,
                 (QtCore.Qt.EditRole,1): trace.curvePen,
                 (QtCore.Qt.EditRole,2): trace.trace.vars.comment,
                 (QtCore.Qt.EditRole,3): trace.trace.vars.comment
                 }.get((role,col))

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        col = index.column()
        return { 0: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled,
                 1: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
                 3: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
                 }.get(col, QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

    def headerData(self, section, orientation, role):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return {
                    1: 'Plot   ',
                    2: 'Name',
                    3: 'Comment',
                    4: 'Filename'
                    }.get(section)
        return None #QtCore.QVariant()

    def setDataComment(self,traceIndex,value):
        comment = value if api2 else str(value.toString())
        trace = self.getTrace(traceIndex)
        if not comment==trace.trace.vars.comment:
            trace.trace.vars.comment = comment
            trace.trace.resave()
        return True
        
    def setDataPen(self,traceIndex,value):
        trace = self.getTrace(traceIndex)
        trace.plot(value)
        return True
        
    def setDataPlot(self,traceIndex,value):
        trace = self.getTrace(traceIndex)
        if trace.curvePen > 0:
            trace.plot(0)
        else:
            trace.plot(-1)
        row = traceIndex.row()
        leftInd = self.createIndex(row, 0, trace)
        rightInd = self.createIndex(row, 4, trace)
        self.dataChanged.emit(leftInd, rightInd)
        return True      

    def setData(self, traceIndex, value, role):
        col = traceIndex.column()
        return { (QtCore.Qt.CheckStateRole,0): partial( self.setDataPlot, traceIndex, value ),
                 (QtCore.Qt.EditRole,1): partial( self.setDataPen, traceIndex, value ),
                 (QtCore.Qt.EditRole,3): partial( self.setDataComment, traceIndex, value ),
                }.get((role,col), lambda: False )()

    def addTrace(self,trace,parentIndex=QtCore.QModelIndex()):
        parentTrace = self.getTrace(parentIndex)
        position = parentTrace.childCount()
        self.beginInsertRows(parentIndex, position, position)
        parentTrace.appendChild(trace)
        trace.parentTrace = parentTrace
        leftColTraceIndex = self.createIndex(position, 0, trace)
        rightColTraceIndex = self.createIndex(position, 4, trace)
        leftPersTraceIndex = QtCore.QPersistentModelIndex(leftColTraceIndex)
        rightPersTraceIndex = QtCore.QPersistentModelIndex(rightColTraceIndex)
        trace.trace.dataChangedCallback = partial(self.updateTrace, leftPersTraceIndex,rightPersTraceIndex)
        self.endInsertRows()

    def dropTrace(self, parentTraceIndex, row):
        self.beginRemoveRows(parentTraceIndex,row,row)
        parentTrace = self.getTrace(parentTraceIndex)
        del parentTrace.childTraces[row]
        self.endRemoveRows()

    def updateTrace(self, leftPersTraceIndex, rightPersTraceIndex):
        leftIndex = QtCore.QModelIndex(leftPersTraceIndex)
        rightIndex = QtCore.QModelIndex(rightPersTraceIndex)
        self.dataChanged.emit(leftIndex, rightIndex)
    