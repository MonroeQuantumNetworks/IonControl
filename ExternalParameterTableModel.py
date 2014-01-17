from PyQt4 import QtGui, QtCore
from functools import partial
from modules.SequenceDict import SequenceDict

class ExternalParameterTableModel( QtCore.QAbstractTableModel ):
    enableChanged = QtCore.pyqtSignal( object )
    headerDataLookup = [ 'E', 'Name', 'Class', 'Instrument' ]
    def __init__(self, parameterDict=None, parent=None):
        super(ExternalParameterTableModel, self).__init__(parent)
        self.parameterDict = parameterDict if parameterDict else SequenceDict()
        self.dataLookup = {  (QtCore.Qt.DisplayRole,2):    lambda row: self.parameterDict.at(row).className,
                             (QtCore.Qt.DisplayRole,3):    lambda row: self.parameterDict.at(row).instrument,
                             (QtCore.Qt.DisplayRole,1):    lambda row: self.parameterDict.at(row).name,
                             (QtCore.Qt.CheckStateRole,0): lambda row: QtCore.Qt.Checked if self.parameterDict.at(row).enabled else QtCore.Qt.Unchecked }
        self.setDataLookup = { (QtCore.Qt.CheckStateRole,0): self.setEnabled  }
        
    def setParameterDict(self, parameterDict):
        self.beginResetModel()
        self.parameterDict = parameterDict
        self.endResetModel()
        
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.parameterDict) if self.parameterDict else 0
    
    def columnCount(self,  parent=QtCore.QModelIndex()):
        return 4
    
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()),lambda row: None)(index.row())
        return None
        
    def setData(self, index, value, role):
        return self.setDataLookup.get((role,index.column()), lambda index, value: False )(index, value)
                
    def setEnabled(self, index, value):
        self.parameterDict.at(index.row()).enabled = value==QtCore.Qt.Checked
        self.enableChanged.emit( str(self.parameterDict.at(index.row()).name) )
        return True
        
    def flags(self, index ):
        if index.column()==0:
            return QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled
        return QtCore.Qt.ItemIsSelectable |   QtCore.Qt.ItemIsEnabled
    
    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Vertical): 
                return str(section)
            elif (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
        return None 
    
    def moveRowUp(self, indexes):
        for index in indexes:
            if index.row()>0:
                self.parameterDict.swap(index.row(), index.row()-1 )
        self.dataChanged.emit( self.createIndex(index.row()-1,0), self.createIndex(index.row(),3) )
        return self.createIndex(index.row()-1,index.column())
    
    def moveRowDown(self, indexes):
        for index in indexes:
            if index.row()<len(self.parameterDict)-1:
                self.parameterDict.swap(index.row(), index.row()+1 )
        self.dataChanged.emit( self.createIndex(index.row(),0), self.createIndex(index.row()+1,3) )
        return self.createIndex(index.row()+1,index.column())
