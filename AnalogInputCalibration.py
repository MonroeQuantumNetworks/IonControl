# -*- coding: utf-8 -*-
"""
Created on Thu Mar 14 09:26:25 2013

@author: wolverine
"""


import magnitude

referenceVoltage = 3.33

class AnalogInputCalibration:
    def __init__(self):
        pass
    
    def convert(self, binary):
        if binary is None:
            return None
        converted = binary * referenceVoltage / 0x3fffff
        return converted
        
    def convertMagnitude(self, binary):
        if binary is None:
            return None
        return magnitude.mg( binary * referenceVoltage / 0x3fffff, 'V')
        
class PowerDetectorCalibration:
    """
        data is being fitted to p*x**2 + m*x + c 
        is valid between minimum and maximum input voltage
    """
    def __init__(self, m, c, p, minimum, maximum):
        self.m = m
        self.c = c
        self.p = p
        self.minimum = minimum
        self.maximum = maximum        
        
    def convert(self, binary):
        if binary is None:
            return None
        volt = binary * referenceVoltage / 0x3fffff
        if volt < self.minimum or volt > self.maximum:
            return "oor"
        dBm = self.p * volt**2 + self.m*volt + self.c
        return dBm
        
    def convertMagnitude(self, binary):
        if binary is None:
            return None
        volt = binary * referenceVoltage / 0x3fffff
        if volt < self.minimum or volt > self.maximum:
            return "oor"
        dBm = self.p * volt**2 + self.m*volt + self.c
        return magnitude.mg( 10**((dBm/10)-3), 'W' )
        