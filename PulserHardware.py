# -*- coding: utf-8 -*-
"""
Encapsulation of the Pulse Programmer Hardware 
"""
from fpgaUtilit import check
from PyQt4 import QtCore 
import struct
from Queue import Queue, Empty
import magnitude

class PulserHardware(object):
    sleepQueue = Queue()   # used to be able to interrupt the sleeping procedure
    timestep = magnitude.mg(20,'ns')

    def __init__(self,xem):
        self._shutter = 0
        self._trigger = 0
        self.xem = xem
        self.Mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
        
    def setHardware(self,xem):
        self.xem = xem
        
    @property
    def shutter(self):
        return self._shutter  #
         
    @shutter.setter
    def shutter(self, value):
        with QtCore.QMutexLocker(self.Mutex):
            check( self.xem.SetWireInValue(0x06, value, 0xFFFF) , 'SetWireInValue' )	
            check( self.xem.SetWireInValue(0x07, value>>16, 0xFFFF)	, 'SetWireInValue' )
            check( self.xem.UpdateWireIns(), 'UpdateWireIns' )
            self._shutter = value
        
    @property
    def trigger(self):
        return self._trigger
            
    @trigger.setter
    def trigger(self,value):
        with QtCore.QMutexLocker(self.Mutex):
            check( self.xem.SetWireInValue(0x08, value, 0xFFFF) , 'SetWireInValue' )	
            check( self.xem.SetWireInValue(0x09, value>>16, 0xFFFF)	, 'SetWireInValue' )
            check( self.xem.UpdateWireIns(), 'UpdateWireIns' )
            check( self.xem.ActivateTriggerIn( 0x41, 2), 'ActivateTrigger' )
            self._trigger = value
        
    def ppUpload(self,binarycode,startaddress=0):
        with QtCore.QMutexLocker(self.Mutex):
            print "starting PP upload",
            check( self.xem.SetWireInValue(0x00, startaddress, 0x0FFF), "ppUpload write start address" )	# start addr at zero
            self.xem.UpdateWireIns()
            check( self.xem.ActivateTriggerIn(0x41, 1), "ppUpload trigger" )
            print len(binarycode), "bytes,",
            num = self.xem.WriteToPipeIn(0x80, bytearray(binarycode) )
            check(num, 'Write to program pipe' )
            print "uploaded pp file {0} bytes".format(num),
            num, data = self.ppDownload(0,num)
            print "Verified {0} bytes. ".format(num),data==binarycode
            return True
            
    def ppDownload(self,startaddress,length):
        with QtCore.QMutexLocker(self.Mutex):
            self.xem.SetWireInValue(0x00, startaddress, 0x0FFF)	# start addr at 3900
            self.xem.UpdateWireIns()
            self.xem.ActivateTriggerIn(0x41, 0)
            self.xem.ActivateTriggerIn(0x41, 1)
            data = bytearray('\000'*length)
            num = self.xem.ReadFromPipeOut(0xA0, data)
            return num, data
        
    def ppIsRunning(self):
        with QtCore.QMutexLocker(self.Mutex):
		#Commented CWC 04032012
            data = '\x00'*32
            self.xem.ReadFromPipeOut(0xA1, data)

            if ((data[:2] != '\xED\xFE') or (data[-2:] != '\xED\x0F')):
                print "Bad data string: ", map(ord, data)
                return True

            data = map(ord, data[2:-2])

            #Decode
            active =  bool(data[1] & 0x80)
    
            return active

    def ppReset(self):#, widget = None, data = None):
        with QtCore.QMutexLocker(self.Mutex):
            self.xem.ActivateTriggerIn(0x40,0)
            self.xem.ActivateTriggerIn(0x41,0)
            print "pp_reset is not working right now... CWC 08302012"

    def ppStart(self):#, widget = None, data = None):
        with QtCore.QMutexLocker(self.Mutex):
            self.xem.ActivateTriggerIn(0x40, 3)  # pp_stop_trig
            self.xem.ActivateTriggerIn(0x40, 2)  # pp_start_trig
            return True

    def ppStop(self):#, widget, data= None):
        with QtCore.QMutexLocker(self.Mutex):
            self.xem.ActivateTriggerIn(0x40, 3)  # pp_stop_trig
            return True

    def interruptRead(self):
        self.sleepQueue.put(False)

    def ppReadData(self,minbytes=4,timeout=0.5,retryevery=0.05):
        with QtCore.QMutexLocker(self.Mutex):
            self.xem.UpdateWireOuts()
            wirevalue = self.xem.GetWireOutValue(0x25)   # pipe_out_available
        byteswaiting = max( (wirevalue & 0xffe)*2, 4 * bool( wirevalue & 0x000 ) )
        #if byteswaiting>0: print "byteswaiting", byteswaiting
        totaltime = 0
        while byteswaiting<minbytes and totaltime<timeout:
            try: 
                self.sleepQueue.get(True, retryevery)
                totaltime = timeout     # we were interrupted
            except Empty:         
                pass                    # expiration is the normal case
            totaltime += retryevery
            with QtCore.QMutexLocker(self.Mutex):
                self.xem.UpdateWireOuts()
                wirevalue = self.xem.GetWireOutValue(0x25)   # pipe_out_available
            byteswaiting = max( (wirevalue & 0xffe)*2, 4 * bool( wirevalue & 0x000 ) )
            #if byteswaiting>0: print "byteswaiting", byteswaiting
        data = bytearray('\x00'*byteswaiting)
        with QtCore.QMutexLocker(self.Mutex):
            self.xem.ReadFromPipeOut(0xa2, data)
        return data
                        
    def ppWriteData(self,data):
        if isinstance(data,bytearray):
            with QtCore.QMutexLocker(self.Mutex):
                return self.xem.WriteToPipeIn(0x81,data)
        else:
            code = bytearray()
            for item in data:
                code.extend(struct.pack('I',item))
            print "ppWriteData length",len(code)
            with QtCore.QMutexLocker(self.Mutex):
                return self.xem.WriteToPipeIn(0x81,code)
                
    def ppClearWriteFifo(self):
        self.xem.ActivateTriggerIn(0x41, 3)
            
    def ppReadLog(self):
        with QtCore.QMutexLocker(self.Mutex):
 		#Commented CWC 04032012
            data = bytearray('\x00'*32)
            self.xem.ReadFromPipeOut(0xA1, data)
            with open(r'debug\log','wb') as f:
                f.write(data)
        return data
        
def sliceview(view,length):
    return tuple(buffer(view, i, length) for i in range(0, len(view), length))    

if __name__ == "__main__":
    import fpgaUtilit
    import PulseProgram
    
    printdata = True
    
    pp = PulseProgram.PulseProgram()
    pp.loadSource(r'prog\Ions\test.pp')
    fpga = fpgaUtilit.FPGAUtilit()
    xem = fpga.openBySerial('12230003NX')
    fpga.uploadBitfile(r'FPGA_ions\fpgafirmware.bit')
    hw = PulserHardware(xem)
    hw.ppUpload( pp.toBinary() )
    xem.UpdateWireOuts()
    print "DataOutPipe", hex(xem.GetWireOutValue(0x25))
    hw.ppWriteData( bytearray('\x12\x34\x00\x00\x21\x22\x23\x24'))
    xem.UpdateWireOuts()
    print "DataOutPipe",hex(xem.GetWireOutValue(0x25))
    hw.ppStart()
    Finished = False
    while not Finished:#for j in range(60):
        data = hw.ppReadData(1000,0.1)
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
