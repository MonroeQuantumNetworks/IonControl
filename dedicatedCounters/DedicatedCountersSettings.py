# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import functools

from PyQt4 import QtCore
import PyQt4.uic

from modules import CountrateConversion
import modules.magnitude as magnitude


DedicatedCountersSettingsForm, DedicatedCountersSettingsBase = PyQt4.uic.loadUiType(r'ui\DedicatedCountersSettings.ui')

class Settings:
    def __init__(self):
        self.counterMask = 0
        self.adcMask = 0
        self.integrationTime = magnitude.mg(100,'ms')
        self.displayUnit = CountrateConversion.DisplayUnit()
        self.unit = 0
        self.pointsToKeep = 400

class DedicatedCountersSettings(DedicatedCountersSettingsForm,DedicatedCountersSettingsBase ):
    valueChanged = QtCore.pyqtSignal(object)

    def __init__(self,config,parent=None):
        DedicatedCountersSettingsForm.__init__(self)
        DedicatedCountersSettingsBase.__init__(self,parent)
        self.config = config
        self.settings = self.config.get('DedicatedCounterSettings.Settings2',Settings())

    def setupUi(self, parent):
        DedicatedCountersSettingsForm.setupUi(self,parent)
        self.integrationTimeBox.setValue( self.settings.integrationTime )
        self.integrationTimeBox.valueChanged.connect( functools.partial(self.onValueChanged,'integrationTime') )
        self.pointsToKeepBox.setValue( self.settings.pointsToKeep )
        self.pointsToKeepBox.valueChanged.connect( functools.partial(self.onValueChanged,'pointsToKeep') )
        for num, channel in enumerate([ self.ch0Check, self.ch1Check, self.ch2Check, self.ch3Check, self.ch4Check, self.ch5Check, self.ch6Check, self.ch7Check]):
            channel.setChecked( self.settings.counterMask & (1<<num) )
            channel.stateChanged.connect( functools.partial( self.onCounterStateChanged,(1<<num) ))
        for num, channel in enumerate([ self.adc0Check, self.adc1Check, self.adc2Check, self.adc3Check]):
            channel.setChecked( self.settings.adcMask & (1<<num) )
            channel.stateChanged.connect( functools.partial( self.onAdcStateChanged,(1<<num) ))
        self.displayUnitCombo.currentIndexChanged[int].connect( self.onIndexChanged )
        self.displayUnitCombo.setCurrentIndex(self.settings.unit)
        self.settings.displayUnit.unit = self.settings.unit
    
    def onIndexChanged(self, index):
        self.settings.displayUnit.unit = index
        self.settings.unit = index
        self.valueChanged.emit( self.settings )
    
    def onValueChanged(self, name, value):
        setattr(self.settings,name, value)
        self.valueChanged.emit( self.settings )
    
    def onCounterStateChanged(self, mask, state):
        self.settings.counterMask = (self.settings.counterMask & ~mask) | (mask if state==QtCore.Qt.Checked else 0)
        self.valueChanged.emit( self.settings )
    
    def onAdcStateChanged(self, mask, state):
        self.settings.adcMask = (self.settings.adcMask & ~mask) | (mask if state==QtCore.Qt.Checked else 0)
        self.valueChanged.emit( self.settings )

    def saveConfig(self):
        self.config['DedicatedCounterSettings.Settings2'] = self.settings
               
