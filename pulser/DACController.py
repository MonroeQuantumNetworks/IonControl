'''
Created on Dec 15, 2014

@author: pmaunz
'''
from OKBase import OKBase
import struct
import numpy

class DACControllerException(Exception):
    pass

class DACController( OKBase ):
    channelCount = 96
    def toInteger(self, iterable):
        result = list()
        for value in iterable:
            if not -10 <= value < 10:
                raise DACControllerException("voltage {0} out of range -10V <= V < 10V")
            result.append( int( value / 10.0 * 0x7fff ) ) 
        return result
    
    def writeVoltage(self, address, line ):
        if len(line)<self.channelCount:
            raise DACControllerException("Line contains only {0} voltages, need {1}".format(len(line), self.channelCount))
        startaddress = address * 2 * self.channelCount   # 2 bytes per channel, 96 channels
        self.xem.WriteToPipeIn( 0x84, bytearray( struct.pack('=HQ', 0x1, startaddress)))  # write start address to extended wire 2
        data = bytearray(numpy.array( self.toInteger(line), dtype=numpy.int16).view(dtype=numpy.int8))
        return self.xem.WriteToPipeIn( 0x83, data )        
    
    def shuttle(self, startLine, beyondEndLine, idleCount=0, direction=0 ):
        self.xem.WriteToPipeIn( 0x84, bytearray( struct.pack('=HQ', 0x1, (startLine * 2 * self.channelCount)<<32 + (beyondEndLine * 2 * self.channelCount))) ) # write start address to extended wire 2
        self.xem.SetWireInValue( 0x01, idleCount & 0xffff )
        self.xem.SetWireInValue( 0x02, direction & 0x1 )
        self.xem.UpdateWireIns()
        self.xem.ActivateTriggerIn( 0x40, 1 ) # set output address
    
    def triggerShuttling(self):
        self.xem.ActivateTriggerIn( 0x40, 0 ) # initiate shuttling