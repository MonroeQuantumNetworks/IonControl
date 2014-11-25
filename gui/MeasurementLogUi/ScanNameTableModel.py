'''
Created on Nov 21, 2014

@author: pmaunz
'''
from PyQt4 import QtCore

class ScanNameTableModel(QtCore.QAbstractTableModel):
    valueChanged = QtCore.pyqtSignal(object)
    headerDataLookup = ['Show', 'Name' ]
    def __init__(self, scanNames, container=None, parent=None, *args): 
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.container = container  
        # scanNames are given as a SortedDict
        self.scanNames = scanNames
        self.dataLookup = {  (QtCore.Qt.CheckStateRole, 0): lambda row: self.scanNames[row].name,
                             (QtCore.Qt.DisplayRole, 1): lambda row: str(self.scanNames[row].startDate)
                              }

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.scanNames) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 2
 
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role, index.column()), lambda row: None)(index.row())
        return None
    
    def setData(self, index, value, role):
        if role==QtCore.Qt.CheckStateRole and index.column()==0:
            
        
    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable if index.column()==0 else QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled

    def headerData(self, section, orientation, role):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
        return None  # QtCore.QVariant()
                
            
