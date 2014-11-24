'''
Created on Nov 21, 2014

@author: pmaunz
'''

from PyQt4 import QtCore
from os.path import exists
from _functools import partial
from Tkconstants import FIRST
from modules.firstNotNone import firstNotNone
import os.path

class MeasurementTableModel(QtCore.QAbstractTableModel):
    valueChanged = QtCore.pyqtSignal(object)
    headerDataLookup = ['Plot', 'Study', 'Scan', 'Name', 'Evaluation', 'Started', 'Comment', 'Filename' ]
    coreColumnCount = 8
    def __init__(self, measurements, extraColumns, traceuiLookup, container=None, parent=None, *args): 
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.container = container 
        self.extraColumns = extraColumns  # list of tuples (source, space, name)
        # measurements are given as a list
        self.measurements = measurements
        self.flagsLookup = { 0: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled,
                             6: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
                            }
        self.dataLookup = {  (QtCore.Qt.CheckStateRole,0): lambda row: self.isPlotted(self.measurements[row]),
                             (QtCore.Qt.DisplayRole, 1): lambda row: self.measurements[row].study,
                             (QtCore.Qt.DisplayRole, 2): lambda row: self.measurements[row].scanType,
                             (QtCore.Qt.DisplayRole, 3): lambda row: self.measurements[row].scanName,
                             (QtCore.Qt.DisplayRole, 4): lambda row: self.measurements[row].evaluation,
                             (QtCore.Qt.DisplayRole, 5): lambda row: str(self.measurements[row].startDate),
                             (QtCore.Qt.DisplayRole, 6): lambda row: self.measurements[row].comment,
                             (QtCore.Qt.DisplayRole, 7): self.getFilename, 
                             (QtCore.Qt.EditRole, 6): lambda row: self.measurements[row].comment
                             }
        self.setDataLookup = { (QtCore.Qt.CheckStateRole,0): self.setPlotted,
                               (QtCore.Qt.EditRole, 6): self.setComment
                              }
        self.traceuiLookup = traceuiLookup
        self.subscribeToTrace()
        
        
    def getFilename(self, row):
        filename = self.measurements[row].filename
        if filename is None:
            return None
        return os.path.split(filename)[1]
        
    def subscribeToTrace(self, first=0, last=None):
        # register listeners
        last = firstNotNone( last, len(self.measurements) )
        for row, measurement in enumerate(self.measurements[first:last]):
            plottedTraceList = measurement.plottedTraceList
            if len(plottedTraceList)>0:
                plottedTraceList[0].trace.commentChanged.subscribe( partial( self.commentChanged, row+first ) )
                plottedTraceList[0].trace.filenameChanged.subscribe( partial( self.filenameChanged, row+first) )
                 
    
    def commentChanged(self, row, event ):
        self.setComment( row, event.comment )
        self.dataChanged.emit( self.index(row,6), self.index(row,6) )

    def filenameChanged(self, row, event ):
        self.setFilename( row, event.filename )
        self.dataChanged.emit( self.index(row,7), self.index(row,7) )
    
    def addColumn(self, extraColumn ):
        self.beginInsertColumns( QtCore.QModelIndex(), self.coreColumnCount+len(self.extraColumns), self.coreColumnCount+len(self.extraColumns))
        self.extraColumns.append( extraColumn )
        self.endInsertColumns()
        
    def removeColumn(self, columnIndex):
        self.beginRemoveColumns( QtCore.QModelIndex(), columnIndex, columnIndex )
        self.extraColumns.pop( columnIndex-self.coreColumnCount )
        self.endRemoveColumns()
        
    def isPlotted(self, measurement):
        count = 0
        plottedTraceList = measurement.plottedTraceList
        total = len(plottedTraceList)
        for pt in plottedTraceList:
            if pt.isPlotted:
                count += 1
        if total==0 or count==0:
            return QtCore.Qt.Unchecked
        if count < total:
            return QtCore.Qt.PartiallyChecked
        return QtCore.Qt.Checked
        
        
    def setPlotted(self, row, value):
        plotted = value == QtCore.Qt.Checked
        self
        if not plotted:
            for pt in self.measurements[row].plottedTraceList:
                pt.plot(0)
        else:
            plottedTraceList = self.measurements[row].plottedTraceList
            if len(plottedTraceList)>0:
                for pt in plottedTraceList:
                    pt.plot(-1)
            else:
                if exists(self.measurements[row].filename):
                    self.loadTrace(self.measurements[row])
        return True
    
    def loadTrace(self, measurement):
        measurement.plottedTraceList = self.traceuiLookup[measurement.ScanType].openFile(measurement.filename)
    
    def setComment(self, row, value):
        if isinstance(value, QtCore.QVariant):
            value = value.toString()
        self.measurements[row].comment = str(value) 
        self.measurements[row]._sa_instance_state.session.commit()
        return True

    def setFilename(self, row, value):
        if isinstance(value, QtCore.QVariant):
            value = value.toString()
        self.measurements[row].filename = str(value) 
        self.measurements[row]._sa_instance_state.session.commit()
        return True
        
    def beginInsertRows(self, event):
        self.firstAdded = event.first
        self.lastAdded = event.last
        return QtCore.QAbstractTableModel.beginInsertRows(self, QtCore.QModelIndex(), event.first, event.last )
    
    def endInsertRows(self):
        self.subscribeToTrace(self.firstAdded, self.lastAdded+1)
        return QtCore.QAbstractTableModel.endInsertRows(self)
        
    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.measurements) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return self.coreColumnCount + len(self.extraColumns)
 
    def data(self, index, role): 
        if index.isValid():
            if index.column()<self.coreColumnCount:
                return self.dataLookup.get((role, index.column()), lambda row: None)(index.row())
            else:
                source, space, name = self.extraColumns[index.column()-self.coreColumnCount]
                if source=='parameter':
                    param = self.measurements[index.row()].parameterByName(space,name)
                    value = param.value if param is not None else None
                elif source=='result':
                    result = self.measurements[index.row()].resultByName(name)
                    value = result.value if result is not None else None
                if role==QtCore.Qt.DisplayRole:
                    return str(value) if value is not None else None
                elif role==QtCore.Qt.EditRole:
                    return value                    
        return None
        
    def setData(self, index, value, role):
        return self.setDataLookup.get((role, index.column()), lambda row, value: False)(index.row(), value)       
    
    def flags(self, index):
        return self.flagsLookup.get( index.column(), QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled )

    def headerData(self, section, orientation, role):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section] if section<self.coreColumnCount else self.extraColumns[section-self.coreColumnCount][2]
            elif (orientation == QtCore.Qt.Vertical):
                return self.measurements[section].id
        return None  # QtCore.QVariant()
                
    def sort(self, column, order):
        if column == 0 and self.variables:
            self.measurements.sort(reverse=order == QtCore.Qt.DescendingOrder)
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.variables) - 1, 1))
            
    def setMeasurements(self, event):
        self.beginResetModel()
        self.measurements = event.measurements 
        self.subscribeToTrace()
        self.endResetModel()
        