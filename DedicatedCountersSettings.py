# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtCore
import magnitude
import functools
from modules import CountrateConversion
       
DedicatedCountersSettingsForm, DedicatedCountersSettingsBase = PyQt4.uic.loadUiType(r'ui\DedicatedCountersSettings.ui')

class Settings:
    counterMask = 0
    adcMask = 0
    integrationTime = magnitude.mg(100,'ms')
    displayUnit = CountrateConversion.DisplayUnit()
    pointsToKeep = 400

class DedicatedCountersSettings(DedicatedCountersSettingsForm,DedicatedCountersSettingsBase ):
    valueChanged = QtCore.pyqtSignal(object)

    def __init__(self,config,parent=0):
        DedicatedCountersSettingsForm.__init__(self,parent)
        DedicatedCountersSettingsBase.__init__(self)
        self.config = config
        self.settings = self.config.get('DedicatedCounterSettings.Settings',Settings())

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
        self.displayUnitCombo.setCurrentIndex(self.settings.displayUnit.unit)
        self.displayUnitCombo.currentIndexChanged[int].connect( self.onIndexChanged )
    
    def onIndexChanged(self, index):
        self.settings.displayUnit.unit = index
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

    def onClose(self):
        self.config['DedicatedCounterSettings.Settings'] = self.settings
               