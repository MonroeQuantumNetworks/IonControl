'''
Created on May 16, 2014

@author: wolverine
'''
import serial  #@UnresolvedImport
import re
import numpy

class PhotoDiodeReader:
    def __init__(self, port=0, baud=115200, deviceaddr=253, timeout=1):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.conn = None
        self.deviceaddr = deviceaddr
        
    def open(self):
        self.conn = serial.Serial( self.port, self.baud, timeout=self.timeout, parity='N', stopbits=1)
        self.conn.write('afe -agc1\n\r')
        self.conn.write('sdds -p0500\n\r')
        
    def close(self):
        self.conn.close()
        
    def query(self, question=None, length=100):
        if question:
            self.conn.write(question)
        return self.conn.read(length)
                
    def value(self):
        lines = self.query(length=500).split('\n\r')
        values = list()
        for line in lines:
            m = re.match('^(\d+)\s+(\d+)$', line)
            if m:
                gain, value = m.group(1), m.group(2)
                gain = int(gain)-1 if gain else 3
                values.append( int(value) / 2.**gain )
        return  numpy.mean(values) if values else None

if __name__=="__main__":
    try:
        mks = PhotoDiodeReader(port=15)
        mks.open()
        result = mks.value()
        print result
        mks.close()
    except Exception as e:
        mks.close()
        raise
    