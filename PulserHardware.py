# -*- coding: utf-8 -*-
"""
Encapsulation of the Pulse Programmer Hardware 
"""
import ok
from fpgaUtilit import check

class PulserHardware(object):
    def __init__(self,xem):
        self._shutter = 0
        self._trigger = 0
        self.xem = xem
        
    def setHardware(self,xem):
        self.xem = xem
        
    @property
    def shutter(self):
        return self._shutter  #
        self.xem.UpdateWireIns()
         
    @shutter.setter
    def shutter(self, value):
        check( self.xem.SetWireInValue(0x06, value, 0xFFFF) , 'SetWireInValue' )	
        check( self.xem.SetWireInValue(0x07, value>>16, 0xFFFF)	, 'SetWireInValue' )
        check( self.xem.UpdateWireIns(), 'UpdateWireIns' )
        self._shutter = value
        self._x = value
        
    def ppUpload(self,binarycode):
        check( self.xem.SetWireInValue(0x00, 0, 0x0FFF), "ppUpload write start address" )	# start addr at zero
        self.xem.UpdateWireIns()
        check( self.xem.ActivateTriggerIn(0x41, 1), "ppUpload trigger" )
        print "Databuf length" ,len(binarycode)
        check( self.xem.WriteToPipeIn(0x80, bytearray(binarycode) ), "ppUpload write data" )
        return True
        


if __name__ == "__main__":
    xem = ok.FrontPanel()
    check( xem.OpenBySerial('12230003NX'), 'OpenBySerial' )
    #fpgaUtilit.check( xem.ConfigureFPGA(r'FPGA_Ions\fpgafirmware.bit'), 'ConfigureFPGA' )
    hw = PulserHardware(xem)
    hw.shutter = 0xfffffffe
    