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

class ExternalParameterBase:
    def __init__(self):
        self.delay = 0.1    # s delay between subsequent updates
        self.jump = False   # if True go to the target value in one jump
        self.stepsize = 1   # the max step taken towards the tarhet value if jump is False
        self.value = 0      # the current value
    
    def saveValue(self):
        """
        save current value
        """
        self.savedValue = self.value
    
    def restoreValue(self):
        """
        restore the value saved previously, this routine only goes stepsize towards this value
        if the stored value is reached returns True, otherwise False. Needs to be called repeatedly
        until it returns True in order to restore the saved value.
        """
        return self.setValue(self.savedValue)
    
    def setValue(self,value):
        """
        go stepsize towards the value. This function returns True if the value is reached. Otherwise
        it should return False. The user should call repeatedly until the intended value is reached
        and True is returned.
        """
        pass
    
    def currentValue(self):
        """
        returns current value
        """
        return self.value
    
    def currentExternalValue(self):
        """
        if the value is determined externally, return the external value, otherwise return value
        """
        return self.value

    def paramDef(self):
        """
        return the parameter definition used by pyqtgraph parametertree to show the gui
        """
        return [{'name': 'stepsize', 'type': 'float', 'value': self.stepsize},
        {'name': 'delay', 'type': 'float', 'value': self.delay, 'step': 0.1},
        {'name': 'jump', 'type': 'bool', 'value': self.jump, 'tip': "This is a checkbox"}]
        
    def update(self,param, changes):
        """
        update the parameter, called by the signal of pyqtgraph parametertree
        """
        for param, change, data in changes:
            print self, "update", param.name(), data
            setattr( self, param.name(), data)
    

class LaserSynthesizerScan(ExternalParameterBase):
    """
    Scan the laser frequency by scanning a synthesizer HP8672A. (The laser is locked to a sideband)
    """
    def __init__(self, instrument="GPIB0::23::INSTR"):
        ExternalParameterBase.__init__(self)
        try:
            self.synthesizer = visa.instrument(instrument) #open visa session
        except:
            print 'Initialization fall'            
        self.stepsize = 1000
    
    def setValue(self,value):
        """
        Move one steps towards the target, return current value
        """
        if isinstance(value,magnitude.Magnitude):
            myvalue = round(value.ounit("kHz").toval())
        else:
            myvalue = round(value)
        if abs(myvalue-self.value)<self.stepsize:
            self._setValue_( myvalue )
            return True
        else:
            self._setValue_( self.value + math.copysign(self.stepsize, myvalue-self.value) )
            return False
            
    def _setValue_(self, v):
        command = "P{0:0>8.0f}Z0K0L0O1".format(v)
        self.synthesizer.write(command)#set voltage
        self.value = v
        
    def currentValue(self):
        return self.value/1000.
    
    def currentExternalValue(self):
        return self.value/1000.

    
class LaserVCOScan(ExternalParameterBase):
    """
    Scan a laser by changing the voltage on a HP power supply. The frequency is controlled via
    a VCO. The laser frequency is determined by reading the wavemeter.
    """
    def __init__(self,instrument="power_supply_next_to_397_box"):
        ExternalParameterBase.__init__(self)
        self.powersupply = visa.instrument(instrument)#open visa session
        self.wavemeter = WavemeterGetFrequency()
        self.savedValue = float(self.powersupply.ask("volt?"))
        print "LaserVCOScan savedValue", self.savedValue
        self.value = self.savedValue
        self.stepsize = 0.01
        self.AOMFreq = 110.0e-3
    
    def setValue(self,value):
        """
        Move one steps towards the target, return current value
        """
        if isinstance(value,magnitude.Magnitude):
            myvalue = value.ounit("V").toval()
        else:
            myvalue = value
        if abs(myvalue-self.value)<=self.stepsize:
            nextvalue = myvalue
            arrived = True
        else:
            nextvalue =  self.value + math.copysign(self.stepsize, myvalue-self.value)
            arrived = False
        self.powersupply.write("volt " + str(nextvalue))
        self.value = nextvalue
        print "setValue", self.value 
        return arrived
            
    def currentValue(self):
        return magnitude.mg(self.value,'V')
    
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

    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'AOMFreq', 'type': 'float', 'value': self.AOMFreq})
        print superior
        return superior
        
class LaserWavemeterScan(ExternalParameterBase):
    """
    Scan a laser by changing the voltage on a HP power supply. The frequency is controlled via
    a VCO. The laser frequency is determined by reading the wavemeter.
    """
    def __init__(self,instrument="power_supply_next_to_397_box"):
        ExternalParameterBase.__init__(self)
        self.wavemeter = WavemeterGetFrequency()
        self.savedValue = 0
        print "LaserWavemeterScan savedValue", self.savedValue
        self.value = self.savedValue
        self.channel = 6
    
    def setValue(self,value):
        """
        Move one steps towards the target, return current value
        """
        if isinstance(value,magnitude.Magnitude):
            myvalue = value.ounit("GHz").toval()
        else:
            myvalue = value
        
        self.wavemeter.set_frequency(myvalue, self.channel)
        self.value = myvalue
        print "setValue", self.value 
        return True
                
    def currentExternalValue(self):
#        self.lastExternalValue = self.wavemeter.get_frequency(4)
#        while self.lastExternalValue <=0:
        self.lastExternalValue = self.wavemeter.get_frequency(self.channel) 
        print self.lastExternalValue
        self.detuning=(self.lastExternalValue)
        counter = 0
        while numpy.abs(self.detuning)>=1 and counter<10:
            self.lastExternalValue = self.wavemeter.get_frequency(self.channel)    
            self.detuning=(self.lastExternalValue-self.value)
            counter += 1
        return self.detuning

    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'channel', 'type': 'int', 'value': self.channel})
        print superior
        return superior

class DummyParameter(ExternalParameterBase):
    """
    DummyParameter, used to debug this part of the software.
    """
    def __init__(self,instrument=''):
        ExternalParameterBase.__init__(self)
        print "Opening DummyInstrument", instrument
        self.savedValue = self.value
    
    def setValue(self,value):
        """
        Move one steps towards the target, return current value
        """
        if isinstance(value,magnitude.Magnitude):
            myvalue = round(value.ounit("kHz").toval())
        else:
            myvalue = round(value)
        if abs(myvalue-self.value)<self.stepsize or self.jump:
            self.value = myvalue 
            return True
        else:
            self.value = ( self.value + math.copysign(self.stepsize, myvalue-self.value) )
            return False
    
        
ExternalScannedParameters = { 'Laser Lock Scan': LaserVCOScan, 
                              'Laser Synthesizer Scan': LaserSynthesizerScan,
                              'Dummy': DummyParameter,
                              'Laser Wavemeter Scan': LaserWavemeterScan}

