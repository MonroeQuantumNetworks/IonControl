'''
Created on Nov 21, 2014

@author: pmaunz
'''
from PyQt4 import QtCore, QtGui
from modules.firstNotNone import firstNotNone
from functools import partial

class DACTableModel(QtCore.QAbstractTableModel):
    headerDataLookup = ['On', 'Name', 'Voltage' ]
    voltageChanged = QtCore.pyqtSignal( object, object )
    enableChanged = QtCore.pyqtSignal( object, object )
    def __init__(self, dacChannels, globalDict, parent=None, *args): 
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        # scanNames are given as a SortedDict
        self.dacChannels = dacChannels
        self.defaultBG = QtGui.QColor(QtCore.Qt.white)
        self.textBG = QtGui.QColor(QtCore.Qt.green).lighter(175)
        self.dataLookup = {  (QtCore.Qt.CheckStateRole, 0): lambda row: QtCore.Qt.Checked if self.dacChannels[row].enabled else QtCore.Qt.Unchecked,
                             (QtCore.Qt.DisplayRole, 1): lambda row: self.dacChannels[row].name,
                             (QtCore.Qt.DisplayRole, 2): lambda row: str(self.dacChannels[row].voltage),
                             (QtCore.Qt.EditRole, 1): lambda row: self.dacChannels[row].name,
                             (QtCore.Qt.EditRole, 2): lambda row: firstNotNone( self.dacChannels[row].voltageText, str(self.dacChannels[row].voltage)),
                             (QtCore.Qt.BackgroundColorRole,2): lambda row: self.textBG if self.dacChannels[row]._voltage.hasDependency else self.defaultBG,
                              }
        self.setDataLookup =  {  (QtCore.Qt.CheckStateRole,0): self.setEnabled,
                                 (QtCore.Qt.EditRole,1): self.setName,
                                 (QtCore.Qt.EditRole,2): self.setVoltage,
                                 (QtCore.Qt.UserRole,2): partial( self.setFieldText, 'voltageText'),
                                 }
        self.globalDict = globalDict

    def setEnabled(self, index, value):
        enabled = value==QtCore.Qt.Checked
        self.dacChannels[index.row()].enabled = enabled
        self.enableChanged.emit( index.row(), enabled )
        return True
    
    def setValue(self, index, value):
        self.setData( index, value, QtCore.Qt.EditRole)
                
    def setName(self, index, value):
        self.dacChannels[index.row()].name = str(value.toString() )
        return True
    
    def setVoltage(self, index, value):
        self.dacChannels[index.row()].voltage = value
        self.voltageChanged.emit( index.row(), value)
        return True
    
    def setFieldText(self, fieldname, index, value):
        setattr( self.dacChannels[index.row()], fieldname, value )
        return True

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.dacChannels) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 3
 
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role, index.column()), lambda row: None)(index.row())
        return None
    
    def setData(self, index, value, role):
        return self.setDataLookup.get((role,index.column()), lambda index, value: False )(index, value)
        
    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable if index.column()==0 else QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable

    def headerData(self, section, orientation, role):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
            elif (orientation == QtCore.Qt.Vertical):
                return str(section)
        return None  # QtCore.QVariant()
