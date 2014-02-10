# -*- coding: utf-8 -*-
"""
Created on Fri Feb 08 22:02:08 2013

@author: pmaunz
"""
from PyQt4 import QtCore, QtGui
import sip
import logging
api2 = sip.getapi("QVariant")==2


class ShutterHardwareTableModel(QtCore.QAbstractTableModel):
    onColor =  QtGui.QColor(QtCore.Qt.green)
    offColor =  QtGui.QColor(QtCore.Qt.red)
    def __init__(self, pulserHardware, outputname, data, size=32, parent=None, *args): 
        """ datain: a list where each item is a row
        
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.pulserHardware = pulserHardware
        self.outputname = outputname
        self.size = size
        self._shutter = getattr(self.pulserHardware,self.outputname)
        self.data, self.dataChangedSignal = data 
        self.dataLookup = { (QtCore.Qt.DisplayRole,0):          lambda row: self.data.names.get(row,None),
                            (QtCore.Qt.BackgroundColorRole,1):  lambda row: self.onColor if self._shutter & (1<<row) else self.offColor,
                            (QtCore.Qt.EditRole,0):             lambda row: self.data.names.get(row,''),
                           }

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return self.size
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 2
 
    def setData(self,index,value,role):
        logger = logging.getLogger(__name__)
        value = str(value if api2 else str(value.toString()))
        if index.column()==0 and role==QtCore.Qt.EditRole:
            if value in self.data.channels and index.column()==self.data.channels[value]: # no change
                return True
            elif value in self.data.channels: # duplicate
                logger.error( "cannot have the same name twice" )
                return False
            else:
                if value != '':
                    self.data.channels[value] = index.row()
                    self.dataChangedSignal.dataChanged.emit( index.row(), index.row() )
                else:
                    if index.row() in self.data.names:
                        self.data.names.pop(index.row())
                        self.dataChangedSignal.dataChanged.emit( index.row(), index.row() )
        return False
        
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()),lambda row: None)(index.row())
        return None
        
    def flags(self, index ):
        return  { 0: QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable,
                  1: QtCore.Qt.ItemIsEnabled }[index.column()]

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Vertical): 
                return str(section)
            elif (orientation == QtCore.Qt.Horizontal): 
                return { 0: 'Name',
                         1: 'Value' }[section]
        return None 

    def onClicked(self,index):
        if index.column()==1:
            self._shutter ^= 1<<index.row()
        setattr(self.pulserHardware,self.outputname,self._shutter)
        self.dataChanged.emit(index,index)
        
    @property
    def shutter(self):
        return self._shutter  #
         
    @shutter.setter
    def shutter(self, value):
        self._shutter = value
        setattr(self.pulserHardware,self.outputname,self._shutter)
        self.dataChanged.emit(self.createIndex(0,1),self.createIndex(self.size,1))
        
    def updateShutter(self, value):
        """ updates the display only,
        called by the hardware backend to indicate changes
        by other means than the gui
        """
        if self._shutter != value:
            self._shutter = value
            self.dataChanged.emit(self.createIndex(0,1),self.createIndex(self.size,1))