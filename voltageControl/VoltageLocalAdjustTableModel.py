'''
Created on Dec 10, 2014

@author: pmaunz
'''

from PyQt4 import QtCore, QtGui

class VoltageLocalAdjustTableModel(QtCore.QAbstractTableModel):
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
                             (QtCore.Qt.DisplayRole, 2): lambda row: str(self.localAdjustList[row].filename),
                             (QtCore.Qt.ToolTipRole, 2): lambda row: str(self.localAdjustList[row].path),
                             (QtCore.Qt.EditRole, 1): lambda row: self.localAdjustList[row].gain.string,                            
                             (QtCore.Qt.BackgroundColorRole,1): lambda row: self.backgroundLookup[self.localAdjustList[row].gain.hasDependency],
                              }

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
                self.localAdjustList[index.row()].gain.value = value
                return True
            if role==QtCore.Qt.UserRole:
                self.localAdjustList[index.row()].gain.string = str(value)
                return True
        if index.column()==0:
            if role==QtCore.Qt.EditRole:
                self.localAdjustList[index.row()].name = str(value)
                return True
            
        return False
        
    def setValue(self, index, value):
        self.setData(index, value, QtCore.Qt.EditRole)
        
    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled  if index.column()==2 else QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable

    def headerData(self, section, orientation, role):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
        return None  # QtCore.QVariant()
                
    def setLocalAdjust(self, localAdjustList ):
        self.beginResetModel()
        self.localAdjustList = localAdjustList
        self.endResetModel()

    def valueRecalcualted(self, name):
        index = self.createIndex(self.globalAdjustDict.index(name),1)
        self.dataChanged.emit( index, index )
        
    def sort(self, column, order):
        if column == 0 and self.valueRecalcualted:
            self.localAdjustList.sort(reverse=order == QtCore.Qt.DescendingOrder)
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.localAdjustList) - 1, 1))
            