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
import logging
from collections import OrderedDict

api2 = sip.getapi("QVariant")==2

class VariableTableModel(QtCore.QAbstractTableModel):
    def __init__(self, variabledict, parameterdict, parent=None, *args): 
        """ variabledict dictionary of variable value pairs as defined in the pulse programmer file
            parameterdict dictionary of parameter value pairs that can be used to calculate the value of a variable
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.variabledict = OrderedDict()
        for name,var in variabledict.iteritems():
            if var.type in ['parameter','address',None]:
                self.variabledict[name] = var
        self.variablelist = [ x for x in self.variabledict.values() if x.type=='parameter' ]
        self.expression = Expression.Expression()
        self.parameterdict = parameterdict
        self.onParameterChanged()   # make sure we update all global variables

    def setVisible(self, visibledict ):
        self.beginRemoveRows(QtCore.QModelIndex(),0,self.rowCount()-1)
        self.variablelist = []
        self.endRemoveRows()
        variablelist = sorted([ x for x in self.variabledict.values() if x.type in visibledict and visibledict[x.type] ], key=attrgetter('index'))
        self.beginInsertRows(QtCore.QModelIndex(),0,len(variablelist)-1)
        self.variablelist = variablelist
        self.endInsertRows()

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.variablelist) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 5
 
    def data(self, index, role): 
        if index.isValid():
            var = self.variablelist[index.row()]
            return { (QtCore.Qt.CheckStateRole,0): QtCore.Qt.Checked if var.enabled else QtCore.Qt.Unchecked,
                     (QtCore.Qt.DisplayRole,1): var.name,
                     (QtCore.Qt.DisplayRole,2): str(var.strvalue if hasattr(var,'strvalue') else var.value),
                     (QtCore.Qt.DisplayRole,3): str(var.encoding),
                     (QtCore.Qt.DisplayRole,4): str(var.value),
                     (QtCore.Qt.EditRole,2): str(var.strvalue if hasattr(var,'strvalue') else var.value),
                     (QtCore.Qt.EditRole,3): str(var.encoding),
                     }.get((role,index.column()))
        return None
        
    def setDataValue(self, index, value):
        try:
            strvalue = str(value if api2 else str(value.toString()))
            variables = self.getVariables()
            variables.update( self.parameterdict )
            result = self.expression.evaluate(strvalue,variables)           
            if isinstance(result, magnitude.Magnitude) and result.dimensionless():
                result.output_prec(0)
            var = self.variablelist[index.row()]
            var.value = result
            var.strvalue = strvalue
            return True    
        except Exception:
            logger = logging.getLogger(__name__)
            logger.error( "No match for {0}".format(value.toString()) )
            return False
        
    def createDependencyGraph(self):
        pass
        
    def onParameterChanged(self):
        for row, var in enumerate(self.variablelist):
            if hasattr(var,'strvalue'):
                result = self.expression.evaluate(var.strvalue, self.parameterdict)
                var.value = result
                self.dataChanged.emit( self.index(row,4), self.index(row,4) )
        
    def setDataEncoding(self,index, value):
        value = str(value.toString())
        self.variablelist[index.row()].encoding = None if value == 'None' else str(value)
        return True
        
    def setVarEnabled(self,index,value):
        print "parameter enabled", value==QtCore.Qt.Checked
        self.variablelist[index.row()].enabled = value == QtCore.Qt.Checked
        return True      

    def setData(self,index, value, role):
        return { (QtCore.Qt.CheckStateRole,0): functools.partial( self.setVarEnabled, index, value ),
                 (QtCore.Qt.EditRole,2): functools.partial( self.setDataValue, index, value ),
                 (QtCore.Qt.EditRole,3): functools.partial( self.setDataEncoding, index, value ),
                }.get((role,index.column()), lambda: False )()

    def flags(self, index ):
        return { 0: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable |  QtCore.Qt.ItemIsEnabled,
                 1: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled,
                 2: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
                 3: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
                 4: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled
                 }.get(index.column(),QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return {
                    0: 'use',
                    1: 'variable',
                    2: 'value',
                    3: 'encoding',
                    4: 'evaluated'
                    }.get(section)
        return None #QtCore.QVariant()
        
    def getVariables(self):
        myvariables = dict()
        for name,var in self.variabledict.iteritems():
            myvariables[name] = var.value if var.enabled else 0
        return myvariables
 
    def getVariableValue(self,name):
        var = self.variabledict.get(name)
        return var.value if var.enabled else 0
