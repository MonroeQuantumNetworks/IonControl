# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:22:09 2013

@author: wolverine
"""


from WavemeterGetFrequency import WavemeterGetFrequency
import numpy
import modules.magnitude as magnitude
import math

try:
    import visa
except:
    print "visa loading failed. Proceeding without."

class ExternalParameterBase:
    def __init__(self,name,config):
        self.name = name
        self.config = config
        self.baseConfigName = 'ExternalParameterBase.'+self.name
        self.delay = self.config.get(self.baseConfigName+'.delay',0.1)       # s delay between subsequent updates
        self.jump = self.config.get(self.baseConfigName+'.jump',False)       # if True go to the target value in one jump
        self.stepsize = self.config.get(self.baseConfigName+'.stepsize',1)   # the max step taken towards the tarhet value if jump is False
        self.value = 0      # the current value
        self.displayValueCallback = None
    
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
        if self.displayValueCallback:
            self.displayValueCallback(value)
    
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
        {'name': 'delay', 'type': 'float', 'value': self.delay, 'step': 0.1, 'tip': "between steps in s"},
        {'name': 'jump', 'type': 'bool', 'value': self.jump}]
        
    def update(self,param, changes):
        """
        update the parameter, called by the signal of pyqtgraph parametertree
        """
        print "ExternalParameterBase.update"
        for param, change, data in changes:
            print self, "update", param.name(), data
            setattr( self, param.name(), data)
            
    def close(self):
        self.config[self.baseConfigName+'.delay'] = self.delay
        self.config[self.baseConfigName+'.jump'] = self.jump
        self.config[self.baseConfigName+'.stepsize'] = self.stepsize

class N6700BPowerSupply(ExternalParameterBase):
    """
    Adjust the current on the N6700B current supply
    """
    def __init__(self,name,config,instrument="QGABField"):
        ExternalParameterBase.__init__(self,name,config)
        print "trying to open '{0}'".format(instrument)
        self.instrument = visa.instrument(instrument) #open visa session
        print "opend {0}".format(instrument)
        self.stepsize = 1000
        self.channel = self.config.get('N6700BPowerSupply.'+self.name+'.channel',3)
        self._getValue_()
    
    def setValue(self,value):
        """
        Move one steps towards the target, return current value
        """
        if isinstance(value,magnitude.Magnitude):
            myvalue = value.ounit("A").toval()
        else:
            myvalue = value
        if abs(myvalue-self.value)<self.stepsize:
            self._setValue_( myvalue )
            ExternalParameterBase.setValue(self, magnitude.mg(myvalue,"A") )
            return True
        else:
            self._setValue_( self.value + math.copysign(self.stepsize, myvalue-self.value) )
            ExternalParameterBase.setValue(self, magnitude.mg(self.value + math.copysign(self.stepsize, myvalue-self.value),"A") )
            return False
            
    def _setValue_(self, v):
        command = "Curr {0},(@{1})".format(v,self.channel)
        self.instrument.write(command)#set voltage
        self.value = v
        
    def _getValue_(self):
        command = "Curr? (@{0})".format(self.channel)
        self.value = float(self.instrument.ask(command))#set voltage
        return self.value
        
    def currentValue(self):
        return magnitude.mg(self.value,"A")
    
    def currentExternalValue(self):
        command = "MEAS:CURR? (@{0})".format(self.channel)
        value = float( self.instrument.ask(command))
        return value  #magnitude.mg(value,"A")

    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'channel', 'type': 'int', 'value': self.channel})
        print superior
        return superior
        
    def close(self):
        ExternalParameterBase.close(self)
        self.config['N6700BPowerSupply.'+self.name+'.channel'] = self.channel

class LaserSynthesizerScan(ExternalParameterBase):
    """
    Scan the laser frequency by scanning a synthesizer HP8672A. (The laser is locked to a sideband)
    """
    def __init__(self,name,config, instrument="GPIB0::23::INSTR"):
        ExternalParameterBase.__init__(self,name,config)
        self.synthesizer = visa.instrument(instrument) #open visa session
        self.stepsize = 1000
        self.value = self.config.get('LaserSynthesizerScan.'+self.name+'.frequency',0)
    
    def setValue(self,value):
        """
        Move one steps towards the target, return current value
        """
        if isinstance(value,magnitude.Magnitude):
            myvalue = round(value.ounit("kHz").toval())
        else:
            myvalue = round(value)
        if abs(myvalue-self.value)<self.stepsize or self.jump:
            self._setValue_( myvalue )
            ExternalParameterBase.setValue(self, magnitude.mg(myvalue/1000.,"MHz") )
            return True
        else:
            self._setValue_( self.value + math.copysign(self.stepsize, myvalue-self.value) )
            ExternalParameterBase.setValue(self, magnitude.mg((self.value + math.copysign(self.stepsize, myvalue-self.value))/1000.,"MHz") )
            return False
            
    def _setValue_(self, v):
        command = "P{0:0>8.0f}Z0K1L6O1".format(v)
        self.synthesizer.write(command)#set voltage
        self.value = v
        
    def currentValue(self):
        return magnitude.mg(self.value/1000.,"MHz")
    
    def currentExternalValue(self):
        return self.value/1000.
        
    def close(self):
        ExternalParameterBase.close(self)
        self.config['LaserSynthesizerScan.'+self.name+'.frequency'] = self.value
    
    def paramDef(self):
        """
        return the parameter definition used by pyqtgraph parametertree to show the gui
        """
        return [{'name': 'stepsize', 'type': 'float', 'value': self.stepsize, 'tip': "in kHz"},
        {'name': 'delay', 'type': 'float', 'value': self.delay, 'step': 0.1, 'tip': "between steps in s"},
        {'name': 'jump', 'type': 'bool', 'value': self.jump}]


    
class LaserVCOScan(ExternalParameterBase):
    """
    Scan a laser by changing the voltage on a HP power supply. The frequency is controlled via
    a VCO. The laser frequency is determined by reading the wavemeter.
    """
    def __init__(self,name,config,instrument="power_supply_next_to_397_box"):
        ExternalParameterBase.__init__(self,name,config)
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
        ExternalParameterBase.setValue(self, magnitude.mg(self.value,"V") )
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
    def __init__(self,name,config,instrument="power_supply_next_to_397_box"):
        ExternalParameterBase.__init__(self,name,config)
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
        ExternalParameterBase.setValue(self, magnitude.mg(myvalue,"GHz") )
        return numpy.abs(self.wavemeter.get_frequency(self.channel)-self.value)<.005
           
                
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
        return self.lastExternalValue 

    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'channel', 'type': 'int', 'value': self.channel})
        print superior
        return superior

    def saveValue(self):
        """
        save current value
        """
        self.savedValue = self.currentExternalValue()

class DummyParameter(ExternalParameterBase):
    """
    DummyParameter, used to debug this part of the software.
    """
    def __init__(self,name,config,instrument=''):
        ExternalParameterBase.__init__(self,name,config)
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
            ExternalParameterBase.setValue(self, magnitude.mg(myvalue,"kHz") )
            return True
        else:
            self.value = ( self.value + math.copysign(self.stepsize, myvalue-self.value) )
            ExternalParameterBase.setValue(self, magnitude.mg(self.value,"kHz") )
            return False
    
        
ExternalScannedParameters = { 'Laser Lock Scan': LaserVCOScan, 
                              'Laser Synthesizer Scan': LaserSynthesizerScan,
                              'Dummy': DummyParameter,
                              'Laser Wavemeter Scan': LaserWavemeterScan,
                              'B-Field Current X': N6700BPowerSupply,
                              'B-Field Current Y': N6700BPowerSupply,
                              'B-Field Current Z': N6700BPowerSupply}

