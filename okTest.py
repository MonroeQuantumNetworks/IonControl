# -*- coding: utf-8 -*-
"""
Encapsulation of the Pulse Programmer Hardware 
"""
import ok 

if __name__ == "__main__":
    xem = ok.FrontPanel()
    print xem.OpenBySerial('12230003NX')
    print xem.ConfigureFPGA(r'FPGA_Ions\fpgafirmware.bit')

    zeros = bytearray( b'\x00'*32)
    data = bytearray( b'\x00'*32)
    while True:
        xem.ReadFromPipeOut(0xA0, data)
        print len(data), len(zeros), zeros==data, hex(data[0])
    
     