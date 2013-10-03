# -*- coding: utf-8 -*-
"""
Created on Fri Feb 08 22:02:08 2013

@author: pmaunz
"""
from PyQt4 import QtCore
from operator import attrgetter
import functools
import modules.magnitude as magnitude
from modules import Expression
import sip

api2 = sip.getapi("QVariant")==2

class GlobalVariableTableModel(QtCore.QAbstractTableModel):
    def __init__(self, variabledict, parent=None, *args): 
        """ variabledict dictionary of variable value pairs as defined in the pulse programmer file
            parameterdict dictionary of parameter value pairs that can be used to calculate the value of a variable
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.variabledict = variabledict
        self.variableList = self.variabledict.values() 
        self.variableKeys = self.variabledict.keys()
        self.expression = Expression.Expression()

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.variableList) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 2
 
    def data(self, index, role): 
        if index.isValid():
            var = self.variableList[index.row()]
            return { (QtCore.Qt.DisplayRole,0): self.variableKeys[index.row()],
                     (QtCore.Qt.DisplayRole,1): str(self.variableList[index.row()]),
                     (QtCore.Qt.EditRole,0): self.variableKeys[index.row()],
                     (QtCore.Qt.EditRole,1): str(self.variableList[index.row()]),
                     }.get((role,index.column()))
        return None
        
    def setDataValue(self, index, value):
        print "setDataValue", index.row(), index.column(), value
        try:
            strvalue = str(value if api2 else str(value.toString()))
            result = self.expression.evaluate(strvalue,self.variabledict)
            name = self.variableKeys[ index.row() ] 
            self.variabledict[name] = result
            self.variableList[ index.row() ] = self.variabledict[ name ]        
            return True    
        except Exception as e:
            print e, "No match for", str(value.toString())
            return False
 
    def setDataName(self, index, value):
        print "setDataName", index.row(), index.column(), value
        try:
            strvalue = str(value if api2 else str(value.toString())).strip()
            name = self.variableKeys[ index.row() ] 
            self.variableKeys[ index.row() ] = strvalue
            value = self.variabledict.pop(name)
            self.variabledict[strvalue] = value
            return True    
        except Exception as e:
            print e, "No match for", str(value.toString())
            return False
       
    def setData(self,index, value, role):
        return { (QtCore.Qt.EditRole,0): functools.partial( self.setDataName, index, value ),
                 (QtCore.Qt.EditRole,1): functools.partial( self.setDataValue, index, value ),
                }.get((role,index.column()), lambda: False )()

    def flags(self, index ):
        return { 0: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
                 1: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
                 }.get(index.column(),QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return {
                    0: 'Name',
                    1: 'value',
                     }.get(section)
        return None #QtCore.QVariant()
        
    def getVariables(self):
        return self.variabledict
 
    def getVariableValue(self,name):
        return self.variabledict[name]
    
    def addVariable(self,name):
        if name not in self.variabledict:
            print "addVariable"
            self.beginInsertRows(QtCore.QModelIndex(),len(self.variabledict),len(self.variabledict))
            self.variabledict[name] = magnitude.mg(0,'')
            self.variableList = list(self.variabledict.values())
            self.variableKeys = list(self.variabledict.keys())
            self.endInsertRows()
        return len(self.variableKeys)-1
        
    def dropVariableByName(self, name):
        if name in self.calibrations:
            self.dropVariableByIndex(self.variableKeys.index(name))        
        
    def dropVariableByIndex(self,index):
        print self.variabledict.keys(), index
        self.beginRemoveRows(QtCore.QModelIndex(),index,index)
        name = self.variableKeys[index]
        self.variabledict.pop(name)
        self.variableList = list(self.variabledict.values())
        self.variableKeys = list(self.variabledict.keys())
        print "dropCAlibration", self.variableKeys 
        self.endRemoveRows()
        print self.variabledict.keys()
        return name
    
