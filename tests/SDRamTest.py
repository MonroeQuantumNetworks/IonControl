'''
Created on Oct 13, 2014

@author: pmaunz
'''


from pulser.PulserHardwareClient import PulserHardware 
from mylogging import LoggingSetup   #@UnusedImport
import random
import sys

if __name__=='__main__':
    pulser = PulserHardware()
    boards = pulser.listBoards()
    for name, desc in boards.iteritems():
        print "name: {0} desc: {1}".format(name, desc.__dict__)
    serial = boards.values()[0].serial
    pulser.openBySerial( serial )
    #pulser.uploadBitfile( r"..\FPGA_Ions\fpgafirmware.bit")
    pulser.uploadBitfile( r"C:\Users\pmaunz\Documents\Programming\IonControl-firmware\fpgafirmware.bit")
    
    datalength = 128
    data = [ random.randint(0,sys.maxint) for _ in range(datalength) ]
    print "data", data
    print "data", [hex(d) for d in data]
    pulser.ppWriteRamWordList(data, 0, check=True)