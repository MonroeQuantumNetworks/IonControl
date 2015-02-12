'''
Created on Feb 12, 2015

@author: wolverine
'''

import ctypes
from externalParameter.ExternalParameterBase import ExternalParameterBase
from modules import magnitude
import logging

HWTYPE_BSC001   =     11    #// 1 Ch benchtop stepper driver
HWTYPE_BSC101   =     12    #// 1 Ch benchtop stepper driver
HWTYPE_BSC002   =     13    #// 2 Ch benchtop stepper driver
HWTYPE_BDC101   =     14    #// 1 Ch benchtop DC servo driver
HWTYPE_SCC001   =     21    #// 1 Ch stepper driver card (used within BSC102,103 units)
HWTYPE_DCC001   =     22    #// 1 Ch DC servo driver card (used within BDC102,103 units)
HWTYPE_ODC001   =     24    #// 1 Ch DC servo driver cube
HWTYPE_OST001   =     25    #// 1 Ch stepper driver cube
HWTYPE_MST601   =     26    #// 2 Ch modular stepper driver module
HWTYPE_TST001   =     29    #// 1 Ch Stepper driver T-Cube
HWTYPE_TDC001   =     31    #// 1 Ch DC servo driver T-Cube
HWTYPE_LTSXXX   =     42    #// LTS300/LTS150 Long Travel Integrated Driver/Stages
HWTYPE_L490MZ   =     43    #// L490MZ Integrated Driver/Labjack
HWTYPE_BBD10X   =     44    #// 1/2/3 Ch benchtop brushless DC servo driver

APTDll = ctypes.WinDLL("dll/APT.dll")

class APTException(Exception):
    pass

class APTInstrument(object):
    def open(self, instrument, HWType=HWTYPE_TDC001):
        if APTDll.APTInit()!=0:
            raise APTException("APT Dll initialization failed")
        plNumUnits = ctypes.c_long()       
        if APTDll.GetNumHWUnitsEx( HWType, ctypes.byref(plNumUnits)) !=0 or plNumUnits.value==0:
            raise APTException("APT No Hardware devices found")
        self.plSerialNumber = ctypes.c_long()
        APTDll.GetHWSerialNumEx( HWTYPE_TDC001, 0, ctypes.byref(self.plSerialNumber))
        logging.getLogger(__name__).info("Found APT device serial number {0}".format(self.plSerialNumber.value))
        if APTDll.InitHWDevice( self.plSerialNumber )!=0:
            raise APTException("Device initialization failed serial number {0}".format(self.plSerialNumber.value))
        self._minpos = ctypes.c_float()
        self._maxpos = ctypes.c_float()
        self._pitch = ctypes.c_float()
        self._units = ctypes.c_long()
        APTDll.MOT_GetStageAxisInfo( self.plSerialNumber, ctypes.byref(self._minpos), ctypes.byref(self._maxpos), ctypes.byref(self._units), ctypes.byref(self._pitch) )
        logging.getLogger(__name__).info("APT min {0} max{1} units {2} pitch {3}".format(self._minpos.value, self._maxpos.value, self._units.value, self._pitch.value))
    
    def homeSearch(self):
        pass
    
    @property
    def minPos(self):
        return self._minpos.value
    
    @property
    def maxPos(self):
        return self._maxpos.value
    
    @property
    def position(self):
        pos = ctypes.c_float()
        APTDll.MOT_GetPosition(self.plSerialNumber, ctypes.byref(pos))
        return pos.value
    
    @position.setter
    def position(self, pos):
        wait = ctypes.c_bool(False)
        pos = ctypes.c_float(pos)
        if APTDll.MOT_MoveAbsoluteEx(self.plSerialNumber, pos, wait)!=0:
            raise APTException( "Error setting position")
    
    def motionRunning(self):
        status = ctypes.c_long()
        APTDll.MOT_GetStatusBits(self.plSerialNumber, ctypes.byref(status))
        return bool(status.value & 0x30) 
    
    def close(self):
        APTDll.APTCleanUp()
    

class APTRotation(ExternalParameterBase):
    """
    Adjust the current on the N6700B current supply
    """
    className = "APT Rotation"
    _dimension = magnitude.mg(1,'')
    def __init__(self,name,config,instrument="COM3"):
        logger = logging.getLogger(__name__)
        ExternalParameterBase.__init__(self,name,config)
        logger.info( "trying to open '{0}'".format(instrument) )
        self.instrument = APTInstrument() #open visa session
        self.instrument.open(instrument)
        self.instrument.homeSearch()
        logger.info( "opened {0}".format(instrument) )
        self.setDefaults()
        self.settings.value[None] = self._getValue(None)
        self.lastValue = None
        if self.settings.limit > self.instrument.maxPos:
            self.settings.limit = magnitude.mg(self.instrument.maxPos,'')

    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
        self.settings.__dict__.setdefault('limit' , magnitude.mg(360,''))       # if True go to the target value in one jump
        self.settings.__dict__.setdefault('belowMargin' , magnitude.mg(0,''))       # if True go to the target value in one jump
            
    def _setValue(self, channel, v):
        if v>self.settings.limit:
            v = self.setting.limit
        self.instrument.position = v.toval()
        self.settings.value[channel] = v
        
    def _getValue(self, channel):
        self.settings.value[channel] = magnitude.mg(self.instrument.position) #set voltage
        return self.settings.value[channel]
        
    def currentValue(self, channel):
        return self.settings.value[channel]
    
    def currentExternalValue(self, channel):
        self.settings.value[channel] = magnitude.mg(self.instrument.position) #set voltage
        return self.settings.value[channel]

    def paramDef(self):
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'limit', 'type': 'magnitude', 'value': self.settings.limit})
        superior.append({'name': 'belowMargin','type': 'magnitude', 'value': self.settings.belowMargin, 'tip': 'if not zero: if coming from above always go that far below and then up'})
        return superior
    
    def close(self):
        self.instrument.close()
        del self.instrument

    def setValue(self, channel, value):
        self.displayValueObservable[channel].fire( value=self._getValue(channel) )
        if self.instrument.motionRunning():
            return False
        if value != self.settings.value[channel]:
            if self.lastValue is None or value < self.lastValue:
                self._setValue( channel, value-self.settings.belowMargin )
                self.lastValue = value-self.settings.belowMargin
                return False
            else:
                self._setValue( channel, value )
                self.lastValue = value
        arrived = not self.instrument.motionRunning()
        if arrived:
            self.persist(channel, self.settings.value[channel])
        return arrived
    
if __name__ == "__main__":
    a = APTRotation("APTRotation", dict(), "")
    print a.getValue(None)
    a.setValue(None, 10)
    print a.getValue(None)
    a.close()
    