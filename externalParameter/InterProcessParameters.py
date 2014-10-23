import logging
import modules.magnitude as magnitude
from ExternalParameterBase import ExternalParameterBase
from multiprocessing.connection import Client



class LockOutputFrequency(ExternalParameterBase):
    """
    Adjust the current on the N6700B current supply
    """
    className = "Digital Lock Output Frequency"
    dimension = magnitude.mg(200,'MHz')
    def __init__(self,name,config,instrument="localhost:16888"):
        logger = logging.getLogger(__name__)
        ExternalParameterBase.__init__(self,name,config)
        logger.info( "trying to open '{0}'".format(instrument) )
        host, port = instrument.split(':')
        self.instrument = Client((host,int(port)), authkey="yb171")
        logger.info( "opened {0}".format(instrument) )
        self.setDefaults()
        self.value = self._getValue()

    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
        self.settings.__dict__.setdefault('stepsize' , magnitude.mg(100,'MHz'))       # if True go to the target value in one jump
            
    def _setValue(self, v):
        self.instrument.send( ('setOutputFrequency', (v, ) ) )
        result = self.instrument.recv()
        if isinstance(result, Exception):
            raise result
        self.value = v
        return result
        
    def _getValue(self):
        self.instrument.send( ('getOutputFrequency', tuple() ) )
        result = self.instrument.recv()
        if isinstance(result, Exception):
            raise result
        return result
        
    def currentValue(self):
        return self.value
    
    def currentExternalValue(self):
        return self._getValue() 

    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
        return superior
    
    def close(self):
        del self.instrument
        
