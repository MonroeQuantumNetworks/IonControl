'''
Created on May 16, 2014

@author: wolverine
'''
from omegacn7500 import OmegaCN7500 #@UnresolvedImport

class OmegaCN7500Reader:
    def __init__(self, port="COM5", baud=9600, deviceaddr=1, timeout=1):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.conn = None
        self.deviceaddr = deviceaddr
        
    def open(self):
        self.conn = OmegaCN7500(self.port, self.deviceaddr )
        
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
    
    
