'''
Created on Jul 24, 2014

@author: wolverine
'''

from Conex.ConexInstrument import ConexInstrument
from ExternalParameterBase import ExternalParameterBase
from modules import magnitude
import math
import logging

class ConexLinear(ExternalParameterBase):
    """
    Adjust the current on the N6700B current supply
    """
    className = "Conex Linear Motion"
    dimension = magnitude.mg(1,'mm')
    def __init__(self,name,config,instrument="COM3"):
        logger = logging.getLogger(__name__)
        ExternalParameterBase.__init__(self,name,config)
        logger.info( "trying to open '{0}'".format(instrument) )
        self.instrument = ConexInstrument() #open visa session
        self.instrument.open(instrument)
        self.instrument.homeSearch()
        logger.info( "opened {0}".format(instrument) )
        self.setDefaults()
        self.value = self._getValue()

    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
            
    def _setValue(self, v):
        self.instrument.position = v.toval('mm')
        self.value = v
        
    def _getValue(self):
        self.value = magnitude.mg(self.instrument.position, 'mm') #set voltage
        return self.value
        
    def currentValue(self):
        return self.value
    
    def currentExternalValue(self):
        self.value = magnitude.mg(self.instrument.position, 'mm') #set voltage
        return self.value

    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        return superior
    
    def close(self):
        del self.instrument
        
    def setValue(self,value):
        self._setValue( value )
        if self.displayValueCallback:
            self.displayValueCallback( self._getValue() )
        return not self.instrument.motionRunning()
        
class ConexRotation(ExternalParameterBase):
    """
    Adjust the current on the N6700B current supply
    """
    className = "Conex Rotation"
    dimension = magnitude.mg(1,'')
    def __init__(self,name,config,instrument="COM3"):
        logger = logging.getLogger(__name__)
        ExternalParameterBase.__init__(self,name,config)
        logger.info( "trying to open '{0}'".format(instrument) )
        self.instrument = ConexInstrument() #open visa session
        self.instrument.open(instrument)
        self.instrument.homeSearch()
        logger.info( "opened {0}".format(instrument) )
        self.setDefaults()
        self.value = self._getValue()

    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
            
    def _setValue(self, v):
        self.instrument.position = v.toval()
        self.value = v
        
    def _getValue(self):
        self.value = magnitude.mg(self.instrument.position) #set voltage
        return self.value
        
    def currentValue(self):
        return self.value
    
    def currentExternalValue(self):
        self.value = magnitude.mg(self.instrument.position) #set voltage
        return self.value

    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        return superior
    
    def close(self):
        del self.instrument

    def setValue(self,value):
        self._setValue( value )
        if self.displayValueCallback:
            self.displayValueCallback( self._getValue() )
        return not self.instrument.motionRunning()
    
    
class PowerWaveplate(ExternalParameterBase):
    """
    Adjust the current on the N6700B current supply
    """
    className = "Power Waveplate"
    dimension = magnitude.mg(1,'W')
    def __init__(self,name,config,instrument="COM3"):
        logger = logging.getLogger(__name__)
        ExternalParameterBase.__init__(self,name,config)
        logger.info( "trying to open '{0}'".format(instrument) )
        self.instrument = ConexInstrument() #open visa session
        self.instrument.open(instrument)
        logger.info( "opened {0}".format(instrument) )
        self.setDefaults()
        self.value = self._getValue()
        if not self.instrument.readyToMove():
            logger.error("Conex device {0} needs to do a home search. Please press the home search button.".format(instrument))
        
    def homeSearch(self):
        self.instrument.homeSearch()  
        
    def resetDevice(self):
        self.instrument.reset()      

    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
        self.settings.__dict__.setdefault('min_power', magnitude.mg(10,'mW') )      # s delay between subsequent updates
        self.settings.__dict__.setdefault('max_power' , magnitude.mg(3.6,'W'))       # if True go to the target value in one jump
        self.settings.__dict__.setdefault('angle_at_min' , magnitude.mg(1))       # if True go to the target value in one jump
        self.settings.__dict__.setdefault('angle_at_max' , magnitude.mg(45))       # if True go to the target value in one jump
        self.settings.__dict__.setdefault('power_limit' , magnitude.mg(1,'W'))       # if True go to the target value in one jump
        self.settings.__dict__.setdefault('min_angle_limit' , magnitude.mg(0))
        self.settings.__dict__.setdefault('max_angle_limit' , magnitude.mg(0))
        
            
    def power(self, angle):
        if self.settings.angle_at_min < angle < self.settings.angle_at_max:
            k = 180/(self.settings.angle_at_max-self.settings.angle_at_min)
            zeroangle = self.settings.angle_at_min
            return (self.settings.max_power-self.settings.min_power)*(0.5*math.sin((k*(angle-zeroangle)-90)*math.pi/180)+0.5)+self.settings.min_power
        return None
    
    def angle(self, power):
        if self.settings.min_power < power < self.settings.max_power:
            k = 180/(self.settings.angle_at_max-self.settings.angle_at_min)
            return (180/math.pi*math.asin(2*(power-self.settings.min_power)/(self.settings.max_power-self.settings.min_power)-1)+90)/k+self.settings.angle_at_min
        return None
            
    def _setValue(self, v):
        setangle =self.angle(v)
        if setangle is not None and self.settings.min_angle_limit <= setangle <= self.settings.max_angle_limit:
            self.instrument.position = setangle.toval()
            self.value = v
        
    def _getValue(self):
        self.value = self.power( magnitude.mg(self.instrument.position) ) #set voltage
        return self.value
        
    def currentValue(self):
        return self.value
    
    def currentExternalValue(self):
        self.value = self.power( magnitude.mg(self.instrument.position) ) #set voltage
        return self.value

    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'min_power', 'type': 'magnitude', 'value': self.settings.min_power})
        superior.append({'name': 'max_power', 'type': 'magnitude', 'value': self.settings.max_power})
        superior.append({'name': 'angle_at_min', 'type': 'magnitude', 'value': self.settings.angle_at_min})
        superior.append({'name': 'angle_at_max', 'type': 'magnitude', 'value': self.settings.angle_at_max})
        superior.append({'name': 'power_limit', 'type': 'magnitude', 'value': self.settings.power_limit})
        superior.append({'name': 'min_angle_limit', 'type': 'magnitude', 'value': self.settings.min_angle_limit, 'readonly': True})
        superior.append({'name': 'max_angle_limit', 'type': 'magnitude', 'value': self.settings.max_angle_limit, 'readonly': True})
        superior.append({'name': 'Home search', 'type': 'action', 'field': 'homeSearch' })
        superior.append({'name': 'Reset device', 'type': 'action', 'field': 'resetDevice' })
        return superior
    
    def close(self):
        del self.instrument

    def setValue(self,value):
        self._setValue( value )
        if self.displayValueCallback:
            self.displayValueCallback( self._getValue() )
        return not self.instrument.motionRunning()

    def update(self, param, changes):
        super(PowerWaveplate, self).update(param, changes)
        highangle = self.angle( self.settings.power_limit )
        self.settings.min_angle_limit = min( self.settings.angle_at_min, highangle)
        self.settings.max_angle_limit = max( self.settings.angle_at_min, highangle)
        self._parameter['min_angle_limit'] = self.settings.min_angle_limit
        self._parameter['max_angle_limit'] = self.settings.max_angle_limit
