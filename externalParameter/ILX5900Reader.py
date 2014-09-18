'''
Created on May 16, 2014

@author: wolverine
'''

import visa   #@UnresolvedImport
from modules.magnitude import mg

class Settings:
    pass

class ILX5900Reader(object):
    @staticmethod
    def connectedInstruments():
        return [name for name in visa.get_instruments_list(True) if name.find('COM')!=0 ]

    def __init__(self, instrument=0, timeout=1, settings=None):
        self.instrument = instrument
        self.conn = None
        self.settings = settings if settings is not None else Settings()
        self.timeout = mg(timeout,'s')
        self.setDefaults()
               
    def setDefaults(self):
        self.settings.__dict__.setdefault('waitTime', mg(0.1, 's') )
        self.settings.__dict__.setdefault('timeout', mg(0.1, 's') )
        self.settings.__dict__.setdefault('C1', 9.7142e-4 )
        self.settings.__dict__.setdefault('C2', 2.3268e-4 )
        self.settings.__dict__.setdefault('C3', 8.0591e-8 )

    @property
    def waitTime(self):
        return self.settings.waitTime.toval('s')

    @waitTime.setter
    def waitTime(self, value):
        self.settings.waitTime = value

    @property
    def timeout(self):
        return self.settings.timeout.toval('s')

    @timeout.setter
    def timeout(self, value):
        self.settings.timeout = value
        
    @property
    def C1(self):
        return self.settings.C1
    
    @C1.setter
    def C1(self, value):
        self.settings.C1 = value
        self.conn.write("Const:Thermistor {0}, {1}, {2}".format(self.settings.C1, self.settings.C2, self.settings.C3 ))

    @property
    def C2(self):
        return self.settings.C2
    
    @C2.setter
    def C2(self, value):
        self.settings.C2 = value
        self.conn.write("Const:Thermistor {0}, {1}, {2}".format(self.settings.C1, self.settings.C2, self.settings.C3 ))

    @property
    def C3(self):
        return self.settings.C3
    
    @C3.setter
    def C3(self, value):
        self.settings.C3 = value
        self.conn.write("Const:Thermistor {0}, {1}, {2}".format(self.settings.C1, self.settings.C2, self.settings.C3 ))

    def open(self):
        self.conn = visa.instrument( self.instrument, timeout=self.settings.timeout.toval('s'))
           
    def close(self):
        self.conn.close()
        
    def value(self):
        #return float(self.conn.ask("N5H1"))
        return float(self.conn.ask("Measure:Temp?"))
    
    def paramDef(self):
        return [{'name': 'timeout', 'type': 'magnitude', 'value': self.settings.timeout, 'tip': "wait timeout for communication", 'field': 'timeout'},
                {'name': 'waitTime', 'type': 'magnitude', 'value': self.settings.waitTime, 'tip': "wait time between queries", 'field': 'waitTime'},
                {'name': 'C1', 'type': 'float', 'value': self.settings.C1, 'tip': "Steinhart Hart Thermistor calibration C1*1e3", 'field': 'C1'},
                {'name': 'C2', 'type': 'float', 'value': self.settings.C2, 'tip': "Steinhart Hart Thermistor calibration C2*1e4", 'field': 'C2'},
                {'name': 'C3', 'type': 'float', 'value': self.settings.C3, 'tip': "Steinhart Hart Thermistor calibration C3*1e7", 'field': 'C3'}]

    


if __name__=="__main__":
    mks = ILX5900Reader()
    mks.open()
    mks.pr3()
    mks.close()
    