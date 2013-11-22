# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:22:09 2013

@author: wolverine
"""


from WavemeterGetFrequency import WavemeterGetFrequency
import numpy
import modules.magnitude as magnitude
import math
from pyqtgraph.parametertree import Parameter
from PyQt4 import QtCore
try:
    import visa
except:
    print "visa loading failed. Proceeding without."
    
    
    
def nextValue( current, target, stepsize, jump ):
    temp = target-current
    return (target,True) if abs(temp)<=stepsize or jump else (current + stepsize.copysign(temp), False)  
            

class ExternalParameterBase(object):
    def __init__(self,name,settings):
        self.name = name
        self.settings = settings
        self.displayValueCallback = None
        self.setDefaults()
        self._parameter = Parameter.create(name='params', type='group',children=self.paramDef())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        
    @property
    def parameter(self):
        # re-create the parameters each time to prevent a exception that says the signal is not connected
        self._parameter = Parameter.create(name='params', type='group',children=self.paramDef())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        return self._parameter        
        
    def setDefaults(self):
        self.settings.__dict__.setdefault('delay', magnitude.mg(100,'ms') )      # s delay between subsequent updates
        self.settings.__dict__.setdefault('jump' , False)       # if True go to the target value in one jump
        self.settings.__dict__.setdefault('value', None )      # the current value       
    
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
        newvalue, arrived = nextValue(self.value, value, self.settings.stepsize, self.settings.jump)
        self._setValue( newvalue )
        if self.displayValueCallback:
            self.displayValueCallback( self.value )
        return arrived
    
    def _setValue(self, v):
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
        return [{'name': 'delay', 'type': 'magnitude', 'value': self.settings.delay, 'tip': "between steps"},
                {'name': 'jump', 'type': 'bool', 'value': self.settings.jump}]
        
    def update(self,param, changes):
        """
        update the parameter, called by the signal of pyqtgraph parametertree
        """
        print "ExternalParameterBase.update"
        for param, change, data in changes:
            print self, "update", param.name(), data
            setattr( self.settings, param.name(), data)
            

class N6700BPowerSupply(ExternalParameterBase):
    """
    Adjust the current on the N6700B current supply
    """
    className = "N6700 Powersupply"
    def __init__(self,name,config,instrument="QGABField"):
        ExternalParameterBase.__init__(self,name,config)
        print "trying to open '{0}'".format(instrument)
        self.instrument = visa.instrument(instrument) #open visa session
        print "opend {0}".format(instrument)
        self.setDefaults()
        self.value = self._getValue()

    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
        self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1,'A'))       # if True go to the target value in one jump
        self.settings.__dict__.setdefault('channel' , 0)       # if True go to the target value in one jump        
            
    def _setValue(self, v):
        command = "Curr {0},(@{1})".format(v.ounit('A').toval(),self.settings.channel)
        self.instrument.write(command)#set voltage
        self.value = v
        
    def _getValue(self):
        command = "Curr? (@{0})".format(self.channel)
        self.value = magnitude.mg(float(self.instrument.ask(command)), 'A') #set voltage
        return self.value
        
    def currentValue(self):
        return self.value
    
    def currentExternalValue(self):
        command = "MEAS:CURR? (@{0})".format(self.channel)
        value = magnitude.mg( float( self.instrument.ask(command)), 'A' )
        return value 

    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'channel', 'type': 'int', 'value': self.channel})
        superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.stepsize})
        return superior
        

class LaserSynthesizerScan(ExternalParameterBase):
    """
    Scan the laser frequency by scanning a synthesizer HP8672A. (The laser is locked to a sideband)
    setValue is frequency of synthesizer
    currentValue and currentExternalValue are current frequency of synthesizer
    """
    className = "Laser Lock Synthesizer"
    def __init__(self,name,config, instrument="GPIB0::23::INSTR"):
        ExternalParameterBase.__init__(self,name,config)
        #self.amplitudeString = "Z0K1L6O1"
        #self.amplitudeString = "O3K0L0N0Z1"
        self.synthesizer = visa.instrument(instrument) #open visa session
        self.synthesizer.write(self.amplitudeString)
        self.setDefaults()
        self.value = self.settings.value

    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
        self.settings.__dict__.setdefault('lockPoint', magnitude.mg(384227.944,'GHz') )      # s delay between subsequent updates
        self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1,'MHz'))       # if True go to the target value in one jump
        self.settings.__dict__.setdefault('amplitudeStr' , "Z0K1L6O1" )       # if True go to the target value in one jump
   
    def setValue(self,value):
        """
        Move one steps towards the target, return current value
        """
        newvalue, arrived = nextValue(self.value, value, self.settings.stepsize, self.settings.jump)
        self._setValue( newvalue )
        if self.displayValueCallback:
            self.displayValueCallback(value,"{0}".format( self.lockPoint - newvalue ) )
        return arrived
            
    def _setValue(self, value ):
        value = value.round('kHz')
        command = "P{0:0>8.0f}".format(value.toval('kHz')) + self.settings.amplitudeStr
        self.synthesizer.write(command)
        self.value = value
        
    def paramDef(self):
        """
        return the parameter definition used by pyqtgraph parametertree to show the gui
        """
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'lockpoint', 'type': 'magnitude', 'value': self.settings.lockPoint})
        superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
        superior.append({'name': 'amplitudeStr', 'type': 'str', 'value': self.settings.amplitudeStr})
        return superior


class MicrowaveSynthesizerScan(ExternalParameterBase):
    """
    Scan the microwave frequency of microwave synthesizer 
    """
    className = "Microwave Synthesizer"
    def __init__(self,name,config, instrument="GPIB0::23::INSTR"):
        ExternalParameterBase.__init__(self,name,config)
        self.synthesizer = visa.instrument(instrument) #open visa session
        self.setDefaults()
    
    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
        self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1,'MHz'))       # if True go to the target value in one jump

    def _setValue(self, v):
        v = v.round('kHz')
        command = ":FREQ:CW {0:.0f}KHZ".format(v.toval('kHz'))
        self.synthesizer.write(command)
        self.value = v
        
    def paramDef(self):
        """
        return the parameter definition used by pyqtgraph parametertree to show the gui
        """
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
        return superior

    
class LaserVCOScan(ExternalParameterBase):
    """
    Scan a laser by changing the voltage on a HP power supply. The frequency is controlled via a VCO. 
    setValue is voltage of vco
    currentValue and currentExternalValue are current applied voltage
    """
    className = "Laser VCO"
    def __init__(self,name,config,instrument="power_supply_next_to_397_box"):
        ExternalParameterBase.__init__(self,name,config)
        self.powersupply = visa.instrument(instrument)#open visa session
        self.savedValue = magnitude.mg( float(self.powersupply.ask("volt?")), 'V')
        print "LaserVCOScan savedValue", self.savedValue
        self.value = self.savedValue
        self.setDefaults()
    
    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
        self.settings.__dict__.setdefault('stepsize' , magnitude.mg(10,'mV'))       # if True go to the target value in one jump
        self.settings.__dict__.setdefault('AOMFreq' , magnitude.mg(1,'MHz'))       # if True go to the target value in one jump
    
    def _setValue(self,value):
        """
        Move one steps towards the target, return current value
        """
        self.powersupply.write("volt {0}".format(value.toval('V')))
        self.value = value
        print "setValue volt {0}".format(value.toval('V'))
            
    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'AOMFreq', 'type': 'magnitude', 'value': self.settings.AOMFreq})
        superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
        return superior
        
class LaserWavemeterScan(LaserVCOScan):
    """
    Scan a laser by changing the voltage on a HP power supply. The frequency is controlled via a VCO. 
    setValue is voltage of vco
    currentValue is applied voltage
    currentExternalValue are frequency read from wavemeter
    """
    
    className = "Laser VCO Wavemeter"
    def __init__(self,name,config,instrument="power_supply_next_to_397_box"):
        LaserVCOScan.__init__(self,name,config,instrument)
        self.wavemeter = WavemeterGetFrequency()
        self.channel = 6

    def currentExternalValue(self):
        self.lastExternalValue = self.wavemeter.get_frequency(self.channel) 
        print self.lastExternalValue
        self.detuning=(self.lastExternalValue)
        counter = 0
        while numpy.abs(self.detuning)>=1 and counter<10:
            self.lastExternalValue = self.wavemeter.get_frequency(self.channel)    
            self.detuning=(self.lastExternalValue-self.value)
            counter += 1
        return self.lastExternalValue       
        
class LaserWavemeterLockScan(ExternalParameterBase):
    """
    Scan a laser by setting the lock point on the wavemeter lock.
    setValue is laser frequency
    currentValue is currently set value
    currentExternalValue is frequency read from wavemeter
    """
    
    className = "Laser Wavemeter Lock"
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
        #print superior
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
    className = "Dummy"
    def __init__(self,name,settings,instrument=''):
        ExternalParameterBase.__init__(self,name,settings)
        print "Opening DummyInstrument", instrument
        self.setDefaults()
        self.settings.value = magnitude.mg( 12, 'kHz')
        self.savedValue = self.settings.value
        self.value = self.settings.value

    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
        self.settings.__dict__.setdefault('AOMFreq', magnitude.mg(123,'MHz') )      # s delay between subsequent updates
        self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1,'MHz'))       # if True go to the target value in one jump
   
    def _setValue(self,value):
        print "Dummy output set to:", value
        self.value = value
         
    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'AOMFreq', 'type': 'magnitude', 'value': self.settings.AOMFreq})
        superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
        return superior

    
        
ExternalScannedParameters = { LaserWavemeterLockScan.className: LaserWavemeterLockScan, 
                              LaserSynthesizerScan.className: LaserSynthesizerScan,
                              LaserVCOScan.className: LaserVCOScan,
                              LaserWavemeterScan.className : LaserWavemeterScan,
                              DummyParameter.className: DummyParameter,
                              N6700BPowerSupply.className: N6700BPowerSupply,
                              MicrowaveSynthesizerScan.className : MicrowaveSynthesizerScan }

