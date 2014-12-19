'''
Created on May 16, 2014

@author: wolverine
'''

import visa   #@UnresolvedImport
from modules.magnitude import mg
from modules.MagnitudeUtilit import value as toValue

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
        if self.settings.Write:
            self.setPID()
            self.ILimHigh = self.settings.ILimHigh
            self.ILimLow = self.settings.ILimLow
            self.Setpoint = self.settings.Setpoint
        else:
            self.readPID()
            self.readLimits()
            self.readSetpoint()
               
    def setDefaults(self):
        self.settings.__dict__.setdefault('waitTime', mg(0.1, 's') )
        self.settings.__dict__.setdefault('timeout', mg(0.1, 's') )
        self.settings.__dict__.setdefault('C1', 0.97142 )
        self.settings.__dict__.setdefault('C2', 2.3268 )
        self.settings.__dict__.setdefault('C3', 0.80591 )
        self.settings.__dict__.setdefault('P', 0.1 )
        self.settings.__dict__.setdefault('I', 0.1 )
        self.settings.__dict__.setdefault('D', 0.1 )
        self.settings.__dict__.setdefault('ILimHigh', 0 )
        self.settings.__dict__.setdefault('ILimLow', -0.5 )
        self.settings.__dict__.setdefault('Write', False )
        self.settings.__dict__.setdefault('Setpoint', 31.65)

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
        
    @property
    def P(self):
        return self.settings.P
    
    @P.setter
    def P(self, value):
        self.settings.P = toValue(value)
        print "P:", self.settings.P
        self.setPID()

    @property
    def I(self):
        return self.settings.I
    
    @I.setter
    def I(self, value):
        self.settings.I = toValue(value)
        print "I:", self.settings.I
        self.setPID()

    @property
    def D(self):
        return self.settings.D
    
    @D.setter
    def D(self, value):
        self.settings.D = toValue(value)
        print "D:", self.settings.D
        self.setPID()
        
    @property
    def ILimHigh(self):
        return self.settings.ILimHigh
    
    @ILimHigh.setter
    def ILimHigh(self, value):
        self.settings.ILimHigh = value.toval('A')
        self.conn.write( ":LIMIT:ITE:HIGH {0}".format(self.settings.ILimHigh))
 
    @property
    def ILimLow(self):
        return self.settings.ILimLow
    
    @ILimLow.setter
    def ILimLow(self, value):
        self.settings.ILimLow = value.toval('A')
        self.conn.write( ":LIMIT:ITE:LOW {0}".format(self.settings.ILimLow))
       
    @property
    def Setpoint(self):
        return self.settings.Setpoint

    @Setpoint.setter
    def Setpoint(self, value):
        self.settings.Setpoint = toValue(value)
        self.conn.write(':SET:TEMP {0}'.format(self.settings.Setpoint))
       
    def setPID(self):
        print "PID {0},{1},{2}".format(self.settings.P, self.settings.I, self.settings.D)
        self.conn.write( "PID {0},{1},{2}".format(self.settings.P, self.settings.I, self.settings.D))
        
    def readPID(self):
        answer = self.conn.ask("PID?")
        self.settings.P, self.settings.I, self.settings.D = map( float, answer.split(",") )

    def readLimits(self):
        self.settings.ILimHigh = mg( float(self.conn.ask(':LIMIT:ITE:HIGH?')), 'A')
        self.settings.ILimLow = mg( float(self.conn.ask(':LIMIT:ITE:LOW?')), 'A')

    def readSetpoint(self):
        self.settings.Setpoint = float(self.conn.ask(":SET:TEMP?"))

    def open(self):
        self.conn = visa.instrument( self.instrument, timeout=self.settings.timeout.toval('s'))
        self.readPID()
           
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
                {'name': 'C3', 'type': 'float', 'value': self.settings.C3, 'tip': "Steinhart Hart Thermistor calibration C3*1e7", 'field': 'C3'},
                {'name': 'P', 'type': 'magnitude', 'value': self.settings.P, 'field': 'P'},
                {'name': 'I', 'type': 'magnitude', 'value': self.settings.I, 'field': 'I'},
                {'name': 'D', 'type': 'magnitude', 'value': self.settings.D, 'field': 'D'},
                {'name': 'I limit pos', 'type': 'magnitude', 'value': self.settings.ILimHigh, 'field': 'ILimHigh'},
                {'name': 'I limit neg', 'type': 'magnitude', 'value': self.settings.ILimLow, 'field': 'ILimLow'},
                {'name': 'Write on startup', 'type': 'bool', 'value': self.settings.Write, 'field': 'Write'},
                {'name': 'Setpoint', 'type': 'bool', 'value': self.settings.Setpoint, 'field': 'Setpoint'}]

    


if __name__=="__main__":
    mks = ILX5900Reader()
    mks.open()
    mks.pr3()
    mks.close()
    