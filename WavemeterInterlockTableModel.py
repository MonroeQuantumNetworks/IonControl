# -*- coding: utf-8 -*-
"""
Created on Fri Feb 08 22:02:08 2013

@author: pmaunz
"""
from PyQt4 import QtCore, QtGui
from operator import attrgetter
from functools import partial

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
    def __init__(self, channeldict, parent=None, *args): 
        """ datain: a list where each item is a row
        
        """
        QtCore.QAbstractTableModel.__init__(self, parent, *args) 
        self.channelDict = channeldict
        self.channelList = channeldict.values()
        self.setDataLookup =   { (QtCore.Qt.EditRole,1): self.setChannel,
                                 (QtCore.Qt.EditRole,3): self.setMin,
                                 (QtCore.Qt.EditRole,4): self.setMax,
                                 (QtCore.Qt.CheckStateRole,0): self.setEnable,
                                }

    dataLookup =   { (QtCore.Qt.CheckStateRole,0): lambda self, row: QtCore.Qt.Checked if self.channelList[row].enable else QtCore.Qt.Unchecked,
                     (QtCore.Qt.DisplayRole,1): lambda self, row: self.channelList[row].channel,
                     (QtCore.Qt.DisplayRole,2): lambda self, row: "{0:.4f} GHz".format(self.channelList[row].current),
                     (QtCore.Qt.BackgroundColorRole,2): lambda self, row: QtGui.QColor(QtCore.Qt.white) if not self.channelList[row].enable else QtGui.QColor(QtCore.Qt.green) if self.channelList[row].inRange else QtGui.QColor(QtCore.Qt.red),
                     (QtCore.Qt.DisplayRole,3): lambda self, row: "{0:.4f} GHz".format(self.channelList[row].min),
                     (QtCore.Qt.DisplayRole,4): lambda self, row: "{0:.4f} GHz".format(self.channelList[row].max),
                     (QtCore.Qt.EditRole,1): lambda self, row: self.channelList[row].channel,
                     (QtCore.Qt.EditRole,3): lambda self, row: "{0:.4f}".format(self.channelList[row].min),
                     (QtCore.Qt.EditRole,4): lambda self, row: "{0:.4f}".format(self.channelList[row].max),                    
                     }
 
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()),lambda self, row: None)(self,index.row())
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
        if channel==self.channelList[index.row()].channel:  # no change
            return True
        if channel not in self.channelDict:
            self.channelDict.pop(self.channelList[index.row()].channel)  # pop the old one from the dict
            self.channelList[index.row()].channel = channel
            self.channelDict[channel] = self.channelList[index.row()]
            return True
        return False      
                
    def setCurrent(self, channel, value):
        ilChannel = self.channelDict[channel]
        index = self.channelList.index(ilChannel)
        ilChannel.current = value
        self.dataChanged.emit( self.createIndex(index,2), self.createIndex(index,2) ) 
        ilChannel.inRange = ilChannel.min < ilChannel.current < ilChannel.max
                
    def setMin(self, index, value):
        self.channelList[index.row()].min = float(value.toString())
        return True

    def setMax(self, index, value):
        self.channelList[index.row()].max = float(value.toString())
        return True
                
    def setEnable(self, index, value):
        enable = value == QtCore.Qt.Checked
        if self.channelList[index.row()].enable != enable:  # it changed
            self.channelList[index.row()].enable = value == QtCore.Qt.Checked
            if enable:
                self.getWavemeterData.emit(self.channelList[index.row()].channel)
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
        self.channelList.append(ilChannel)
        self.endInsertRows()
    
    def removeChannel(self, index):
        self.beginRemoveRows(QtCore.QModelIndex(), index, index)
        self.channelDict.pop( self.channelList[index].channel )
        del self.channelList[index]
        self.endRemoveRows()

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.channelDict) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 5
 
    def sort(self, column, order ):
        pass