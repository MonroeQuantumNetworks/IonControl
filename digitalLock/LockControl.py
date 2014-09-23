import PyQt4.uic
from PyQt4 import QtCore

import logging
from modules.magnitude import mg
from modules.enum import enum

from controller.ControllerClient import freqToBin, voltageToBin, voltageToBinExternal

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
        self.errorsigHarmonic = mg(1)
        self.offset = mg(0,'V')
        self.pCoefficient = mg(0)
        self.iCoefficient = mg(0)
        self.errorsigFrequencyShift = mg(0,'Hz')
        self.resonanceFrequency = mg(12642.817,'MHz')
        self.filter = LockControl.FilterOptions.NoFilter
        self.harmonicOutput = LockControl.HarmonicOutputOptions.Off
        self.mode = 0
        self.dcThreshold = mg(0,'V')
        self.enableDCThreshold = False
        self.coreMode = 0
        
    def __setstate__(self, d):
        self.__dict__ = d
        self.__dict__.setdefault( 'enableLowPass', False )
        self.__dict__.setdefault( 'mode', 0 )
        self.__dict__.setdefault( 'filter', LockControl.FilterOptions.NoFilter )
        self.__dict__.setdefault( 'harmonicOutput', LockControl.HarmonicOutputOptions.Off )
        self.__dict__.setdefault( 'resonanceFrequency', mg(12642.817,'MHz') )
        self.__dict__.setdefault( 'errorsigFrequencyShift', mg(0,'MHz') )
        self.__dict__.setdefault( 'dcThreshold', mg(0,'V') )
        self.__dict__.setdefault( 'enableDCThreshold', False )
        self.__dict__.setdefault( 'coreMode', 0 )
        self.__dict__.setdefault( 'errorsigHarmonic', mg(1) )
        self.mode = self.mode & (~1)  # clear the lock enable bit
        

class LockControl(Form, Base):
    dataChanged = QtCore.pyqtSignal( object )
    AutoStates = enum('idle', 'autoOffset', 'autoLock')
    FilterOptions = enum('NoFilter','Lowp_50_29','Lowp_40_29','Low_30_20','Lowp_100_29', 'Lowp_200_29', 'Lowp_300_29', 'Lowp_300_13', 'Lowp_200_9', 'Lowp100_17')
    HarmonicOutputOptions = enum('Off','On','External')
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
        self.setupSpinBox('magErrorsigHarmonic', 'errorsigHarmonic', self.setErrorsigHarmonic, '')
        self.setupSpinBox('magFrequencyShift', 'errorsigFrequencyShift', self.setErrorsigFrequencyShift, 'MHz')
        self.setupSpinBox('magOffset', 'offset', self.setOffset, 'V')
        self.setupSpinBox('magPCoeff', 'pCoefficient', self.setpCoefficient, '')
        self.setupSpinBox('magICoeff', 'iCoefficient', self.setiCoefficient, '')
        self.setupSpinBox('magResonanceFreq', 'resonanceFrequency', self.setResonanceFreq, 'MHz')
        self.setupSpinBox('magDCThreshold', 'dcThreshold', self.onDCThreshold, 'V')
        
        self.filterCombo.addItems( self.FilterOptions.mapping.keys() )
        self.filterCombo.setCurrentIndex( self.lockSettings.filter )
        self.filterCombo.currentIndexChanged[int].connect( self.onFilterChange )
        self.harmonicOutputCombo.addItems( self.HarmonicOutputOptions.mapping.keys() )
        self.harmonicOutputCombo.setCurrentIndex( self.lockSettings.harmonicOutput )
        self.harmonicOutputCombo.currentIndexChanged[int].connect( self.onHarmonicOutputChange )
        self.autoLockButton.clicked.connect( self.onAutoLock )
        self.lockButton.clicked.connect( self.onLock )
        self.unlockButton.clicked.connect( self.onUnlock )
        self.dataChanged.emit( self.lockSettings )
        self.dcThresholdBox.setChecked( self.lockSettings.enableDCThreshold )
        self.dcThresholdBox.stateChanged.connect( self.onDCThresholdEnable )
        self._setHarmonics()
                
    def setErrorsigFrequencyShift(self, value):
        self.lockSettings.errorsigFrequencyShift = value
        self.calculateOffset()
                      
    def onDCThresholdEnable(self, state):
        self.lockSettings.enableDCThreshold = state == QtCore.Qt.Checked
        self.onDCThreshold(self.lockSettings.dcThreshold)
        
    def onDCThreshold(self, value):
        binvalue = voltageToBinExternal(value) if self.lockSettings.enableDCThreshold else 0
        self.controller.setDCThreshold( binvalue )
        self.lockSettings.dcThreshold = value
        self.dataChanged.emit( self.lockSettings )
        
    def onFilterChange(self, filterMode):
        self.lockSettings.filter = filterMode
        self.lockSettings.mode = setBit( self.lockSettings.mode, 1, self.lockSettings.filter>0 )
        self.controller.setFilter( self.lockSettings.filter )
        self.controller.setMode(self.lockSettings.mode)
        self.dataChanged.emit(self.lockSettings )
        
    def onHarmonicOutputChange(self, outputMode ):
        self.lockSettings.harmonicOutput = outputMode
        self.lockSettings.mode = setBit( self.lockSettings.mode, 14, outputMode==1 )
        self.lockSettings.mode = setBit( self.lockSettings.mode, 15, outputMode==2 )
        self.controller.setMode(self.lockSettings.mode)
        self.dataChanged.emit(self.lockSettings )
        
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
        self.calculateOffset()

    def setResonanceFreq(self, value):
        self.lockSettings.resonanceFrequency = value
        self.calculateOffset()
        
    def calculateOffset(self):
        offsetFrequency = abs( self.lockSettings.resonanceFrequency - abs( self.lockSettings.harmonic ) / self.lockSettings.errorsigHarmonic * 
                               (self.lockSettings.referenceFrequency + self.lockSettings.errorsigFrequencyShift )  + 
                               (-1 if self.lockSettings.harmonic<0 else 1) * self.lockSettings.outputFrequency )
        self.magOffsetFreq.setValue(offsetFrequency)

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
        self.calculateOffset()

    def setOutputAmplitude(self, value):
        binvalue = int(value.toval(''))
        self.controller.setOutputAmplitude(binvalue)
        self.lockSettings.outputAmplitude = value
        self.dataChanged.emit( self.lockSettings )

    def setHarmonic(self, value):
        self.lockSettings.harmonic = int(value.toval(''))
        self._setHarmonics()
        
    def setErrorsigHarmonic(self, value):
        self.lockSettings.errorsigHarmonic = int(value.toval(''))
        self._setHarmonics()
        
    def _setHarmonics(self):
        self.controller.setHarmonic(self.lockSettings.harmonic)
        self.controller.setFixedPointHarmonic( int( self.lockSettings.harmonic*( (1<<56)/float(self.lockSettings.errorsigHarmonic)))  )
        self.lockSettings.coreMode = 0 if self.lockSettings.errorsigHarmonic==1 else 1
        self.controller.setCoreMode( self.lockSettings.coreMode )
        self.dataChanged.emit( self.lockSettings )
        self.calculateOffset()
        
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
        
