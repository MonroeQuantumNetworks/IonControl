'''
Created on Jun 21, 2014

@author: pmaunz
'''

from InstrumentLoggingReader import InstrumentLoggingReader
from Queue import Queue
from InstrumentReaderBase import InstrumentReaderBase


def wrapModbus(classname, serialclass):
    return type(classname, (ModbusInstrumentReader,), dict({"serialclass": serialclass}) )

class ModbusInstrumentReader( InstrumentReaderBase ):
    """test """
    def __init__(self, name, settings, instrument, newDataSlot=None ):
        InstrumentReaderBase.__init__(self, name, settings)
        barereader = self.serialclass(instrument)
        barereader.open()
        self.commandQueue = Queue()
        self.reader = InstrumentLoggingReader(name, barereader, self.commandQueue)
        self.reader.setTimeout(self.settings.timeout.toval("s"))
        self.reader.setReadWait(self.settings.readWait.toval("s"))
        self.reader.start()
        if newDataSlot is not None:
            self.reader.newData.connect( newDataSlot )
         
    def close(self):
        self.commandQueue.put(("stop", ()) )
         
    def update(self,param, changes):
        InstrumentReaderBase.update(self, param, changes)
        self.commandQueue.put( ("setReadWait", (self.settings.readWait.toval("s"),) ) )
        self.commandQueue.put( ("setTimeout", (self.settings.timeout.toval("s"),) ) )
        

