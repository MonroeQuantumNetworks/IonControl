import PyQt4.uic

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

class TraceControl(Form, Base):
    StateOptions = enum('stopped','running','single')
    def __init__(self,controller,config,traceui,view,parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        self.controller = controller
        self.config = config
        self.traceSettings = TraceSettings()#self.config.get("TraceControl.Settings",TraceSettings())
        self.state = self.StateOptions.stopped
        self.traceui = traceui
        self.view = view
        self.controller.scopeDataAvailable.connect( self.onData )
        self.errorSigTrace = None
        self.freqTrace = None
        self.errorSigCurve = None
        self.freqCurve = None
    
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
        
    def onAddTrace(self):
        if self.errorSigCurve:
            self.traceui.addTrace( self.errorSigCurve )
            self.errorSigCurve = None
        if self.freqCurve:
            self.traceui.addTrace( self.freqCurve )
            self.freqCurve = None

    def setState(self, state):
        self.state = state
        self.statusLabel.setText( self.StateOptions.reverse_mapping[self.state] )

    def onData(self, data):
        if data.errorSig:
            errorSig = map( binToVoltageV, data.errorSig )
            self.errorSigTrace = Trace()
            self.errorSigTrace.x = numpy.arange(len(errorSig))*sampleTime.toval('us')
            self.errorSigTrace.y = numpy.array( errorSig )
            if self.errorSigCurve is None:
                self.errorSigCurve = PlottedTrace(self.errorSigTrace, self.view, pen=-1, style=PlottedTrace.Style.lines, name="Error Signal")  #@UndefinedVariable 
                self.errorSigCurve.plot()
            else:
                self.errorSigCurve.replot()                
        if data.frequency:
            frequency = map( binToFreqHz, data.frequency )
            self.freqTrace = Trace()
            self.freqTrace.x = numpy.arange(len(frequency))*sampleTime.toval('us')
            self.freqTrace.y = numpy.array( frequency )
            if self.freqCurve is None:
                self.freqCurve = PlottedTrace(self.freqTrace, self.view, pen=-1, style=PlottedTrace.Style.lines, name="Frequency")  #@UndefinedVariable 
                self.freqCurve.plot()
            else:
                self.freqCurve.replot()                           
        if self.state==self.StateOptions.running:
            self.controller.triggerScope()
        else:
            self.setState(self.StateOptions.stopped)         

    def onRun(self):
        self.controller.triggerScope()
        self.setState(self.StateOptions.running)
    
    def onStop(self):
        self.setState( self.StateOptions.stopped)
    
    def onSingle(self):
        self.controller.triggerScope()
        self.setState( self.StateOptions.single )

    def setTriggerMode(self, mode):
        self.controller.setTriggerMode(mode)
    
    def setTriggerLevel(self, value):
        self.controller.setTriggerLevel( voltageToBin(value) )
    
    def setSamples(self, samples):
        self.controller.setSamples(int(samples.toval()))
    
    def setSubSample(self, subsample):
        self.controller.setSubSample(int(subsample.toval()))
    
         
    def saveConfig(self):
        self.config["TraceControl.Settings"] = self.traceSettings