# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtGui, QtCore
import functools
from MagnitudeSpinBox import MagnitudeSpinBox
import magnitude
       
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
        self.globalAdjustDict = dict()
        self.adjust = dict()
        self.adjust["__GAIN__"] = 1.0

    def setupUi(self, parent):
        VoltageGlobalAdjustForm.setupUi(self,parent)
        self.gainBox.setValue(self.settings.gain)
        self.gainBox.valueChanged.connect( functools.partial(self.onValueChanged, "__GAIN__") )
        self.setupGlobalAdjust(dict())
        
    def setupGlobalAdjust(self, adjustDict):
        self.globalAdjustDict = adjustDict
        for index, name in enumerate(self.globalAdjustDict.keys()):
            label = QtGui.QLabel(self)
            label.setText(name)
            self.gridLayout.addWidget( label, 2+index, 1, 1, 1 )
            Box = MagnitudeSpinBox(self)
            Box.setValue( 0 )
            Box.valueChanged.connect( functools.partial(self.onValueChanged, name) )
            self.gridLayout.addWidget( Box, 2+index, 2, 1, 1 )
            self.adjust[name] = Box.value()
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, len(self.globalAdjustDict)+2, 1, 1, 1)
        self.updateOutput.emit(self.adjust)

        
    def onValueChanged(self, attribute, value):
        self.adjust[attribute]=value.toval() if isinstance(value, magnitude.Magnitude) else value
        self.updateOutput.emit(self.adjust)
    
    def onClose(self):
        self.config[self.configname] = self.settings
        