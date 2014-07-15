'''
Created on May 16, 2014

@author: wolverine
'''
import serial  #@UnresolvedImport
import re
import math

class TerranovaReader:
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
                
    def value(self):
        reply = self.query("F")  
        m = re.match('\s*(\d+)\s+([-0-9]+)\s*', reply)
        mantissa = float(m.group(1))
        exponent = int(m.group(2))
        return  mantissa * math.pow(10,exponent)

if __name__=="__main__":
    mks = TerranovaReader()
    mks.open()
    result = mks.value()
    print result
    mks.close()
    