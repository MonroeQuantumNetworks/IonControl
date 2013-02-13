# -*- coding: utf-8 -*-
"""
Created on Fri Feb 08 22:02:08 2013

@author: pmaunz
"""
from PyQt4 import QtCore, QtGui

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
        self.shutter = getattr(self.pulserHardware,self.outputname)
#        size = 8
#        [bool(235 & (1 << size - i - 1)) for i in xrange(size)]
    def rowCount(self, parent=QtCore.QModelIndex()): 
        return self.size
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 2
 
    def setData(self,index,value,role):
        value = str(value.toString())
        if index.column()==0 and role==QtCore.Qt.EditRole:
            if value in self.shutterNameDict and index.column()==self.shutterNameDict[value]: # no change
                return True
            elif value in self.shutterNameDict: # douplicate
                print "cannot have the same name twice"
                return False
            else:
                old = self.shutterdict.get(index.column())
                if old in self.shutterNameDict:
                    self.shutterNameDict.popitem(self.shutterdict[index.column()])                    
                if value != '':
                    self.shutterNameDict[value] = index.column()
                    self.shutterdict[index.column()] = value
                else:
                    if index.column() in self.shutterdict:
                        self.shutterdict.popitem(self.shutterdict[index.column()])
        return False
        
    def data(self, index, role): 
        if index.isValid():
            return { (QtCore.Qt.DisplayRole,0): self.shutterdict.get(index.row(),None),
                     (QtCore.Qt.BackgroundColorRole,1): self.onColor if self.shutter & (1<<index.row()) else self.offColor,
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
            self.shutter ^= 1<<index.row()
        setattr(self.pulserHardware,self.outputname,self.shutter)
        self.dataChanged.emit(index,index)