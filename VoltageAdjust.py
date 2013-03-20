# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtGui, QtCore
import os.path
import functools
       
VoltageAdjustForm, VoltageAdjustBase = PyQt4.uic.loadUiType(r'ui\VoltageAdjust.ui')
    
class Adjust:
    def __init__(self):
        self.line = 0.0
        self.lineGain = 1.0
        self.globalGain = 1.0

class Settings:
    def __init__(self):
        self.adjust = Adjust()
    
class VoltageAdjust(VoltageAdjustForm, VoltageAdjustBase ):
    updateOutput = QtCore.pyqtSignal(object)
    
    def __init__(self,config,parent=0):
        VoltageAdjustForm.__init__(self,parent)
        VoltageAdjustBase.__init__(self)
        self.config = config
        self.configname = 'VoltageAdjust.Settings'
        self.settings = self.config.get(self.configname,Settings())
        self.adjust = self.settings.adjust

    def setupUi(self, parent):
        VoltageAdjustForm.setupUi(self,parent)
        self.lineBox.setValue( self.adjust.line )
        self.lineGainBox.setValue( self.adjust.lineGain )
        self.globalGainBox.setValue( self.adjust.globalGain )
        self.lineBox.valueChanged.connect( functools.partial(self.onValueChanged,"line") )
        self.lineGainBox.valueChanged.connect( functools.partial(self.onValueChanged,"lineGain") )
        self.globalGainBox.valueChanged.connect( functools.partial(self.onValueChanged,"globalGain") )
        
    def onValueChanged(self, attribute, value):
        setattr(self.adjust,attribute,value) 
        self.updateOutput.emit(self.adjust)
    
    def onClose(self):
        self.config[self.configname] = self.settings
        