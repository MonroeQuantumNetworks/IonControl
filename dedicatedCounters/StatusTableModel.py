from PyQt4 import QtCore
from modules.firstNotNone import firstNotNone


class StatusTableModel(QtCore.QAbstractTableModel):
    colorLookup = { (0,True): QtCore.Qt.green, (1,True): QtCore.Qt.red, (0,False): QtCore.Qt.white, (1,False): QtCore.Qt.white }
    def __init__(self, description, parent=None, *args): 
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.description = description
        self.externalStatus = 0
                        
    def setData(self, data):
        self.externalStatus = data
        self.dataChanged.emit( self.createIndex(1,0), self.createIndex(1,len(self.description)))
                        
    def add(self, key, value ):
        if key not in self.data:
            self.beginInsertRows(QtCore.QModelIndex(), len(self.data), len(self.data))
            self.data[key] = value
            self.endInsertRows()
             
    def remove(self, index):
        self.beginRemoveRows(QtCore.QModelIndex(), index, index)
        self.data.popAt(index)
        self.endRemoveRows()
                               
    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.description) if self.description else 0
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 2

    def data(self, index, role): 
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                if index.column()==0:
                    return self.description[ index.row() ][0]
            elif role == QtCore.Qt.BackgroundColorRole:
                if index.column()==1:
                    return self.colorLookup[(self.description[ index.row() ][2], bool(self.externalStatus & (1<<self.description[ index.row() ][1])) )]
        return None
        
    def flags(self, index ):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def headerData(self, section, orientation, role ):
        return None #QtCore.QVariant()
    