# -*- coding: utf-8 -*-
"""
Created on Fri Feb 08 22:02:08 2013

@author: pmaunz
"""
from PyQt4 import QtCore
from modules import Expression

class Parameter:
    def __init__(self,name, value, strvalue=None):
        self.name = name
        self.value = value
        self.strvalue = strvalue

class ParameterTableModel(QtCore.QAbstractTableModel):
    def __init__(self, variabledict, parameterdict, parent=None, *args): 
        """ variabledict dictionary of variable value pairs as defined in the pulse programmer file
            parameterdict dictionary of parameter value pairs that can be used to calculate the value of a variable
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.variabledict = variabledict
        self.parameterlist = [ Parameter(name, val ) for name, val in parameterdict.iteritems() ]
        self.expression = Expression.Expression()
        self.parameterdict = parameterdict

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.parameterlist) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 3
 
    def data(self, index, role): 
        if index.isValid():
            par = self.parameterlist[index.row()]
            return { (QtCore.Qt.DisplayRole,0): par.name,
                     (QtCore.Qt.DisplayRole,1): str(par.strvalue if par.strvalue is not None else par.value),
                     (QtCore.Qt.DisplayRole,2): str(par.value),
                     (QtCore.Qt.EditRole,1): str(par.strvalue if par.strvalue is not None else par.value),
                     }.get((role,index.column()))
        return None
        
    def setDataValue(self, index, value):
        try:
            strvalue = str(value.toString())
            result = self.expression.evaluate(strvalue,self.parameterdict)           
            if result.dimensionless():
                result.output_prec(0)
            var = self.parameterlist[index.row()]
            var.value = result
            var.strvalue = strvalue
            self.parameterdict[var.name] = result
            return True    
        except Exception as e:
            print e, "No match for", str(value.toString())
            return False
        
    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole and index.column()==1:
            return self.setDataValue( index, value )
        return False
        
    def flags(self, index ):
        return { 0: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled,
                 1: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
                 2: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled,
                 }.get(index.column(),QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return {
                    0: 'variable',
                    1: 'value',
                    2: 'evaluated'
                    }.get(section)
        return None #QtCore.QVariant()
        
    def getVariables(self):
        myvariables = dict()
        for name,var in self.variabledict.iteritems():
            myvariables[name] = var.value
        return myvariables
        
    def getVariableValue(self,name):
        return self.variabledict.get(name).value()
 