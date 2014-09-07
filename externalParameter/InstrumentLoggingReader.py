'''
Created on Jun 21, 2014

@author: pmaunz
'''
from PyQt4 import QtCore
import logging
import Queue
import time

def processReturn( returnvalue ):
    if isinstance( returnvalue, Exception ):
        raise returnvalue
    else:
        return returnvalue

class InstrumentLoggingReader(QtCore.QThread):  
    newData = QtCore.pyqtSignal( object, object )    
    def __init__(self, name, reader, commandQueue, responseQueue, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.exiting = False
        self.reader = reader
        self.commandQueue = commandQueue
        self.responseQueue = responseQueue
        self._readWait = 0
        self.name = name
   
    def run(self):
        while not self.exiting:
            try:
                try:
                    command, arguments  = self.commandQueue.get(block=False)
                    logging.getLogger(__name__).debug("{0} {1}".format(command,arguments))
                    self.responseQueue.put( getattr( self, command)( *arguments ) )
                except Queue.Empty:
                    pass
                data = self.reader.value()
                self.newData.emit( self.name, (time.time(), data) )
            except Exception:
                logging.getLogger(__name__).exception("Exception in QueueReader")
        self.newData.emit( self.name, None )
        logging.getLogger(__name__).info( "InstrumentLoggingReader thread finished." )
        self.reader.close()
        del self.reader
        
    def paramDef(self):
        return self.reader.paramDef()
        
    def directUpdate(self, field, data):
        setattr( self.reader, field, data )
       
    def stop(self):
        self.exiting = True
        