# -*- coding: utf-8 -*-
"""
Created on Fri Feb 08 22:02:08 2013

@author: pmaunz
"""
from PyQt4 import QtCore


class LoadingHistoryModel(QtCore.QAbstractTableModel):
    def __init__(self, history, parent=None, *args): 
        """ datain: a list where each item is a row
        
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self._history = history

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self._history) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 3
 
    def data(self, index, role): 
        if index.isValid():
            item = self.history[len(self.history)-index.row()-1]
            #print item.trappedAt, item.loadingTime, item.trappingTime
            return { (QtCore.Qt.DisplayRole,0): item.trappedAt.strftime('%Y-%m-%d %H:%M:%S'),
                     (QtCore.Qt.DisplayRole,1): self.formatDelta(item.loadingTime) if item.loadingTime else None,
                     (QtCore.Qt.DisplayRole,2): self.formatDelta(item.trappingTime) if item.trappingTime else None,
                     }.get((role,index.column()),None)
        return None
        
    def flags(self, index ):
        return  QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return { 0: 'Trapped at',
                         1: 'Loading Time',
                         2: 'Trapping Time' }.get(section)
        return None #QtCore.QVariant()
        
    @property
    def history(self):
        return self._history
        
    @history.setter
    def history(self,value):
        self._history = value
        self.dataChanged.emit( self.index(0,0), self.index(len(self._history)-1,2) )
        
    def append(self,value):
        self.beginInsertRows(QtCore.QModelIndex(),0,0)
        self.history.append(value)
        self.endInsertRows()
 
    def formatDelta(self, delta):
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        hours = hours + delta.days*24
        seconds = seconds + delta.microseconds*1e-6
        components = list()
        if (hours>0): components.append("{0}".format(hours))
        components.append("{0:02d}:{1:02.0f}".format(int(minutes),seconds))
        return ":".join(components)

    def updateLast(self,attr,value):
        setattr(self.history[-1], attr, value)
        self.dataChanged.emit(self.createIndex(0,0),self.createIndex(0,2))
        
    def removeRow(self,row):
        index = len(self.history)-row-1
        self.beginRemoveRows( QtCore.QModelIndex(), index, index   )
        del self._history[0]
        self.endRemoveRows()