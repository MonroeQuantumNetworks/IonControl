# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 14:53:26 2013

@author: plmaunz
"""

import logging
import struct

from pulser.PulserHardwareClient import check
from modules.magnitude import mg
from modules.Expression import Expression
from pulseProgram.PulseProgram import encode, decode
from pulser.PulserConfig import DAADInfo
from gui.ExpressionValue import ExpressionValue
from modules.SetterProperty import SetterProperty

class DACException(Exception):
    pass

class DACChannelSetting(object):
    expression = Expression()
    def __init__(self, globalDict=None ):
        self._globalDict = None
        self._voltage = ExpressionValue(None, self._globalDict)
        self.enabled = False
        self.name = ""
        
    @property
    def outputVoltage(self):
        return self._voltage.value if self.enabled else mg(0,'V')

    @property
    def globalDict(self):
        return self._globalDict
    
    @globalDict.setter
    def globalDict(self, globalDict):
        self._globalDict = globalDict
        self._voltage.globalDict = globalDict
        
    @property
    def voltage(self):
        return self._voltage.value
    
    @voltage.setter
    def voltage(self, v):
        self._voltage.value = v
    
    @property
    def voltageText(self):
        return self._voltage.string
    
    @voltageText.setter
    def voltageText(self, s):
        self._voltage.string = s
        
    @SetterProperty
    def onChange(self, onChange):
        self._voltage.observable.subscribe(onChange)
    
class DAC:
    def __init__(self,pulser):
        self.pulser = pulser
        self.numChannels = self.pulser.getConfiguration()['DACChannels']
        config = self.pulser.pulserConfiguration()
        self.dacInfo = config.dac if config else DAADInfo() 

    def rawToMagnitude(self, raw):
        return decode( raw, self.dacInfo.encoding )

    def setVoltage(self, channel, voltage):
        intVoltage = encode( voltage, self.dacInfo.encoding )
        self.sendCommand(channel, 0, intVoltage)
        return intVoltage
    
    def sendCommand(self, channel, cmd, data):
        logger = logging.getLogger(__name__)
        if self.pulser:
            check( self.pulser.SetWireInValue(0x03, (channel & 0xff)<<4 | (cmd & 0xf) ), "DAC" ) 
            self.pulser.WriteToPipeIn(0x84, bytearray(struct.pack('=HQ', 0x12, data)) )
            self.pulser.UpdateWireIns()
            check( self.pulser.ActivateTriggerIn(0x40,4), "DAC trigger")
            self.pulser.UpdateWireIns()
        else:
            logger.warning( "Pulser not available" )
            
    def update(self, channelmask):
        pass
        
        
if __name__ == "__main__":
    ad = DAC(None)
    