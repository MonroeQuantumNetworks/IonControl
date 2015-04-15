'''
Created on Jan 18, 2015

@author: pmaunz
'''
from PyQt4 import QtCore
from voltageControl.ShuttlingDefinition import ShuttlingGraph

class ShuttleEdgeTableModel(QtCore.QAbstractTableModel):
    def __init__(self, config, shuttlingGraph, parent=None, *args): 
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.config = config 
        self.shuttlingGraph = shuttlingGraph
        self.columnHeaders = ['From Name','From Line','To Name','To Line','Steps per line', 'Idle count' ]
        self.dataLookup = {  (QtCore.Qt.DisplayRole, 0): lambda row: self.shuttlingGraph[row].startName,
                             (QtCore.Qt.DisplayRole, 1): lambda row: self.shuttlingGraph[row].startLine,
                             (QtCore.Qt.DisplayRole, 2): lambda row: self.shuttlingGraph[row].stopName,
                             (QtCore.Qt.DisplayRole, 3): lambda row: self.shuttlingGraph[row].stopLine,
                             (QtCore.Qt.DisplayRole, 4): lambda row: self.shuttlingGraph[row].steps,
                             (QtCore.Qt.DisplayRole, 5): lambda row: self.shuttlingGraph[row].idleCount,
                             (QtCore.Qt.EditRole, 0): lambda row: self.shuttlingGraph[row].startName,
                             (QtCore.Qt.EditRole, 1): lambda row: self.shuttlingGraph[row].startLine,
                             (QtCore.Qt.EditRole, 2): lambda row: self.shuttlingGraph[row].stopName,
                             (QtCore.Qt.EditRole, 3): lambda row: self.shuttlingGraph[row].stopLine,
                             (QtCore.Qt.EditRole, 4): lambda row: self.shuttlingGraph[row].steps,
                             (QtCore.Qt.EditRole, 5): lambda row: self.shuttlingGraph[row].idleCount,
                              }
        self.setDataLookup = {(QtCore.Qt.EditRole, 0): ShuttlingGraph.setStartName,
                             (QtCore.Qt.EditRole, 1): ShuttlingGraph.setStartLine,
                             (QtCore.Qt.EditRole, 2): ShuttlingGraph.setStopName,
                             (QtCore.Qt.EditRole, 3): ShuttlingGraph.setStopLine,
                             (QtCore.Qt.EditRole, 4): ShuttlingGraph.setSteps,
                             (QtCore.Qt.EditRole, 5): ShuttlingGraph.setIdleCount
                              }
                        
    def setShuttlingGraph(self, shuttlingGraph):
        self.beginResetModel()
        self.shuttlingGraph = shuttlingGraph
        self.endResetModel()
                        
    def add(self, edge ):
        if self.shuttlingGraph.isValidEdge(edge):
            self.beginInsertRows(QtCore.QModelIndex(), len(self.shuttlingGraph), len(self.shuttlingGraph))
            self.shuttlingGraph.addEdge(edge)
            self.endInsertRows()
             
    def remove(self, index):
        self.beginRemoveRows(QtCore.QModelIndex(), index, index)
        self.shuttlingGraph.removeEdge(index)
        self.endRemoveRows()
                               
    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.shuttlingGraph) if self.shuttlingGraph else 0
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return len(self.columnHeaders) 

    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()), lambda row: None)(index.row())
        return None
    
    def setData(self, index, value, role):
        if isinstance( value, QtCore.QVariant ):
            value = value.toPyObject()
        return self.setDataLookup.get((role,index.column()), lambda g, row, value: False)(self.shuttlingGraph, index.row(), value)
        
    def flags(self, index ):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.columnHeaders[section]
            else:
                return str(section)
        return None #QtCore.QVariant()
    