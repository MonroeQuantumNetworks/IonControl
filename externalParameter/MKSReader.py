'''
Created on May 16, 2014

@author: wolverine
'''

import serial   #@UnresolvedImport
import re

class MKSReader:
    def __init__(self, port=0, baud=9600, deviceaddr=253, timeout=1):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.conn = None
        self.deviceaddr = deviceaddr
        
    def open(self):
        self.conn = serial.Serial( self.port, self.baud, timeout=self.timeout)
        
    def close(self):
        self.conn.close()
        
    def query(self, question, length=100):
        self.conn.write(question)
        return self.conn.read(length)
        
    def setupDatalogger(self, time):
        self.conn.write("@{0}DLT!{1};FF".format(self.deviceaddr, time))
        reply = self.conn.read(100)
        print reply
        
    def startLogger(self):
        print self.query("@{0}DLC!START;FF".format(self.deviceaddr))

    def stopLogger(self):
        print self.query("@{0}DLC!STOP;FF".format(self.deviceaddr))
        
    def getLog(self):
        print self.query("@{0}DL?;FF".format(self.deviceaddr), length=1000)

    def test(self):
        print self.query("@{0}DLC?;FF".format(self.deviceaddr))
        print self.query("@{0}DLT?;FF".format(self.deviceaddr))

    def pr3(self):
        devicestr = "@{0}".format(self.deviceaddr)
        reply = self.query("{0}PR3?;FF".format(devicestr))  
        m = re.match(devicestr+'ACK([0-9.E-]+);FF', reply)
        return float(m.group(1))
        
    def value(self):
        return self.pr3()
    
    


if __name__=="__main__":
    mks = MKSReader()
    mks.open()
    mks.pr3()
    mks.close()
    