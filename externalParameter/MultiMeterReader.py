'''
Created on May 16, 2014

@author: wolverine
'''

import visa   #@UnresolvedImport

class MultiMeterReader:
    @staticmethod
    def connectedInstruments():
        return [name for name in visa.get_instruments_list(True) if name.find('COM')!=0 ]

    def __init__(self, instrument=0, timeout=1, settings=None):
        self.instrument = instrument
        self.timeout = timeout
        self.conn = None
        
    def open(self):
        self.conn = visa.instrument( self.instrument, timeout=self.timeout)
        self.conn.write("F1T4R-2RAZ1N5")
        
    def close(self):
        self.conn.close()
        
    def value(self):
        #return float(self.conn.ask("N5H1"))
        return float(self.conn.ask("F1T3"))
    
    


if __name__=="__main__":
    mks = MultiMeterReader()
    mks.open()
    mks.pr3()
    mks.close()
    