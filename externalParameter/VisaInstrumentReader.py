'''
Created on Sep 5, 2014

@author: wolverine
'''

from externalParameter.InstrumentReaderBase import InstrumentReaderBase
from InstrumentLoggingReader import InstrumentLoggingReader
from Queue import Queue

def wrapVisa(classname, visaclass):
    return type(classname, (VisaInstrumentReader,), dict({"visaclass": visaclass}) )

class VisaInstrumentReader( InstrumentReaderBase ):
    """test """
    def __init__(self, name, settings, instrument, newDataSlot=None ):
        InstrumentReaderBase.__init__(self, name, settings)
        barereader = self.visaclass(instrument)
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
        self.reader.wait()
         
    def update(self,param, changes):
        InstrumentReaderBase.update(self, param, changes)
        self.commandQueue.put( ("setReadWait", (self.settings.readWait.toval("s"),) ) )
        self.commandQueue.put( ("setTimeout", (self.settings.timeout.toval("s"),) ) )
        
