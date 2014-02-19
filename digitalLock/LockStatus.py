import PyQt4.uic
from PyQt4 import QtGui, QtCore

import logging
from modules.magnitude import mg
import math

Form, Base = PyQt4.uic.loadUiType(r'digitalLock\ui\LockStatus.ui')

frequencyQuantum = mg(1,'GHz') / 0xffffffffffff
voltageQuantum = mg(5,'V') / 0xffff

def convertFreq( binvalue ):
    return binvalue * frequencyQuantum

def convertVoltage( binvalue ):
    return binvalue * voltageQuantum

class LockStatus(Form, Base):
    def __init__(self,controller,config,parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        self.controller = controller
        self.config = config
        self.lockSettings = None
        self.lastLockData = list()
    
    def setupUi(self):
        Form.setupUi(self,self)
        self.controller.streamDataAvailable.connect( self.onData )
        self.controller.lockStatusChanged.connect( self.onLockChange )
        
    def onLockChange(self, data=None):
        pass
    
    def onControlChanged(self, value):
        self.lockSettings = value
        self.onLockChange()
    
    def onData(self, data=None ):
        if data is not None:
            self.lastLockData = data
        if len(self.lastLockData)>0 and self.lockSettings is not None:
            item = data[-1]
            referenceFrequency = self.lockSettings.referenceFrequency + convertFreq(item.freqAvg)
            referenceFrequency.significantDigits = (math.log(abs(referenceFrequency/frequencyQuantum))+1) if referenceFrequency>0 else 3
            outputFrequency = self.lockSettings.outputFrequency + convertFreq(item.freqAvg)* self.lockSettings.harmonic
            outputFrequency.significantDigits = (math.log(abs(outputFrequency/frequencyQuantum))+1) if outputFrequency>0 else 3
            binvalue = (item.freqMax - item.freqMin) 
            referenceFrequencyDelta = convertFreq(binvalue) 
            referenceFrequencyDelta.significantDigits = (math.log(abs(binvalue))) if binvalue>0 else 3
            binvalue *= self.lockSettings.harmonic
            outputFrequencyDelta = convertFreq(binvalue)
            outputFrequencyDelta.significantDigits = (math.log(abs(binvalue))+1) if binvalue>0 else 3
            
            errorSigAvg = convertVoltage( item.errorSigAvg )
            errorSigAvg.significantDigits = math.log(abs(item.errorSigAvg)) if abs(item.errorSigAvg)>0 else 3
            binvalue = item.errorSigMax - item.errorSigMin
            errorSigDelta = convertVoltage(binvalue )
            errorSigDelta.significantDigits = math.log(binvalue) if binvalue>0 else 3            
            
            self.referenceFreqLabel.setText( str(referenceFrequency) )
            self.referenceFreqRangeLabel.setText( str(referenceFrequencyDelta) )
            self.outputFreqLabel.setText( str(outputFrequency))
            self.outputFreqRangeLabel.setText( str(outputFrequencyDelta))
            
            self.errorSignalLabel.setText( str(errorSigAvg))
            self.errorSignalRangeLabel.setText( str(errorSigDelta))
            
    def saveConfig(self):
        pass
