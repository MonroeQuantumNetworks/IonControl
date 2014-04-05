'''
Created on Apr 5, 2014

@author: pmaunz
'''
from pulser.PulserHardwareServer import PulserHardwareServer
import sys
from PyQt4 import QtGui
import time
from random import randint
from collections import OrderedDict

writtendata = OrderedDict()

def testSequentialData( length ):
    print "testing {0:x}".format(length)
    data = [ randint(0, 0x100000 ) for _ in range(length)]
    start_time = time.time()
    try:
        pulser.ppWriteRamWordlist( data, 0 )
    except Exception:
        print "exception"
    datacopy = list([0]*len(data))
    datacopy = pulser.ppReadRamWordList( datacopy, 0 )
#     beginning = list([0]*100)
#     beginning = pulser.ppReadRamWordList( beginning, 0 )
    print "testing {0:x} took {1} seconds".format(length, time.time()-start_time )
    print data==datacopy
#     print beginning==data[0:100]
#     if data!=datacopy:
#         print data
#         print datacopy
#         print beginning
#         last = True
#         for index, (left,right) in enumerate(zip(data,datacopy)):
#             if (left==right)!=last:
#                 last = not last
#                 print index, left, right

def testWriteAddress( address, length ):
    data = [ randint(0, 0x100000000 ) for _ in range(length)]
    start_time = time.time()
    pulser.ppWriteRamWordlist( data, address )
    print "testing {0} at address {2:x} took {1} seconds".format(length, time.time()-start_time, address )
    return data

def testExpectedData( address, data):
    readData = pulser.ppReadRamWordList( [0]*len(data), address )
    print "reading old data from address {0:x} matches {1}".format( address, data==readData )
#     if data!=readData:
#         print data
#         print readData

if __name__=="__main__":
    pulser = PulserHardwareServer()
    pulser.openBySerial("132800061D")
    pulser.uploadBitfile(r"C:\Users\pmaunz\Documents\Programming\IonControl-firmware\fpgafirmware.bit")
    for factor in [128]: #range(28,256):
        testSequentialData(128*1024*factor) 
#     for address in range(0,257):
#         writtendata[128*address*4*1024] = testWriteAddress( 128*address*4*1024, 128*1024 )
#     for address, data in writtendata.iteritems():
#         testExpectedData( address, data )
#     
#     print "done"
    #sys.exit(app.exec_())
 
 
