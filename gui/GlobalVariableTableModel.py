# -*- coding: utf-8 -*-
"""
Created on Fri Feb 08 22:02:08 2013

@author: pmaunz
"""
import logging

from PyQt4 import QtCore, QtGui
import sip

from modules import Expression
import modules.magnitude as magnitude
from modules import MagnitudeUtilit
from externalParameter.persistence import DBPersist
from externalParameter.decimation import StaticDecimation
import time
from modules.magnitude import is_magnitude
from functools import partial
from collections import defaultdict
from modules.MagnitudeParser import isIdentifier

api2 = sip.getapi("QVariant") == 2

class GlobalVariableTableModel(QtCore.QAbstractTableModel):
    valueChanged = QtCore.pyqtSignal(object)
    headerDataLookup = ['Name', 'Value']
    expression = Expression.Expression()
    persistSpace = 'globalVar'
    def __init__(self, config, variables, parent=None, *args): 
        """ variabledict dictionary of variable value pairs as defined in the pulse programmer file
            parameterdict dictionary of parameter value pairs that can be used to calculate the value of a variable
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.config = config
        self.variables = variables
        self.normalFont = QtGui.QFont("MS Shell Dlg 2",-1,QtGui.QFont.Normal )
        self.boldFont = QtGui.QFont("MS Shell Dlg 2",-1,QtGui.QFont.Bold )
        self.boldSet = self.config.get('GlobalVariables.BoldSet', set())
        self.dataLookup = { (QtCore.Qt.DisplayRole, 0): lambda row: self.variables.keyAt(row),
                             (QtCore.Qt.DisplayRole, 1): lambda row: str(self.variables.at(row)),
                             (QtCore.Qt.EditRole, 0):    lambda row: self.variables.keyAt(row),
                             (QtCore.Qt.EditRole, 1):    lambda row: str(self.variables.at(row)),
                             (QtCore.Qt.FontRole,0): lambda row: self.boldFont if self.variables.keyAt(row) in self.boldSet else self.normalFont,
                             (QtCore.Qt.FontRole,1): lambda row: self.boldFont if self.variables.keyAt(row) in self.boldSet else self.normalFont,
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
            self.valueChanged.emit(name)
            self.variables.observables[name].fire(name=name, value=result)
            self.decimation[name].decimate(time.time(), result, partial(self.persistCallback, name))
            return True    
        except Exception:
            logger.exception("No match for {0}".format(str(value.toString())))
            return False
 
    def persistCallback(self, source, data):
        time, value, minval, maxval = data
        unit = None
        if is_magnitude(value):
            value, unit = value.toval(returnUnit=True)
        self.persistence.persist(self.persistSpace, source, time, value, minval, maxval, unit)

    def setDataName(self, index, value):
        try:
            strvalue = str(value if api2 else str(value.toString())).strip()
            if isIdentifier(strvalue):
                self.variables.renameAt(index.row(), strvalue)
                return True
            else:
                logging.getLogger(__name__).warning("'{0}' is not a valid identifier".format(strvalue))    
                return False
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
        name = self.variables.keyAt(index.row())
        old = self.variables[name]
        if not old.isIdenticalTo(value):
            self.variables[name] = value
            self.valueChanged.emit(name)
            self.variables.observables[name].fire(name=name, value=value)
            self.decimation[name].decimate(time.time(), value, partial(self.persistCallback, name))

    def getVariables(self):
        return self.variables
 
    def getVariableValue(self, name):
        return self.variables[name]
    
    def addVariable(self, name):
        if name=="":
            name = 'NewGlobalVariable'
        if name not in self.variables and isIdentifier(name):
            self.beginInsertRows(QtCore.QModelIndex(), len(self.variables), len(self.variables))
            self.variables[name] = magnitude.mg(0, '')
            self.endInsertRows()
        return len(self.variables) - 1
        
    def dropVariableByName(self, name):
        if name in self.variables:
            self.dropVariableByIndex(self.variables.index(name))        
        
    def dropVariableByIndex(self, row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        name = self.variables.keyAt(row)
        self.variables.pop(name)
        self.endRemoveRows()
        return name
    
    def sort(self, column, order):
        if column == 0 and self.variables:
            self.variables.sort(reverse=order == QtCore.Qt.DescendingOrder)
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.variables) - 1, 1))
            
    def restoreCustomOrder(self):
        self.variables.sortToMatch( self.variables.customOrder )
        self.dataChanged.emit(self.index(0, 0), self.index(len(self.variables) - 1, 1))
            
    def moveRow(self, rows, up=True):
        if up:
            if len(rows) > 0 and rows[0] > 0:
                for row in rows:
                    self.variables.swap(row, row - 1)
                    self.dataChanged.emit(self.createIndex(row - 1, 0), self.createIndex(row, 3))
                    self.variables.customOrder = list( self.variables._keys )
                return True
        else:
            if len(rows) > 0 and rows[0] < len(self.variables) - 1:
                for row in rows:
                    self.variables.swap(row, row + 1)
                    self.dataChanged.emit(self.createIndex(row, 0), self.createIndex(row + 1, 3))
                    self.variables.customOrder = list( self.variables._keys )
                return True
        return False
    
    def toggleBold(self, index):
        key = self.variables.keyAt(index.row())
        if key in self.boldSet:
            self.boldSet.remove(key)
        else:
            self.boldSet.add(key)
        self.dataChanged.emit( self.createIndex(index.row(), 0), self.createIndex(index.row(), 3) )
    
    def update(self, updlist):
        for destination, key, value in updlist:
            value = MagnitudeUtilit.mg(value)
            if destination=='Global' and key in self.variables:
                old = self.variables[key]
                if value.dimension() != old.dimension() or value != old:
                    self.variables[key] = value
                    self.variables.observables[key].fire(name=key, value=value)
                    self.valueChanged.emit(key)
                    index = self.variables.index(key)
                    self.dataChanged.emit(self.createIndex(index, 1), self.createIndex(index, 1))
                    self.decimation[key].decimate(time.time(), value, partial(self.persistCallback, key))

    def saveConfig(self):
        self.config['GlobalVariables.BoldSet'] = self.boldSet