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
    pp.loadSource(r'prog\Ions-samples\test.pp')
    fpga = fpgaUtilit.FPGAUtilit()
    xem = fpga.openBySerial('12230003NX')
    fpga.uploadBitfile(r'FPGA_ions\fpgafirmware.bit')
    hw = PulserHardware.PulserHardware(None)
    hw.xem = xem
    
    bytebuffer = bytearray([17]*1024)
    backbuffer = bytearray([0]*1024)
    hw.ppWriteRam( bytebuffer, 256 )
    hw.ppReadRam( backbuffer, 256)
    
    
    hw.ppUpload( pp.toBinary() )
    xem.UpdateWireOuts()
    print "DataOutPipe", hex(xem.GetWireOutValue(0x20))
    xem.UpdateWireOuts()
    print "DataOutPipe",hex(xem.GetWireOutValue(0x20))
    hw.ppStart()
    Finished = False
    while not Finished:#for j in range(60):
        data = hw.ppReadData(1000,0.1)
        if printdata:
            for i in sliceview(data,4):
                (num,) = struct.unpack('I',i)
                Finished |= (num==0xffffffff)
                print hex(num)
        else:
            for i in sliceview(data,4):
                (num,) = struct.unpack('I',i)
                Finished |= (num==0xffffffff)
            if len(data)>0:
                print "read {0} bytes".format(len(data))
            else:
                print ".",
            
    xem.UpdateWireOuts()
    print "DataOutPipe",hex(xem.GetWireOutValue(0x20))
    print "byteswaiting" , xem.GetWireOutValue(0x25) & 0xfff  # pipe_out_available
