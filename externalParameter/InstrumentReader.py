'''
Created on Jun 21, 2014

@author: pmaunz
'''

from InstrumentLoggingReader import processReturn
from InstrumentReaderBase import InstrumentReaderBase


def wrapInstrument(classname, serialclass):
    return type(classname, (InstrumentReader,), dict({"serialclass": serialclass}) )

class InstrumentReader( InstrumentReaderBase ):
    def __init__(self, name, settings, instrument, newDataSlot=None ):
        port = int(instrument)
        child = self.serialclass(port=port, settings=settings)
        child.open()
        super( InstrumentReader, self ).__init__(name, settings, child, newDataSlot)
         
    def close(self):
        self.commandQueue.put(("stop", ()) )
        processReturn( self.responseQueue.get() )
        self.reader.wait()
         
