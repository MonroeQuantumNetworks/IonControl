'''
Created on May 16, 2014

@author: wolverine
'''

import visa   #@UnresolvedImport
from modules.magnitude import mg
from modules.AttributeRedirector import AttributeRedirector

class Settings:
    pass

class SpectrumAnalyzerN9342Peak(object):
    @staticmethod
    def connectedInstruments():
        return [name for name in visa.get_instruments_list(True) if name.find('COM')!=0 ]

    def __init__(self, instrument=0, timeout=1, settings=None):
        self.settings = settings if settings is not None else Settings()
        self.instrument = instrument
        self.timeout = timeout
        self.conn = None
        self.setDefaults()
        
    def setDefaults(self):
        self.settings.__dict__.setdefault('timeout', mg(500,'ms'))
        self.settings.__dict__.setdefault('measureSeparation', mg(500,'ms'))

    def open(self):
        self.conn = visa.instrument( self.instrument, timeout=self.timeout)
        self.conn.write(':CALCulate:MARKer1:CPEak ON')
       
    measureSeparation = AttributeRedirector( "settings", "measureSeparation" )
    timeout = AttributeRedirector( "settings", "timeout" )        
    
    def close(self):
        self.conn.close()
        
    def value(self):
        return float(self.conn.ask(":CALCulate:MARKer1:Y?"))
    
    @property
    def waitTime(self):
        return self.settings.measureSeparation.toval('s')

    def paramDef(self):
        return [{'name': 'timeout', 'type': 'magnitude', 'value': self.timeout, 'tip': "wait time for communication", 'field': 'timeout'},
                {'name': 'measure separation', 'type': 'magnitude', 'value': self.measureSeparation, 'tip': "time between two reading", 'field': 'measureSeparation'}]

    

