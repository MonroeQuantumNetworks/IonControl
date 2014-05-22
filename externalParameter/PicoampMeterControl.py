'''
Created on May 21, 2014

@author: pmaunz
'''

from PyQt4 import QtCore, QtGui 
import PyQt4.uic
from modules.magnitude import mg
from functools import partial
from scan.ScanList import scanList

Form, Base = PyQt4.uic.loadUiType(r'ui\PicoampMeterControl.ui')

class MeterState:
    def __init__(self):
        self.zeroCheck = True
        self.voltageEnabled = False
        self.voltageRange = 10
        self.currentLimit = 25e-6
        self.voltage = 0
        self.autoRange = False
        self.instrument = ""
        self.start = mg(0,"V")
        self.stop = mg(10,"V")
        self.steps = mg(10)
        self.scanType = 0

class PicoampMeterControl(Base, Form):
    def __init__(self,config, traceui, plotdict, parent, meter):
        self.config = config
        self.traceui = traceui
        self.plotdict = plotdict
        self.parent = parent
        self.meter = meter
        super(PicoampMeterControl, self).__init__()
        self.meterState = self.config.get("PicoampMeterState", MeterState() )
            
    def setupUi(self, parent):
        super(PicoampMeterControl,self).setupUi(parent)
        self.instrumentEdit.setText( self.meterState.instrument )
        self.instrumentEdit.returnPressed.connect( self.openInstrument )
        self.enableMeasurementBox.setChecked( not self.meterState.zeroCheck )
        self.enableMeasurementBox.stateChanged.connect( self.onZeroCheck )
        self.autoRangeBox.setChecked( self.meterState.autoRange )
        self.autoRangeBox.stateChanged.connect( self.onAutoRange )
        self.voltageRangeSelect.setCurrentIndex( self.voltageRangeSelect.findText("{0}".format(self.meterState.voltageRange)))
        self.voltageRangeSelect.currentIndexChanged[int].connect( self.onVoltageRange )
        self.currentLimitSelect.setCurrentIndex( self.currentLimitSelect.findText("{0:.1e}".format(self.meterState.currentLimit)))
        self.currentLimitSelect.currentIndexChanged[int].connect( self.onCurrentLimit )
        self.enableOutputBox.setChecked(False)
        self.enableOutputBox.stateChanged.connect( self.onEnableOutput )
        self.voltageEdit.setValue( self.meterState.voltage )
        self.voltageEdit.valueChanged.connect( self.onVoltage )
        self.startEdit.setValue( self.meterState.start )
        self.startEdit.valueChanged.connect( partial( self.onValueChanged, 'start') )
        self.stopEdit.setValue( self.meterState.stop )
        self.startEdit.valueChanged.connect( partial( self.onValueChanged, 'stop') )
        self.stepsEdit.setValue( self.meterState.steps )
        self.startEdit.valueChanged.connect( partial( self.onValueChanged, 'steps') )
        self.zeroButton.clicked.connect( self.onZero )
        self.measureButton.clicked.connect( self.onMeasure )
        self.scanButton.clicked.connect( self.onScan )
        self.scanTypeCombo.setCurrentIndex( self.meterState.scanType )
        self.scanTypeCombo.currentIndexChanged[int].connect( partial(self.onValueChanged, 'scanType') )
        
    def onScan(self):
        self.startScan()
                
    def startScan(self):
        self.scanList = scanList(self.meterState.start, self.meterState.stop, self.meterState.steps,self.meterState.scanType)
        self.currentIndex = 0
        QtCore.QTimer.singleShot(0, self.initPoint )
    
    def initPoint(self):
        if self.currentIndex<len(self.scanList):
            self.meter.setVoltage( self.scanList[self.currentIndex] )
            QtCore.QTimer.singleShot(0, self.takeScanPoint )
        else:
            self.meter.setVoltage( self.meterState.voltage )
            self.finalizeScan()
    
    def takeScanPoint(self):
        value = float(self.meter.read())
        QtCore.QTimer.singleShot(0, self.initPoint )
    
    def finalizeScan(self):
        pass
        
    def onMeasure(self):
        value = float(self.meter.read())
        self.currentLabel.setText(str(value))
        
    def onZero(self):
        self.meter.zero()
        
    def onValueChanged(self, attr, value):
        setattr( self.meterState, attr, value )
        
    def onVoltage(self, value):
        raw = value.toval("V")
        self.meter.setVoltage(raw)
        
    def onEnableOutput(self, value):
        enable = value == QtCore.Qt.Checked
        self.meter.voltageEnable(enable)
        self.meterState.enableOutput = enable
        
    currentLimits = [2.5e-5, 2.5e-4, 2.5e-3, 2.5e-2]
    def onCurrentLimit(self, index):
        limit = self.currentLimits[index]
        self.meter.setCurrentLimit(limit)
        self.meterState.currentLimit = limit
        
    voltageRanges = [10,50,500]
    def onVoltageRange(self, index):
        vrange = self.voltageRanges[index]
        self.meter.setVoltageRange( vrange )
        self.meterState.voltageRange = vrange
        
    def onZeroCheck(self, value):
        enable = value != QtCore.Qt.Checked
        self.meter.setZeroCheck(enable)
        self.meterState.zeroCheck = enable

    def onAutoRange(self, value):
        enable = value == QtCore.Qt.Checked
        self.meter.setAutoRange(enable)
        self.meterState.autoRange = enable

    def openInstrument(self):
        self.meterState.instrument = str(self.instrumentEdit.text())
        self.meter.open( self.meterState.instrument )
 
    def saveConfig(self):
        self.config["PicoampMeterState"] = self.meterState
        
