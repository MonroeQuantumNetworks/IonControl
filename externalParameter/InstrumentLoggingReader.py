'''
Created on Jun 21, 2014

@author: pmaunz
'''
from PyQt4 import QtCore
import logging
from time import sleep
import Queue
import time

class InstrumentLoggingReader(QtCore.QThread):  
    newData = QtCore.pyqtSignal( object, object )    
    def __init__(self, name, reader, commandQueue, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.exiting = False
        self.reader = reader
        self.commandQueue = commandQueue
        self._readTimeout = 1
        self._readWait = 0
        self.name = name
   
    def run(self):
        while not self.exiting:
            try:
                try:
                    command, arguments = self.commandQueue.get(block=False)
                    logging.getLogger(__name__).debug("{0} {1}".format(command,arguments))
                    getattr( self, command)( *arguments )
                except Queue.Empty:
                    pass
                data = self.reader.value()
                self.newData.emit( self.name, (time.time(), data) )
                sleep( self._readWait )
            except Exception:
                logging.getLogger(__name__).exception("Exception in QueueReader")
        self.newData.emit( self.name, None )
        logging.getLogger(__name__).info( "InstrumentLoggingReader thread finished." )
        self.reader.close()
        del self.reader
        
    def timeout(self):
        return self._readTimeout
    
    def setTimeout(self, timeout):
        self._readTimeout = timeout
        self.reader.readTimeout = timeout
        
    def readWait(self):
        return self._readWait
    
    def setReadWait(self, time):
        self._readWait = time
        
    def stop(self):
        self.exiting = True
        