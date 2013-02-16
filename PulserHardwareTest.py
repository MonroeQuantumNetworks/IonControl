# -*- coding: utf-8 -*-
"""
Encapsulation of the Pulse Programmer Hardware 
"""
from PulserHardware import check, sliceview
import PulserHardware
import struct
import time
import fpgaUtilit
import PulseProgram

printdata = True

if __name__ == "__main__":
    pp = PulseProgram.PulseProgram()
    pp.loadSource(r'prog\Ions\test-48bit.pp')
    fpga = fpgaUtilit.FPGAUtilit()
    xem = fpga.openBySerial('12230003NX')
    fpga.uploadBitfile(r'FPGA_ions\fpgafirmware-48bit.bit')
    hw = PulserHardware.PulserHardware(xem)
    hw.ppUpload( pp.toBinary() )
    xem.UpdateWireOuts()
    print "DataOutPipe", hex(xem.GetWireOutValue(0x20))
    xem.UpdateWireOuts()
    print "DataOutPipe",hex(xem.GetWireOutValue(0x20))
    hw.ppStart()
    Finished = False
    while not Finished:#for j in range(60):
        data = hw.ppReadData(6,1)
        if printdata:
            for i in sliceview(data,6):
                (num,address) = struct.unpack('IH',i)
                Finished |= (num==0xffffffff)
                print "data", hex(address), hex(num)
        else:
            for i in sliceview(data,4):
                (num,address) = struct.unpack('IH',i)
                Finished |= (num==0xffffffff)
            if len(data)>0:
                print "read {0} bytes".format(len(data))
            else:
                print ".",
            
    xem.UpdateWireOuts()
    print "DataOutPipe",hex(xem.GetWireOutValue(0x20))
    print "byteswaiting" , xem.GetWireOutValue(0x25) & 0xfff  # pipe_out_available
