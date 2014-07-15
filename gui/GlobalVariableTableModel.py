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
from modules import MagnitudeUtilit


api2 = sip.getapi("QVariant")==2

class GlobalVariableTableModel(QtCore.QAbstractTableModel):
    valueChanged = QtCore.pyqtSignal( object )
    headerDataLookup = ['Name', 'Value']
    expression = Expression.Expression()
    def __init__(self, variables, parent=None, *args): 
        """ variabledict dictionary of variable value pairs as defined in the pulse programmer file
            parameterdict dictionary of parameter value pairs that can be used to calculate the value of a variable
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.variables = variables
        self.dataLookup =  { (QtCore.Qt.DisplayRole,0): lambda row: self.variables.keyAt(row),
                             (QtCore.Qt.DisplayRole,1): lambda row: str(self.variables.at(row)),
                             (QtCore.Qt.EditRole,0):    lambda row: self.variables.keyAt(row),
                             (QtCore.Qt.EditRole,1):    lambda row: str(self.variables.at(row)),
                             }
        self.setDataLookup = { (QtCore.Qt.EditRole,0): self.setDataName,
                               (QtCore.Qt.EditRole,1): self.setValue,
                               }

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.variables) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 2
 
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()),lambda row: None)(index.row())
        return None
        
    def setDataValue(self, index, value):
        logger = logging.getLogger(__name__)
        try:
            strvalue = str(value if api2 else str(value.toString()))
            result = self.expression.evaluate(strvalue,self.variabledict)
            name = self.variables.keyAt(index.row())
            self.variables[name] = result
            self.valueChanged.emit(name)
            return True    
        except Exception:
            logger.exception( "No match for {0}".format( str(value.toString()) ) )
            return False
 
    def setDataName(self, row, value):
        try:
            strvalue = str(value if api2 else str(value.toString())).strip()
            
            self.variables.renameAt(row, strvalue)
            return True    
        except Exception:
            logger = logging.getLogger(__name__)
            logger.exception( "No match for {0}".format( str(value.toString()) ) )
            return False
       
    def setData(self,index, value, role):
        return self.setDataLookup.get((role,index.column()), lambda row, value: False )(index, value)

    def flags(self, index ):
        return QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
        return None #QtCore.QVariant()
            
    def setValue(self, index, value):
        name = self.variables.keyAt(index.row())
        old = self.variables[name]
        if not old.isIdenticalTo(value):
            self.variables[name] = value
            self.valueChanged.emit(name)

    def getVariables(self):
        return self.variables
 
    def getVariableValue(self,name):
        return self.variables[name]
    
    def addVariable(self,name):
        if name not in self.variables:
            self.beginInsertRows(QtCore.QModelIndex(),len(self.variables),len(self.variables))
            self.variables[name] = magnitude.mg(0,'')
            self.endInsertRows()
        return len(self.variables)-1
        
    def dropVariableByName(self, name):
        if name in self.variables:
            self.dropVariableByIndex(self.variables.index(name))        
        
    def dropVariableByIndex(self,row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row )
        name = self.variables.keyAt(row)
        self.variables.pop(name)
        self.endRemoveRows()
        return name
    
    def sort(self, column, order ):
        if column==0 and self.variables:
            self.variables.sort(reverse=order==QtCore.Qt.DescendingOrder)
            self.dataChanged.emit(self.index(0,0),self.index(len(self.variables) -1,1))
            
    def moveRow(self, rows, up=True):
        if up:
            if len(rows)>0 and rows[0]>0:
                for row in rows:
                    self.variables.swap(row, row-1 )
                    self.dataChanged.emit( self.createIndex(row-1,0), self.createIndex(row,3) )
                return True
        else:
            if len(rows)>0 and rows[0]<len(self.variables)-1:
                for row in rows:
                    self.variables.swap(row, row+1 )
                    self.dataChanged.emit( self.createIndex(row,0), self.createIndex(row+1,3) )
                return True
        return False
    
    def update(self, updlist ):
        for key, value in updlist:
            value = MagnitudeUtilit.mg(value)
            if key in self.variables:
                old = self.variables[key]
                if value.dimension()!=old.dimension() or value!=old:
                    self.variables[key] = value
                    self.valueChanged.emit(key)
                    index = self.variables.index(key)
                    self.dataChanged.emit( self.createIndex(index,1), self.createIndex(index,1))
