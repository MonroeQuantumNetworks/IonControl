# -*- coding: utf-8 -*-
"""
Created on Fri Feb 08 22:02:08 2013

@author: pmaunz
"""
import functools
import re

from PyQt4 import QtCore, QtGui


class ShutterTableModel(QtCore.QAbstractTableModel):
    def __init__(self, variabledict, channelNameData, parent=None, *args): 
        """ datain: a list where each item is a row
        
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.variabledict = variabledict
        self.maskdict = dict()
        self.variablelist = []
        for name, var in self.variabledict.iteritems():
            if var.type is not None:
                m = re.match("\s*shutter(?:\s+(\w+)){0,1}",var.type)
                if m:
                    self.variablelist.append(var)
                    if m.group(1) is not None and m.group(1) in self.variabledict:
                        self.maskdict[name] = self.variabledict[m.group(1)]
        #self.variablelist = sorted(self.variablelist, key=attrgetter('index')) 
        #print self.variablelist 
        self.channelNames, self.channelSignal = channelNameData
        self.channelSignal.dataChanged.connect( self.onHeaderChanged )

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.variablelist) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 32
 
    def currentState(self,index):
        var = self.variablelist[index.row()]
        mask = self.maskdict[var.name].data if var.name in self.maskdict else 0xffffffff
        value = var.data
        bit = 0x80000000>>index.column()
        if mask & bit:
            if value & bit:
                return 1
            else:
                return -1
        else:
            return 0
        
    def setState(self,index,state):
        bit = 0x80000000>>index.column()
        var = self.variablelist[index.row()]
        if var.name in self.maskdict:
            if state == 0:
                self.maskdict[var.name].data = self.maskdict[var.name].data & ~bit 
            else:
                self.maskdict[var.name].data = (self.maskdict[var.name].data & ~bit) | bit
        if state == -1:
            var.data = var.data & ~bit 
        elif state == 1:
            var.data = (var.data & ~bit) | bit
        self.dataChanged.emit(index,index)
        
        
    def displayData(self,index):
        return str(self.currentState(index))
        
    colorLookup = { -1: QtGui.QColor(QtCore.Qt.red), 0: QtGui.QColor(QtCore.Qt.white), 1: QtGui.QColor(QtCore.Qt.green) }
    def displayDataColor(self,index):
        return self.colorLookup[self.currentState(index)]
        
    def displayToolTip(self, index):
        return "ToolTip"
  
    def data(self, index, role): 
        if index.isValid():
            return { #(QtCore.Qt.DisplayRole): functools.partial( self.displayData, index),
                     (QtCore.Qt.BackgroundColorRole): functools.partial( self.displayDataColor, index),
                     #(QtCore.Qt.ToolTipRole): functools.partial( self.displayToolTip, index )
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
        oldState = self.currentState(index)
        if self.variablelist[index.row()].name in self.maskdict:
            newState = (oldState+2)%3 -1
        else:
            newState = -oldState
        self.setState(index,newState)
        #print index.row(), index.column()
        
    def getVariables(self):
        returndict = dict()
        #print "Maskdict: ", self.maskdict
        for var in self.maskdict.values() + self.variablelist:
            returndict[var.name] = var.data
        return returndict