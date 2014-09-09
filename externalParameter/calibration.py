'''
Created on Aug 30, 2014

@author: pmaunz
'''
from modules.magnitude import mg

class PowerDetectorCalibration:
    """
        data is being fitted to p*x**2 + m*x + c 
        is valid between minimum and maximum input voltage
    """
    name = "Rf Power Detector Cal"
    def __init__(self, name="default"):
        self.m = -36.47
        self.c = 60.7152
        self.p = -1.79545
        self.minimum = 0.6
        self.maximum = 2
        self.digits = 5     
        
    def __setstate__(self, d):
        self.__dict__ = d
        self.__dict__.setdefault( 'digits', 5)
        
    def convert(self, volt):
        if volt is None:
            return None
        if volt < self.minimum or volt > self.maximum:
            return "oor"
        dBm = self.p * volt**2 + self.m*volt + self.c
        return dBm
        
    def convertMagnitude(self, volt):
        if volt is None:
            return None
        if volt < self.minimum or volt > self.maximum:
            return "oor"
        dBm = self.p * volt**2 + self.m*volt + self.c
        value = mg( 10**((dBm/10)-3), 'W' )
        value.significantDigits = self.digits
        return value
        
    def paramDef(self):
        return [{'name': 'function', 'type': 'str', 'value': "dBm = p*V^2 + m*V + c",'readonly':True},
                         {'name': 'p', 'type': 'float', 'value': self.p, 'object': self },
                         {'name': 'm', 'type': 'float', 'value': self.m, 'object': self },
                         {'name': 'c', 'type': 'float', 'value': self.c, 'object': self },
                         {'name': 'min', 'type': 'float', 'value': self.minimum, 'object': self },
                         {'name': 'max', 'type': 'float', 'value': self.maximum, 'object': self },
                         {'name': 'digits', 'type': 'int', 'value': self.digits, 'object': self, 'tip': 'significant digits'} ]

calibrationDict = { PowerDetectorCalibration.name: PowerDetectorCalibration }