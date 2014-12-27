from PyQt4 import QtCore


class GenericTableModel(QtCore.QAbstractTableModel):
    def __init__(self, config, data, objectName, columnHeaders, parent=None, *args): 
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.config = config 
        self.objectName = objectName
        self.data = data
        self.columnHeaders = columnHeaders
                        
    def setDataTable(self, data):
        self.beginResetModel()
        self.data = data
        self.endResetModel()
                        
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
        return len(self.data) if self.data else 0
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return len(self.columnHeaders) 

    def data(self, index, role): 
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return str(self.data[index.row()][index.column()])
        return None
        
    def flags(self, index ):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.columnHeaders[section]
        return None #QtCore.QVariant()
    