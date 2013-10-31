# -*- coding: utf-8 -*-
"""
Encapsulation of the Pulse Programmer Hardware 
"""
from fpgaUtilit import check
from PyQt4 import QtCore 
import struct
from Queue import Queue, Empty
import modules.magnitude as magnitude
from modules import enum
import math
import traceback
import time
import multiprocessing
from PulserHardwareServer import PulserHardwareServer

class QueueReader(QtCore.QThread):
       
    def __init__(self, pulserHardware, dataQueue, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.exiting = False
        self.pulserHardware = pulserHardware
        self.Mutex = pulserHardware.Mutex          # the mutex is to protect the ok library
        self.running = False
        self.dataMutex = QtCore.QMutex()           # protects the thread data
        self.dataQueue = dataQueue
        self.dataHandler = { 'Data': lambda data : self.pulserHardware.dataAvailable.emit(data),
                             'DedicatedData': lambda data: self.pulserHardware.dedicatedDataAvailable.emit(data),
                             'FinishException': lambda data: self.finish() }
   
    def finish(self):
        self.exiting = True
        
    def flushData(self):
        with QtCore.QMutexLocker(self.dataMutex):
            self.data = Data()
        print "flushData"
    
    def run(self):
        try:
            while not self.exiting:
                data = self.dataQueue.get()
                #print "QueueReader", data.__class__.__name__
                self.dataHandler[ data.__class__.__name__ ]( data )
        except Exception as e:
            print e
        print "PulserHardware client thread finished."
                

class PulserHardware(QtCore.QObject):
    sleepQueue = Queue()   # used to be able to interrupt the sleeping procedure

    dataAvailable = QtCore.pyqtSignal( 'PyQt_PyObject' )
    dedicatedDataAvailable = QtCore.pyqtSignal( 'PyQt_PyObject' )
    shutterChanged = QtCore.pyqtSignal( 'PyQt_PyObject' )
    
    timestep = magnitude.mg(20,'ns')

    def __init__(self):
        #print "PulserHardware __init__" 
        #traceback.print_stack()
        super(PulserHardware,self).__init__()
        self._shutter = 0
        self._trigger = 0
        self.xem = None
        self.Mutex = QtCore.QMutex
        self._adcCounterMask = 0
        self._integrationTime = magnitude.mg(100,'ms')
        
        self.dataQueue = multiprocessing.Queue()
        self.clientPipe, self.serverPipe = multiprocessing.Pipe()
        
        self.serverProcess = PulserHardwareServer(self.dataQueue, self.serverPipe )
        self.serverProcess.start()
        
        self.queueReader = QueueReader(self, self.dataQueue)
        self.queueReader.start()

    def shutdown(self):
        self.clientPipe.send( ('finish', () ) )
        self.serverProcess.join()
        self.queueReader.wait()
        
    def __getattr__(self,name):
        if name.startswith('__') and name.endswith('__'):
            return super(PulserHardware, self).__getattr__(key)
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
            
    def setShutterBit(self, bit, value):
        self.clientPipe.send( ('setShutterBit', (bit, value) ) )  
        self.shutterChanged.emit()
        return processReturn( self.clientPipe.recv() )
  
    def wordListToBytearray(self, wordlist):
        """ convert list of words to binary bytearray
        """
        self.binarycode = bytearray()
        for index, word in enumerate(wordlist):
#            if self.debug:
#                print hex(index), hex(word)
            self.binarycode += struct.pack('I', word)
        return self.binarycode        

    def bytearrayToWordList(self, barray):
        wordlist = list()
        for offset in range(0,len(barray),4):
            (w,) = struct.unpack_from('I',buffer(barray),offset)
            wordlist.append(w)
        return wordlist
            

def processReturn( returnvalue ):
    if isinstance( returnvalue, Exception ):
        raise returnvalue
    else:
        return returnvalue

if __name__ == "__main__":
    import fpgaUtilit
    import PulseProgram
    
    printdata = True
    
    pp = PulseProgram.PulseProgram()
    pp.loadSource(r'prog\Ions\ram_test.pp')
    #pp.loadSource(r'prog\Ions\ScanParameter.pp')
    fpga = fpgaUtilit.FPGAUtilit()
    xem = fpga.openBySerial('12320003V5')
    fpga.uploadBitfile(r'FPGA_ions\fpgafirmware.bit')
    hw = PulserHardware(fpga,startReader=False)
    data = bytearray( struct.pack('IIIIIIII',0x12345678,0xabcdef,0x1,0x10,0x100,0x1000,0x567,0x67) )
    length = len(data)
    hw.ppWriteRam( data, 8 )
    print length
    backdata = bytearray([0]*length )
    hw.ppReadRam( backdata, 8 )
    print "data readback comparison, matches", data[0:len(backdata)] == backdata
    hw.ppUpload( pp.toBinary() )
    xem.UpdateWireOuts()
    print "DataOutPipe", hex(xem.GetWireOutValue(0x25))
    hw.ppWriteData( bytearray('\x12\x34\x00\x00\x21\x22\x23\x24'))
    xem.UpdateWireOuts()
    print "DataOutPipe",hex(xem.GetWireOutValue(0x25))
    hw.ppStart()
    Finished = False
    while not Finished:#for j in range(60):
        data, overrun = hw.ppReadData(4,1.0)
        if printdata:
            for i in sliceview(data,4):
                (num,) = struct.unpack('I',i)
                Finished |= (num==0xffffffff)
                print "data", hex(num)
        else:
            for i in sliceview(data,4):
                (num,) = struct.unpack('I',i)
                Finished |= (num==0xffffffff)
            if len(data)>0:
                print "read {0} bytes".format(len(data))
            else:
                print ".",
            
    xem.UpdateWireOuts()
    print "DataOutPipe",hex(xem.GetWireOutValue(0x25))
    print "byteswaiting" , xem.GetWireOutValue(0x25) & 0xfff  # pipe_out_available
