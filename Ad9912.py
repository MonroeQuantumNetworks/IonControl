# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 14:53:26 2013

@author: plmaunz
"""

import math
from fpgaUtilit import check

class Ad9912Exception(Exception):
    pass

class Ad9912:
    channels = 6
    def __init__(self,xem):
        self.xem = xem
        self.frequency = [None]*self.channels
        self.phase = [None]*self.channels
        self.amplitude = [None]*self.channels

    def setFrequency(self, channel, frequency):
        intFrequency = int(round(2**48 * frequency.ounit('GHz').toval()))
        self.sendCommand(channel, 0, intFrequency >> 16 )
        self.sendCommand(channel, 4, intFrequency & 0xffff )
    
    def setPhase(self, channel, phase):
        intPhase = int(round(2**14 * phase.ounit('rad').toval()/(2*math.pi)))
        self.sendCommand(channel, 1, intPhase & 0x3fff )
    
    def setAmplitude(self, channel, amplitude):
        intAmplitude = int(round(amplitude))
        self.sendCommand(channel, 2, intAmplitude & 0x3ff )
        
    def sendCommand(self, channel, cmd, data):
        #print "Ad9912.sendCommand", hex(channel), hex(cmd), hex(data)
        if self.xem:
            check( self.xem.SetWireInValue(0x03, (channel & 0xf)<<4 | (cmd & 0xf) ), "Ad9912" )
            check( self.xem.SetWireInValue(0x01, data & 0xffff ), "Ad9912" )
            check( self.xem.SetWireInValue(0x02, (data >> 16) &0xffff ), "Ad9912" )
            self.xem.UpdateWireIns()
            check( self.xem.ActivateTriggerIn(0x40,1), "Ad9912 trigger")
            self.xem.UpdateWireIns()
        else:
            print "Pulser not available"
        
    def update(self, channelmask):
        #print "Apply DDS settings"
        if self.xem:
            check( self.xem.SetWireInValue(0x08, channelmask & 0x3f), "Ad9912 apply" )
            self.xem.UpdateWireIns()
            self.xem.ActivateTriggerIn(0x41,2)
        else:
            print "Pulser not available"
        
    def reset(self, mask):
        #print "Resetting DDS"
        if self.xem:
            if mask & 0x3: check( self.xem.ActivateTriggerIn(0x42,0), "DDS Reset board 0" )
            if mask & 0xc: check( self.xem.ActivateTriggerIn(0x42,1), "DDS Reset board 1" )
            if mask & 0x30: check( self.xem.ActivateTriggerIn(0x42,2), "DDS Reset board 2" )
        else:
            print "Pulser not available"

    def updateSettings(self,fpgaUtilit):
        self.xem = fpgaUtilit.xem
        #self.Mutex = fpgaUtilit.Mutex        
        
if __name__ == "__main__":
    import modules.magnitude as magnitude
    
    ad = Ad9912(None)
    ad.setFrequency( 0, magnitude.mg(250,'MHz'))
    