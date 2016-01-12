'''
Created on Jun 21, 2014

@author: pmaunz
'''
from ExternalParameterBase import ExternalParameterBase
from Queue import Queue
from externalParameter.InstrumentLoggingReader import InstrumentLoggingReader, processReturn
from externalParameter.ExternalParameterBase import InstrumentMeta

class ReaderMeta(InstrumentMeta):
    def __new__(self, name, bases, dct):
        instrclass = type.__new__(self, name, bases, dct)
#         if name!='InstrumentReaderBase':
#             if 'className' not in dct:
#                 raise InstrumentException("Instrument class needs to have class attribute 'className'")
#             InstrumentDict[dct['className']] = instrclass
        return instrclass

class InstrumentReaderBase( ExternalParameterBase ):
    __metaclass__ = ReaderMeta
    def __init__(self, name, settings, globalDict, childobject, newDataSlot=None ):
        self.settings = settings
        self.commandQueue = Queue()
        self.responseQueue = Queue()
        self.reader = InstrumentLoggingReader(name, childobject, self.commandQueue, self.responseQueue )
        self.reader.start()
        ExternalParameterBase.__init__(self, name, settings, globalDict)
        self.newData = self.reader.newData
         
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

