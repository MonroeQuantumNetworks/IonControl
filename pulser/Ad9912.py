# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 14:53:26 2013

@author: plmaunz
"""

import logging
import math
import struct

from pulser.PulserHardwareClient import check
from modules.magnitude import mg

class Ad9912Exception(Exception):
    pass

class Ad9912:
    def __init__(self,pulser):
        self.pulser = pulser

    def rawToMagnitude(self, raw):
        return mg(1000,' MHz') * (raw / float(2**48))

    def setSquareEnabled(self, channel, enable):
        self.sendCommand(channel, 3, 1 if enable else 0)

    def setFrequency(self, channel, frequency):
        intFrequency = int(round(2**48 * frequency.toval('GHz'))) & 0xffffffffffff
        self.sendCommand(channel, 0, intFrequency)
        return intFrequency
    
    def setFrequencyRaw(self, channel, intFrequency):
        self.sendCommand(channel, 0, intFrequency)
        #self.sendCommand(channel, 0, intFrequency >> 16 )
        #self.sendCommand(channel, 4, intFrequency & 0xffff ) # Frequency fine
        return intFrequency        
    
    def setPhase(self, channel, phase):
        intPhase = int(round(2**14 * phase.toval()/(2*math.pi)))
        self.sendCommand(channel, 1, intPhase & 0x3fff )
    
    def setAmplitude(self, channel, amplitude):
        intAmplitude = int(round(amplitude))
        self.sendCommand(channel, 2, intAmplitude & 0x3ff )
        
    def sendCommand(self, channel, cmd, data):
        logger = logging.getLogger(__name__)
        if self.pulser:
            check( self.pulser.SetWireInValue(0x03, (channel & 0xff)<<4 | (cmd & 0xf) ), "Ad9912" ) 
            self.pulser.WriteToPipeIn(0x84, bytearray(struct.pack('=HQ', 0x12, data)) )
            self.pulser.UpdateWireIns()
            check( self.pulser.ActivateTriggerIn(0x40,1), "Ad9912 trigger")
            self.pulser.UpdateWireIns()
        else:
            logger.warning( "Pulser not available" )
        
    def update(self, channelmask):
        logger = logging.getLogger(__name__)
        if self.pulser:
            self.pulser.WriteToPipeIn(0x84, bytearray(struct.pack('=HQ', 0x11, channelmask)) )
            self.pulser.ActivateTriggerIn(0x41,2)
        else:
            logger.warning( "Pulser not available" )
        
    def reset(self, mask):
        logger = logging.getLogger(__name__)
        if self.pulser:
            check(  self.pulser.SetWireInValue(0x04, mask&0xffff ) , "AD9912 reset mask" )
            check( self.pulser.ActivateTriggerIn(0x42,0), "DDS Reset" )
        else:
            logger.warning( "Pulser not available" )

        
if __name__ == "__main__":
    import modules.magnitude as magnitude
    
    ad = Ad9912(None)
    ad.setFrequency( 0, magnitude.mg(250,'MHz'))
    