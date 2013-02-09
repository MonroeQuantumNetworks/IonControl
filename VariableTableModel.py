# -*- coding: utf-8 -*-
"""
Created on Fri Feb 08 22:02:08 2013

@author: pmaunz
"""
from PyQt4 import QtCore, QtGui
from operator import attrgetter
import functools
import re
import magnitude

class VariableTableModel(QtCore.QAbstractTableModel):
    def __init__(self, variabledict, parent=None, *args): 
        """ datain: a list where each item is a row
        
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.variabledict = variabledict.copy()
        self.variablelist = sorted([ x for x in self.variabledict.values() if x.type=='parameter' ], key=attrgetter('index')) 
        print self.variablelist 

    def setVisible(self, visibledict ):
        print self.rowCount()
        self.beginRemoveRows(QtCore.QModelIndex(),0,self.rowCount()-1)
        self.variablelist = []
        self.endRemoveRows()
        variablelist = sorted([ x for x in self.variabledict.values() if x.type in visibledict and visibledict[x.type] ], key=attrgetter('index'))
        print variablelist, len(variablelist)
        self.beginInsertRows(QtCore.QModelIndex(),0,len(variablelist)-1)
        self.variablelist = variablelist
        self.endInsertRows()

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.variablelist) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 3
 
    def data(self, index, role): 
        if index.isValid():
            return { (QtCore.Qt.DisplayRole,0): self.variablelist[index.row()].name,
                     (QtCore.Qt.DisplayRole,1): str(self.variablelist[index.row()].value),
                     (QtCore.Qt.DisplayRole,2): str(self.variablelist[index.row()].encoding),
                     (QtCore.Qt.EditRole,1): str(self.variablelist[index.row()].value),
                     (QtCore.Qt.EditRole,2): str(self.variablelist[index.row()].encoding),
                     }.get((role,index.column()))
        return None
        
    def setDataValue(self, index, value):
        m = re.match("\s*([-+0-9.]+)\s*(\w*)\s*",str(value.toString()))
        if m:
            value, unit = m.groups()
            print value, unit
            mag = magnitude.mg( float(value), unit )
            if mag.dimensionless():
                mag.output_prec(0)
            self.variablelist[index.row()].value = mag
            print self.variablelist[index.row()].value
            return True    
        print "No match for", str(value.toString())
        return False
        
    def setDataEncoding(self,index, value):
        value = str(value.toString())
        self.variablelist[index.row()].encoding = None if value == 'None' else str(value)
        return True

    def setData(self,index, value, role):
        return { (QtCore.Qt.EditRole,1): functools.partial( self.setDataValue, index, value ),
                 (QtCore.Qt.EditRole,2): functools.partial( self.setDataEncoding, index, value ),
                }.get((role,index.column()), lambda: False )()

    def flags(self, index ):
        return { 0: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled,
                 1: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
                 2: QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
                 }.get(index.column(),QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return {
                    0: 'variable',
                    1: 'value',
                    2: 'encoding',
                    }.get(section)
        return None #QtCore.QVariant()
