# -*- coding: utf-8 -*-
"""
Encapsulation of the Pulse Programmer Hardware 
"""
import ok
from fpgaUtilit import check
from PyQt4 import QtCore 

class PulserHardware(object):
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
            print "setShutter"
            check( self.xem.SetWireInValue(0x06, value, 0xFFFF) , 'SetWireInValue' )	
            check( self.xem.SetWireInValue(0x07, value>>16, 0xFFFF)	, 'SetWireInValue' )
            check( self.xem.UpdateWireIns(), 'UpdateWireIns' )
            self._shutter = value
        
    @property
    def trigger(self):
        return 0
            
    @trigger.setter
    def trigger(self,value):
        print "Trigger out not implemented"
        
    def ppUpload(self,binarycode,startaddress=0):
        with QtCore.QMutexLocker(self.Mutex):
            print "starting PP upload"
            check( self.xem.SetWireInValue(0x00, startaddress, 0x0FFF), "ppUpload write start address" )	# start addr at zero
            self.xem.UpdateWireIns()
            check( self.xem.ActivateTriggerIn(0x41, 1), "ppUpload trigger" )
            print "Databuf length" ,len(binarycode)
            num = self.xem.WriteToPipeIn(0x80, bytearray(binarycode) )
            print "uploaded pp file {0} bytes".format(num)
            num, data = self.ppDownload(0,num)
            print "Read {0} bytes back. ".format(num),data==binarycode
            with open(r'debug\binary_back','wb') as f:
                f.write(data)
            return True
            
    def ppDownload(self,startaddress,length):
        with QtCore.QMutexLocker(self.Mutex):
            self.xem.SetWireInValue(0x00, startaddress, 0x0FFF)	# start addr at 3900
            self.xem.UpdateWireIns()
            self.xem.ActivateTriggerIn(0x41, 0)
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


    def ppReadData(self,minbytes,timeout=0.5):
        with QtCore.QMutexLocker(self.Mutex):
            self.xem.UpdateWireOuts()
            byteswaiting = self.xem.GetWireOutValue(0x25) & 0xfff  # pipe_out_available
            tries = 0
            while byteswaiting<minbytes and tries<10:
                time.sleep(timeout/10)
                tries +=1
                byteswaiting = self.xem.GetWireOutValue(0x25) & 0xfff  # pipe_out_available
            data = bytearray('\x00'*byteswaiting)
            self.xem.ReadFromPipeOut(0xa2, data)
            return data
            
    def ppReadLog(self):
        with QtCore.QMutexLocker(self.Mutex):
 		#Commented CWC 04032012
            data = bytearray('\x00'*32)
            self.xem.ReadFromPipeOut(0xA1, data)
            with open(r'debug\log','wb') as f:
                f.write(data)
        

if __name__ == "__main__":
    import fpgaUtilit
    import time
    fpga = fpgaUtilit.FPGAUtilit()
    xem = fpga.openBySerial('12230003NX')
    hw = PulserHardware( xem )
    fpga.uploadBitfile(r'FPGA_Ions\fpgafirmware.bit')
    #fpgaUtilit.check( xem.ConfigureFPGA(r'FPGA_Ions\fpgafirmware.bit'), 'ConfigureFPGA' )
    #hw = PulserHardware(xem)
    hw.shutter = 0xfffffffe

    hw.ppUpload( bytearray(b'\x06\x00\x00\x07\x00\x00\x00\x38\x07\x00\x00\x08\x00\x00\x00\x0f\x07\x00\x00\x0a\x00\x00\x00\x13\xff\xff\xff\x00\x00\x00\x00\x00') )
    hw.ppStart()
    for i in range(20):
        data = hw.ppReadData(100,1.0)
        print "read {0} bytes".format(len(data))
        print data
    #print xem.ActivateTriggerIn(0x41, 0 )

    #hw.ppReadLog()
    #check( xem.SetWireInValue(0x00, 7, 0x0FFF), "ppUpload write start address" )	# start addr at zero
    #xem.UpdateWireIns()
    #check( xem.ActivateTriggerIn(0x41, 1), "ppUpload trigger" )
     