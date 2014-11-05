# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 23:45:54 2013

@author: pmaunz
"""

import functools
import logging

from PyQt4 import QtCore, QtGui
import PyQt4.uic

from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.SequenceDict import SequenceDict
from modules.firstNotNone import firstNotNone
from modules.Expression import Expression

UiForm, UiBase = PyQt4.uic.loadUiType(r'ui\ExternalParameterUi.ui')

class ExternalParameterControlTableModel( QtCore.QAbstractTableModel ):
    valueChanged = QtCore.pyqtSignal(str, object)
    expression = Expression()
    foregroundLookup = { True: QtGui.QBrush( QtCore.Qt.blue), False: QtGui.QBrush( QtCore.Qt.black)}  
    def __init__(self, controlUi, parameterList=None, parent=None):
        super(ExternalParameterControlTableModel, self).__init__(parent)
        self.parameterDict = SequenceDict()
        self.controlUi = controlUi
        self.headerLookup = ['Name', 'Control', 'External']
        self.dataLookup =  { (QtCore.Qt.DisplayRole,0): lambda row: self.parameterDict.keyAt(row),
                             (QtCore.Qt.DisplayRole,1): lambda row: str(self.targetValues[row]),
                             (QtCore.Qt.EditRole,1): lambda row: firstNotNone( self.parameterDict.at(row).strValue, str(self.targetValues[row]) ),
                             (QtCore.Qt.UserRole,1): lambda row: self.parameterDict.at(row).dimension,
                             (QtCore.Qt.DisplayRole,2): lambda row: str(self.externalValues[row]),
                             (QtCore.Qt.ToolTipRole,2): lambda row: str(self.toolTips[row]),
                             (QtCore.Qt.ForegroundRole,1): lambda row: self.foregroundLookup[self.parameterDict.at(row).strValue is not None]
                     }
        self.setDataLookup = {
                             (QtCore.Qt.EditRole,1): lambda index, value: self.setValue( index, value ),
                             (QtCore.Qt.UserRole,1): lambda index, value: self.setStrValue( index, value ),
                              }


    def setParameterList(self, parameterList):
        self.beginResetModel()
        self.parameterDict = SequenceDict(parameterList)
        self.targetValues = [inst.currentValue() for inst in self.parameterDict.values()]
        self.externalValues = self.targetValues[:]
        self.toolTips = [None]*len(self.externalValues )
        for index,inst in enumerate(self.parameterDict.values()):
            inst.displayValueCallback = functools.partial( self.showValue, index )
        self.endResetModel()
        
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.parameterDict)
    
    def columnCount(self,  parent=QtCore.QModelIndex()):
        return 3
    
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()),lambda row: None)(index.row())
        return None

    def setData(self,index, value, role):
        return self.setDataLookup.get( (role,index.column() ), lambda index, value: False)(index, value)
                      
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
        self._setValue( index.row(), value )
        
    def _setValue(self, row, value):
        logger = logging.getLogger(__name__)
        logger.debug( "setValue {0}".format( value ) )
        if value != self.targetValues[row]:
            self.targetValues[row] = value
            self.setValueFollowup(row)
        return True
 
    def setStrValue(self, index, strValue):
        self.parameterDict.at( index.row() ).strValue = strValue
        return True
        
    def setValueFollowup(self, row):
        logger = logging.getLogger(__name__)
        logger.debug( "setValueFollowup {0}".format( self.parameterDict.at(row).currentValue() ) )
        delay = int( self.parameterDict.at(row).settings.delay.toval('ms') )
        if not self.parameterDict.at(row).setValue( self.targetValues[row] ):
            QtCore.QTimer.singleShot(delay,functools.partial(self.setValueFollowup,row) )

    def update(self, iterable):
        for destination, name, value in iterable:
            if destination=='External':
                row = self.parameterDict.index(name)
                self.parameterDict.at(row).setSavedValue( value )     # set saved value to make this new value the default
                self.setValue( self.createIndex( row,1), value )
                self.parameterDict.at(row).strValue = None
                logging.info("Pushed to external parameter {0} value {1}".format(name,value)) 
                
    def evaluate(self, name):
        for row, value in enumerate(self.parameterDict.values()):
            expr = value.strValue
            if expr is not None:
                value = self.expression.evaluateAsMagnitude(expr, self.controlUi.globalDict)
                self._setValue( row, value )
                self.parameterDict.at(row).setSavedValue( value )     # set saved value to make this new value the default
                leftInd = self.createIndex(row, 1)
                self.dataChanged.emit( leftInd, leftInd )

class ControlUi(UiForm,UiBase):
    
    def __init__(self, globalDict=None, parent=None):
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
        self.globalDict = firstNotNone( globalDict, dict() )
    
    def setupUi(self,EnabledParameters,MainWindow):
        UiForm.setupUi(self,MainWindow)
        self.tableModel = ExternalParameterControlTableModel(self)
        self.tableView.setModel( self.tableModel )
        self.delegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.tableView.setItemDelegateForColumn(1,self.delegate) 
        self.setupParameters(EnabledParameters)
        
    def setupParameters(self,EnabledParameters):
        logger = logging.getLogger(__name__)
        logger.debug( "ControlUi.setupParameters {0}".format( EnabledParameters ) ) 
        self.enabledParameters = EnabledParameters
        self.tableModel.setParameterList( self.enabledParameters )
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setStretchLastSection(True)   
        self.evaluate(None)     
        
    def keys(self):
        return self.tableModel.parameterDict.keys()
    
    def update(self, iterable):
        self.tableModel.update( iterable )
        self.tableView.viewport().repaint()
        
    def evaluate(self, name):
        self.tableModel.evaluate(name)

    
