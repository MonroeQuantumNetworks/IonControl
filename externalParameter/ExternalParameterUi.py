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
from modules.Observable import Observable
import itertools

UiForm, UiBase = PyQt4.uic.loadUiType(r'ui\ExternalParameterUi.ui')

class ExternalParameterControlTableModel( QtCore.QAbstractTableModel ):
    valueChanged = QtCore.pyqtSignal(str, object)
    expression = Expression()
    backgroundLookup = {True:QtGui.QColor(QtCore.Qt.green).lighter(175), False:QtGui.QColor(QtCore.Qt.white)}
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
                             #(QtCore.Qt.ToolTipRole,2): lambda row: str(self.toolTips[row]),
                             (QtCore.Qt.BackgroundRole,1): lambda row: self.backgroundLookup[self.parameterDict.at(row).strValue is not None],
                             (QtCore.Qt.ToolTipRole,1): lambda row: self.parameterDict.at(row).strValue if self.parameterDict.at(row).strValue is not None else None
                     }
        self.setDataLookup = {
                             (QtCore.Qt.EditRole,1): lambda index, value: self.setValue( index, value ),
                             (QtCore.Qt.UserRole,1): lambda index, value: self.setStrValue( index, value ),
                              }
        self.adjustingDevices = 0
        self.doneAdjusting = Observable()

    def setParameterList(self, outputChannelDict):
        self.beginResetModel()
        self.parameterDict = SequenceDict(outputChannelDict)
        self.targetValues = [inst.value for inst in self.parameterDict.values()]
        self.externalValues = self.targetValues[:]
        self.toolTips = [None]*len(self.externalValues )
        for index,inst in enumerate(self.parameterDict.values()):
            inst.observable.clear()
            inst.observable.subscribe( functools.partial( self.showValue, index ) )
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
        self.externalValues[index] = value.value
        self.toolTips[index] = tooltip
        leftInd = self.createIndex(index, 2)
        rightInd = self.createIndex(index, 2)
        self.dataChanged.emit(leftInd, rightInd) 
            
    def setValue(self, index, value):
        self._setValue( index.row(), value )
        
    def _setValue(self, row, value):
        logger = logging.getLogger(__name__)
        logger.debug( "setValue {0}".format( value ) )
        if self.targetValues[row] is None or value != self.targetValues[row]:
            self.targetValues[row] = value
            self.adjustingDevices += 1
            logger.debug("Increased adjusting instruments to {0}".format(self.adjustingDevices))
            self.setValueFollowup(row)
        return True
 
    def setStrValue(self, index, strValue):
        self.parameterDict.at( index.row() ).strValue = strValue
        return True
        
    def setValueFollowup(self, row):
        try:
            logger = logging.getLogger(__name__)
            logger.debug( "setValueFollowup {0}".format( self.parameterDict.at(row).value ) )
            delay = int( self.parameterDict.at(row).delay.toval('ms') )
            if not self.parameterDict.at(row).setValue( self.targetValues[row] ):
                QtCore.QTimer.singleShot(delay,functools.partial(self.setValueFollowup,row) )
            else:
                self.adjustingDevices -= 1
                logger.debug("Decreased adjusting instruments to {0}".format(self.adjustingDevices))
                if self.adjustingDevices==0:
                    self.doneAdjusting.firebare()
                    self.doneAdjusting.callbacks = list()
        except Exception as e:
            logger.exception(e)
            logger.warning( "Exception during setValueFollowup, number of adjusting devices likely to be faulty")

    def update(self, iterable):
        for destination, name, value in iterable:
            if destination=='External':
                row = self.parameterDict.index(name)
                self.parameterDict.at(row).savedValue = value    # set saved value to make this new value the default
                self.setValue( self.createIndex( row,1), value )
                self.parameterDict.at(row).strValue = None
                logging.info("Pushed to external parameter {0} value {1}".format(name,value)) 
                
    def evaluate(self, name):
        for row, value in enumerate(self.parameterDict.values()):
            expr = value.strValue
            if expr is not None:
                value = self.expression.evaluateAsMagnitude(expr, self.controlUi.globalDict)
                self._setValue( row, value )
                self.parameterDict.at(row).savedValue = value   # set saved value to make this new value the default
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
    
    def setupUi(self, outputChannels ,MainWindow):
        UiForm.setupUi(self,MainWindow)
        self.tableModel = ExternalParameterControlTableModel(self)
        self.tableView.setModel( self.tableModel )
        self.delegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.tableView.setItemDelegateForColumn(1,self.delegate) 
        self.setupParameters( outputChannels )
        
    def setupParameters(self, outputChannels):
        self.tableModel.setParameterList( outputChannels )
        self.tableView.resizeColumnsToContents()
        self.tableView.horizontalHeader().setStretchLastSection(True)   
        try:
            self.evaluate(None)
        except KeyError as e:
            logging.getLogger(__name__).warning(str(e))
        
    def keys(self):
        return self.tableModel.parameterDict.keys()
    
    def update(self, iterable):
        self.tableModel.update( iterable )
        self.tableView.viewport().repaint()
        
    def evaluate(self, name):
        self.tableModel.evaluate(name)
        
    def isAdjusting(self):
        return self.tableModel.adjustingDevices>0
    
    def callWhenDoneAdjusting(self, callback):
        if self.isAdjusting():
            self.tableModel.doneAdjusting.subscribe(callback)
        else:
            QtCore.QTimer.singleShot(0, callback)
            

    
