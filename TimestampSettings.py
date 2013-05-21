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
    def __init__(self):
        self.enable = False
        self.binwidth =  magnitude.mg(1,'us')
        self.roiStart =  magnitude.mg(0,'us')
        self.roiWidth =  magnitude.mg(1,'ms')
        self.integrate = 0
        self.channel = 0
        self.saveRawData = False
    
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
        self.saveRawDataCheckBox.setChecked(self.settings.saveRawData)
        self.binwidthSpinBox.setValue(self.settings.binwidth)
        self.binwidthSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'binwidth') )
        self.roiStartSpinBox.setValue(self.settings.roiStart)
        self.roiStartSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'roiStart') )
        self.roiWidthSpinBox.setValue(self.settings.roiWidth)
        self.roiWidthSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'roiWidth') )
        self.enableCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,' enable' ) )
        self.saveRawDataCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,' saveRawData' ) )
        self.integrateCombo.setCurrentIndex( self.settings.integrate )
        self.integrateCombo.currentIndexChanged[int].connect( self.onIntegrationChanged )
        self.channelSpinBox.setValue( self.settings.channel )
        self.channelSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'channel') )

    def onValueChanged(self, param, value):
        print "ValueChanged", param, value
        setattr(self.settings, param, value)
        
    def onStateChanged(self, attr, state):
        setattr(self.settings,attr,state == QtCore.Qt.Checked)
        
    def onIntegrationChanged(self, value):
        self.settings.integrate = value
        
    def onClose(self):
        self.config[self.configname] = self.settings
        