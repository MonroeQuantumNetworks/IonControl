'''
Created on Jul 24, 2014

@author: wolverine
'''

from Conex.ConexInstrument import ConexInstrument, ConexInstrumentException
from ExternalParameterBase import ExternalParameterBase
from modules import magnitude
import math
import logging
import serial.tools.list_ports


class ConexLinear(ExternalParameterBase):
    """
    Adjust the position of the Conex linear stage
    """
    className = "Conex Linear Motion"
    _outputChannels = {None: 'mm'}
    _channelParams = {None: ({'name': 'belowMargin','type': 'magnitude', 'value': magnitude.mg(0,'mm'), 'tip': 'if not zero: if coming from above always go that far below and then up'},
                             {'name': 'limit', 'type': 'magnitude', 'value': magnitude.mg(25,'mm')})}

    def __init__(self, name, config, globalDict, instrument="COM3"):
        if instrument[0:3].upper() != 'COM':  # we assume it is a serial number
            found = [desc for desc in serial.tools.list_ports.comports() if desc.serial_number == instrument]
            if not found:
                raise ConexInstrumentException("Device with serial numnber '{0}' not found.".format(instrument))
            instrument = found[0].device
        logger = logging.getLogger(__name__)
        ExternalParameterBase.__init__(self, name, config, globalDict)
        logger.info( "trying to open '{0}'".format(instrument) )
        self.instrument = ConexInstrument() #open visa session
        self.instrument.open(instrument)
        self.instrument.homeSearch()
        logger.info("opened {0}".format(instrument) )
        self.setDefaults()
        self.initializeChannelsToExternals()
        self.lastValue = None

    def _setValue(self, channel, v):
        try:
            if v>self.outputChannels[channel].settings.limit:
                v = self.outputChannels[channel].settings.limit
            self.instrument.position = v.toval('mm')
        except ConexInstrumentException as e:
            if str(e).find("Try a home search."):
                self.instrument.homeSearch()
            else:
                raise e
        return v
        
    def getValue(self, channel):
        return magnitude.mg(self.instrument.position, 'mm') 
        
    def close(self):
        del self.instrument
        
    def setValue(self, channel, value):
        reported = self.getValue(channel) 
        if self.instrument.motionRunning():
            return reported, False
        if value != self.outputChannels[channel].settings.value:
            if self.lastValue is None or value < self.lastValue:
                self._setValue( channel, value-self.outputChannels[channel].settings.belowMargin )
                self.lastValue = value-self.outputChannels[channel].settings.belowMargin
                return reported, False
            else:
                self._setValue( channel, value )
                self.lastValue = value
        arrived = not self.instrument.motionRunning()
        return reported, arrived

    @classmethod
    def connectedInstruments(cls):
        if map(int,serial.VERSION.split('.'))[0] < 3:
            logging.getLogger(__name__).warning("Found PySerial version {0}, expected at least version 3.0.1. Please update: 'pip install --update pyserial'".format(serial.VERSION))
            return []
        return [desc.serial_number for desc in serial.tools.list_ports.comports() if desc.vid == 0 and desc.pid == 0]


class ConexRotation(ExternalParameterBase):
    """
    Adjust the position of the Conex rotation stage
    """
    className = "Conex Rotation"
    _outputChannels = {None: ''}

    def __init__(self, name, config, globalDict, instrument="COM3"):
        if instrument[0:3].upper() != 'COM':  # we assume it is a serial number
            found = [desc for desc in serial.tools.list_ports.comports() if desc.serial_number == instrument]
            if not found:
                raise ConexInstrumentException("Device with serial numnber '{0}' not found.".format(instrument))
            instrument = found[0].device
        logger = logging.getLogger(__name__)
        ExternalParameterBase.__init__(self, name, config, globalDict)
        logger.info( "trying to open '{0}'".format(instrument) )
        self.instrument = ConexInstrument() #open visa session
        self.instrument.open(instrument)
        self.instrument.homeSearch()
        logger.info( "opened {0}".format(instrument) )
        self.setDefaults()
        self.initializeChannelsToExternals()
        self.lastValue = None

    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
        self.settings.__dict__.setdefault('limit' , magnitude.mg(360,''))       # if True go to the target value in one jump
        self.settings.__dict__.setdefault('belowMargin' , magnitude.mg(0,''))       # if True go to the target value in one jump
            
    def _setValue(self, channel, v):
        if v>self.settings.limit:
            v = self.setting.limit
        self.instrument.position = v.toval()
        return v
        
    def getValue(self, channel):
        return magnitude.mg(self.instrument.position) #set voltage

    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'limit', 'type': 'magnitude', 'value': self.settings.limit})
        superior.append({'name': 'belowMargin','type': 'magnitude', 'value': self.settings.belowMargin, 'tip': 'if not zero: if coming from above always go that far below and then up'})
        return superior
    
    def close(self):
        del self.instrument

    def setValue(self, channel, value):
        reported = self.getValue(channel)
        if self.instrument.motionRunning():
            return reported, False
        if value != self.outputChannels[channel].settings.value:
            if self.lastValue is None or value < self.lastValue:
                self._setValue( channel, value-self.settings.belowMargin )
                self.lastValue = value-self.settings.belowMargin
                return reported, False
            else:
                self._setValue( channel, value )
                self.lastValue = value
        arrived = not self.instrument.motionRunning()
        return reported, arrived
    
    @classmethod
    def connectedInstruments(cls):
        return [desc.serial_number for desc in serial.tools.list_ports.comports() if desc.vid == 0 and desc.pid == 0]


