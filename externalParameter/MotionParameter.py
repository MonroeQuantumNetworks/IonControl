'''
Created on Jul 24, 2014

@author: wolverine
'''

from Conex.ConexInstrument import ConexInstrument
from ExternalParameterBase import ExternalParameterBase
from modules import magnitude
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
            self.displayValueCallback( self.value )
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
            self.displayValueCallback( self.value )
        return not self.instrument.motionRunning()
