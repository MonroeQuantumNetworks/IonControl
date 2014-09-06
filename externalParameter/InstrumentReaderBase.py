'''
Created on Jun 21, 2014

@author: pmaunz
'''
from ExternalParameterBase import ExternalParameterBase
from Queue import Queue
from externalParameter.InstrumentLoggingReader import InstrumentLoggingReader, processReturn

class InstrumentReaderBase( ExternalParameterBase ):
    def __init__(self, name, settings, childobject, newDataSlot=None ):
        self.settings = settings
        self.commandQueue = Queue()
        self.responseQueue = Queue()
        self.reader = InstrumentLoggingReader(name, childobject, self.commandQueue, self.responseQueue )
        self.reader.start()
        ExternalParameterBase.__init__(self, name, settings)
        if newDataSlot is not None:
            self.reader.newData.connect( newDataSlot )
         
    def setDefaults(self):
        pass
            
    def update(self, param, changes):
        for param, _, data in changes:
            self.commandQueue.put( ("directUpdate", (param.opts['field'], data)) )
            setattr( self.settings, param.opts['field'], data )
            processReturn( self.responseQueue.get() )
                
    def paramDef(self):
        self.commandQueue.put( ("paramDef", tuple()) )
        param = processReturn( self.responseQueue.get() )
        return param

