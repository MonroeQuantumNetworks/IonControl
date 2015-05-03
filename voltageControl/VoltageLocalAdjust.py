# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
from PyQt4 import QtCore
import PyQt4.uic

from modules.SequenceDict import SequenceDict
from VoltageLocalAdjustTableModel import VoltageLocalAdjustTableModel   #@UnresolvedImport
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from externalParameter.VoltageOutputChannel import VoltageOutputChannel
from _collections import defaultdict
from modules.Observable import Observable
from gui.ExpressionValue import ExpressionValue
import os.path
from modules.Utility import unique


Form, Base = PyQt4.uic.loadUiType(r'ui\VoltageLocalAdjust.ui')

class Settings:
    def __init__(self):
        self.gain = 1.0
        self.gainCache = dict()
    
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault( 'gainCache', dict() )
        
class LocalAdjustRecord(object):
    def __init__(self, name="", path=None, gain=0, globalDict=None):
        self.name = name
        self.path = path
        self.gain = gain if isinstance(gain, ExpressionValue) else ExpressionValue(name, globalDict, gain)
        self.solution = None
        self.solutionPath = None
        
    def __getstate__(self):
        return (self.name, self.path, self.gain)
    
    def __setstate__(self, state):
        self.name, self.path, self.gain = state
        self.solution = None
        self.solutionPath = None
        
    @property
    def filename(self):
        return os.path.split(self.path)[1] if self.path else ""
    
    @property
    def globalDict(self):
        return self.gain.globalDict
    
    @globalDict.setter
    def globalDict(self, globalDict):
        self.gain.globalDict = globalDict
    
    def __hash__(self):
        return hash( (self.solution, self.gain) )
        
            
class VoltageLocalAdjust(Form, Base ):
    updateOutput = QtCore.pyqtSignal(object, object)
    outputChannelsChanged = QtCore.pyqtSignal(object)
    filesChanged = None
    
    def __init__(self, config, globalDict, parent=None):
        Form.__init__(self)
        Base.__init__(self,parent)
        self.config = config
        self.configname = 'VoltageLocalAdjust.Settings'
        self.settings = self.config.get(self.configname,Settings())
        self.localAdjustList = self.config.get( self.configname+".local" , list() )
        for record in self.localAdjustList:
            record.globalDict = globalDict
            record.gain.observable.subscribe( self.onValueChanged, unique=True )
        self.historyCategory = 'VoltageLocalAdjust'
        self.adjustHistoryName = None
        self.globalDict = globalDict
        self.savedValue = defaultdict( lambda: None )
        self.displayValueObservable = defaultdict( lambda: Observable() )

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        self.tableModel = VoltageLocalAdjustTableModel( self.localAdjustList, self.globalDict )
        self.filesChanged = self.tableModel.filesChanged
        self.tableView.setModel( self.tableModel )
        self.tableView.setSortingEnabled(True)   # triggers sorting
        self.delegate =  MagnitudeSpinBoxDelegate(self.globalDict)
        self.tableView.setItemDelegateForColumn(1,self.delegate)
        self.addButton.clicked.connect( self.onAdd )
        self.removeButton.clicked.connect( self.onRemove )
        
    def onValueChanged(self, event):
        if event.origin=='recalculate':
            self.tableModel.valueRecalcualted(event.name)
        self.updateOutput.emit(self.localAdjustList,0)

    def onAdd(self):
        newrecord = self.tableModel.add( LocalAdjustRecord(globalDict=self.globalDict) )
        newrecord.gain.observable.subscribe( self.onValueChanged, unique=True )
    
    def onRemove(self):
        for index in sorted(unique([ i.row() for i in self.tableView.selectedIndexes() ]),reverse=True):
            self.tableModel.drop(index)
        
    def saveConfig(self):
        self.config[self.configname] = self.settings
        self.config[self.configname+".local"] = self.localAdjustList
        
    def setValue(self, channel, value):
        self.localAdjustList[channel].gain = value 
        return True
    
    def currentValue(self, channel):
        return self.localAdjustList[channel].gain
    
    def saveValue(self, channel):
        self.savedValue[channel] = self.localAdjustList[channel].gain
    
    def restoreValue(self, channel):
        if self.savedValue[channel] is not None:
            self.localAdjustList[channel].gain = self.savedValue[channel]
        return True
    
    def strValue(self, channel):
        adjust = self.localAdjustList[channel].gain
        return adjust.string if adjust.hasDependency else None
    
    def setStrValue(self, channel, value):
        pass
    
    def outputChannels(self):
        self._outputChannels = dict(( (index, VoltageOutputChannel(self, None, index)) for index in range(self.localAdjustList) ))      
        return self._outputChannels
        