class PowerWaveplate(ExternalParameterBase):
    className = "Power Waveplate"
    _outputChannels = {None: 'W'}

    def __init__(self, name, config, globalDict, instrument="COM3"):
        if instrument[0:3].upper() != 'COM':  # we assume it is a serial number
            found = [desc for desc in serial.tools.list_ports.comports() if desc.serial_number == instrument]
            if not found:
                raise ConexInstrumentException("Device with serial numnber '{0}' not found.".format(instrument))
            instrument = found[0].device
        logger = logging.getLogger(__name__)
        ExternalParameterBase.__init__(self, name, config, globalDict)
        logger.info( "trying to open '{0}'".format(instrument) )
        self.instrument = ConexInstrument() #open visa session
        self.instrument.open(instrument)
        logger.info( "opened {0}".format(instrument) )
        self.setDefaults()
        self.initializeChannelsToExternals()
        if not self.instrument.readyToMove():
            logger.warning("Conex device {0} needs to do a home search. Please press the home search button.".format(instrument))
        self.lastValue = None
        self.arrived = False
        
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
        self.settings.__dict__.setdefault('max_angle_limit' , magnitude.mg(360))
        self.settings.__dict__.setdefault('belowMargin' , magnitude.mg(0,'mW'))       # if True go to the target value in one jump

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
            
    def _setValue(self, channel, v):
        setangle =self.angle(v)
        if setangle is not None and self.settings.min_angle_limit <= setangle <= self.settings.max_angle_limit:
            self.instrument.position = setangle.toval()

    def getValue(self, channel):
        return self.power(magnitude.mg(self.instrument.position))  # set voltage

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
        superior.append({'name': 'belowMargin','type': 'magnitude', 'value': self.settings.belowMargin, 'tip': 'if not zero: if coming from above always go that far below and then up'})
        return superior
    
    def close(self):
        del self.instrument

    def setValue(self, channel, value):
        reported = self.getValue(channel)
        logging.getLogger(__name__).debug("{0} -> {1}".format(reported, value))
        if self.instrument.motionRunning():
            return reported, False
        if value != self.outputChannels[channel].settings.value:
            if self.lastValue is None or value < self.lastValue:
                self._setValue( channel, value-self.settings.belowMargin )
                logging.getLogger(__name__).debug("set {0}".format( value-self.settings.belowMargin))
                self.lastValue = value-self.settings.belowMargin
                return reported, False
            else:
                self._setValue( channel, value )
                logging.getLogger(__name__).debug("set {0}".format( value))
                self.lastValue = value
        arrived, self.arrived = self.arrived, not self.instrument.motionRunning() # buffers arrived state to fix a bug where an external parameter's final value was one step off.
        reported = self.getValue(channel)
        logging.getLogger(__name__).debug(" -> {0} arrived {1}".format(reported, arrived))
        return reported, arrived and self.arrived

    def update(self, param, changes):
        super(PowerWaveplate, self).update(param, changes)
        highangle = self.angle( self.settings.power_limit )
        self.settings.min_angle_limit = min( self.settings.angle_at_min, highangle)
        self.settings.max_angle_limit = max( self.settings.angle_at_min, highangle)
        self._parameter['min_angle_limit'] = self.settings.min_angle_limit
        self._parameter['max_angle_limit'] = self.settings.max_angle_limit

    @classmethod
    def connectedInstruments(cls):
        return [desc.serial_number for desc in serial.tools.list_ports.comports() if desc.vid == 0 and desc.pid == 0]
