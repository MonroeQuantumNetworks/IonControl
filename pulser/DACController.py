'''
Created on Dec 15, 2014

@author: pmaunz
'''
from OKBase import OKBase, check
import struct
import numpy
from itertools import chain

class DACControllerException(Exception):
    pass

class DACController( OKBase ):
    channelCount = 100
    def toInteger(self, iterable):
        result = list()
        for value in chain(iterable[0::4], iterable[1::4], iterable[2::4], iterable[3::4]):
            if not -10 <= value < 10:
                raise DACControllerException("voltage {0} out of range -10V <= V < 10V".format(value))
            result.append( int( value / 10.0 * 0x7fff ) ) 
        return result # list(chain(range(96)[0::4], range(96)[1::4], range(96)[2::4], range(96)[3::4])) # list( [0x000 for _ in range(96)]) #result #
    
    def writeVoltage(self, address, line ):
        if len(line)<self.channelCount:
            raise DACControllerException("Line contains only {0} voltages, need {1}".format(len(line), self.channelCount))
        startaddress = address * 2 * self.channelCount   # 2 bytes per channel, 96 channels
        self.xem.WriteToPipeIn( 0x84, bytearray( struct.pack('=HQ', 0x3, startaddress)))  # write start address to extended wire 2
        
        data = bytearray(numpy.array( self.toInteger(line), dtype=numpy.int16).view(dtype=numpy.int8))
        print self.toInteger(line)
        check( self.xem.ActivateTriggerIn( 0x40, 2), 'ActivateTrigger' )
        return self.xem.WriteToPipeIn( 0x83, data )        
    
    def shuttle(self, startLine, beyondEndLine, idleCount=0, direction=0 ):
        self.xem.WriteToPipeIn( 0x84, bytearray( struct.pack('=HQHQ', 0x1, startLine*2*self.channelCount, 0x2, beyondEndLine*2*self.channelCount) )) # write start address to extended wire 2
        check( self.xem.ActivateTriggerIn( 0x43, 6), 'ActivateTrigger' )
        self.xem.SetWireInValue( 0x01, idleCount & 0xffff )
        self.xem.SetWireInValue( 0x02, direction & 0x1 )
        self.xem.UpdateWireIns()
        self.xem.ActivateTriggerIn( 0x40, 1 ) # set output address
    
    def triggerShuttling(self):
        check( self.xem.ActivateTriggerIn( 0x40, 0), 'ActivateTrigger' )
