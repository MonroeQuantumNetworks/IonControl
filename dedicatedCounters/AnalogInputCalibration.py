# -*- coding: utf-8 -*-
"""
Created on Thu Mar 14 09:26:25 2013

@author: wolverine
Analog Input calibrations
to create a new calibration derive a new class from AnalogInputCalibration,
overwrite the necessary functions and add the new class to AnalogInputCalibrationMap
"""


import modules.magnitude as magnitude


referenceVoltage = 3.33

class Parameters:
    pass

class AnalogInputCalibration(object):
    def __init__(self,name="default"):
        self.name = name
        self.parameters = Parameters()
    
    def convert(self, binary):
        """convert the binary representation from the ADC chip to voltage
        """
        if binary is None:
            return None
        count = binary >> 32             # extract Number fo samples in FPGA code after 8/28/2015
        binary = binary & 0xffffffff     # remove the counter bits 
        if count>0:
            converted = float(binary * referenceVoltage / 0x3fffff) / count
        else:
            converted = float(binary * referenceVoltage / 0x3fffffff)             
        return converted
        
    def convertMagnitude(self, binary):
        """convert the binary representation from the ADC chip to a magnitude object
        """
        if binary is None:
            return None
        return magnitude.mg( self.convert(binary), 'V')
        
    def paramDef(self):
        """
        return the parameter definition used by pyqtgraph parametertree to show the gui
        """
        return []
        
    def update(self,param, changes):
        """
        update the parameter, called by the signal of pyqtgraph parametertree
        """
        for param, _, data in changes:
            setattr( self.parameters, param.name(), data)

class AnalogInputCalibrationAD7608(AnalogInputCalibration):
    referenceVoltage = 5.0
    def __init__(self,name="AD7608"):
        super(AnalogInputCalibrationAD7608, self).__init__(name)
    
    def convert(self, binary):
        """convert the binary representation from the ADC chip to voltage
        """
        if binary is None:
            return None
        count = binary >> 32             # extract Number fo samples in FPGA code after 8/28/2015
        binary = binary & 0xffffffff     # remove the counter bits 
        if binary & 0x80000000:
            numeric = -0x80000000 + (binary&0x7fffffff)
        else:
            numeric = binary
        if count>0:
            converted = numeric * self.referenceVoltage / 0x8000 / count
        else:
            converted = numeric * self.referenceVoltage / 0x800000
        return converted
        
    def convertMagnitude(self, binary):
        """convert the binary representation from the ADC chip to a magnitude object
        """
        if binary is None:
            return None
        return magnitude.mg( self.convert(binary), 'V')
        

        
class PowerDetectorCalibration(AnalogInputCalibration):
    """
        data is being fitted to p*x**2 + m*x + c 
        is valid between minimum and maximum input voltage
    """
    def __init__(self, name="default"):
        AnalogInputCalibration.__init__(self,name)
        self.parameters = Parameters()
        self.parameters.m = -36.47
        self.parameters.c = 60.7152
        self.parameters.p = -1.79545
        self.parameters.minimum = 0.6
        self.parameters.maximum = 2        
        
    def convert(self, binary):
        if binary is None:
            return None
        count = binary >> 32             # extract Number fo samples in FPGA code after 8/28/2015
        binary = binary & 0xffffffff     # remove the counter bits 
        if count>0:
            volt = binary * referenceVoltage / 0x3fff / count
        else:
            volt = binary * referenceVoltage / 0x3fffff 
        if volt < self.parameters.minimum or volt > self.parameters.maximum:
            return float('nan')
        dBm = self.parameters.p * volt**2 + self.parameters.m*volt + self.parameters.c
        return dBm
        
    def convertMagnitude(self, binary):
        if binary is None:
            return None
        dBm = self.convert(binary)
        return magnitude.mg( 10**((dBm/10)-3), 'W' )
        
    def paramDef(self):
        return [{'name': 'function', 'type': 'str', 'value': "dBm = p*V^2 + m*V + c",'readonly':True},
                         {'name': 'p', 'type': 'float', 'value': self.parameters.p },
                         {'name': 'm', 'type': 'float', 'value': self.parameters.m },
                         {'name': 'c', 'type': 'float', 'value': self.parameters.c },
                         {'name': 'min', 'type': 'float', 'value': self.parameters.minimum},
                         {'name': 'max', 'type': 'float', 'value': self.parameters.maximum}]

class PowerDetectorCalibrationAD7608(AnalogInputCalibration):
    """
        data is being fitted to p*x**2 + m*x + c 
        is valid between minimum and maximum input voltage
    """
    referenceVoltage = 5.0
    def __init__(self, name="default"):
        AnalogInputCalibration.__init__(self,name)
        self.parameters = Parameters()
        self.parameters.m = -36.47
        self.parameters.c = 60.7152
        self.parameters.p = -1.79545
        self.parameters.minimum = 0.6
        self.parameters.maximum = 2        
        
    def convert(self, binary):
        if binary is None:
            return None
        count = binary >> 32             # extract Number fo samples in FPGA code after 8/28/2015
        binary = binary & 0xffffffff     # remove the counter bits 
        if binary & 0x80000000:
            numeric = -0x80000000 + (binary&0x7fffffff)
        else:
            numeric = binary
        if count>0:
            volt = numeric * self.referenceVoltage / 0x8000 / count
        else:
            volt = numeric * self.referenceVoltage / 0x800000
        if volt < self.parameters.minimum or volt > self.parameters.maximum:
            return float('nan')
        dBm = self.parameters.p * volt**2 + self.parameters.m*volt + self.parameters.c
        return dBm
        
    def convertMagnitude(self, binary):
        if binary is None:
            return None
        dBm = self.convert(binary)
        return magnitude.mg( 10**((dBm/10)-3), 'W' )
        
    def paramDef(self):
        return [{'name': 'function', 'type': 'str', 'value': "dBm = p*V^2 + m*V + c",'readonly':True},
                         {'name': 'p', 'type': 'float', 'value': self.parameters.p },
                         {'name': 'm', 'type': 'float', 'value': self.parameters.m },
                         {'name': 'c', 'type': 'float', 'value': self.parameters.c },
                         {'name': 'min', 'type': 'float', 'value': self.parameters.minimum},
                         {'name': 'max', 'type': 'float', 'value': self.parameters.maximum}]
         
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
                              'Rf power detector': PowerDetectorCalibration,
                              'AD7608 Voltage': AnalogInputCalibrationAD7608,
                              'Rf power detector AD7608': PowerDetectorCalibrationAD7608 }