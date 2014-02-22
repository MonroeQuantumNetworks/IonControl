import PyQt4.uic
import logging

from PyQt4 import QtCore
from modules.MagnitudeUtilit import setSignificantDigits
from trace.PlottedTrace import PlottedTrace 
from trace.Trace import Trace
from operator import attrgetter, methodcaller
import numpy

from controller.ControllerClient import frequencyQuantum, voltageQuantum, binToFreq, binToVoltage, sampleTime
from modules.magnitude import mg

Form, Base = PyQt4.uic.loadUiType(r'digitalLock\ui\LockStatus.ui')



class StatusData:
    pass

class Settings:
    def __init__(self):
        self.averageTime = mg(100,'ms')
        self.maxSamples = mg(2000,'')
        
    def __setstate__(self, s):
        self.__dict__ = s
        self.__dict__.setdefault( 'averageTime', mg(100,'ms') )
        self.__dict__.setdefault( 'maxSamples', mg(2000,'') )

class LockStatus(Form, Base):
    newDataAvailable = QtCore.pyqtSignal( object )
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
        self.settings = self.config.get("LockStatus.settings",Settings())
        self.lastXValue = 0

    def setupSpinBox(self, localname, settingsname, updatefunc, unit ):
        box = getattr(self, localname)
        value = getattr(self.settings, settingsname)
        box.setValue( value )
        box.dimension = unit
        box.valueChanged.connect( updatefunc )
        updatefunc( value )
   
    def setupUi(self):
        Form.setupUi(self,self)
        self.setupSpinBox('magHistoryAccum', 'averageTime', self.setAverageTime, 'ms')
        self.setupSpinBox('magMaxHistory', 'maxSamples', self.setMaxSamples, '')
        self.controller.streamDataAvailable.connect( self.onData )
        self.controller.lockStatusChanged.connect( self.onLockChange )
        self.addTraceButton.clicked.connect( self.onAddTrace )
        self.controller.setStreamEnabled(True)
        
    def onAddTrace(self):
        if self.errorSigCurve:
            self.traceui.addTrace( self.errorSigCurve, pen=-1 )
            self.errorSigCurve = None
        if self.freqTrace:
            self.traceui.addTrace( self.freqCurve, pen=-1 )
            self.freqCurve = None
        
    def setAverageTime(self, value):
        self.settings.averageTime = value        
        self.controller.setStreamAccum(int((value / sampleTime).toval()))
        
    def setMaxSamples(self, samples):
        self.settings.maxSamples = samples
        
    def onLockChange(self, data=None):
        pass
    
    def onControlChanged(self, value):
        self.lockSettings = value
        self.onLockChange()
    
    def convertStatus(self, item):
        if self.lockSettings is None:
            return None
        status = StatusData()

        status.regulatorFrequency = binToFreq(item.freqSum / float(item.samples))
        setSignificantDigits(status.regulatorFrequency, frequencyQuantum)
        status.referenceFrequency = self.lockSettings.referenceFrequency + status.regulatorFrequency
        setSignificantDigits(status.referenceFrequency, frequencyQuantum)


        status.outputFrequency = self.lockSettings.outputFrequency + binToFreq(item.freqSum / float(item.samples) )* self.lockSettings.harmonic
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
        
        status.errorSigAvg = binToVoltage( item.errorSigSum/float(item.samples) )
        setSignificantDigits( status.errorSigAvg, voltageQuantum )
        binvalue = item.errorSigMax - item.errorSigMin
        status.errorSigDelta = binToVoltage(binvalue )
        setSignificantDigits( status.errorSigDelta, voltageQuantum )            
        status.errorSigMax = binToVoltage(item.errorSigMax)
        setSignificantDigits( status.errorSigMax, voltageQuantum )            
        status.errorSigMin = binToVoltage(item.errorSigMin)
        setSignificantDigits( status.errorSigMin, voltageQuantum )            
        return status
    
    def onData(self, data=None ):
        logger = logging.getLogger()
        logger.debug( "received streaming data {0} {1}".format(len(data),data[-1] if len(data)>0 else ""))
        if data is not None:
            self.lastLockData = list()
            for item in data:
                converted = self.convertStatus(item)
                if converted is not None:
                    self.lastLockData.append( converted)
        if self.lastLockData is not None:
            self.plotData()
            if self.lastLockData:
                item = self.lastLockData[-1]
                
                self.referenceFreqLabel.setText( str(item.referenceFrequency) )
                self.referenceFreqRangeLabel.setText( str(item.referenceFrequencyDelta) )
                self.outputFreqLabel.setText( str(item.outputFrequency))
                self.outputFreqRangeLabel.setText( str(item.outputFrequencyDelta))
                
                self.errorSignalLabel.setText( str(item.errorSigAvg))
                self.errorSignalRangeLabel.setText( str(item.errorSigDelta))
                logger.debug("error  signal min {0} max {1}".format(item.errorSigMin, item.errorSigMax ))
                self.newDataAvailable.emit( item )
        else:
            logger.info("no lock control information")
            
    def plotData(self):
        if len(self.lastLockData)>0:
            to_plot = zip(*(attrgetter('errorSigAvg','errorSigMin', 'errorSigMax')(e) for e in self.lastLockData))
            x = numpy.arange( self.lastXValue, self.lastXValue+len(to_plot[0] ))
            self.lastXValue += len(to_plot[0] )
            y = numpy.array( map( methodcaller('toval','V'), to_plot[0] ) )
            bottom = numpy.array( map( methodcaller('toval','V'), numpy.array(to_plot[0])-numpy.array(to_plot[1]) ) ) 
            top = numpy.array( map( methodcaller('toval','V'), numpy.array(to_plot[2])-numpy.array(to_plot[0]) ) )          
            if self.errorSigTrace is None:
                self.errorSigTrace = Trace()
                self.errorSigTrace.x = x
                self.errorSigTrace.y = y
                self.errorSigTrace.bottom = bottom
                self.errorSigTrace.top = top
            else:
                oldSamples = self.settings.maxSamples.toval()-len(x)
                if len(self.errorSigTrace.x) > oldSamples:
                    self.errorSigTrace.x = numpy.append( self.errorSigTrace.x[-oldSamples:], x )
                    self.errorSigTrace.y = numpy.append( self.errorSigTrace.y[-oldSamples:], y )
                    self.errorSigTrace.bottom = numpy.append( self.errorSigTrace.bottom[-oldSamples:], bottom )
                    self.errorSigTrace.top = numpy.append( self.errorSigTrace.top[-oldSamples:], top )
                else:
                    self.errorSigTrace.x = numpy.append( self.errorSigTrace.x, x )
                    self.errorSigTrace.y = numpy.append( self.errorSigTrace.y, y )
                    self.errorSigTrace.bottom = numpy.append( self.errorSigTrace.bottom, bottom )
                    self.errorSigTrace.top = numpy.append( self.errorSigTrace.top, top )
                
            if self.errorSigCurve is None:
                self.errorSigCurve = PlottedTrace(self.errorSigTrace, self.view, pen=-1, style=PlottedTrace.Styles.points, name="Error Signal")  #@UndefinedVariable 
                self.errorSigCurve.plot()
            else:
                self.errorSigCurve.replot()            
               
            to_plot = zip(*(attrgetter('regulatorFrequency','referenceFrequencyMin', 'referenceFrequencyMax')(e) for e in self.lastLockData))
            y = numpy.array( map( methodcaller('toval','MHz'), to_plot[0] ) )
            bottom = numpy.array( map( methodcaller('toval','MHz'), numpy.array(to_plot[0])-numpy.array(to_plot[1]) ) ) 
            top = numpy.array( map( methodcaller('toval','MHz'), numpy.array(to_plot[2])-numpy.array(to_plot[0]) ) )          
            if self.freqTrace is None:
                self.freqTrace = Trace()
                self.freqTrace.x = x
                self.freqTrace.y = y
                self.freqTrace.bottom = bottom
                self.freqTrace.top = top
            else:
                oldSamples = self.settings.maxSamples.toval()-len(x)
                if len(self.errorSigTrace.x) > oldSamples:
                    self.freqTrace.x = numpy.append( self.freqTrace.x[-oldSamples:], x )
                    self.freqTrace.y = numpy.append( self.freqTrace.y[-oldSamples:], y )
                    self.freqTrace.bottom = numpy.append( self.freqTrace.bottom[-oldSamples:], bottom )
                    self.freqTrace.top = numpy.append( self.freqTrace.top[-oldSamples:], top )
                else:
                    self.freqTrace.x = numpy.append( self.freqTrace.x, x )
                    self.freqTrace.y = numpy.append( self.freqTrace.y, y )
                    self.freqTrace.bottom = numpy.append( self.freqTrace.bottom, bottom )
                    self.freqTrace.top = numpy.append( self.freqTrace.top, top )
                
            if self.freqCurve is None:
                self.freqCurve = PlottedTrace(self.freqTrace, self.view, pen=-1, style=PlottedTrace.Styles.points, name="Repetition rate")  #@UndefinedVariable
                self.freqCurve.plot()
            else:
                self.freqCurve.replot()                        
             
           
    def saveConfig(self):
        self.config["LockStatus.settings"] = self.settings
        
