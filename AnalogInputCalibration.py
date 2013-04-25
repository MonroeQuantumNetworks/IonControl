# -*- coding: utf-8 -*-
"""
Created on Thu Mar 14 09:26:25 2013

@author: wolverine
"""


import magnitude

referenceVoltage = 3.33

class AnalogInputCalibration:
    def __init__(self,name="default"):
        self.name = name
    
    def convert(self, binary):
        if binary is None:
            return None
        converted = binary * referenceVoltage / 0x3fffff
        return converted
        
    def convertMagnitude(self, binary):
        if binary is None:
            return None
        return magnitude.mg( binary * referenceVoltage / 0x3fffff, 'V')
        
    def paramDef(self):
        """
        return the parameter definition used by pyqtgraph parametertree to show the gui
        """
        return [{'name': 'name', 'type': 'str', 'value': "default"}]
        
    def update(self,param, changes):
        """
        update the parameter, called by the signal of pyqtgraph parametertree
        """
        for param, change, data in changes:
            print self, "update", param.name(), data
            setattr( self, param.name(), data)

        
class PowerDetectorCalibration(AnalogInputCalibration):
    """
        data is being fitted to p*x**2 + m*x + c 
        is valid between minimum and maximum input voltage
    """
    def __init__(self, name="default"):
        AnalogInputCalibration.__init__(self,name)
        self.m = -36.47
        self.c = 60.7152
        self.p = -1.79545
        self.minimum = 0.6
        self.maximum = 2        
        
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
        
    def paramDef(self):
        superior = AnalogInputCalibration.paramDef(self)
        superior.append([{'name': 'function', 'type': 'str', 'value': "dBm = p*V^2 + m*V + c",'readonly':True},
                         {'name': 'p', 'type': 'float', 'value': self.p },
                         {'name': 'm', 'type': 'float', 'value': self.m },
                         {'name': 'c', 'type': 'float', 'value': self.c }])
        return superior
        
class PowerDetectorCalibrationTwo(PowerDetectorCalibration):
    """
        Temporary fix until the parameters can be changed from the gui
    """
    def __init__(self, name="default"):
        PowerDetectorCalibration.__init__(self,name)
        self.m = -58.3
        self.c = 62.28
        self.p = 9.26
        self.minimum = 0.57
        self.maximum = 2.0       
        
        
AnalogInputCalibrationMap = { 'Voltage': AnalogInputCalibration,
                              'Rf power detector': PowerDetectorCalibration }