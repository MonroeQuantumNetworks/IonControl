'''
Created on Jun 21, 2014

@author: pmaunz
'''

from modules import magnitude
from InstrumentLoggingReader import InstrumentLoggingReader
from Queue import Queue
from InstrumentReaderBase import InstrumentReaderBase
import logging


def wrapSerial(classname, serialclass):
    return type(classname, (SerialInstrumentReader,), dict({"serialclass": serialclass}) )

class SerialInstrumentReader( InstrumentReaderBase ):
    """test """
    def __init__(self, name, settings, instrument, newDataSlot=None ):
        InstrumentReaderBase.__init__(self, name, settings)
        port = int(instrument)
        reader = self.serialclass(port=port)
        reader.open()
        self.commandQueue = Queue()
        self.reader = InstrumentLoggingReader(reader, self.commandQueue)
        if newDataSlot is not None:
            self.reader.newData.connect( newDataSlot )
         
    def close(self):
        self.commandQueue.put(("exiting",True))
        self.reader.join()
        
    def update(self,param, changes):
        InstrumentReaderBase.update(self, param, changes)
        self.commandQueue.put( "readWait", self.settings.readWait.toval("s") )
        self.commandQueue.put( "readTimeout", self.settings.readTimeout.toval("s") )
        
