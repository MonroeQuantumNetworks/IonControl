# -*- coding: utf-8 -*-
"""
Created on Wed Jan 02 09:53:48 2013

@author: plmaunz

This is the model used with TraceTableView to view the list of traces in a table.
"""

import functools

from PyQt4 import QtCore, QtGui
import sip


api2 = sip.getapi("QVariant")==2

class TraceComboDelegate(QtGui.QItemDelegate):
    
    """
    This class is responsible for the combo box editor in the trace table,
    which is used to select which pen to use in drawing the trace on the plot.
    The pen icons are in the array penicons, which is determined when the delegate
    is constructed.
    """    
    
    def __init__(self, penicons):
        """Construct the TraceComboDelegate object, and set the penicons array."""
        QtGui.QItemDelegate.__init__(self)
        self.penicons = penicons        
        
    def createEditor(self,parent, option, index ):
        """Create the combo box editor used to select which pen icon to use.
           The for loop adds each pen icon into the combo box."""
        editor = QtGui.QComboBox(parent);
        #for icon, string in zip(self.penicons, ["{0}".format(i) for i in range(0,len(self.penicons))] ):
        for icon, string in zip(self.penicons, ['']*len(self.penicons) ):
            editor.addItem( icon, string )
        return editor
        
    def setEditorData(self,editor, index):
        value = index.model().data(index, QtCore.Qt.EditRole) 
        editor.setCurrentIndex(value)
        
    def setModelData(self,editor, model, index):
        value = editor.currentIndex()
        model.setData(index, value, QtCore.Qt.EditRole)
         
    def updateEditorGeometry(self,editor, option, index ):
        editor.setGeometry(option.rect)
    
class TraceTableModel(QtCore.QAbstractTableModel):
    
    """
    This class is the data model used to displaying the traces in a table.
    
    instance variables:
    TraceList -- the list of all traces, stored as PlottedTrace objects
    penicons -- the list of icons available for the different traces
    """
    
    def __init__(self, TraceList, penicons, parent=None, *args): 
        """ datain: a list where each item is a row"""
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.TraceList = TraceList
        self.penicons = penicons
        
    def addTrace(self,trace):
        self.beginInsertRows(QtCore.QModelIndex(),len(self.TraceList),len(self.TraceList))
        self.TraceList.append(trace)
        trace.trace.dataChangedCallback = functools.partial( self.updateTrace, len(self.TraceList)-1 )
        self.endInsertRows()
        return len(self.TraceList)-1
        
    def dropTrace(self,index):
        self.beginRemoveRows(QtCore.QModelIndex(),index,index)
        del self.TraceList[index]
        self.endRemoveRows()

    def updateTrace(self,index):
        modindex1 = self.createIndex(index,0)
        modindex2 = self.createIndex(index,4)
        self.dataChanged.emit(modindex1,modindex2)
 
    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.TraceList) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 5
 
    def data(self, index, role): 
        row = index.row()
        col = index.column()
        traceplot = self.TraceList[row]
        if index.isValid():
            return { (QtCore.Qt.DisplayRole,2): traceplot.trace.name,
                     (QtCore.Qt.DisplayRole,3): traceplot.trace.vars.comment,
                     (QtCore.Qt.DisplayRole,4): getattr( traceplot.trace, 'fileleaf', None ),
                     (QtCore.Qt.CheckStateRole,0): traceplot.curvePen>0,
                     (QtCore.Qt.DecorationRole,1): QtGui.QIcon(self.penicons[traceplot.curvePen]) if hasattr(traceplot, 'curve') and traceplot.curve is not None else None,
                     (QtCore.Qt.BackgroundColorRole,1): QtGui.QColor(QtCore.Qt.white) if not (hasattr(traceplot, 'curve') and traceplot.curve is not None) else None,
                     (QtCore.Qt.EditRole,1): traceplot.curvePen,
                     (QtCore.Qt.EditRole,2): traceplot.trace.vars.comment,
                     (QtCore.Qt.EditRole,3): traceplot.trace.vars.comment
                     }.get((role,col))
        return None

    def setDataComment(self,index,value):
        comment = value if api2 else str(value.toString())
        if not comment==self.TraceList[index.row()].trace.vars.comment:
            self.TraceList[index.row()].trace.vars.comment = comment
            self.TraceList[index.row()].trace.resave()
        return True
        
    def setDataPen(self,index,value):   
        self.TraceList[index.row()].plot(value)
        return True
        
    def setDataPlot(self,index,value):
        if self.TraceList[index.row()].curvePen>0:
            self.TraceList[index.row()].plot(0)
        else:
            self.TraceList[index.row()].plot(-1)
        self.updateTrace(index.column())
        return True      
        
    def setData(self,index, value, role):
        return { (QtCore.Qt.CheckStateRole,0): functools.partial( self.setDataPlot, index, value ),
                 (QtCore.Qt.EditRole,1): functools.partial( self.setDataPen, index, value ),
                 (QtCore.Qt.EditRole,3): functools.partial( self.setDataComment, index, value ),
                }.get((role,index.column()), lambda: False )()

    def flags(self, index ):
        return { 0: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled,
                 1: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
                 3: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
                 }.get(index.column(),QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return {
                    1: 'Plot   ',
                    2: 'Name',
                    3: 'Comment',
                    4: 'Filename'
                    }.get(section)
        return None #QtCore.QVariant()
    