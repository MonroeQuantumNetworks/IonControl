# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 23:45:54 2013

@author: pmaunz
"""

import functools
import logging

from PyQt4 import QtCore
import PyQt4.uic

from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate


UiForm, UiBase = PyQt4.uic.loadUiType(r'ui\ExternalParameterUi.ui')

class ExternalParameterControlTableModel( QtCore.QAbstractTableModel ):
    valueChanged = QtCore.pyqtSignal(str, object)
    def __init__(self, controlUi, parameterList=None, parent=None):
        super(ExternalParameterControlTableModel, self).__init__(parent)
        self.parameterList = list()
        self.names = list()
        self.controlUi = controlUi
        self.headerLookup = ['Name', 'Control', 'External']
        self.dataLookup =  { (QtCore.Qt.DisplayRole,0): lambda row: self.names[row],
                             (QtCore.Qt.DisplayRole,1): lambda row: str(self.targetValues[row]),
                             (QtCore.Qt.EditRole,1): lambda row: str(self.targetValues[row]),
                             (QtCore.Qt.UserRole,1): lambda row: self.parameterList[row].dimension,
                             (QtCore.Qt.DisplayRole,2): lambda row: str(self.externalValues[row]),
                             (QtCore.Qt.ToolTipRole,2): lambda row: str(self.toolTips[row]),
                     }

    def setParameterList(self, parameterList):
        self.beginResetModel()
        self.parameterList = parameterList.values()
        self.names = parameterList.keys()
        self.targetValues = [inst.currentValue() for inst in self.parameterList]
        self.externalValues = self.targetValues[:]
        self.toolTips = [None]*len(self.externalValues )
        for index,inst in enumerate(self.parameterList):
            inst.displayValueCallback = functools.partial( self.showValue, index )
        self.endResetModel()
        
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.parameterList)
    
    def columnCount(self,  parent=QtCore.QModelIndex()):
        return 3
    
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()),lambda row: None)(index.row())
        return None

    def setData(self,index, value, role):
        return self.dataLookup.get( (role,index.column() ), lambda row: None)(index.row())
                      
    def flags(self, index ):
        return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable if index.column()==1 else QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole) and (orientation == QtCore.Qt.Horizontal): 
            return self.headerLookup[section]
        return None #QtCore.QVariant()
 
    def showValue(self, index, value, tooltip=None):
        self.externalValues[index] = value
        self.toolTips[index] = tooltip
        leftInd = self.createIndex(index, 2)
        rightInd = self.createIndex(index, 2)
        self.dataChanged.emit(leftInd, rightInd) 
            
    def setValue(self, index, value):
        logger = logging.getLogger(__name__)
        logger.debug( "setValue {0}".format( value ) )
        self.targetValues[index.row()] = value
        self.setValueFollowup(index)
        
    def setValueFollowup(self, index):
        logger = logging.getLogger(__name__)
        logger.debug( "setValueFollowup {0}".format( self.parameterList[index.row()].currentValue() ) )
        delay = int( self.parameterList[index.row()].settings.delay.toval('ms') )
        if not self.parameterList[index.row()].setValue( self.targetValues[index.row()] ):
            QtCore.QTimer.singleShot(delay,functools.partial(self.setValueFollowup,index) )

    def update(self, iterable):
        for destination, name, value in iterable:
            if destination=='External':
                row = self.names.index(name)
                self.parameterList[row].setSavedValue( value )     # set saved value to make this new value the default
                self.setValue( self.createIndex( row,1), value )
                

class ControlUi(UiForm,UiBase):
    
    def __init__(self, parent=None):
        UiBase.__init__(self,parent)
        UiForm.__init__(self)
        self.spacerItem = None
        self.myLabelList = list()
        self.myBoxList = list()
        self.myDisplayList = list()
        self.targetValue = dict()
        self.currentValue = dict()
        self.displayWidget = dict()
        self.tagetValue = dict()
    
    def setupUi(self,EnabledParameters,MainWindow):
        UiForm.setupUi(self,MainWindow)
        self.tableModel = ExternalParameterControlTableModel(self)
        self.tableView.setModel( self.tableModel )
        self.delegate = MagnitudeSpinBoxDelegate()
        self.tableView.setItemDelegateForColumn(1,self.delegate) 
        self.setupParameters(EnabledParameters)
        
    def setupParameters(self,EnabledParameters):
        logger = logging.getLogger(__name__)
        logger.debug( "ControlUi.setupParameters {0}".format( EnabledParameters ) ) 
        self.enabledParameters = EnabledParameters
        self.tableModel.setParameterList( self.enabledParameters )
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setStretchLastSection(True)        
        
    def keys(self):
        return self.tableModel.names
    
    def update(self, iterable):
        self.tableModel.update( iterable )
        

    
