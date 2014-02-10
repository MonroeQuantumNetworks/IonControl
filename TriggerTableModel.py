# -*- coding: utf-8 -*-
"""
Created on Fri Feb 08 22:02:08 2013

@author: pmaunz
"""
from PyQt4 import QtCore, QtGui
import functools

class TriggerTableModel(QtCore.QAbstractTableModel):
    def __init__(self, variabledict, channelNameData, parent=None, *args): 
        """ datain: a list where each item is a row
        
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.variabledict = variabledict
        self.variablelist = [ x for x in self.variabledict.values() if x.type=='trigger' ]
        self.channelNames, self.channelSignal = channelNameData
        self.channelSignal.dataChanged.connect( self.onHeaderChanged )

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.variablelist) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 32
 
    def currentState(self,index):
        data = self.variablelist[index.row()].data
        bit = 0x80000000>>index.column()
        return bool( bit & data )
        
    def setState(self,index,state):
        bit = 0x80000000>>index.column()
        var = self.variablelist[index.row()]
        if state:
            var.data = (var.data & ~bit) | bit
        else:
            var.data = var.data & ~bit 
        self.dataChanged.emit(index,index)
                
    def displayData(self,index):
        return str(self.currentState(index))
        
    def displayDataColor(self,index):
        return QtGui.QColor(QtCore.Qt.green) if self.currentState(index) else QtGui.QColor(QtCore.Qt.white)
  
    def data(self, index, role): 
        if index.isValid():
            return { #(QtCore.Qt.DisplayRole): functools.partial( self.displayData, index),
                     (QtCore.Qt.BackgroundColorRole): functools.partial( self.displayDataColor, index),
                     }.get(role,lambda : None)()
        return None
        
    def flags(self, index ):
        return  QtCore.Qt.ItemIsEnabled 

    def onHeaderChanged(self, first, last):
        self.headerDataChanged.emit( QtCore.Qt.Horizontal, first, last )        

    def headerData(self, section, orientation, role ):
        index = 31-section
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal):
                if index in self.channelNames.names:
                    return self.channelNames.names[index]
                return index
            elif (orientation == QtCore.Qt.Vertical): 
                return self.variablelist[section].name
        return None #QtCore.QVariant()

    def onClicked(self,index):
        self.setState(index,not self.currentState(index))

    def getVariables(self):
        myvariables = dict()
        for var in self.variablelist:
            myvariables[var.name] = var.data
        return myvariables
