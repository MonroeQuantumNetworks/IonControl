# -*- coding: utf-8 -*-
"""
Encapsulation of the Pulse Programmer Hardware OUTSIDE of the running pulser
"""
import ok
import fpgaUtilit

class PulserHardware(object):
    def __init__(self,xem):
        self._shutter = 0
        self._trigger = 0
        self.xem = xem
        
    @property
    def shutter(self):
        return self._shutter  #
        self.xem.UpdateWireIns()
         
    @shutter.setter
    def shutter(self, value):
        fpgaUtilit.check( self.xem.SetWireInValue(0x06, value, 0xFFFF) , 'SetWireInValue' )	
        fpgaUtilit.check( self.xem.SetWireInValue(0x07, value>>16, 0xFFFF)	, 'SetWireInValue' )
        fpgaUtilit.check( self.xem.UpdateWireIns(), 'UpdateWireIns' )
        self._shutter = value
        self._x = value


if __name__ == "__main__":
    xem = ok.FrontPanel()
    fpgaUtilit.check( xem.OpenBySerial('12230003NX'), 'OpenBySerial' )
    #fpgaUtilit.check( xem.ConfigureFPGA(r'FPGA_Ions\fpgafirmware.bit'), 'ConfigureFPGA' )
    hw = PulserHardware(xem)
    hw.shutter = 0xfffffffe
    