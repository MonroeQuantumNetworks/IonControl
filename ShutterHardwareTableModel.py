# -*- coding: utf-8 -*-
"""
Created on Fri Feb 08 22:02:08 2013

@author: pmaunz
"""
from PyQt4 import QtCore, QtGui
import sip
api2 = sip.getapi("QVariant")==2


class ShutterHardwareTableModel(QtCore.QAbstractTableModel):
    onColor =  QtGui.QColor(QtCore.Qt.green)
    offColor =  QtGui.QColor(QtCore.Qt.red)
    def __init__(self, shutterdict, pulserHardware, outputname, size=32, parent=None, *args): 
        """ datain: a list where each item is a row
        
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.shutterdict = shutterdict
        self.shutterNameDict = dict((value, key) for key, value in shutterdict.iteritems())
        self.pulserHardware = pulserHardware
        self.outputname = outputname
        self.size = size
        self._shutter = getattr(self.pulserHardware,self.outputname)
#        size = 8
#        [bool(235 & (1 << size - i - 1)) for i in xrange(size)]
    def rowCount(self, parent=QtCore.QModelIndex()): 
        return self.size
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 2
 
    def setData(self,index,value,role):
        value = str(value if api2 else str(value.toString()))
        if index.column()==0 and role==QtCore.Qt.EditRole:
            if value in self.shutterNameDict and index.column()==self.shutterNameDict[value]: # no change
                return True
            elif value in self.shutterNameDict: # duplicate
                print "cannot have the same name twice"
                return False
            else:
                old = self.shutterdict.get(index.row())
                if old in self.shutterNameDict:
                    self.shutterNameDict.pop(self.shutterdict[index.row()])                    
                if value != '':
                    self.shutterNameDict[value] = index.row()
                    self.shutterdict[index.row()] = value
                else:
                    if index.row() in self.shutterdict:
                        self.shutterdict.pop(index.row())
        return False
        
    def data(self, index, role): 
        if index.isValid():
            return { (QtCore.Qt.DisplayRole,0): self.shutterdict.get(index.row(),None),
                     (QtCore.Qt.BackgroundColorRole,1): self.onColor if self._shutter & (1<<index.row()) else self.offColor,
                     (QtCore.Qt.EditRole,0): self.shutterdict.get(index.row(),''),
                     }.get((role,index.column()),None)
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