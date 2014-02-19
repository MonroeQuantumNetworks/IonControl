import PyQt4.uic
from PyQt4 import QtGui, QtCore, QtSvg

from functools import partial
import logging
from modules.magnitude import mg

from controller.ControllerClient import freqToBin, voltageToBin 

Form, Base = PyQt4.uic.loadUiType(r'digitalLock\ui\LockControl.ui')


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
        

class LockControl(Form, Base):
    dataChanged = QtCore.pyqtSignal( object )
    def __init__(self,controller,config,parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        self.controller = controller
        self.config = config
        self.lockSettings = self.config.get("LockSettings",LockSettings())
    
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
        self.autoLockButton.clicked.connect( self.onAutoLock )
        self.lockButton.clicked.connect( self.onLock )
        self.unlockButton.clicked.connect( self.onUnlock )
        
    def onLock(self):
        pass
    
    def onUnlock(self):
        pass
    
    def onAutoLock(self):
        pass
        
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
