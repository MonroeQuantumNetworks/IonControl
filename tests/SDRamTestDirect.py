'''
Created on Oct 13, 2014

@author: pmaunz
'''


from pulser.PulserHardwareServer import PulserHardwareServer 
from mylogging import LoggingSetup   #@UnusedImport
import random
import sys

if __name__=='__main__':
    pulser = PulserHardwareServer()
    boards = pulser.listBoards()
    for name, desc in boards.iteritems():
        print "name: {0} desc: {1}".format(name, desc.__dict__)
    serial = boards.values()[0].serial
    pulser.openBySerial( serial )
    #pulser.uploadBitfile( r"..\FPGA_Ions\fpgafirmware.bit")
    pulser.uploadBitfile( r"C:\Users\pmaunz\Documents\Programming\IonControl-firmware\fpgafirmware.bit")
    
    datalength = 128
    data = bytearray([ random.randint(0,255) for _ in range(datalength) ])
    print "data written", [hex(int(d)) for d in data]
    pulser.ppWriteRam(data, 0)
    datacopy = bytearray([0]*len(data))
    pulser.xem.ActivateTriggerIn( 0x41, 8 ) # Ram set read address
    pulser.ppReadRam(datacopy, 0)
    print "data read   ", [hex(int(d)) for d in datacopy]
    pulser.ppReadRam(datacopy, 0)
    print "data read   ", [hex(int(d)) for d in datacopy]
    pulser.ppReadRam(datacopy, 0)
    print "data read   ", [hex(int(d)) for d in datacopy]
    pulser.ppReadRam(datacopy, 0)
    print "data read   ", [hex(int(d)) for d in datacopy]

    data = bytearray([ 0xff for _ in range(datalength) ])
    print "data written", [hex(int(d)) for d in data]
    pulser.ppWriteRam(data, 0)
    datacopy = bytearray([0]*len(data))
    pulser.ppReadRam(datacopy, 0)
    print "data read   ", [hex(int(d)) for d in datacopy]
    pulser.ppReadRam(datacopy, 0)
    print "data read   ", [hex(int(d)) for d in datacopy]
    pulser.ppReadRam(datacopy, 0)
    print "data read   ", [hex(int(d)) for d in datacopy]
    pulser.ppReadRam(datacopy, 0)
    print "data read   ", [hex(int(d)) for d in datacopy]
