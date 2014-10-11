# -*- coding: utf-8 -*-
"""
Encapsulation of the Pulse Programmer Hardware 
"""
from Queue import Queue
import logging
import multiprocessing
from multiprocessing.sharedctypes import Array
import numpy

from PyQt4 import QtCore 

from PulserHardwareServer import FinishException
from pulser.OKBase import ErrorMessages, FPGAException
from PulserHardwareServer import PulserHardwareServer
import modules.magnitude as magnitude


def check(number, command):
    if number is not None and number<0:
        raise FPGAException("OpalKelly exception '{0}' in command {1}".format(ErrorMessages.get(number,number),command))


class QueueReader(QtCore.QThread):      
    def __init__(self, pulserHardware, dataQueue, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.exiting = False
        self.pulserHardware = pulserHardware
        self.running = False
        self.dataMutex = QtCore.QMutex()           # protects the thread data
        self.dataQueue = dataQueue
        self.dataHandler = { 'Data': lambda data, size : self.pulserHardware.dataAvailable.emit(data, size),
                             'DedicatedData': lambda data, size: self.pulserHardware.dedicatedDataAvailable.emit(data),
                             'FinishException': lambda data, size: self.raise_(FinishException()),
                             'LogicAnalyzerData': lambda data, size: self.onLogicAnalyzerData(data) }
   
    def onLogicAnalyzerData(self, data): 
        self.pulserHardware.logicAnalyzerDataAvailable.emit(data)
        
    def raise_(self, ex):
        raise ex
   
    def run(self):
        logger = logging.getLogger(__name__)
        logger.info( "QueueReader thread started." )
        while True:
            try:
                data = self.dataQueue.get()
                self.dataHandler[ data.__class__.__name__ ]( data, self.dataQueue.qsize() )
            except (KeyboardInterrupt, SystemExit, FinishException):
                break
            except Exception:
                logger.exception("Exception in QueueReader")
        logger.info( "QueueReader thread finished." )

class LoggingReader(QtCore.QThread):
    def __init__(self, loggingQueue, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.running = False
        self.loggingQueue = loggingQueue
        
    def run(self):
        logger = logging.getLogger(__name__)
        logger.debug("LoggingReader Thread running")
        while True:
            try:
                record = self.loggingQueue.get()
                if record is None: # We send this as a sentinel to tell the listener to quit.
                    logger.debug("LoggingReader Thread shutdown requested")
                    break
                clientlogger = logging.getLogger(record.name)
                if record.levelno>=clientlogger.getEffectiveLevel():
                    clientlogger.handle(record) # No level or filter logic applied - just do it!
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                logger.exception("Exception in Logging Reader Thread")
        logger.info("LoggingReader Thread finished")

                

class PulserHardware(QtCore.QObject):
    serverClass = PulserHardwareServer
    sleepQueue = Queue()   # used to be able to interrupt the sleeping procedure

    dataAvailable = QtCore.pyqtSignal( 'PyQt_PyObject', object )
    dedicatedDataAvailable = QtCore.pyqtSignal( 'PyQt_PyObject' )
    logicAnalyzerDataAvailable = QtCore.pyqtSignal( 'PyQt_PyObject' )
    shutterChanged = QtCore.pyqtSignal( 'PyQt_PyObject' )
    ppActiveChanged = QtCore.pyqtSignal( object )
    
    timestep = magnitude.mg(20,'ns')

    sharedMemorySize = 256*1024
    def __init__(self):
        super(PulserHardware,self).__init__()
        self._shutter = 0
        self._trigger = 0
        self.xem = None
        self.Mutex = QtCore.QMutex
        self._adcCounterMask = 0
        self._integrationTime = magnitude.mg(100,'ms')
        
        self.dataQueue = multiprocessing.Queue()
        self.clientPipe, self.serverPipe = multiprocessing.Pipe()
        self.loggingQueue = multiprocessing.Queue()
        self.sharedMemoryArray = Array( 'L', self.sharedMemorySize , lock=True )
                
        self.serverProcess = self.serverClass(self.dataQueue, self.serverPipe, self.loggingQueue, self.sharedMemoryArray )
        self.serverProcess.start()

        self.queueReader = QueueReader(self, self.dataQueue)
        self.queueReader.start()
        
        self.loggingReader = LoggingReader(self.loggingQueue)
        self.loggingReader.start()
        self.ppActive = False


    def shutdown(self):
        self.clientPipe.send( ('finish', () ) )
        self.serverProcess.join()
        self.queueReader.wait()
        self.loggingReader.wait()
        logging.getLogger(__name__).debug("PulseHardwareClient Shutdown completed")
        
    def __getattr__(self,name):
        if name.startswith('__') and name.endswith('__'):
            return super(PulserHardware, self).__getattr__(name)
        def wrapper(*args):
            self.clientPipe.send( (name, args) )
            return processReturn( self.clientPipe.recv() )
        setattr(self, name, wrapper)
        return wrapper      
        
    @property
    def shutter(self):
        self.clientPipe.send( ('getShutter', () ) )
        return processReturn( self.clientPipe.recv() )
         
    @shutter.setter
    def shutter(self, value):
        self.clientPipe.send( ('setShutter', (value,) ) )      
        _shutter = processReturn( self.clientPipe.recv() )
        self.shutterChanged.emit( _shutter )          
        
    @property
    def trigger(self):
        self.clientPipe.send( ('getTrigger', () ) )
        return processReturn( self.clientPipe.recv() )
            
    @trigger.setter
    def trigger(self,value):
        self.clientPipe.send( ('setTrigger', (value,) ) )        
        return processReturn( self.clientPipe.recv() )
            
    @property
    def counterMask(self):
        self.clientPipe.send( ('getCounterMask', () ) )
        return processReturn( self.clientPipe.recv() )
        
    @counterMask.setter
    def counterMask(self, value):
        self.clientPipe.send( ('setCounterMask', (value,) ) )        
        return processReturn( self.clientPipe.recv() )

    @property
    def adcMask(self):
        self.clientPipe.send( ('getAdcMask', () ) )
        return processReturn( self.clientPipe.recv() )
        
    @adcMask.setter
    def adcMask(self, value):
        self.clientPipe.send( ('setAdcMask', (value,) ) )        
        return processReturn( self.clientPipe.recv() )
        
    @property
    def integrationTime(self):
        self.clientPipe.send( ('getIntegrationTime', () ) )
        return processReturn( self.clientPipe.recv() )
        
    @integrationTime.setter
    def integrationTime(self, value):
        self.clientPipe.send( ('setIntegrationTime', (value,) ) )        
        return processReturn( self.clientPipe.recv() )
            
    def ppStart(self):
        self.clientPipe.send( ('ppStart', () ) )
        value = processReturn( self.clientPipe.recv() )
        self.ppActive = True
        self.ppActiveChanged.emit(True)
        return value
            
    def ppStop(self):
        self.clientPipe.send( ('ppStop', () ) )
        value = processReturn( self.clientPipe.recv() )
        self.ppActive = False
        self.ppActiveChanged.emit(False)
        return value
            
    def setShutterBit(self, bit, value):
        self.clientPipe.send( ('setShutterBit', (bit, value) ) )  
        _shutter = processReturn( self.clientPipe.recv() )
        self.shutterChanged.emit( _shutter )
        return _shutter 
  
    def wordListToBytearray(self, wordlist):
        """ convert list of words to binary bytearray
        """
        return bytearray(numpy.array(wordlist, dtype=numpy.int64).view(dtype=numpy.int8))

    def bytearrayToWordList(self, barray):
        return list(numpy.array( barray, dtype=numpy.int8).view(dtype=numpy.int64 ))
            
    
    def ppWriteRamWordList(self, wordlist, address, check=True):
        for start in range(0, len(wordlist), self.sharedMemorySize ):
            length = min( self.sharedMemorySize, len(wordlist)-start )
            self.sharedMemoryArray[0:length] = wordlist[start:start+length]
            self.clientPipe.send( ('ppWriteRamWordListShared', (length, address+4*start, check) ) )
            processReturn( self.clientPipe.recv() )
        return True
            
    def ppReadRamWordList(self, wordlist, address):
        readlist = list()
        for start in range(0, len(wordlist), self.sharedMemorySize ):
            length = min( self.sharedMemorySize, len(wordlist)-start )
            self.clientPipe.send( ('ppReadRamWordListShared', (length, address+4*start) ) )
            processReturn( self.clientPipe.recv() )
            readlist.extend( self.sharedMemoryArray[0:length] )
        return readlist

def processReturn( returnvalue ):
    if isinstance( returnvalue, Exception ):
        raise returnvalue
    else:
        return returnvalue

