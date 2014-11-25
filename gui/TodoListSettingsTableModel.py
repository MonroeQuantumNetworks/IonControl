# -*- coding: utf-8 -*-
"""
Created on Fri Feb 08 22:02:08 2013

@author: pmaunz
"""
import logging

from PyQt4 import QtCore
import sip

from modules import Expression
import modules.magnitude as magnitude
from externalParameter.persistence import DBPersist
from externalParameter.decimation import StaticDecimation
import time
from functools import partial
from collections import defaultdict

api2 = sip.getapi("QVariant") == 2

class TodoListSettingsTableModel(QtCore.QAbstractTableModel):
    headerDataLookup = ['Name', 'Value']
    expression = Expression.Expression()
    persistSpace = 'globalVar'
    def __init__(self, settings, globalDict, parent=None, *args): 
        """ variabledict dictionary of variable value pairs as defined in the pulse programmer file
            parameterdict dictionary of parameter value pairs that can be used to calculate the value of a variable
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.variables = settings
        self.globalDict = globalDict
        self.dataLookup = { (QtCore.Qt.DisplayRole, 0): lambda row: self.variables.keyAt(row),
                             (QtCore.Qt.DisplayRole, 1): lambda row: str(self.variables.at(row)),
                             (QtCore.Qt.EditRole, 0):    lambda row: self.variables.keyAt(row),
                             (QtCore.Qt.EditRole, 1):    lambda row: str(self.variables.at(row)),
                             }
        self.setDataLookup = { (QtCore.Qt.EditRole, 0): self.setDataName,
                               (QtCore.Qt.EditRole, 1): self.setValue,
                               }
        self.decimation = defaultdict(lambda: StaticDecimation(magnitude.mg(10, 's')))
        self.persistence = DBPersist()

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.variables) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 2
 
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role, index.column()), lambda row: None)(index.row())
        return None
        
    def setDataValue(self, index, value):
        logger = logging.getLogger(__name__)
        try:
            strvalue = str(value if api2 else str(value.toString()))
            result = self.expression.evaluate(strvalue, self.variabledict)
            name = self.variables.keyAt(index.row())
            self.variables[name] = result
            self.decimation[name].decimate(time.time(), result, partial(self.persistCallback, name))
            return True    
        except Exception:
            logger.exception("No match for {0}".format(str(value.toString())))
            return False
 
    def setDataName(self, index, value):
        try:
            strvalue = str(value).strip()
            
            self.variables.renameAt(index.row(), strvalue)
            return True    
        except Exception:
            logger = logging.getLogger(__name__)
            logger.exception("No match for {0}".format(str(value.toString())))
            return False
       
    def setData(self, index, value, role):
        return self.setDataLookup.get((role, index.column()), lambda row, value: False)(index, value)

    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled

    def headerData(self, section, orientation, role):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
        return None  # QtCore.QVariant()
            
    def setValue(self, index, value):
        if index.column()==1:
            name = self.variables.keyAt(index.row())
            old = self.variables[name]
            if not old.isIdenticalTo(value):
                self.variables[name] = value
        elif index.column()==0:
            self.setDataName( index, value )

    def getVariables(self):
        return self.variables
 
    def getVariableValue(self, name):
        return self.variables[name]
    
    def addSetting(self):
        if None not in self.variables:
            self.beginInsertRows(QtCore.QModelIndex(), len(self.variables), len(self.variables))
            self.variables[None] = magnitude.mg(0, '')
            self.endInsertRows()
        return len(self.variables) - 1
        
    def dropSetting(self, row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        name = self.variables.keyAt(row)
        self.variables.pop(name)
        self.endRemoveRows()
        return name
    
    def choice(self, index):
        if index.column()==0:
            return self.globalDict.keys()
        return None
    
    def setSettings(self, settings):
        self.beginResetModel()
        self.variables = settings
        self.endResetModel()
