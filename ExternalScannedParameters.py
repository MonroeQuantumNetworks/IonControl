# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:22:09 2013

@author: wolverine
"""


from WavemeterGetFrequency import WavemeterGetFrequency
import numpy
import magnitude
import math

try:
    import visa
except:
    print "visa loading failed. Prceeding without."

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
    

class LaserSynthesizerScan:
    def __init__(self):
        self.synthesizer = visa.instrument("GPIB0::23::INSTR") #open visa session
        self.savedValue = 3098000
        self.lastValue = self.savedValue
        self.stepsize = 1000
        self.delay = 0.1
    
    def saveValue(self):
        #self.savedValue = float(self.synthesizer.ask("volt?"))
        #self.lastValue = self.savedValue
        pass
    
    def restoreValue(self):
        self.setValue( self.savedValue )        
    
    def setValue(self,value):
        """
        Move one steps towards the target, return current value
        """
        if isinstance(value,magnitude.Magnitude):
            myvalue = round(value.ounit("kHz").toval())
        else:
            myvalue = round(value)
        if abs(myvalue-self.lastValue)<self.stepsize:
            self._setValue_( myvalue )
            return True
        else:
            self._setValue_( self.lastValue + math.copysign(self.stepsize, myvalue-self.lastValue) )
            return False
            
    def _setValue_(self, v):
        command = "P{0:0>8.0f}Z0K0L0O1".format(v)
        self.synthesizer.write(command)#set voltage
        self.lastValue = v
        
    def currentValue(self):
        return self.lastValue/1000.
    
    def currentExternalValue(self):
        return self.lastValue/1000.
   
    
class LaserVCOScan:
    def __init__(self):
        self.powersupply = visa.instrument("power_supply_next_to_397_box")#open visa session
        self.wavemeter = WavemeterGetFrequency()
        self.savedValue = float(self.powersupply.ask("volt?"))
        print "LaserVCOScan savedValue", self.savedValue
        self.lastValue = self.savedValue
        self.stepsize = 0.01
        self.AOMFreq = 110.0e-3
    
    def saveValue(self):
        self.savedValue = float(self.powersupply.ask("volt?"))
        print "LaserVCOScan savedValue", self.savedValue
        self.lastValue = self.savedValue
   
    def restoreValue(self):
        self.setValue( self.savedValue )        
              
    def setValue(self,value):
        """
        Move one steps towards the target, return current value
        """
        if isinstance(value,magnitude.Magnitude):
            myvalue = round(value.ounit("V").toval())
        else:
            myvalue = round(value)
        if abs(myvalue-self.lastValue)<self.stepsize:
            self.powersupply.write("volt " + str(myvalue))
            return True
        else:
            self.powersupply.write("volt " + str( self.lastValue + math.copysign(self.stepsize, myvalue-self.lastValue) ))
            return False
            
    def currentValue(self):
        return self.lastValue
    
    def currentExternalValue(self):
#        self.lastExternalValue = self.wavemeter.get_frequency(4)
#        while self.lastExternalValue <=0:
        self.lastExternalValue = self.wavemeter.get_frequency(0) 
        print self.lastExternalValue
        self.detuning=(self.lastExternalValue*2-2*self.AOMFreq)-755222.766
        counter = 0
        while numpy.abs(self.detuning)>=1 and counter<10:
            self.lastExternalValue = self.wavemeter.get_frequency(4)    
            self.detuning=(self.lastExternalValue*2-2*self.AOMFreq)-755222.766
            counter += 1
        return self.detuning

        
ExternalScannedParameters = { 'Laser Lock Scan': LaserVCOScan, 'Laser Synthesizer Scan': LaserSynthesizerScan }
