'''
Created on Jul 2, 2015

@author: Geoffrey Ji
'''
from PyQt4 import QtCore, QtGui

from modules import firstNotNone


class AWGTableModel(QtCore.QAbstractTableModel):
    headerDataLookup = ["Variable", "Value"]
    valueChanged = QtCore.pyqtSignal( object, object )
    
    def __init__(self, waveform, globalDict, parent=None, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.waveform = waveform
        self.globalDict = globalDict
        self.defaultBG = QtGui.QColor(QtCore.Qt.white)
        self.textBG = QtGui.QColor(QtCore.Qt.green).lighter(175)
        
        self.dataLookup = {
            (QtCore.Qt.DisplayRole, 0): lambda row: self.waveform.vars.keys()[row],
            (QtCore.Qt.DisplayRole, 1): lambda row: str(self.waveform.vars.values()[row]['value']),
            (QtCore.Qt.EditRole, 1): lambda row: firstNotNone( self.waveform.vars.values()[row]['text'], str(self.waveform.vars.values()[row]['value'])),
            (QtCore.Qt.BackgroundColorRole,1): lambda row: self.defaultBG if self.waveform.vars.values()[row]['text'] is None else self.textBG,
        }
        self.setDataLookup =  { 
            (QtCore.Qt.EditRole,1): self.setValue,
            (QtCore.Qt.UserRole,1): self.setText
        }
        
    def setValue(self, index, value):
        self.waveform.vars[self.waveform.vars.keys()[index.row()]]['value'] = value
        self.valueChanged.emit(self.waveform.vars.keys()[index.row()], value)
        return True
    
    def setText(self, index, value):
        self.waveform.vars[self.waveform.vars.keys()[index.row()]]['text'] = value
        return True
    
    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.waveform.vars) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 2
    
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role, index.column()), lambda row: None)(index.row())
        return None
    
    def setWaveform(self, waveform):
        self.beginResetModel()
        self.waveform = waveform
        self.endResetModel()
        
    def setData(self, index, value, role):
        return self.setDataLookup.get((role,index.column()), lambda index, value: False )(index, value)
        
    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled if index.column()==0 else QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable

    def headerData(self, section, orientation, role):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
            elif (orientation == QtCore.Qt.Vertical):
                return str(section)
        return None  # QtCore.QVariant()
    
    def evaluate(self, name):
        pass