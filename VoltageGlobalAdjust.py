# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtGui, QtCore
import os.path
from MagnitudeSpinBox import MagnitudeSpinBox
       
VoltageGlobalAdjustForm, VoltageGlobalAdjustBase = PyQt4.uic.loadUiType(r'ui\VoltageGlobalAdjust.ui')

class Settings:
    def __init__(self):
        self.gain = 1.0
        self.adjust = dict()
    
class VoltageGlobalAdjust(VoltageGlobalAdjustForm, VoltageGlobalAdjustBase ):
    updateOutput = QtCore.pyqtSignal(object)
    
    def __init__(self,config,parent=0):
        VoltageGlobalAdjustForm.__init__(self,parent)
        VoltageGlobalAdjustBase.__init__(self)
        self.config = config
        self.configname = 'VoltageGlobalAdjust.Settings'
        self.settings = self.config.get(self.configname,Settings())
        self.globalAdjustList = dict()

    def setupUi(self, parent):
        VoltageGlobalAdjustForm.setupUi(self,parent)
        self.gainBox.setValue(self.settings.gain)
        self.setupGlobalAdjust()
        
    def setupGlobalAdjust(self):
        for index, name in enumerate(self.globalAdjustList.keys()):
            label = QtGui.QLabel(self)
            label.setText(name)
            self.gridLayout.addWidget( label, 2+index, 0, 1, 1 )
            Box = MagnitudeSpinBox(self)
            Box.setValue( self.globalAdjustList[name] )
            self.gridLayout.addWidget( Box, 2+index, 1, 1, 1 )
        
    def onValueChanged(self, attribute, value):
        setattr(self.adjust,attribute,value) 
        self.updateOutput.emit(self.adjust)
    
    def onClose(self):
        self.config[self.configname] = self.settings
        