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
from modules.MagnitudeParser import isIdentifier
from functools import partial

api2 = sip.getapi("QVariant") == 2

class GlobalVariableTableModel(QtCore.QAbstractTableModel):
    valueChanged = QtCore.pyqtSignal(object)
    headerDataLookup = ['Name', 'Value']
    expression = Expression.Expression()
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
        self.dataLookup = { (QtCore.Qt.DisplayRole, 0): lambda row: self.variables[row].name,
                             (QtCore.Qt.DisplayRole, 1): lambda row: str(self.variables[row].value),
                             (QtCore.Qt.EditRole, 0):    lambda row: self.variables[row].name,
                             (QtCore.Qt.EditRole, 1):    lambda row: str(self.variables[row].value),
                             (QtCore.Qt.FontRole,0): lambda row: self.boldFont if self.variables[row].name in self.boldSet else self.normalFont,
                             (QtCore.Qt.FontRole,1): lambda row: self.boldFont if self.variables[row].name in self.boldSet else self.normalFont,
                             }
        self.setDataLookup = { (QtCore.Qt.EditRole, 0): self.setDataName,
                               (QtCore.Qt.EditRole, 1): self.setValue,
                               }
        self.connectAllVariableSignals()

    def connectAllVariableSignals(self):
        for item in self.variables:
            try:
                item.valueChanged.connect(self.onValueChanged, QtCore.Qt.UniqueConnection)
            except:
                pass

    def endResetModel(self):
        super(GlobalVariableTableModel, self).endResetModel()
        self.connectAllVariableSignals()

    def onValueChanged(self, name, value, origin):
        self.valueChanged.emit(name)

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
            return True
        except Exception:
            logger.exception("No match for {0}".format(str(value.toString())))
            return False
 
    def setDataName(self, index, value):
        try:
            strvalue = str(value if api2 else str(value.toString())).strip()
            if isIdentifier(strvalue):
                self.variables.updateKey(index.row(), strvalue)
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
        name = self.variables[index.row()].name
        old = self.variables.map[name]
        if not old.isIdenticalTo(value):
            self.variables.map[name] = value

    def getVariables(self):
        return self.variables.map
 
    def getVariableValue(self, name):
        return self.variables.map[name]
    
    def addVariable(self, name):
        if name=="":
            name = 'NewGlobalVariable'
        if name not in self.variables.map and isIdentifier(name):
            self.beginInsertRows(QtCore.QModelIndex(), len(self.variables), len(self.variables))
            self.variables.map[name] = magnitude.mg(0, '')
            self.variables.map.valueChanged(name).connect(partial(self.onValueChanged, name))
            self.endInsertRows()
        return len(self.variables) - 1
        
    def dropVariableByName(self, name):
        if name in self.variables.map:
            self.variables.map.pop(name)
        
    def dropVariableByIndex(self, row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        dropped = self.variables.pop(row)
        self.endRemoveRows()
        return dropped.name
    
    def sort(self, column, order):
        pass
        # if column == 0 and self.variables:
        #     self.variables.sort(reverse=order == QtCore.Qt.DescendingOrder)
        #     self.dataChanged.emit(self.index(0, 0), self.index(len(self.variables) - 1, 1))
            
    def restoreCustomOrder(self):
        pass
        # self.variables.sortToMatch( self.variables.customOrder )
        # self.dataChanged.emit(self.index(0, 0), self.index(len(self.variables) - 1, 1))
            
    def moveRow(self, rows, up=True):
        pass
        # if up:
        #     if len(rows) > 0 and rows[0] > 0:
        #         for row in rows:
        #             self.variables.swap(row, row - 1)
        #             self.dataChanged.emit(self.createIndex(row - 1, 0), self.createIndex(row, 3))
        #             self.variables.customOrder = list( self.variables._keys )
        #         return True
        # else:
        #     if len(rows) > 0 and rows[0] < len(self.variables) - 1:
        #         for row in rows:
        #             self.variables.swap(row, row + 1)
        #             self.dataChanged.emit(self.createIndex(row, 0), self.createIndex(row + 1, 3))
        #             self.variables.customOrder = list( self.variables._keys )
        #         return True
        # return False
    
    def toggleBold(self, index):
        key = self.variables[index.row()].name
        if key in self.boldSet:
            self.boldSet.remove(key)
        else:
            self.boldSet.add(key)
        self.dataChanged.emit( self.createIndex(index.row(), 0), self.createIndex(index.row(), 3) )
    
    def update(self, updlist):
        for destination, key, value in updlist:
            value = MagnitudeUtilit.mg(value)
            if destination=='Global' and key in self.variables.map:
                old = self.variables.map[key]
                if value.dimension() != old.dimension() or value != old:
                    self.variables.map[key] = value
                    index = self.variables.keyindex(key)
                    self.dataChanged.emit(self.createIndex(index, 1), self.createIndex(index, 1))

    def saveConfig(self):
        self.config['GlobalVariables.BoldSet'] = self.boldSet