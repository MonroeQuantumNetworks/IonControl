import PyQt4.uic

from modules.MagnitudeUtilit import setSignificantDigits
from trace.PlottedTrace import PlottedTrace 
from trace.Trace import Trace
from operator import attrgetter, methodcaller
import numpy

from controller.ControllerClient import frequencyQuantum, voltageQuantum, binToFreq, binToVoltage
from modules.magnitude import mg

Form, Base = PyQt4.uic.loadUiType(r'digitalLock\ui\LockStatus.ui')



class StatusData:
    pass

class Settings:
    def __init__(self):
        self.averageSamples = mg(1,'')

class LockStatus(Form, Base):
    def __init__(self,controller,config,traceui,view,parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        self.controller = controller
        self.config = config
        self.lockSettings = None
        self.lastLockData = list()
        self.traceui = traceui
        self.errorSigCurve = None
        self.errorSigTrace = None
        self.freqCurve = None
        self.freqTrace = None
        self.view = view
        self.settings = Settings()#self.config.get("LockStatus.settings",Settings())

    def setupSpinBox(self, localname, settingsname, updatefunc, unit ):
        box = getattr(self, localname)
        value = getattr(self.settings, settingsname)
        box.setValue( value )
        box.dimension = unit
        box.valueChanged.connect( updatefunc )
        updatefunc( value )
   
    def setupUi(self):
        Form.setupUi(self,self)
        self.setupSpinBox('magHistoryAccum', 'averageSamples', self.setAverageSamples, '')
        self.controller.streamDataAvailable.connect( self.onData )
        self.controller.lockStatusChanged.connect( self.onLockChange )
        self.addTraceButton.clicked.connect( self.onAddTrace )
        
    def onAddTrace(self):
        if self.errorSigCurve:
            self.traceui.addTrace( self.errorSigCurve )
            self.errorSigCurve = None
        if self.freqTrace:
            self.traceui.addTrace( self.freqCurve )
            self.freqCurve = None
        
    def setAverageSamples(self, value):
        self.controller.setStreamAccum(int(value.toval()))
        
    def onLockChange(self, data=None):
        pass
    
    def onControlChanged(self, value):
        self.lockSettings = value
        self.onLockChange()
    
    def convertStatus(self, item):
        if self.lockSettings is None:
            return None
        status = StatusData()
        status.referenceFrequency = self.lockSettings.referenceFrequency + binToFreq(item.freqAvg)
        setSignificantDigits(status.referenceFrequency, frequencyQuantum)

        status.outputFrequency = self.lockSettings.outputFrequency + binToFreq(item.freqAvg)* self.lockSettings.harmonic
        setSignificantDigits(status.outputFrequency, frequencyQuantum)

        binvalue = (item.freqMax - item.freqMin) 
        status.referenceFrequencyDelta = binToFreq(binvalue) 
        setSignificantDigits(status.referenceFrequencyDelta, frequencyQuantum)        
        status.referenceFrequencyMax = binToFreq(item.freqMax)
        setSignificantDigits(status.referenceFrequencyMax, frequencyQuantum)
        status.referenceFrequencyMin = binToFreq(item.freqMin)
        setSignificantDigits(status.referenceFrequencyMin, frequencyQuantum)

        binvalue *= self.lockSettings.harmonic
        status.outputFrequencyDelta = binToFreq(binvalue)
        setSignificantDigits(status.outputFrequencyDelta, frequencyQuantum*self.lockSettings.harmonic)
        status.outputFrequencyMax = self.lockSettings.outputFrequency + binToFreq(item.freqMax)* self.lockSettings.harmonic
        setSignificantDigits(status.outputFrequencyMax, frequencyQuantum)
        status.outputFrequencyMin = self.lockSettings.outputFrequency + binToFreq(item.freqMin)* self.lockSettings.harmonic
        setSignificantDigits(status.outputFrequencyMin, frequencyQuantum)
        
        status.errorSigAvg = binToVoltage( item.errorSigAvg )
        setSignificantDigits( status.errorSigAvg.significantDigits, voltageQuantum )
        binvalue = item.errorSigMax - item.errorSigMin
        status.errorSigDelta = binToVoltage(binvalue )
        setSignificantDigits( status.errorSigDelta, voltageQuantum )            
        status.errorSigMax = binToVoltage(item.errorSigMax)
        setSignificantDigits( status.errorSigMax, voltageQuantum )            
        status.errorSigMin = binToVoltage(item.errorSigMax)
        setSignificantDigits( status.errorSigMin, voltageQuantum )            
        return status
    
    def onData(self, data=None ):
        if data is not None:
            self.lastLockData = map(self.convertStatus, data)
        self.plotData()
        if self.lastLockData:
            item = self.lastLockData[-1]
            
            self.referenceFreqLabel.setText( str(item.referenceFrequency) )
            self.referenceFreqRangeLabel.setText( str(item.referenceFrequencyDelta) )
            self.outputFreqLabel.setText( str(item.outputFrequency))
            self.outputFreqRangeLabel.setText( str(item.outputFrequencyDelta))
            
            self.errorSignalLabel.setText( str(item.errorSigAvg))
            self.errorSignalRangeLabel.setText( str(item.errorSigDelta))
            
    def plotData(self):
        to_plot = zip(*(attrgetter('errorSigAvg','errorSigMin', 'errorSigMax')(e) for e in self.lastLockData))
        x = numpy.arange( len(to_plot[0] ))
        y = numpy.array( map( methodcaller('toval','V'), to_plot[0] ) )
        bottom = self.errorSigTrace.y - numpy.arange( map( methodcaller('toval','V'), to_plot[1] ) ) 
        top = numpy.arange( map( methodcaller('toval','V'), to_plot[2] ) ) - self.errorSigTrace.y  
        if self.errorSigTrace is None:
            self.errorSigTrace = Trace()
            self.errorSigTrace.x = x
            self.errorSigTrace.y = y
            self.errorSigTrace.bottom = bottom
            self.errorSigTrace.top = top
        else:
            self.errorSigTrace.x = numpy.append( self.errorSigTrace.x, x )
            self.errorSigTrace.y = numpy.append( self.errorSigTrace.y, y )
            self.errorSigTrace.bottom = numpy.append( self.errorSigTrace.bottom, bottom )
            self.errorSigTrace.top = numpy.append( self.errorSigTrace.top, top )
            
        if self.errorSigCurve is None:
            self.errorSigCurve = PlottedTrace(self.errorSigTrace, self.view, pen=-1, style=PlottedTrace.Style.points, name="Error Signal")  #@UndefinedVariable 
            self.errorSigCurve.plot()
        else:
            self.errorSigCurve.replot()            
           
        to_plot = zip(*(attrgetter('referenceFrequency','referenceFrequencyMin', 'referenceFrequencyMax')(e) for e in self.lastLockData))
        x = numpy.arange( len(to_plot[0] ))
        y = numpy.array( map( methodcaller('toval','MHz'), to_plot[0] ) )
        bottom = self.errorSigTrace.y - numpy.arange( map( methodcaller('toval','MHz'), to_plot[1] ) ) 
        top = numpy.arange( map( methodcaller('toval','MHz'), to_plot[2] ) ) - self.errorSigTrace.y             
        if self.freqTrace is None:
            self.freqTrace = Trace()
            self.freqTrace.x = x
            self.freqTrace.y = y
            self.freqTrace.bottom = bottom
            self.freqTrace.top = top
        else:
            self.freqTrace.x = numpy.append( self.freqTrace.x, x )
            self.freqTrace.y = numpy.append( self.freqTrace.y, y )
            self.freqTrace.bottom = numpy.append( self.freqTrace.bottom, bottom )
            self.freqTrace.top = numpy.append( self.freqTrace.top, top )
            
        if self.freqCurve is None:
            self.freqCurve = PlottedTrace(self.freqTrace, self.view, pen=-1, style=PlottedTrace.Style.points, name="Repetition rate")  #@UndefinedVariable
            self.freqCurve.plot()
        else:
            self.freqCurve.replot()                        
             
           
    def saveConfig(self):
        pass
