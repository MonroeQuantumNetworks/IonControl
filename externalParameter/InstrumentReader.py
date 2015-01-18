'''
Created on Jun 21, 2014

@author: pmaunz
'''

from InstrumentLoggingReader import processReturn
from InstrumentReaderBase import InstrumentReaderBase
from modules.Observable import Observable


def wrapInstrument(classname, serialclass):
    return type(classname, (InstrumentReader,), dict({"serialclass": serialclass}) )

class InstrumentReader( InstrumentReaderBase ):
    def __init__(self, name, settings, instrument ):
        child = self.serialclass(instrument=instrument, settings=settings)
        child.open()
        super( InstrumentReader, self ).__init__(name, settings, child, self.newDataSlot)
        self._inputChannels = { None: None }
        self.inputObservable[None] = Observable()
         
    def newDataSlot(self, name, data):
        self.inputObservable[None].fire( name=name, data=data )
         
    def close(self):
        self.commandQueue.put(("stop", ()) )
        processReturn( self.responseQueue.get() )
        self.reader.wait()
        
    @classmethod
    def connectedInstruments(cls):
        if hasattr( cls.serialclass, 'connectedInstruments' ):
            return cls.serialclass.connectedInstruments()
        return []
         
