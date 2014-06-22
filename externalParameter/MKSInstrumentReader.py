'''
Created on Jun 21, 2014

@author: pmaunz
'''

from modules import magnitude
from InstrumentLoggingReader import InstrumentLoggingReader
from Queue import Queue
from MKSReader import MKSReader
from InstrumentReaderBase import InstrumentReaderBase
import logging


class MKSInstrumentReader( InstrumentReaderBase ):
    """test """
    className = "MKS Vacuum Gauge"
    def __init__(self, name, settings, instrument):
        InstrumentReaderBase(self, name, settings)
        port = int(instrument)
        reader = MKSReader(port=port)
        reader.open()
        self.commandQueue = Queue()
        self.reader = InstrumentLoggingReader(reader, self.commandQueue)
        self.newData = self.reader.newData
         
    def close(self):
        self.commandQueue.put(("exiting",True))
        self.reader.join()
        
    def update(self,param, changes):
        InstrumentReaderBase.update(self, param, changes)
        self.commandQueue.put( "readWait", self.settings.readWait )
        self.commandQueue.put( "readTimeout", self.settings.readTimeout )
        
 