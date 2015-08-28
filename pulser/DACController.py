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
    @classmethod
    def shuttleLookupCode(cls, edge, channelCount):
        return struct.pack('=IIII', (edge.interpolStopLine)*2*channelCount, (edge.interpolStartLine)*2*cls.channelCount,
                             edge.idleCount, 0x0)

    
    def toInteger(self, iterable):
        result = list()
        for value in chain(iterable[0::4], iterable[1::4], iterable[2::4], iterable[3::4]):
            if not -10 <= value < 10:
                raise DACControllerException("voltage {0} out of range -10V <= V < 10V".format(value))
            result.append( int( value / 10.0 * 0x7fff ) ) 
        return result # list(chain(range(96)[0::4], range(96)[1::4], range(96)[2::4], range(96)[3::4])) # list( [0x000 for _ in range(96)]) #result #
    
    def writeVoltage(self, address, line ):
        if len(line)<self.channelCount:
            line = numpy.append( line, [0.0]*(self.channelCount-len(line) ))   # extend the line to the channel count
        startaddress = address * 2 * self.channelCount   # 2 bytes per channel, 96 channels
        # set the host write address
        self.xem.WriteToPipeIn( 0x84, bytearray( struct.pack('=HQ', 0x4, startaddress)))  # write start address to extended wire 2
        check( self.xem.ActivateTriggerIn( 0x43, 6), 'HostSetWriteAddress' )
        
        data = bytearray(numpy.array( self.toInteger(line), dtype=numpy.int16).view(dtype=numpy.int8))
        print len(data), self.toInteger(line)
        #check( self.xem.ActivateTriggerIn( 0x40, 2), 'ActivateTrigger' )
        return self.xem.WriteToPipeIn( 0x83, data )
    
    def writeVoltages(self, address, lineList ):
        if self.xem:
            startaddress = address * 2 * self.channelCount   # 2 bytes per channel, 96 channels
            # set the host write address
            self.xem.WriteToPipeIn( 0x84, bytearray( struct.pack('=HQ', 0x4, startaddress)))  # write start address to extended wire 2
            check( self.xem.ActivateTriggerIn( 0x43, 6), 'HostSetWriteAddress' )
            
            odata = numpy.array( lineList ).reshape( (len(lineList),28,4) ).swapaxes(1,2).flatten()
            maximum = numpy.amax(odata)
            minimum = numpy.amin(odata)
            if maximum>=10.0:
                raise DACControllerException("voltage {0} out of range V >= 10V".format(maximum))
            if minimum<-10:
                raise DACControllerException("voltage {0} out of range V < -10V".format(maximum))
            odata *= 0x7fff/10.0          
            outdata = bytearray(odata.astype(numpy.int16).view(dtype=numpy.int8))
            logging.getLogger(__name__).info("uploading {0} bytes to DAC controller, {1} voltage samples".format(len(outdata),len(outdata)/self.channelCount/2))
            self.xem.WriteToPipeIn( 0x83, outdata )
            return outdata
        return bytearray()

    def verifyVoltages(self, address, data ):
        if self.xem:
            startaddress = address * 2 * self.channelCount   # 2 bytes per channel, 96 channels
            # set the host write address
            self.xem.WriteToPipeIn( 0x84, bytearray( struct.pack('=HQ', 0x3, startaddress)))  # write start address to extended wire 2
            check( self.xem.ActivateTriggerIn( 0x43, 7), 'HostSetWriteAddress' )
            
            returndata = bytearray(len(data))
            self.xem.ReadFromPipeOut( 0xa3, returndata )
            matches = data == returndata
            if not matches:
                logging.getLogger(__name__).error("Data verification failure")
            else:
                logging.getLogger(__name__).info("Data verified")
            return returndata
        return bytearray()

    
    def readVoltage(self, address, line=None):
        if self.xem:
            if len(line)<self.channelCount:
                line = numpy.append( line, [0.0]*(self.channelCount-len(line) ))   # extend the line to the channel count
            startaddress = address * 2 * self.channelCount   # 2 bytes per channel, 96 channels
            # set the host write address
            self.xem.WriteToPipeIn( 0x84, bytearray( struct.pack('=HQ', 0x3, startaddress)))  # write start address to extended wire 2
            check( self.xem.ActivateTriggerIn( 0x43, 7), 'HostSetReadAddress' )
            
            data = bytearray(2*self.channelCount)
            self.xem.ReadFromPipeOut( 0xa3, data )
            result = numpy.array( data, dtype=numpy.int8 ).view(dtype=numpy.int16)
            if line is not None:
                matches = all(result == numpy.array(self.toInteger(line)))
                if not matches:
                    logging.getLogger(__name__).warning( "{0} {1}".format(len(self.toInteger(line)),list(self.toInteger(line))))
                    logging.getLogger(__name__).warning( "{0} {1}".format(len(result),list(result)))            
                    #raise DACControllerException("Data read from memory does not match data written")
                    logging.getLogger(__name__).info("Data written and read does NOT match")
                else:
                    logging.getLogger(__name__).info("Data written and read matches")
            return result
        return bytearray()

    def writeShuttleLookup(self, shuttleEdges, startAddress=0 ):
        if self.xem:
            data = bytearray()
            for shuttleEdge in shuttleEdges:
                data.extend( self.shuttleLookupCode(shuttleEdge, self.channelCount ) )
            self.xem.SetWireInValue(0x3, startAddress<<3 )
            self.xem.UpdateWireIns()
            self.xem.ActivateTriggerIn( 0x40, 2)
            written = self.xem.WriteToPipeIn( 0x85, data )
            logging.getLogger(__name__).info("Wrote ShuttleLookup table {0} bytes, {1} entries".format(written,written/16))   
            self.xem.SetWireInValue(0x3, startAddress<<3 )
            self.xem.UpdateWireIns()
            self.xem.ActivateTriggerIn( 0x40, 2)
            mybuffer = bytearray( len(data) )
            self.xem.ReadFromPipeOut( 0xa4, mybuffer )
            if data==mybuffer:
                logging.getLogger(__name__).info("Written and read lookup data matches")
            else:
                logging.getLogger(__name__).error("Written and read lookup data do NOT match")
               
    
    def shuttleDirect(self, startLine, beyondEndLine, idleCount=0, immediateTrigger=False ):
        if self.xem:
            self.xem.WriteToPipeIn( 0x86, bytearray( struct.pack('=IIII', (0x01000000 | self.boolToCode(immediateTrigger)), 
                                                      idleCount, startLine*2*self.channelCount, beyondEndLine*2*self.channelCount)))
        
    @staticmethod
    def boolToCode( b, bit=0 ):
        return 1<<bit if b else 0
        
    def shuttle(self, lookupIndex, reverseEdge=False, immediateTrigger=False):
        if self.xem:
            self.xem.WriteToPipeIn( 0x86, bytearray(struct.pack('=IIII', 0x03000000,  0x0, 
                                                  self.boolToCode(reverseEdge, 1)|self.boolToCode(immediateTrigger), lookupIndex)))
        
    def shuttlePath(self, path):
        if self.xem:
            data = bytearray()
            for lookupIndex, reverseEdge, immediateTrigger in path:
                data.extend( struct.pack('=IIII', 0x03000000,  0x0, self.boolToCode(reverseEdge, 1)|self.boolToCode(immediateTrigger), lookupIndex))
            self.xem.WriteToPipeIn( 0x86, data)        
    
    def triggerShuttling(self):
        if self.xem:
            check( self.xem.ActivateTriggerIn( 0x40, 0), 'ActivateTrigger' )
