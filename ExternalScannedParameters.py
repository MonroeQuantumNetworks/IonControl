# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:22:09 2013

@author: wolverine
"""

#import visa
from WavemeterGetFrequency import WavemeterGetFrequency
import numpy
import magnitude

class ExternalParameter:

    def __init__(self):
        pass
    
    def saveValue(self):
        pass
    
    def restoreValue(self):
        pass
    
    def setValue(self,value):
        pass
    
    def currentExternalValue(self):
        pass
    
    
class LaserVCOScan:
    def __init__(self):
        self.powersupply = visa.instrument("power_supply_next_to_397_box")#open visa session
        self.wavemeter = WavemeterGetFrequency()
        self.savedValue = float(self.powersupply.ask("volt?"))
        self.lastValue = self.savedValue
        self.stepsize = 0.01
        self.AOMFreq = 110.7e-3
    
    def saveValue(self):
        self.savedValue = float(self.powersupply.ask("volt?"))
        self.lastValue = self.savedValue
   
    def restoreValue(self):
        self.setValue( self.savedValue )        
    
    def setValue(self,value):
        if isinstance(value,magnitude.Magnitude):
            myvalue = value.ounit("V").toval()
        else:
            myvalue = value
        for v in numpy.linspace(self.lastValue, myvalue, int(round(abs(self.lastValue-myvalue)/self.stepsize)) ):
            self.powersupply.write("volt " + str(v))#set voltage
            self.lastValue = v
        
    def currentValue(self):
        return self.lastValue
    
    def currentExternalValue(self):
        self.lastExternalValue = self.wavemeter.get_frequency(4)
        while self.lastExternalValue <=0:
            self.lastExternalValue = self.wavemeter.get_frequency(4)    
        self.detuning=(self.lastExternalValue*2-2*self.AOMFreq)-755222.766
        return self.detuning

        
ExternalScannedParameters = { 'Laser Lock Scan': LaserVCOScan }
