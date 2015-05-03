'''
Created on Dec 10, 2014

@author: pmaunz
'''

from PyQt4 import QtCore, QtGui
from modules import MagnitudeUtilit

class VoltageLocalAdjustTableModel(QtCore.QAbstractTableModel):
    filesChanged = QtCore.pyqtSignal( object, object )
    voltageChanged = QtCore.pyqtSignal(  )
    headerDataLookup = ['Solution', 'Amplitude' ,'Filepath']
    def __init__(self, localAdjustList, globalDict, parent=None, *args): 
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.localAdjustList = localAdjustList  
        # scanNames are given as a SortedDict
        defaultBG = QtGui.QColor(QtCore.Qt.white)
        textBG = QtGui.QColor(QtCore.Qt.green).lighter(175)
        self.backgroundLookup = { True:textBG, False:defaultBG}
        self.dataLookup = {  (QtCore.Qt.DisplayRole, 0): lambda row: self.localAdjustList[row].name,
                             (QtCore.Qt.DisplayRole, 1): lambda row: str(self.localAdjustList[row].gain.value),
                             (QtCore.Qt.DisplayRole, 2): lambda row: str(self.localAdjustList[row].path),
                             (QtCore.Qt.EditRole, 2): lambda row: str(self.localAdjustList[row].path),
                             (QtCore.Qt.EditRole, 1): lambda row: self.localAdjustList[row].gain.string,                            
                             (QtCore.Qt.BackgroundColorRole,1): lambda row: self.backgroundLookup[self.localAdjustList[row].gain.hasDependency],
                              }

    def add(self, record ):
        self.beginInsertRows(QtCore.QModelIndex(),len(self.localAdjustList), len(self.localAdjustList))
        self.localAdjustList.append( record )
        self.endInsertRows()
        return record
        
    def drop(self, row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        del self.localAdjustList[row]
        self.endRemoveRows()

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.localAdjustList) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 3
 
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role, index.column()), lambda row: None)(index.row())
        return None
    
    def setData(self, index, value, role):
        if index.column()==1:
            if role==QtCore.Qt.EditRole:
                self.localAdjustList[index.row()].gain.value = MagnitudeUtilit.value( value )
                return True
            if role==QtCore.Qt.UserRole:
                self.localAdjustList[index.row()].gain.string = value
                return True
        if index.column()==0:
            if role==QtCore.Qt.EditRole:
                self.localAdjustList[index.row()].name = str(value.toPyObject())
                return True
        if index.column()==2:
            if role==QtCore.Qt.EditRole:
                self.localAdjustList[index.row()].path = str(value.toPyObject())
                self.filesChanged.emit( self.localAdjustList, list() )
                return True
            
        return False
        
    def setValue(self, index, value):
        self.setData(index, value, QtCore.Qt.EditRole)
        
    def flags(self, index):
        return  QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable

    def headerData(self, section, orientation, role):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
        return None  # QtCore.QVariant()
                
    def setLocalAdjust(self, localAdjustList ):
        self.beginResetModel()
        self.localAdjustList = localAdjustList
        self.endResetModel()

    def valueRecalcualted(self, record):
        index = self.createIndex(self.localAdjustList.index(record),1)
        self.dataChanged.emit( index, index )
        
    def sort(self, column, order):
        if column == 0 and self.valueRecalcualted:
            self.localAdjustList.sort(reverse=order == QtCore.Qt.DescendingOrder)
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.localAdjustList) - 1, 1))
            
