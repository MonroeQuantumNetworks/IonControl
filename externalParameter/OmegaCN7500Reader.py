'''
Created on May 16, 2014

@author: wolverine
'''
from omegacn7500 import OmegaCN7500 #@UnresolvedImport
import serial.tools.list_ports
from modules.magnitude import mg

class Settings:
    pass

class OmegaCN7500Reader(object):
    @staticmethod
    def connectedInstruments():
        return [name for name,_,_ in serial.tools.list_ports.comports() ]

    def __init__(self, instrument="COM5", baud=9600, deviceaddr=1, timeout=1, settings=None):
        self.instrument = instrument
        self.baud = baud
        self.conn = None
        self.deviceaddr = deviceaddr
        self.settings = settings if settings is not None else Settings()
        self.setDefaults()
        self.timeout = mg(timeout,'s')
        
    def __setstate__(self, d):
        self.__dict__ = d
        self.__dict__.setdefault('settings', Settings())
        self.setDefaults()
        
    def open(self):
        self.conn = OmegaCN7500(self.instrument, self.deviceaddr )
        self.conn.serial.timeout = self.settings.timeout.toval('s')
        
    def close(self):
        self.conn = None
        
    def value(self):
        return self.conn.get_pv()

    def setDefaults(self):
        self.settings.__dict__.setdefault('timeout', mg(500,'ms'))
        self.settings.__dict__.setdefault('measureSeparation', mg(500,'ms'))

    def paramDef(self):
        return [{'name': 'timeout', 'type': 'magnitude', 'value': self.timeout, 'tip': "wait time for communication", 'field': 'timeout'},
                {'name': 'measure separation', 'type': 'magnitude', 'value': self.measureSeparation, 'tip': "time between two reading", 'field': 'measureSeparation'}]
        
    @property
    def waitTime(self):
        return self.settings.measureSeparation.toval('s')
    
    @property
    def measureSeparation(self):
        return self.settings.measureSeparation
    
    @measureSeparation.setter
    def measureSeparation(self, value):
        self.settings.measureSeparation = value
        
    @property
    def timeout(self):
        return self.settings.timeout
    
    @timeout.setter
    def timeout(self, value):
        self.settings.timeout = value
        if self.conn is not None:
            self.conn.serial.timeout = self.settings.timeout.toval('s')
    
    

if __name__=="__main__":
    mks = OmegaCN7500Reader()
    mks.open()
    result = mks.value()
    print result
    mks.close()
    
    
