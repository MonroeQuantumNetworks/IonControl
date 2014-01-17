# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtGui, QtCore
import functools
from MagnitudeSpinBox import MagnitudeSpinBox
import modules.magnitude as magnitude
       
VoltageGlobalAdjustForm, VoltageGlobalAdjustBase = PyQt4.uic.loadUiType(r'ui\VoltageGlobalAdjust.ui')

class Settings:
    def __init__(self):
        self.gain = 1.0
        self.adjust = dict()
        
    
class VoltageGlobalAdjust(VoltageGlobalAdjustForm, VoltageGlobalAdjustBase ):
    updateOutput = QtCore.pyqtSignal(object)
    
    def __init__(self,config,parent=None):
        VoltageGlobalAdjustForm.__init__(self)
        VoltageGlobalAdjustBase.__init__(self,parent)
        self.config = config
        self.configname = 'VoltageGlobalAdjust.Settings'
        self.settings = self.config.get(self.configname,Settings())
        self.globalAdjustDict = dict()
        self.adjust = dict()
        self.adjust["__GAIN__"] = 1.0
        self.myLabelList = list()
        self.myBoxList = list()
        self.historyCategory = 'VoltageGlobalAdjust'
        self.adjustHistoryName = None
        self.spacerItem = None

    def setupUi(self, parent):
        VoltageGlobalAdjustForm.setupUi(self,parent)
        self.gainBox.setValue(self.settings.gain)
        self.gainBox.valueChanged.connect( functools.partial(self.onValueChanged, "__GAIN__") )
        self.setupGlobalAdjust('none',dict())
        
    def setupGlobalAdjust(self, name, adjustDict):
        if self.spacerItem:
            self.gridLayout.removeItem( self.spacerItem )
        else:
            self.spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        if self.adjustHistoryName:
            self.config[(self.historyCategory,self.adjustHistoryName)] = self.adjust
        oldadjust = self.config.get((self.historyCategory,name),dict())
        self.adjustHistoryName = name
        self.globalAdjustDict = adjustDict
        #print self.globalAdjustDict
        self.adjust = dict()
        for index, name in enumerate(self.globalAdjustDict.keys()):
            if index<len(self.myLabelList):
                self.myLabelList[index].setText(name)
                self.myLabelList[index].show()
            else:
                label = QtGui.QLabel(self)
                label.setText(name)
                self.myLabelList.append(label)
                self.gridLayout.addWidget( label, 2+index, 1, 1, 1 )
            if index<len(self.myBoxList):
                self.myBoxList[index].valueChanged.disconnect()
                self.myBoxList[index].setValue( oldadjust.get(name,0) )
                self.myBoxList[index].valueChanged.connect( functools.partial(self.onValueChanged, name) )
                self.myBoxList[index].show()
                self.adjust[name] = self.myBoxList[index].value()
            else:
                Box = MagnitudeSpinBox(self)
                Box.setValue( oldadjust.get(name,0) )
                Box.valueChanged.connect( functools.partial(self.onValueChanged, name) )
                self.gridLayout.addWidget( Box, 2+index, 2, 1, 1 )
                self.myBoxList.append( Box )
                self.adjust[name] = Box.value()
        for index in range( len(self.globalAdjustDict.keys()), len(self.myLabelList)):
            self.myLabelList[index].hide()
            self.myBoxList[index].hide()
        self.gridLayout.addItem(self.spacerItem, len(self.globalAdjustDict)+2, 1, 1, 1)
        self.updateOutput.emit(self.adjust)
        
    def onValueChanged(self, attribute, value):
        self.adjust[attribute]=value.toval() if isinstance(value, magnitude.Magnitude) else value
        self.updateOutput.emit(self.adjust)
    
    def saveConfig(self):
        self.config[self.configname] = self.settings
        if self.adjustHistoryName:
            self.config[(self.historyCategory,self.adjustHistoryName)] = self.adjust
        