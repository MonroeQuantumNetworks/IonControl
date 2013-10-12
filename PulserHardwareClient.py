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
        self.dataHandler = { 'Data': pulserHardware.dataAvailable,
                             'DedicatedData': pulserHardware.dedicatedDataAvailable }
   
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
                self.dataHandler[ data.__class__.__name__ ].emit( data )
        except Exception as e:
            print e
                

class PulserHardware(QtCore.QObject):
    sleepQueue = Queue()   # used to be able to interrupt the sleeping procedure

    dataAvailable = QtCore.pyqtSignal( 'PyQt_PyObject' )
    dedicatedDataAvailable = QtCore.pyqtSignal( 'PyQt_PyObject' )
    shutterChanged = QtCore.pyqtSignal( 'PyQt_PyObject' )
    
    timestep = magnitude.mg(20,'ns')

    def __init__(self,fpgaUtilit,startReader=True):
        #print "PulserHardware __init__" 
        #traceback.print_stack()
        super(PulserHardware,self).__init__()
        self._shutter = 0
        self._trigger = 0
        self.fpga = fpgaUtilit
        self.xem = self.fpga.xem if self.fpga is not None else None
        self.Mutex = self.fpga.Mutex if self.fpga is not None else None
        self._adcCounterMask = 0
        self._integrationTime = magnitude.mg(100,'ms')
        
        self.dataQueue = multiprocessing.Queue()
        self.clientPipe, self.serverPipe = multiprocessing.Pipe()
        
        self.serverProcess = PulserHardwareServer(self.dataQueue, self.serverPipe )
        self.serverProcess.start()
        
        self.pipeReader = PipeReader(self)
        if startReader and self.xem:
            self.pipeReader.start()

    def updateSettings(self,fpgaUtilit):
        self.stopPipeReader()
        self.fpga = fpgaUtilit
        self.xem = self.fpga.xem
        self.Mutex = self.fpga.Mutex
        self.pipeReader = PipeReader(self)
        self.pipeReader.start()        

    def stopPipeReader(self):
        self.pipeReader.finish()
        self.interruptRead()
        self.pipeReader.wait()
        
    def setHardware(self,xem):
        self.xem = xem
        if self.xem and not self.pipeReader.isRunning():
            self.pipeReader.start()            
        
    @property
    def shutter(self):
        self.clientPipe.send( ('getShutter', () ) )
        return self.clientPipe.recv()
         
    @shutter.setter
    def shutter(self, value):
        self.clientPipe.send( ('setShutter', (value,) ) )        
        
    def setShutterBit(self, bit, value):
        self.clientPipe.send( ('setShutterBit', (bit, value) ) )        
        
    @property
    def trigger(self):
        self.clientPipe.send( ('getTrigger', () ) )
        return self.clientPipe.recv()
            
    @trigger.setter
    def trigger(self,value):
        self.clientPipe.send( ('setTrigger', (value,) ) )        
            
    @property
    def counterMask(self):
        self.clientPipe.send( ('getCounterMask', () ) )
        return self.clientPipe.recv()
        
    @counterMask.setter
    def counterMask(self, value):
        self.clientPipe.send( ('setCounterMask', (value,) ) )        

    @property
    def adcMask(self):
        self.clientPipe.send( ('getAdcMask', () ) )
        return self.clientPipe.recv()
        
    @adcMask.setter
    def adcMask(self, value):
        self.clientPipe.send( ('setAdcMask', (value,) ) )        
        
    @property
    def integrationTime(self):
        self.clientPipe.send( ('getIntegrationTime', () ) )
        return self.clientPipe.recv()
        
    @integrationTime.setter
    def integrationTime(self, value):
        self.clientPipe.send( ('setIntegrationTime', (value,) ) )        
            
    def getIntegrationTimeBinary(self, value):
        self.clientPipe.send( ('getIntegrationTimeBinary', (value, ) ) )
        return self.clientPipe.recv()
        
    def ppUpload(self,binarycode,startaddress=0):
        self.clientPipe.send( ('ppUpload', (binarycode,startaddress) ) )
        return self.clientPipe.recv()
            
    def ppDownload(self,startaddress,length):
        self.clientPipe.send( ('ppDownload', (startaddress,length) ) )
        return self.clientPipe.recv()
        
    def ppIsRunning(self):
        self.clientPipe.send( ('ppIsRunning', () ) )
        return self.clientPipe.recv()
        
    def ppReset(self):#, widget = None, data = None):
        self.clientPipe.send( ('ppReset', () ) )        

    def ppStart(self):#, widget = None, data = None):
        self.clientPipe.send( ('ppStart', () ) )
        return self.clientPipe.recv()

    def ppStop(self):#, widget, data= None):
        self.clientPipe.send( ('ppStop', () ) )
        return self.clientPipe.recv()

    def interruptRead(self):
        self.sleepQueue.put(False)
                    
    def ppWriteData(self,data):
        self.clientPipe.send( ('ppWriteData', (data, ) ) )
        return self.clientPipe.recv()
                
    def ppWriteRam(self,data,address):
        self.clientPipe.send( ('ppWriteRam', (data,address) ) )
        return self.clientPipe.recv()
            
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
            
    def ppWriteRamWordlist(self,wordlist,address):
        self.clientPipe.send( ('ppWriteRamWordlist', (wordlist,address) ) )        

    def ppReadRam(self,data,address):
        self.clientPipe.send( ('ppReadRam', (data,address) ) )
        return self.clientPipe.recv()
            
    def ppReadRamWordList(self, wordlist, address):
        self.clientPipe.send( ('ppReadRam', (wordlist, address) ) )
        return self.clientPipe.recv()
                
    def ppClearWriteFifo(self):
        self.clientPipe.send( ('ppClearWriteFifo', (wordlist,address) ) )        
            
    def ppFlushData(self):
        self.clientPipe.send( ('ppFlushData', (wordlist,address) ) )        

    def ppClearReadFifo(self):
        self.clientPipe.send( ('ppClearReadFifo', (wordlist,address) ) )        
            
    def ppReadLog(self):
        self.clientPipe.send( ('ppReadLog', (wordlist, address) ) )
        return self.clientPipe.recv()
        

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
