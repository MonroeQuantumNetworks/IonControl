# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 14:53:26 2013

@author: plmaunz
"""

import logging
import math

from pulser.PulserHardwareClient import check
from modules.magnitude import mg

class Ad9912Exception(Exception):
    pass

class Ad9912:
    channels = 6
    def __init__(self,pulser):
        self.pulser = pulser
        self.frequency = [None]*self.channels
        self.phase = [None]*self.channels
        self.amplitude = [None]*self.channels

    def rawToMagnitude(self, raw):
        return mg(1000,' MHz') * (raw / float(2**48))

    def setFrequency(self, channel, frequency, even=False):
        intFrequency = int(round(2**48 * frequency.ounit('GHz').toval()))
        intFrequency = intFrequency &0xfffffffffffe if even else intFrequency
        self.sendCommand(channel, 0, intFrequency >> 16 )
        self.sendCommand(channel, 4, intFrequency & 0xffff )
        return intFrequency
    
    def setFrequencyRaw(self, channel, intFrequency):
        self.sendCommand(channel, 0, intFrequency >> 16 )
        self.sendCommand(channel, 4, intFrequency & 0xffff )
        return intFrequency        
    
    def setPhase(self, channel, phase):
        intPhase = int(round(2**14 * phase.ounit('rad').toval()/(2*math.pi)))
        self.sendCommand(channel, 1, intPhase & 0x3fff )
    
    def setAmplitude(self, channel, amplitude):
        intAmplitude = int(round(amplitude))
        self.sendCommand(channel, 2, intAmplitude & 0x3ff )
        
    def sendCommand(self, channel, cmd, data):
        logger = logging.getLogger(__name__)
        if self.pulser:
            check( self.pulser.SetWireInValue(0x03, (channel & 0xf)<<4 | (cmd & 0xf) ), "Ad9912" )
            check( self.pulser.SetWireInValue(0x01, data & 0xffff ), "Ad9912" )
            check( self.pulser.SetWireInValue(0x02, (data >> 16) &0xffff ), "Ad9912" )
            self.pulser.UpdateWireIns()
            check( self.pulser.ActivateTriggerIn(0x40,1), "Ad9912 trigger")
            self.pulser.UpdateWireIns()
        else:
            logger.error( "Pulser not available" )
        
    def update(self, channelmask):
        logger = logging.getLogger(__name__)
        if self.pulser:
            check( self.pulser.SetWireInValue(0x08, channelmask & 0xff), "Ad9912 apply" )
            self.pulser.UpdateWireIns()
            self.pulser.ActivateTriggerIn(0x41,2)
        else:
            logger.error( "Pulser not available" )
        
    def reset(self, mask):
        logger = logging.getLogger(__name__)
        if self.pulser:
            if mask & 0x3: check( self.pulser.ActivateTriggerIn(0x42,0), "DDS Reset board 0" )
            if mask & 0xc: check( self.pulser.ActivateTriggerIn(0x42,1), "DDS Reset board 1" )
            if mask & 0x30: check( self.pulser.ActivateTriggerIn(0x42,2), "DDS Reset board 2" )
        else:
            logger.error( "Pulser not available" )

        
if __name__ == "__main__":
    import modules.magnitude as magnitude
    
    ad = Ad9912(None)
    ad.setFrequency( 0, magnitude.mg(250,'MHz'))
    