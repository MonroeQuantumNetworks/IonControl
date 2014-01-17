# -*- coding: utf-8 -*-
"""
Created on Fri Feb 08 22:02:08 2013

@author: pmaunz
"""
from PyQt4 import QtCore, QtGui
from operator import attrgetter
from functools import partial
from modules.SequenceDict import SequenceDict

class InterlockChannel:
    def __init__(self):
        self.enable = False
        self.channel = 0
        self.min = 0.0
        self.max = 0.0
        self.current = 0
        self.inRange = False

class WavemeterInterlockTableModel(QtCore.QAbstractTableModel):
    getWavemeterData = QtCore.pyqtSignal( object )
    headerDataLookup = [ 'Enable', 'Channel', 'Current','Minimum', 'Maximum']
    attributeLookup = ['enable', 'channel', 'current', 'min', 'max']
    def __init__(self, channeldict, parent=None, *args): 
        """ datain: a list where each item is a row
        
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.channelDict = channeldict
        self.setDataLookup =   { (QtCore.Qt.EditRole,1): self.setChannel,
                                 (QtCore.Qt.EditRole,3): self.setMin,
                                 (QtCore.Qt.EditRole,4): self.setMax,
                                 (QtCore.Qt.CheckStateRole,0): self.setEnable, }
        self.dataLookup =  { (QtCore.Qt.CheckStateRole,0): lambda row: QtCore.Qt.Checked if self.channelDict.at(row).enable else QtCore.Qt.Unchecked,
                             (QtCore.Qt.DisplayRole,1):    lambda row: self.channelDict.at(row).channel,
                             (QtCore.Qt.DisplayRole,2):    lambda row: "{0:.4f} GHz".format(self.channelDict.at(row).current),
                             (QtCore.Qt.BackgroundColorRole,2): lambda row: QtGui.QColor(QtCore.Qt.white) if not self.channelDict.at(row).enable else QtGui.QColor(0xa6,0xff,0xa6,0xff) if self.channelDict.at(row).inRange else QtGui.QColor(0xff,0xa6,0xa6,0xff),
                             (QtCore.Qt.DisplayRole,3):    lambda row: "{0:.4f} GHz".format(self.channelDict.at(row).min),
                             (QtCore.Qt.DisplayRole,4):    lambda row: "{0:.4f} GHz".format(self.channelDict.at(row).max),
                             (QtCore.Qt.EditRole,1):       lambda row: self.channelDict.at(row).channel,
                             (QtCore.Qt.EditRole,3):       lambda row: "{0:.4f}".format(self.channelDict.at(row).min),
                             (QtCore.Qt.EditRole,4):       lambda row: "{0:.4f}".format(self.channelDict.at(row).max),   }
 
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()),lambda row: None)(index.row())
        return None
        
    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
        return None 

    def setData(self, index, value, role):
        return self.setDataLookup.get((role,index.column()), lambda index, value: False )(index, value)

    def flags(self, index ):
        if index.column() in [1,3,4]:
            return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable
        if index.column()==0:
            return  QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled
        return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def setChannel(self,index,value):
        channel, ok  = value.toInt()
        if channel==self.channelDict.at(index.row()).channel:  # no change
            return True
        if channel not in self.channelDict:
            ilChannel = self.channelDict.pop(self.channelDict.at(index.row()).channel)  # pop the old one from the dict
            ilChannel.channel = channel
            self.channelDict[channel] = ilChannel
            return True
        return False      
                
    def setCurrent(self, channel, value):
        ilChannel = self.channelDict[channel]
        index = self.channelDict.index(channel)
        ilChannel.current = value
        self.dataChanged.emit( self.createIndex(index,2), self.createIndex(index,2) ) 
        ilChannel.inRange = ilChannel.min < ilChannel.current < ilChannel.max
                
    def setMin(self, index, value):
        self.channelDict.at(index.row()).min = float(value.toString())
        return True

    def setMax(self, index, value):
        self.channelDict.at(index.row()).max = float(value.toString())
        return True
                
    def setEnable(self, index, value):
        enable = value == QtCore.Qt.Checked
        if self.channelDict.at(index.row()).enable != enable:  # it changed
            self.channelDict.at(index.row()).enable = value == QtCore.Qt.Checked
            if enable:
                self.getWavemeterData.emit(self.channelDict.at(index.row()).channel)
            self.dataChanged.emit( self.createIndex(index.row(),2), self.createIndex(index.row(),2) )
        return True
    
    def addChannel(self):
        s = set( range(len(self.channelDict)+1) )
        for ch in self.channelDict.keys():
            s.discard(ch)
        ch = sorted(s)[0]
        index = len(self.channelDict)
        self.beginInsertRows(QtCore.QModelIndex(),index,index)
        ilChannel = InterlockChannel()
        ilChannel.channel = ch
        self.channelDict[ch] = ilChannel
        self.endInsertRows()
    
    def removeChannel(self, index):
        self.beginRemoveRows(QtCore.QModelIndex(), index, index)
        self.channelDict.pop( self.channelDict.at(index).channel )
        self.endRemoveRows()

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.channelDict) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 5
 
    def sort(self, column, order ):
        self.beginResetModel()
        self.channelDict.sortByAttribute( self.attributeLookup[column], order==QtCore.Qt.DescendingOrder )
        self.endResetModel()
