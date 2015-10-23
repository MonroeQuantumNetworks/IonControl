'''
Created on Nov 21, 2014

@author: pmaunz
'''

from PyQt4 import QtCore, QtGui 
from os.path import exists
from _functools import partial
from modules.firstNotNone import firstNotNone
from modules.enum import enum
import os.path
from dateutil.tz import tzlocal

class MeasurementTableModel(QtCore.QAbstractTableModel):
    valueChanged = QtCore.pyqtSignal(object)
    headerDataLookup = ['Plot', 'Study', 'Scan', 'Name', 'Evaluation', 'Target', 'Parameter', 'Pulse Program', 'Started', 'Comment', 'Filename' ]
    column = enum('plot', 'study', 'scan', 'name', 'evaluation', 'target', 'parameter', 'pulseprogram', 'started', 'comment', 'filename')
    coreColumnCount = 11
    def __init__(self, measurements, extraColumns, traceuiLookup, container=None, parent=None, *args): 
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.container = container 
        self.extraColumns = extraColumns  # list of tuples (source, space, name)
        # measurements are given as a list
        self.measurements = measurements
        self.flagsLookup = { self.column.plot: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled,
                             self.column.comment: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
                            }
        self.failedBG =  QtGui.QColor(0xff,0xa6,0xa6,0xff)
        self.defaultBG = QtGui.QColor(QtCore.Qt.white)
        self.dataLookup = {  (QtCore.Qt.CheckStateRole, self.column.plot): lambda row: self.isPlotted(self.measurements[row]),
                             (QtCore.Qt.DisplayRole, self.column.study): lambda row: self.measurements[row].study,
                             (QtCore.Qt.DisplayRole, self.column.scan): lambda row: self.measurements[row].scanType,
                             (QtCore.Qt.DisplayRole, self.column.name): lambda row: self.measurements[row].scanName,
                             (QtCore.Qt.DisplayRole, self.column.evaluation): lambda row: self.measurements[row].evaluation,
                             (QtCore.Qt.DisplayRole, self.column.target): lambda row: self.measurements[row].scanTarget,
                             (QtCore.Qt.DisplayRole, self.column.parameter): lambda row: self.measurements[row].scanParameter,
                             (QtCore.Qt.DisplayRole, self.column.pulseprogram): lambda row: self.measurements[row].scanPP,
                             (QtCore.Qt.DisplayRole, self.column.started): lambda row: self.measurements[row].startDate.astimezone(tzlocal()).strftime('%Y-%m-%d %H:%M:%S'),
                             (QtCore.Qt.DisplayRole, self.column.comment): lambda row: self.measurements[row].comment,
                             (QtCore.Qt.DisplayRole, self.column.filename): self.getFilename,
                             (QtCore.Qt.EditRole, self.column.comment): lambda row: self.measurements[row].comment,
                             (QtCore.Qt.BackgroundColorRole,self.column.plot): lambda row: self.defaultBG if self.measurements[row].failedAnalysis is None else self.failedBG,
                             (QtCore.Qt.BackgroundColorRole, self.column.study): lambda row: self.defaultBG if self.measurements[row].failedAnalysis is None else self.failedBG,
                             (QtCore.Qt.BackgroundColorRole, self.column.scan): lambda row: self.defaultBG if self.measurements[row].failedAnalysis is None else self.failedBG,
                             (QtCore.Qt.BackgroundColorRole, self.column.name): lambda row: self.defaultBG if self.measurements[row].failedAnalysis is None else self.failedBG,
                             (QtCore.Qt.BackgroundColorRole, self.column.evaluation): lambda row: self.defaultBG if self.measurements[row].failedAnalysis is None else self.failedBG,
                             (QtCore.Qt.BackgroundColorRole, self.column.target): lambda row: self.defaultBG if self.measurements[row].failedAnalysis is None else self.failedBG,
                             (QtCore.Qt.BackgroundColorRole, self.column.parameter): lambda row: self.defaultBG if self.measurements[row].failedAnalysis is None else self.failedBG,
                             (QtCore.Qt.BackgroundColorRole, self.column.pulseprogram): lambda row: self.defaultBG if self.measurements[row].failedAnalysis is None else self.failedBG,
                             (QtCore.Qt.BackgroundColorRole, self.column.started): lambda row: self.defaultBG if self.measurements[row].failedAnalysis is None else self.failedBG,
                             (QtCore.Qt.BackgroundColorRole, self.column.comment): lambda row: self.defaultBG if self.measurements[row].failedAnalysis is None else self.failedBG,
                             (QtCore.Qt.BackgroundColorRole, self.column.filename): lambda row: self.defaultBG if self.measurements[row].failedAnalysis is None else self.failedBG
                             }
        self.setDataLookup = { (QtCore.Qt.CheckStateRole,self.column.plot): self.setPlotted,
                               (QtCore.Qt.EditRole, self.column.comment): self.setComment
                              }
        self.traceuiLookup = traceuiLookup
        self.subscriptions = list()
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
                callback = partial( self.commentChanged, row+first )
                plottedTraceList[0].trace.commentChanged.subscribe( callback )
                self.subscriptions.append( (plottedTraceList[0].trace.commentChanged, callback ))
                callback = partial( self.filenameChanged, row+first)
                plottedTraceList[0].trace.filenameChanged.subscribe( callback )
                self.subscriptions.append( (plottedTraceList[0].trace.filenameChanged, callback ))
                
    def clearSubscriptions(self):
        for observable, callback in self.subscriptions:
            observable.unsubscribe( callback )
        self.subscriptions[:] = []
    
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
                if self.measurements[row].filename is not None and exists(self.measurements[row].filename):
                    self.loadTrace(self.measurements[row])
        return True
    
    def loadTrace(self, measurement):
        measurement.plottedTraceList = self.traceuiLookup[measurement.scanType].openFile(measurement.filename)
    
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
        self.clearSubscriptions()
        self.subscribeToTrace()
        self.endResetModel()
        