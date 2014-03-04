import PyQt4.uic

from PyQt4 import QtCore
from digitalLock.controller.ControllerClient import voltageToBin, binToVoltageV, sampleTime, binToFreqHz
from modules.magnitude import mg
from modules.enum import enum
import numpy
from trace.Trace import Trace
from trace.PlottedTrace import PlottedTrace

Form, Base = PyQt4.uic.loadUiType(r'digitalLock\ui\TraceControl.ui')

class TraceSettings:
    def __init__(self):
        self.samples = mg(2000,'')
        self.subsample = mg(0,'')
        self.triggerLevel = mg(0,'V')
        self.triggerMode = 0
        self.frequencyPlot = None
        self.errorSigPlot = None

    def __setstate__(self, s):
        self.__dict__ = s
        self.__dict__.setdefault( 'frequencyPlot', None )
        self.__dict__.setdefault( 'errorSigPlot', None )

class TraceControl(Form, Base):
    StateOptions = enum('stopped','running','single')
    newDataAvailable = QtCore.pyqtSignal( object )
    def __init__(self,controller,config,traceui,plotDict,parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        self.controller = controller
        self.config = config
        self.traceSettings = self.config.get("TraceControl.Settings",TraceSettings())
        self.state = self.StateOptions.stopped
        self.traceui = traceui
        self.plotDict = plotDict
        self.controller.scopeDataAvailable.connect( self.onData )
        self.errorSigTrace = None
        self.freqTrace = None
        self.errorSigCurve = None
        self.freqCurve = None
        self.lockSettings = None
    
    def setupSpinBox(self, localname, settingsname, updatefunc, unit ):
        box = getattr(self, localname)
        value = getattr(self.traceSettings, settingsname)
        box.setValue( value )
        box.dimension = unit
        box.valueChanged.connect( updatefunc )
        updatefunc( value )
    
    def setupUi(self):
        Form.setupUi(self,self)
        self.setupSpinBox('magNumberSamples', 'samples', self.setSamples, '')
        self.setupSpinBox('magSubsample', 'subsample', self.setSubSample, '')
        self.setupSpinBox('magTriggerLevel', 'triggerLevel', self.setTriggerLevel, 'V')
        self.comboTriggerMode.currentIndexChanged[int].connect( self.setTriggerMode )
        self.comboTriggerMode.setCurrentIndex( self.traceSettings.triggerMode )
        self.runButton.clicked.connect( self.onRun )
        self.singleButton.clicked.connect( self.onSingle )
        self.stopButton.clicked.connect(self.onStop)
        self.addTraceButton.clicked.connect( self.onAddTrace )
        self.frequencyPlotCombo.addItems( self.plotDict.keys() )
        self.errorSigPlotCombo.addItems( self.plotDict.keys() )
        if self.traceSettings.frequencyPlot is not None and self.traceSettings.frequencyPlot in  self.plotDict:
            self.frequencyPlotCombo.setCurrentIndex( self.frequencyPlotCombo.findText(self.traceSettings.frequencyPlot))
        else:   
            self.traceSettings.frequencyPlot = str( self.frequencyPlotCombo.currentText() )
        if self.traceSettings.errorSigPlot is not None and self.traceSettings.errorSigPlot in  self.plotDict:
            self.errorSigPlotCombo.setCurrentIndex( self.errorSigPlotCombo.findText(self.traceSettings.errorSigPlot))
        else:   
            self.traceSettings.frequencyPlot = str( self.errorSigPlotCombo.currentText() )
        self.frequencyPlotCombo.currentIndexChanged[QtCore.QString].connect( self.onChangeFrequencyPlot )
        self.errorSigPlotCombo.currentIndexChanged[QtCore.QString].connect( self.onChangeErrorSigPlot )
        
    def onChangeFrequencyPlot(self, name):
        name = str(name)
        if name!=self.traceSettings.frequencyPlot and name in self.plotDict:
            self.traceSettings.frequencyPlot = name
            if self.freqCurve is not None:
                self.freqCurve.setView( self.plotDict[name])                      
    
    def onChangeErrorSigPlot(self, name):
        name = str(name)
        if name!=self.traceSettings.errorSigPlot and name in self.plotDict:
            self.traceSettings.errorSigPlot = name
            if self.errorSigCurve is not None:
                self.errorSigCurve.setView( self.plotDict[name])
        
    def onControlChanged(self, value):
        self.lockSettings = value
    
    def setState(self, state):
        self.state = state
        self.statusLabel.setText( self.StateOptions.reverse_mapping[self.state] )

    def onData(self, data):
        if data.errorSig:
            errorSig = map( binToVoltageV, data.errorSig )
            if self.errorSigTrace is None:
                self.errorSigTrace = Trace()
            self.errorSigTrace.x = numpy.arange(len(errorSig))*(sampleTime.toval('us')*(1+self.traceSettings.subsample.toval()))
            self.errorSigTrace.y = numpy.array( errorSig )
            if self.errorSigCurve is None:
                self.errorSigCurve = PlottedTrace(self.errorSigTrace, self.plotDict[self.traceSettings.errorSigPlot]['view'], pen=-1, style=PlottedTrace.Styles.lines, name="Error Signal")  #@UndefinedVariable 
                self.errorSigCurve.plot()
                self.traceui.addTrace( self.errorSigCurve, pen=-1 )
            else:
                self.errorSigCurve.replot()                
            self.newDataAvailable.emit( self.errorSigTrace )                          
        if data.frequency:
            frequency = map( binToFreqHz, data.frequency )
            if self.freqTrace is None:
                self.freqTrace = Trace()
            self.freqTrace.x = numpy.arange(len(frequency))*(sampleTime.toval('us')*(1+self.traceSettings.subsample.toval()))
            self.freqTrace.y = numpy.array( frequency )
            if self.freqCurve is None:
                self.freqCurve = PlottedTrace(self.freqTrace, self.plotDict[self.traceSettings.frequencyPlot]['view'], pen=-1, style=PlottedTrace.Styles.lines, name="Frequency")  #@UndefinedVariable 
                self.freqCurve.plot()
                self.traceui.addTrace( self.freqCurve, pen=-1 )
            else:
                self.freqCurve.replot() 
        if self.state==self.StateOptions.running:
            self.controller.armScope()
        else:
            self.setState(self.StateOptions.stopped)         

    def onAddTrace(self):
        if self.errorSigCurve:
            self.errorSigCurve = None
            self.errorSigTrace = None
        if self.freqCurve:
            self.freqCurve = None
            self.errorSigTrace = None

    def onRun(self):
        self.controller.armScope()
        self.setState(self.StateOptions.running)
    
    def onStop(self):
        self.setState( self.StateOptions.stopped)
    
    def onSingle(self):
        self.controller.armScope()
        self.setState( self.StateOptions.single )

    def setTriggerMode(self, mode):
        self.traceSettings.triggerMode = mode
        self.controller.setTriggerMode(mode)
    
    def setTriggerLevel(self, value):
        self.traceSettings.triggerLevel = value
        self.controller.setTriggerLevel( voltageToBin(value) )
    
    def setSamples(self, samples):
        self.traceSettings.samples = samples
        self.controller.setSamples(int(samples.toval()))
    
    def setSubSample(self, subsample):
        self.traceSettings.subsample = subsample
        self.controller.setSubSample(int(subsample.toval()))
    
         
    def saveConfig(self):
        self.config["TraceControl.Settings"] = self.traceSettings
