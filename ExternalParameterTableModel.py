from PyQt4 import QtGui, QtCore

class ExternalParameterTableModel( QtCore.QAbstractTableModel ):
    def __init__(self, parameterList=None, parent=None):
        super(ExternalParameterTableModel, self).__init__(parent)
        if parameterList:
            self.parameterList = parameterList
        else:
            self.parameterList = list()
        
    def setParameterList(self, parameterList):
        self.beginResetModel()
        self.parameterList = parameterList
        self.endResetModel()
        
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.parameterList)
    
    def columnCount(self,  parent=QtCore.QModelIndex()):
        return 3
    
    def data(self, index, role): 
        if index.isValid():
            return { (QtCore.Qt.DisplayRole,1): self.parameterList[index.row()].className,
                     (QtCore.Qt.DisplayRole,2): self.parameterList[index.row()].instrument,
                     (QtCore.Qt.DisplayRole,0): self.parameterList[index.row()].name,
                     }.get((role,index.column()),None)
        return None
        
    def flags(self, index ):
        return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Vertical): 
                return str(section)
            elif (orientation == QtCore.Qt.Horizontal): 
                return { 0: 'Name',
                         1: 'Class',
                         2: 'Instrument' }[section]
        return None 
