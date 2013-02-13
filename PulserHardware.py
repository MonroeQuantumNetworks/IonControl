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
        self.Mutex = QtCore.QMutex()
        
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
        
    def ppUpload(self,binarycode):
        with QtCore.QMutexLocker(self.Mutex):
            check( self.xem.SetWireInValue(0x00, 0, 0x0FFF), "ppUpload write start address" )	# start addr at zero
            self.xem.UpdateWireIns()
            check( self.xem.ActivateTriggerIn(0x41, 1), "ppUpload trigger" )
            print "Databuf length" ,len(binarycode)
            check( self.xem.WriteToPipeIn(0x80, bytearray(binarycode) ), "ppUpload write data" )
            print "uploaded pp file"
            return True
        
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

    def ppReadData(self):
        with QtCore.QMutexLocker(self.Mutex):
            self.xem.UpdateWireOuts()
            byteswaiting = self.xem.GetWireOutValue(25)   # pipe_out_available
            print byteswaiting
        

if __name__ == "__main__":
    xem = ok.FrontPanel()
    check( xem.OpenBySerial('12230003NX'), 'OpenBySerial' )
    #fpgaUtilit.check( xem.ConfigureFPGA(r'FPGA_Ions\fpgafirmware.bit'), 'ConfigureFPGA' )
    hw = PulserHardware(xem)
    hw.shutter = 0xfffffffe
    