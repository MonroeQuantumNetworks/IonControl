'''
Created on Dec 15, 2014

@author: pmaunz
'''
from pulser.OKBase import OKBase, check
# import logging
import struct
import numpy
from itertools import chain
import logging

class DACControllerException(Exception):
    pass


class DACController( OKBase ):
    channelCount = 112
    def toInteger(self, iterable):
        result = list()
        for value in chain(iterable[0::4], iterable[1::4], iterable[2::4], iterable[3::4]):
            if not -10 <= value < 10:
                raise DACControllerException("voltage {0} out of range -10V <= V < 10V".format(value))
            result.append( int( value / 10.0 * 0x7fff ) ) 
        return result # list(chain(range(96)[0::4], range(96)[1::4], range(96)[2::4], range(96)[3::4])) # list( [0x000 for _ in range(96)]) #result #
    
    def writeVoltage(self, address, line ):
        if len(line)<self.channelCount:
            line.extend( [0.0]*(self.channelCount-len(line) ))   # extend the line to the channel count
        startaddress = address * 2 * self.channelCount   # 2 bytes per channel, 96 channels
        # set the host write address
        self.xem.WriteToPipeIn( 0x84, bytearray( struct.pack('=HQ', 0x3, startaddress)))  # write start address to extended wire 2
        check( self.xem.ActivateTriggerIn( 0x43, 6), 'HostSetWriteAddress' )
        
        data = bytearray(numpy.array( self.toInteger(line), dtype=numpy.int16).view(dtype=numpy.int8))
        print len(data), self.toInteger(line)
        #check( self.xem.ActivateTriggerIn( 0x40, 2), 'ActivateTrigger' )
        return self.xem.WriteToPipeIn( 0x83, data )
    
    def readVoltage(self, address, line=None):
        startaddress = address * 2 * self.channelCount   # 2 bytes per channel, 96 channels
        # set the host write address
        self.xem.WriteToPipeIn( 0x84, bytearray( struct.pack('=HQ', 0x3, startaddress)))  # write start address to extended wire 2
        check( self.xem.ActivateTriggerIn( 0x43, 7), 'HostSetReadAddress' )
        
        data = bytearray(2*self.channelCount)
        self.xem.ReadFromPipeOut( 0xa3, data )
        result = numpy.array( data, dtype=numpy.int8 ).view(dtype=numpy.int16)
        if line is not None:
            matches = all(result == self.toInteger(line))
            if not matches:
                logging.getLogger(__name__).error( "{0} {1}".format(len(self.toInteger(line)),list(self.toInteger(line))))
                logging.getLogger(__name__).error( "{0} {1}".format(len(result),list(result)))            
                #raise DACControllerException("Data read from memory does not match data written")
                logging.getLogger(__name__).info("Data written and read does NOT match")
            else:
                logging.getLogger(__name__).info("Data written and read matches")
        return result
        
    def writeShuttleLookup(self, shuttleEdges, startAddress=0 ):
        data = bytearray()
        for shuttleEdge in shuttleEdges:
            data.extend( shuttleEdge.code( self.channelCount ) )
        self.xem.SetWireInValue(0x3, startAddress<<3 )
        self.xem.UpdateWireIns()
        self.xem.ActivateTriggerIn( 0x40, 2)
        self.xem.WriteToPipeIn( 0x85, data )       
    
    def shuttle(self, startLine, beyondEndLine, idleCount=0, direction=0, soft_trigger=0 ):
        startCode = ( startLine*2*self.channelCount & 0x7fffffff ) | ((direction & 0x1) << 31 )
        self.xem.WriteToPipeIn( 0x86, struct.pack('=IIII', (0x01000001) | ((soft_trigger &0x1)<<1) , idleCount, startCode, beyondEndLine*2*self.channelCount))
    
    def triggerShuttling(self):
        check( self.xem.ActivateTriggerIn( 0x40, 0), 'ActivateTrigger' )

