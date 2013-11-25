from PyQt4 import QtGui, QtCore
from functools import partial

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
        return 4
    
    def data(self, index, role): 
        if index.isValid():
            return { (QtCore.Qt.DisplayRole,2): self.parameterList[index.row()].className,
                     (QtCore.Qt.DisplayRole,3): self.parameterList[index.row()].instrument,
                     (QtCore.Qt.DisplayRole,1): self.parameterList[index.row()].name,
                     (QtCore.Qt.CheckStateRole,0): QtCore.Qt.Checked if self.parameterList[index.row()].enabled else QtCore.Qt.Unchecked,
                     }.get((role,index.column()),None)
        return None
        
    def setData(self, index, value, role):
        return { (QtCore.Qt.CheckStateRole,0): partial( self.setEnabled, index, value )
                }.get((role,index.column()), lambda: False )()
                
    def setEnabled(self, index, value):
        self.parameterList[index.row()].enabled = value==QtCore.Qt.Checked
        return True
        
    def flags(self, index ):
        return { 0: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled,
                 1: QtCore.Qt.ItemIsSelectable |   QtCore.Qt.ItemIsEnabled,
                 2: QtCore.Qt.ItemIsSelectable |   QtCore.Qt.ItemIsEnabled,
                 3: QtCore.Qt.ItemIsSelectable |   QtCore.Qt.ItemIsEnabled
                 }.get(index.column(),QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Vertical): 
                return str(section)
            elif (orientation == QtCore.Qt.Horizontal): 
                return { 0: 'E',
                         1: 'Name',
                         2: 'Class',
                         3: 'Instrument' }[section]
        return None 
