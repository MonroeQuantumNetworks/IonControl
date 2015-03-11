# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
from PyQt4 import QtCore
import PyQt4.uic

from modules.SequenceDict import SequenceDict
from VoltageGlobalAdjustTableModel import VoltageGlobalAdjustTableModel   #@UnresolvedImport
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from externalParameter.VoltageOutputChannel import VoltageOutputChannel
from _collections import defaultdict
from modules.Observable import Observable


VoltageGlobalAdjustForm, VoltageGlobalAdjustBase = PyQt4.uic.loadUiType(r'ui\VoltageGlobalAdjust.ui')

class Settings:
    def __init__(self):
        self.gain = 1.0
        self.gainCache = dict()
    
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault( 'gainCache', dict() )
    
class VoltageGlobalAdjust(VoltageGlobalAdjustForm, VoltageGlobalAdjustBase ):
    updateOutput = QtCore.pyqtSignal(object, object)
    outputChannelsChanged = QtCore.pyqtSignal(object)
    
    def __init__(self, config, globalDict, parent=None):
        VoltageGlobalAdjustForm.__init__(self)
        VoltageGlobalAdjustBase.__init__(self,parent)
        self.config = config
        self.configname = 'VoltageGlobalAdjust.Settings'
        self.settings = self.config.get(self.configname,Settings())
        self.globalAdjustDict = SequenceDict()
        self.myLabelList = list()
        self.myBoxList = list()
        self.historyCategory = 'VoltageGlobalAdjust'
        self.adjustHistoryName = None
        self.globalDict = globalDict
        self.adjustCache = self.config.get(self.configname+".cache",dict()) 
        self.savedValue = defaultdict( lambda: None )
        self.displayValueObservable = defaultdict( lambda: Observable() )

    def setupUi(self, parent):
        VoltageGlobalAdjustForm.setupUi(self,parent)
        self.gainBox.setValue(self.settings.gain)
        self.gainBox.valueChanged.connect( self.onGainChanged )
        self.tableModel = VoltageGlobalAdjustTableModel( self.globalAdjustDict, self.globalDict )
        self.tableView.setModel( self.tableModel )
        self.tableView.setSortingEnabled(True)   # triggers sorting
        self.delegate =  MagnitudeSpinBoxDelegate(self.globalDict)
        self.tableView.setItemDelegateForColumn(1,self.delegate)
        
    def onGainChanged(self, gain):
        self.settings.gain = gain
        self.updateOutput.emit(self.globalAdjustDict, self.settings.gain)        
        
    def setupGlobalAdjust(self, name, adjustDict):
        if name!=self.adjustHistoryName:
            self.adjustCache[self.adjustHistoryName] = [v.data for v in self.globalAdjustDict.values()]
            self.settings.gainCache[self.adjustHistoryName] = self.settings.gain
            self.settings.gain = self.settings.gainCache.get( name, self.settings.gain )
            if name in self.adjustCache:
                for data in self.adjustCache[name]:
                    if data[0] in adjustDict:
                        adjustDict[data[0]].data = data
            self.adjustHistoryName = name
        self.globalAdjustDict = adjustDict
        for name, adjust in self.globalAdjustDict.iteritems():
            adjust.observable.subscribe( self.onValueChanged, unique=True )
        self.tableModel.setGlobalAdjust( adjustDict )
        self.outputChannelsChanged.emit( self.outputChannels() )
        self.gainBox.setValue(self.settings.gain)
        self.updateOutput.emit(self.globalAdjustDict, self.settings.gain)        
        
    def onValueChanged(self, event):
        if event.origin=='recalculate':
            self.tableModel.valueRecalcualted(event.name)
        self.updateOutput.emit(self.globalAdjustDict, self.settings.gain)
    
    def saveConfig(self):
        self.config[self.configname] = self.settings
        self.adjustCache[self.adjustHistoryName] = [v.data for v in self.globalAdjustDict.values()]
        self.config[self.configname+".cache"] = self.adjustCache
        
    def setValue(self, channel, value):
        self.globalAdjustDict[channel].value = value 
        return True
    
    def currentValue(self, channel):
        return self.globalAdjustDict[channel].value
    
    def saveValue(self, channel):
        self.savedValue[channel] = self.globalAdjustDict[channel].value
    
    def restoreValue(self, channel):
        if self.savedValue[channel] is not None:
            self.globalAdjustDict[channel].value = self.savedValue[channel]
        return True
    
    def strValue(self, channel):
        adjust = self.globalAdjustDict[channel]
        return adjust.string if adjust.hasDependency else None
    
    def setStrValue(self, channel, value):
        pass
    
    def outputChannels(self):
        self._outputChannels = dict(( (channelName, VoltageOutputChannel(self, None, channelName)) for channelName in self.globalAdjustDict.iterkeys() ))      
        return self._outputChannels
        
