'''
Created on Jul 27, 2014

@author: pmaunz
'''

from PulserHardwareServer import PulserHardwareServer, sliceview
import struct
import logging

class PMTReaderServer( PulserHardwareServer ):
    class DedicatedData:
        def __init__(self):
            self.data = [None]*33
            
        def count(self):
            return self.data[0:32]
            
        def analog(self):
            return []
            
        def integration(self):
            return self.data[32]

    def __init__(self, dataQueue=None, commandPipe=None, loggingQueue=None, sharedMemoryArray=None):
        super( PMTReaderServer, self ).__init__(dataQueue, commandPipe, loggingQueue, sharedMemoryArray )
        
    def readDataFifo(self):
        """ run is responsible for reading the data back from the FPGA
            0x6nxxxxxx count result from channel n (0-15)
            0x7nxxxxxx count result from channel n+16 (16-31)
        """
        data, self.dedicatedData.overrun = self.ppReadData(4)
        if data:
            for s in sliceview(data,4):
                (token,) = struct.unpack('I',s)
                if token & 0xc0000000 == 0xc0000000: # dedicated results
                    channel = (token >>24) & 0x3f
                    if self.dedicatedData.data[channel] is not None:
                        self.dataQueue.put( self.dedicatedData )
                        self.dedicatedData = self.DedicatedData()
                    self.dedicatedData.data[channel] = token & 0xffffff
            if self.data.overrun:
                logging.getLogger(__name__).info( "Overrun detected, triggered data queue" )
                self.dataQueue.put( self.dedicatedData )
                
 
