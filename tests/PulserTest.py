'''
Created on Apr 3, 2014

@author: wolverine
'''

from pulser.PulserHardwareClient import PulserHardware

def testSequentialData( length ):
    data = range(1000)
    pulser.ppWriteRamWordlist( data, 0 )


if __name__=="__main__":
    pulser = PulserHardware()
    #pulser.openBySerial("12230003NX")
    #pulser.uploadBitfile(r"..\FPGA_ions\fpgafirmware.bit")
    #testSequentialData( 1000 )
    