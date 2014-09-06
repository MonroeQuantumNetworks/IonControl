'''
Created on May 16, 2014

@author: wolverine
'''
import serial  #@UnresolvedImport
import re
import numpy
from modules.magnitude import mg

class Settings:
    pass

class PhotoDiodeReader(object):
    def __init__(self, port=0, baud=115200, deviceaddr=253, timeout=1, settings=None):
        self.port = port
        self.baud = baud
        self.conn = None
        self.deviceaddr = deviceaddr
        self.settings = settings if settings is not None else Settings()
        self.setDefaults()
        
    def setDefaults(self):
        self.settings.__dict__.setdefault('timeout', mg(500,'ms'))
        self.settings.__dict__.setdefault('measureSeparation', mg(500,'ms'))
        
    @property
    def measureSeparation(self):
        return self.settings.measureSeparation
    
    @measureSeparation.setter
    def measureSeparation(self, sep):
        self.settings.measureSeparation = sep
        self.writeMeasureSeparation()    
        
    @property
    def timeout(self):
        return self.settings.timeout
    
    @timeout.setter
    def timeout(self, val):
        self.conn.timeout = val.toval('s')
        self.settings.timeout = val
        
    def open(self):
        self.conn = serial.Serial( self.port, self.baud, timeout=self.settings.timeout.toval('s'), parity='N', stopbits=1)
        self.conn.write('afe -agc1\n\r')
        self.conn.read(1000)
        self.writeMeasureSeparation()
        
    def writeMeasureSeparation(self):
        self.conn.write('sdds -p{0:04d}\n\r'.format(int(self.settings.measureSeparation.toval('ms'))))
        self.conn.read(1000)       
        
    def close(self):
        self.conn.close()
        
    def query(self, question=None, length=100, timeout=None):
        if question:
            self.conn.write(question)
        if timeout is not None:
            self.conn.timeout = timeout
            self.settings.timeout = timeout
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
    
    def paramDef(self):
        return [{'name': 'timeout', 'type': 'magnitude', 'value': self.timeout, 'tip': "wait time for communication", 'field': 'timeout'},
                {'name': 'measure separation', 'type': 'magnitude', 'value': self.measureSeparation, 'tip': "time between two reading", 'field': 'measureSeparation'}]


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
    