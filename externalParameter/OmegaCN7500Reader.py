'''
Created on May 16, 2014

@author: wolverine
'''
from omegacn7500 import OmegaCN7500 #@UnresolvedImport
import serial.tools.list_ports

class OmegaCN7500Reader:
    @staticmethod
    def connectedInstruments():
        return [name for name,_,_ in serial.tools.list_ports.comports() ]

    def __init__(self, instrument="COM5", baud=9600, deviceaddr=1, timeout=1):
        self.instrument = instrument
        self.baud = baud
        self.timeout = timeout
        self.conn = None
        self.deviceaddr = deviceaddr
        
    def open(self):
        self.conn = OmegaCN7500(self.instrument, self.deviceaddr )
        
    def close(self):
        pass
        
    def value(self):
        return self.conn.get_pv()

if __name__=="__main__":
    mks = OmegaCN7500Reader()
    mks.open()
    result = mks.value()
    print result
    mks.close()
    
    
