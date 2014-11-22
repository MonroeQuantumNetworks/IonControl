'''
Created on Nov 21, 2014

@author: pmaunz
'''

from PyQt4 import QtCore

class MeasurementTableModel(QtCore.QAbstractTableModel):
    valueChanged = QtCore.pyqtSignal(object)
    headerDataLookup = ['Study', 'Scan', 'Name', 'Evaluation', 'Started', 'Title', 'Filename' ]
    def __init__(self, measurements, parent=None, *args): 
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        # measurements are given as a list
        self.measurements = measurements
        self.dataLookup = {  (QtCore.Qt.DisplayRole, 0): lambda row: self.measurements[row].study,
                             (QtCore.Qt.DisplayRole, 1): lambda row: self.measurements[row].scanType,
                             (QtCore.Qt.DisplayRole, 2): lambda row: self.measurements[row].scanName,
                             (QtCore.Qt.DisplayRole, 3): lambda row: self.measurements[row].evaluation,
                             (QtCore.Qt.DisplayRole, 4): lambda row: str(self.measurements[row].startDate),
                             (QtCore.Qt.DisplayRole, 5): lambda row: self.measurements[row].title,
                             (QtCore.Qt.DisplayRole, 6): lambda row: self.measurements[row].filename
                             }

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.measurements) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 7
 
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role, index.column()), lambda row: None)(index.row())
        return None
        
    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled

    def headerData(self, section, orientation, role):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
            elif (orientation == QtCore.Qt.Vertical):
                return self.measurements[section].id
        return None  # QtCore.QVariant()
                
    def sort(self, column, order):
        if column == 0 and self.variables:
            self.measurements.sort(reverse=order == QtCore.Qt.DescendingOrder)
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.variables) - 1, 1))
            
