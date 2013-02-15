# -*- coding: utf-8 -*-
"""
Encapsulation of the Pulse Programmer Hardware 
"""
from PulserHardware import check, sliceview
import PulserHardware
import struct
import time
import fpgaUtilit

if __name__ == "__main__":
    fpga = fpgaUtilit.FPGAUtilit()
    xem = fpga.openBySerial('12230003NX')
    hw = PulserHardware.PulserHardware( xem )
#    hw.ppStop()
    fpga.uploadBitfile(r'FPGA_Ions\fpgafirmware.bit')

#    hw.shutter = 0xfffffffe
#    xem.ResetFPGA()
#    check( xem.ActivateTriggerIn(0x41, 0), "ppUpload trigger" )
    data = bytearray(b'\x06\x00\x00\x07'+b'\x07\x00\x00\x0f'+b'\x07\x00\x00\x0a'+b'\x00\x00\x00\x38'+
                     b'\x08\x00\x00\x00'+b'\x00\x00\x00\x13'+b'\xff\xff\x0f\x00'+b'\x00\x00\x00\x00'+
                     b'\x00\x00\x00\x00')
    zeros = bytearray( b'\x00'*len(data))
#    hw.ppUpload( data )
    while True:
        #time.sleep(1)
        read, downdata = hw.ppDownload( 0, len(data) )
        print len(data), len(downdata), data==downdata, zeros==downdata
#        xem.UpdateWireOuts()
        #print xem.GetWireOutValue(0x25) & 0xffc  # pipe_out_available
        #print hex(hw.ppReadLog()[0])
        with open(r'debug\000','wb') as f:
            f.write(downdata)
        xem.ActivateTriggerIn(0x40,0)
#    hw.ppStart()
#    for i in range(10):
#        data = hw.ppReadData(100,0.1)
#        print "read {0} bytes".format(len(data))
#        print "slices:", len(sliceview(data,4))
#        for i in sliceview(data,4):
#            (num,) = struct.unpack('I',i)
#            print hex(num)
#    hw.ppStop()
#    hw.ppReadLog()
        
    #print xem.ActivateTriggerIn(0x41, 0 )

    #hw.ppReadLog()
    #check( xem.SetWireInValue(0x00, 7, 0x0FFF), "ppUpload write start address" )	# start addr at zero
    #xem.UpdateWireIns()
    #check( xem.ActivateTriggerIn(0x41, 1), "ppUpload trigger" )
     