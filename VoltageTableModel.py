# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 13:06:13 2013

@author: wolverine
"""

from PyQt4 import QtCore, QtGui

class VoltageTableModel(QtCore.QAbstractTableModel):
    def __init__(self, voltageBlender, parent=None, *args): 
        """ datain: a list where each item is a row
        
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.blender = voltageBlender
        #self.electrodes, self.aoNums, self.dsubNums, self.outputVoltage

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.blender.electrodes) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 4
 
    def onDataChanged(self,x1,y1,x2,y2):
        self.dataChanged.emit(self.index(x1,y1),self.index(x2,y2))
        print "VoltageTableModel dataChanged", x1,y1,x2,y2
 
        
    def displayToolTip(self, index):
        return "ToolTip"
  
    def data(self, index, role): 
        if role!=QtCore.Qt.DisplayRole:
            return None
        if index.isValid():
            return { 0: str(self.blender.electrodes[index.row()]) if self.blender.electrodes is not None else None,
                     1: str(self.blender.outputVoltage[index.row()]) if self.blender.outputVoltage is not None else None,
                     2: self.blender.aoNums[index.row()] if self.blender.aoNums is not None else None,
                     3: self.blender.dsubNums[index.row()] if self.blender.dsubNums is not None else None,
                     }.get(index.column(),lambda : None)
        return None
        
    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return { 0: "Electrode", 1: "voltage", 2: "ao channel", 3: "dsub pin" }[section]
            elif (orientation == QtCore.Qt.Vertical): 
                return section
        return None #QtCore.QVariant()

    def flags(self, index ):
        return QtCore.Qt.ItemIsEnabled 
