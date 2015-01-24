import logging
import modules.magnitude as magnitude
from ExternalParameterBase import ExternalParameterBase
from multiprocessing.connection import Client

class LockOutputFrequency(ExternalParameterBase):
    """
    Adjust the current on the N6700B current supply
    """
    className = "Digital Lock Output Frequency"
    _dimension = magnitude.mg(200,'MHz')
    _outputChannels = { "OutputFrequency": "MHz" }    # a single channel with key None designates a device only supporting a single channel
    def __init__(self,name,config,instrument="localhost:16888"):
        logger = logging.getLogger(__name__)
        ExternalParameterBase.__init__(self,name,config)
        logger.info( "trying to open '{0}'".format(instrument) )
        host, port = instrument.split(':')
        self.instrument = Client((host,int(port)), authkey="yb171")
        logger.info( "opened {0}".format(instrument) )
        self.setDefaults()
        self.getAllValues()
        
    def getAllValues(self):
        for channel in self._outputChannels.iterkeys():
            self.settings.value[channel] = self._getValue(channel)

    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
        self.settings.__dict__.setdefault('stepsize' , magnitude.mg(100,'MHz'))       # if True go to the target value in one jump
            
    def _setValue(self, channel, v):
        self.instrument.send( ('set{0}'.format(channel), (v, ) ) )
        result = self.instrument.recv()
        if isinstance(result, Exception):
            raise result
        self.settings.value[channel] = v
        return result
        
    def _getValue(self, channel):
        self.instrument.send( ('get{0}'.format(channel), tuple() ) )
        result = self.instrument.recv()
        if isinstance(result, Exception):
            raise result
        return result
        
    def currentValue(self, channel):
        return self.settings.value[channel]
    
    def currentExternalValue(self, channel):
        return self._getValue() 

    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
        return superior
    
    def close(self):
        del self.instrument
        
