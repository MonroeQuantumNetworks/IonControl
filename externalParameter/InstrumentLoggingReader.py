'''
Created on Jun 21, 2014

@author: pmaunz
'''
from PyQt4 import QtCore
import logging
from time import sleep
import Queue

class InstrumentLoggingReader(QtCore.QThread):  
    newData = QtCore.pyqtSignal( object )    
    def __init__(self, reader, commandQueue, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.exiting = False
        self.reader = reader
        self.commandQueue = commandQueue
        self._readTimeout = 1
        self._readWait = 1
   
    def run(self):
        while not self.exiting:
            try:
                try:
                    command = self.commandQueue.get(block=False)
                    setattr( self, command[0], command[1] )
                except Queue.Empty:
                    pass
                data = self.reader.value()
                self.newdata.emit( data )
                sleep( self.readWait )
            except Exception:
                logging.getLogger(__name__).exception("Exception in QueueReader")
        logging.getLogger(__name__).info( "InstrumentLoggingReader thread finished." )
        self.reader.close()
        del self.reader
        
    @property
    def readTimeout(self):
        return self._readTimeout
    
    @readTimeout.setter
    def readTimeout(self, timeout):
        self._readTimeout = timeout
        self.reader.readTimeout = timeout
        
    @property
    def readWait(self):
        return self._readWait
    
    @readWait.setter
    def readWait(self, time):
        self._readWait = time
        