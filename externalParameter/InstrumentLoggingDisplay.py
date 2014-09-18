# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 23:45:54 2013

@author: pmaunz
"""

from PyQt4 import QtCore
import PyQt4.uic

from modules.SequenceDict import SequenceDict
from InstrumentLoggingHandler import LoggingData

UiForm, UiBase = PyQt4.uic.loadUiType(r'ui\ExternalParameterUi.ui')

class InstrumentLoggingDisplayTableModel( QtCore.QAbstractTableModel ):
    valueChanged = QtCore.pyqtSignal(str, object)
    def __init__(self, controlUi, parameterList=None, parent=None):
        super(InstrumentLoggingDisplayTableModel, self).__init__(parent)
        self.names = list()
        self.controlUi = controlUi
        self.headerLookup = ['Name', 'Raw', 'Decimated', 'Calibrated']
        self.dataLookup =  { (QtCore.Qt.DisplayRole,0): lambda row: self.data.keyAt(row),
                             (QtCore.Qt.DisplayRole,1): lambda row: str(self.data.at(row).raw),
                             (QtCore.Qt.DisplayRole,3): lambda row: str(self.data.at(row).calibrated),
                             (QtCore.Qt.DisplayRole,2): lambda row: str(self.data.at(row).decimated),
                     }
        self.data = SequenceDict()

        
    def setData(self, enabledObjects):
        self.beginResetModel()
        # drop everything that is not in the enabled parameter keys
        for key in self.data.keys():
            if key not in enabledObjects:
                self.data.pop(key)
        for key in enabledObjects.keys():
            self.data.__setdefault__( key, LoggingData() )
        self.endResetModel()
        
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.data)
    
    def columnCount(self,  parent=QtCore.QModelIndex()):
        return 4
    
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get( (role,index.column()) ,lambda row: None)(index.row())
        return None

    def flags(self, index ):
        return  QtCore.Qt.ItemIsEnabled |  QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole) and (orientation == QtCore.Qt.Horizontal): 
            return self.headerLookup[section]
        return None #QtCore.QVariant()
 
    def update(self, key, value):
        if key in self.data:
            self.data[key].update(value)
            index = self.data.index(key)
            leftInd = self.createIndex(index, 1)
            rightInd = self.createIndex(index, 3)
            self.dataChanged.emit(leftInd, rightInd) 

class InstrumentLoggingDisplay(UiForm,UiBase):   
    def __init__(self, parent=None):
        UiBase.__init__(self,parent)
        UiForm.__init__(self)
    
    def setupUi(self,EnabledParameters,MainWindow):
        UiForm.setupUi(self,MainWindow)
        self.tableModel = InstrumentLoggingDisplayTableModel(self)
        self.tableView.setModel( self.tableModel )
        self.setupParameters(EnabledParameters)
        
    def setupParameters(self,EnabledParameters):
        self.tableModel.setData( EnabledParameters )
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setStretchLastSection(True)
        
    def update(self, key, value):
        self.tableModel.update(key, value)   
        

    
