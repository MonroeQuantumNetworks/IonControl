# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
import magnitude
import functools

from PyQt4 import QtCore
       
TimestampSettingsForm, TimestampSettingsBase = PyQt4.uic.loadUiType(r'ui\TimestampSettings.ui')

from modules import enum

class Settings:
    enable = False
    binwidth =  magnitude.mg(1,'us')
    roiStart =  magnitude.mg(0,'us')
    roiWidth =  magnitude.mg(1,'ms')
    integrate = 0
    channel = 0
    
class TimestampSettings(TimestampSettingsForm, TimestampSettingsBase ):
    integrationMode = enum.enum('IntegrateAll','IntegrateRun','NoIntegration')    
    
    def __init__(self,config,parentname,parent=None):
        TimestampSettingsForm.__init__(self)
        TimestampSettingsBase.__init__(self,parent)
        self.config = config
        self.configname = 'TimestampSettings.'+parentname
        self.settings = self.config.get(self.configname,Settings())

    def setupUi(self, parent):
        TimestampSettingsForm.setupUi(self,parent)
        self.enableCheckBox.setChecked(self.settings.enable)
        self.binwidthSpinBox.setValue(self.settings.binwidth)
        self.binwidthSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'binwidth') )
        self.roiStartSpinBox.setValue(self.settings.roiStart)
        self.roiStartSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'roiStart') )
        self.roiWidthSpinBox.setValue(self.settings.roiWidth)
        self.roiWidthSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'roiWidth') )
        self.enableCheckBox.stateChanged.connect( self.onStateChanged )
        self.integrateCombo.setCurrentIndex( self.settings.integrate )
        self.integrateCombo.currentIndexChanged[int].connect( self.onIntegrationChanged )
        self.channelSpinBox.setValue( self.settings.channel )
        self.channelSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'channel') )

    def onValueChanged(self, param, value):
        print "ValueChanged", param, value
        setattr(self.settings, param, value)
        
    def onStateChanged(self, state):
        self.settings.enable = state == QtCore.Qt.Checked
        
    def onIntegrationChanged(self, value):
        self.settings.integrate = value
        
    def onClose(self):
        self.config[self.configname] = self.settings
        