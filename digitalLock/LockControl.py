import PyQt4.uic
from PyQt4 import QtCore

import logging
from modules.magnitude import mg
from modules.enum import enum

from controller.ControllerClient import freqToBin, voltageToBin 

Form, Base = PyQt4.uic.loadUiType(r'digitalLock\ui\LockControl.ui')


def setBit( var, index, val ):
    """Set the index:th bit of v to x, and return the new value."""
    mask = 1 << index
    var &= ~mask
    if val:
        var |= mask
    return var    

class LockSettings(object):
    def __init__(self):
        self.referenceFrequency = mg(0,'MHz')
        self.referenceAmplitude = mg(0)
        self.outputFrequency = mg(0,'MHz')
        self.outputAmplitude = mg(0)
        self.harmonic = mg(107)
        self.offset = mg(0,'V')
        self.pCoefficient = mg(0)
        self.iCoefficient = mg(0)
        self.filter = LockControl.FilterOptions.NoFilter
        self.mode = 0
        
    def __setstate__(self, d):
        self.__dict__ = d
        self.__dict__.setdefault( 'enableLowPass', False )
        self.__dict__.setdefault( 'mode', 0 )
        self.__dict__.setdefault( 'filter', LockControl.FilterOptions.NoFilter )
        

class LockControl(Form, Base):
    dataChanged = QtCore.pyqtSignal( object )
    AutoStates = enum('idle', 'autoOffset', 'autoLock')
    FilterOptions = enum('NoFilter','Lowp_50_29','Lowp_40_29','Low_30_20','Lowp_100_29', 'Lowp_200_29', 'Lowp_300_29', 'Lowp_300_13', 'Lowp_200_9', 'Lowp100_17')
    def __init__(self,controller,config,parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        self.controller = controller
        self.config = config
        self.lockSettings = self.config.get("LockSettings",LockSettings())
        self.autoState = self.AutoStates.idle
    
    def setupSpinBox(self, localname, settingsname, updatefunc, unit ):
        box = getattr(self, localname)
        value = getattr(self.lockSettings, settingsname)
        box.setValue( value )
        box.dimension = unit
        box.valueChanged.connect( updatefunc )
        updatefunc( value )
    
    def setupUi(self):
        Form.setupUi(self,self)
        self.setupSpinBox('magReferenceFreq', 'referenceFrequency', self.setReferenceFrequency, 'MHz')
        self.setupSpinBox('magReferenceAmpl', 'referenceAmplitude', self.setReferenceAmplitude, '')
        self.setupSpinBox('magOutputFreq', 'outputFrequency', self.setOutputFrequency, 'MHz')
        self.setupSpinBox('magOutputAmpl', 'outputAmplitude', self.setOutputAmplitude, '')
        self.setupSpinBox('magHarmonic', 'harmonic', self.setHarmonic, '')
        self.setupSpinBox('magOffset', 'offset', self.setOffset, 'V')
        self.setupSpinBox('magPCoeff', 'pCoefficient', self.setpCoefficient, '')
        self.setupSpinBox('magICoeff', 'iCoefficient', self.setiCoefficient, '')
        self.filterCombo.addItems( self.FilterOptions.mapping.keys() )
        self.filterCombo.setCurrentIndex( self.lockSettings.filter )
        self.filterCombo.currentIndexChanged[int].connect( self.onFilterChange )
        self.autoLockButton.clicked.connect( self.onAutoLock )
        self.lockButton.clicked.connect( self.onLock )
        self.unlockButton.clicked.connect( self.onUnlock )
        self.dataChanged.emit( self.lockSettings )
        
    def onFilterChange(self, filterMode):
        self.lockSettings.filter = filterMode
        self.lockSettings.mode = setBit( self.lockSettings.mode, 1, self.lockSettings.filter>0 )
        self.controller.setFilter( self.lockSettings.filter )
        self.controller.setMode(self.lockSettings.mode)
        
    def onLock(self):
        self.lockSettings.mode = setBit( self.lockSettings.mode, 0, True)
        self.controller.setMode(self.lockSettings.mode)
    
    def onUnlock(self):
        self.lockSettings.mode = setBit( self.lockSettings.mode, 0, False)
        self.controller.setMode(self.lockSettings.mode)
    
    def onAutoLock(self):
        self.autoOffset()
        
    def setReferenceFrequency(self, value):
        binvalue = freqToBin(value)
        self.controller.setReferenceFrequency(binvalue)
        self.lockSettings.referenceFrequency = value
        self.dataChanged.emit( self.lockSettings )

    def setReferenceAmplitude(self, value):
        binvalue = int(value.toval(''))
        self.controller.setReferenceAmplitude(binvalue)
        self.lockSettings.referenceAmplitude = value
        self.dataChanged.emit( self.lockSettings )
        
    def setOutputFrequency(self, value):
        binvalue = freqToBin(value)
        self.controller.setOutputFrequency(binvalue)
        self.lockSettings.outputFrequency = value
        self.dataChanged.emit( self.lockSettings )

    def setOutputAmplitude(self, value):
        binvalue = int(value.toval(''))
        self.controller.setOutputAmplitude(binvalue)
        self.lockSettings.outputAmplitude = value
        self.dataChanged.emit( self.lockSettings )

    def setHarmonic(self, value):
        binvalue = int(value.toval(''))
        self.controller.setHarmonic(binvalue)
        self.lockSettings.hamonic = value
        self.dataChanged.emit( self.lockSettings )
        
    def setOffset(self, value):
        binvalue = voltageToBin(value)
        self.controller.setInputOffset(binvalue)
        logging.getLogger(__name__).debug("offset {0} binary {1:x}".format(value,binvalue))
        self.lockSettings.offset = value
        self.dataChanged.emit( self.lockSettings )
        
    def setpCoefficient(self, pCoeff):       
        binvalue = int(pCoeff.toval(''))
        self.controller.setpCoeff(binvalue)
        self.lockSettings.pCoefficient = pCoeff
        self.dataChanged.emit( self.lockSettings )

    def setiCoefficient(self, iCoeff):       
        binvalue = int(iCoeff.toval(''))
        self.controller.setiCoeff(binvalue)
        self.lockSettings.iCoefficient = iCoeff
        self.dataChanged.emit( self.lockSettings )

    def saveConfig(self):
        self.config["LockSettings"] = self.lockSettings
        
    def onTraceData(self , data):
        pass
    
    def onStreamData(self, data):
        if self.autoState == self.AutoStates.autoOffset:
            newOffset = (data.errorSigMax + data.errorSigMin)/2 + self.lockSettings.offset
            self.magOffset.setValue( newOffset )
            self.setOffset(newOffset)
            self.autoState = self.AutoStates.idle
    
    def autoOffset(self):
        if self.autoState == self.AutoStates.idle:
            self.autoState = self.AutoStates.autoOffset
        
