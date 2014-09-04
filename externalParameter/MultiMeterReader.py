'''
Created on May 16, 2014

@author: wolverine
'''

import visa   #@UnresolvedImport

class MultiMeterReader:
    def __init__(self, instrument=0, timeout=1):
        self.instrument = instrument
        self.timeout = timeout
        self.conn = None
        
    def open(self):
        self.conn = visa.instrument( self.instrument, timeout=self.timeout)
        
    def close(self):
        self.conn.close()
        
    def value(self):
        return float(self.conn.ask("N5H1"))
    
    


if __name__=="__main__":
    mks = MultiMeterReader()
    mks.open()
    mks.pr3()
    mks.close()
    