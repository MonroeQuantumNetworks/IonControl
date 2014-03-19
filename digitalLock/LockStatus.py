import PyQt4.uic
import logging

from PyQt4 import QtCore
from modules.MagnitudeUtilit import setSignificantDigits
from trace.PlottedTrace import PlottedTrace 
from trace.Trace import Trace
from operator import attrgetter, methodcaller
import numpy
import functools
from modules.DataDirectory import DataDirectory
from datetime import datetime

from controller.ControllerClient import frequencyQuantum, voltageQuantum, binToFreq, binToVoltage, sampleTime
from modules.magnitude import mg
import math
Form, Base = PyQt4.uic.loadUiType(r'digitalLock\ui\LockStatus.ui')

from modules.PyqtUtility import updateComboBoxItems

class StatusData:
    pass

class Settings:
    def __init__(self):
        self.averageTime = mg(100,'ms')
        self.maxSamples = mg(2000,'')
        self.frequencyPlot = None
        self.errorSigPlot = None
        
    def __setstate__(self, s):
        self.__dict__ = s
        self.__dict__.setdefault( 'averageTime', mg(100,'ms') )
        self.__dict__.setdefault( 'maxSamples', mg(2000,'') )
        self.__dict__.setdefault( 'frequencyPlot', None )
        self.__dict__.setdefault( 'errorSigPlot', None )

class LockStatus(Form, Base):
    newDataAvailable = QtCore.pyqtSignal( object )
    def __init__(self,controller,config,traceui,plotDict,parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        self.controller = controller
        self.config = config
        self.lockSettings = None
        self.lastLockData = list()
        self.traceui = traceui
        self.errorSigCurve = None
        self.trace = None
        self.freqCurve = None
        self.plotDict = plotDict
        self.settings = self.config.get("LockStatus.settings",Settings())
        self.lastXValue = 0
        self.logFile = None

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
        self.initPlotCombo( self.frequencyPlotCombo, 'frequencyPlot' , self.onChangeFrequencyPlot)
        self.initPlotCombo( self.errorSigPlotCombo, 'errorSigPlot' , self.onChangeErrorSigPlot)
        self.clearButton.clicked.connect( self.onClear )
        
    def initPlotCombo(self, combo, plotAttrName, onChange ):
        combo.addItems( self.plotDict.keys() )
        plotName = getattr(self.settings,plotAttrName)
        if plotName is not None and plotName in self.plotDict:
            combo.setCurrentIndex( combo.findText(plotName))
        else:   
            setattr( self.settings, plotAttrName, str( combo.currentText()) )
        combo.currentIndexChanged[QtCore.QString].connect( onChange )       

    def onPlotConfigurationChanged(self, plotDict):
        self.plotDict = plotDict
        if self.settings.frequencyPlot not in self.plotDict:
            self.settings.frequencyPlot = self.plotDict.keys()[0]
        if self.settings.errorSigPlot not in self.plotDict:
            self.settings.errorSigPlot = self.plotDict.keys()[0]
        updateComboBoxItems( self.frequencyPlotCombo, self.plotDict.keys() )
        updateComboBoxItems( self.errorSigPlotCombo, self.plotDict.keys() )       
        
    def onChangeFrequencyPlot(self, name):
        name = str(name)
        if name!=self.settings.frequencyPlot and name in self.plotDict:
            self.settings.frequencyPlot = name
            if self.freqCurve is not None:
                self.freqCurve.setView( self.plotDict[name]['view'])                      
    
    def onChangeErrorSigPlot(self, name):
        name = str(name)
        if name!=self.settings.errorSigPlot and name in self.plotDict:
            self.settings.errorSigPlot = name
            if self.errorSigCurve is not None:
                self.errorSigCurve.setView( self.plotDict[name]['view'])
        
    def setAverageTime(self, value):
        self.settings.averageTime = value        
        mySampleTime = sampleTime.copy()
        if self.lockSettings is not None and self.lockSettings.filter >0:
            mySampleTime *= 2
        accumNumber = int((value / mySampleTime ).toval())
        self.controller.setStreamAccum(accumNumber)
        
    def setMaxSamples(self, samples):
        self.settings.maxSamples = samples
        
    def onLockChange(self, data=None):
        pass
    
    def onControlChanged(self, value):
        self.lockSettings = value
        self.setAverageTime(self.settings.averageTime)
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
        status.outputFrequencyDelta = abs(binToFreq(binvalue))
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
        
        status.errorSigRMS = binToVoltage( math.sqrt(item.errorSigSumSq/float(item.samples)) )
        setSignificantDigits( status.errorSigRMS, voltageQuantum )
        
        status.time = item.samples * sampleTime.toval('s')          
        return status
    
    logFrequency = ['regulatorFrequency', 'referenceFrequency', 'referenceFrequencyMin', 'referenceFrequencyMax', 
                      'outputFrequency', 'outputFrequencyMin', 'outputFrequencyMax']
    logVoltage = ['errorSigAvg', 'errorSigMin', 'errorSigMax', 'errorSigRMS']                 
    def writeToLogFile(self, status):
        if self.lockSettings and self.lockSettings.mode & 1 == 1:  # if locked
            if not self.logFile:
                self.logFile = open( DataDirectory().sequencefile("LockLog.txt")[0], "w" )
                self.logFile.write( " ".join( self.logFrequency + self.logVoltage ) )
                self.logFile.write( "\n" )
            self.logFile.write( "{0} ".format(datetime.now()))
            self.logFile.write(  " ".join( map( repr, map( methodcaller('toval','Hz'), (getattr(status, field) for field in self.logFrequency) ) ) ) )
            self.logFile.write(  " ".join( map( repr, map( methodcaller('toval','mV'), (getattr(status, field) for field in self.logVoltage) ) ) ) )
            self.logFile.write("\n")
            self.logFile.flush()
        
    
    def onData(self, data=None ):
        logger = logging.getLogger()
        logger.debug( "received streaming data {0} {1}".format(len(data),data[-1] if len(data)>0 else ""))
        if data is not None:
            self.lastLockData = list()
            for item in data:
                converted = self.convertStatus(item)
                if converted is not None:
                    self.lastLockData.append( converted )
                    self.writeToLogFile(converted)
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
                self.errorSignalRMSLabel.setText( str(item.errorSigRMS))
                logger.debug("error  signal min {0} max {1}".format(item.errorSigMin, item.errorSigMax ))
                self.newDataAvailable.emit( item )
        else:
            logger.info("no lock control information")
            
    def plotData(self):
        if len(self.lastLockData)>0:
            to_plot = zip(*(attrgetter('errorSigAvg','errorSigMin', 'errorSigMax','time')(e) for e in self.lastLockData))
            x = numpy.arange( self.lastXValue, self.lastXValue+len(to_plot[0] ))
            self.lastXValue += len(to_plot[0] )
            y = numpy.array( map( methodcaller('toval','V'), to_plot[0] ) )
            bottom = numpy.array( map( methodcaller('toval','V'), numpy.array(to_plot[0])-numpy.array(to_plot[1]) ) ) 
            top = numpy.array( map( methodcaller('toval','V'), numpy.array(to_plot[2])-numpy.array(to_plot[0]) ) )          
            if self.trace is None:
                self.trace = Trace()
                self.trace.x = x
                self.trace.y = y
                self.trace.bottom = bottom
                self.trace.top = top
                self.trace.name = "History"
                self.trace.addColumn( 'freq' )
                self.trace.addColumn( 'freqBottom' )
                self.trace.addColumn( 'freqTop' )
            else:
                oldSamples = self.settings.maxSamples.toval()-len(x)
                if len(self.trace.x) > oldSamples:
                    self.trace.x = numpy.append( self.trace.x[-oldSamples:], x )
                    self.trace.y = numpy.append( self.trace.y[-oldSamples:], y )
                    self.trace.bottom = numpy.append( self.trace.bottom[-oldSamples:], bottom )
                    self.trace.top = numpy.append( self.trace.top[-oldSamples:], top )
                else:
                    self.trace.x = numpy.append( self.trace.x, x )
                    self.trace.y = numpy.append( self.trace.y, y )
                    self.trace.bottom = numpy.append( self.trace.bottom, bottom )
                    self.trace.top = numpy.append( self.trace.top, top )
                
            if self.errorSigCurve is None:
                self.errorSigCurve = PlottedTrace(self.trace, self.plotDict[self.settings.errorSigPlot]['view'], pen=-1, style=PlottedTrace.Styles.points, name="Error Signal")  #@UndefinedVariable 
                self.trace.filenameCallback =  functools.partial( self.errorSigCurve.traceFilename, "LockHistory.txt" )
                self.errorSigCurve.plot()
                self.traceui.addTrace( self.errorSigCurve, pen=-1 )
            else:
                self.errorSigCurve.replot()            
               
            to_plot = zip(*(attrgetter('regulatorFrequency','referenceFrequencyMin', 'referenceFrequencyMax')(e) for e in self.lastLockData))
            y = numpy.array( map( methodcaller('toval','Hz'), to_plot[0] ) )
            bottom = numpy.array( map( methodcaller('toval','Hz'), numpy.array(to_plot[0])-numpy.array(to_plot[1]) ) ) 
            top = numpy.array( map( methodcaller('toval','Hz'), numpy.array(to_plot[2])-numpy.array(to_plot[0]) ) )          
            oldSamples = self.settings.maxSamples.toval()-len(x)
            if len(self.trace.x) > oldSamples:
                self.trace.freq = numpy.append( self.trace.freq[-oldSamples:], y )
                self.trace.freqBottom = numpy.append( self.trace.freqBottom[-oldSamples:], bottom )
                self.trace.freqTop = numpy.append( self.trace.freqTop[-oldSamples:], top )
            else:
                self.trace.freq = numpy.append( self.trace.freq, y )
                self.trace.freqBottom = numpy.append( self.trace.freqBottom, bottom )
                self.trace.freqTop = numpy.append( self.trace.freqTop, top )
                
            if self.freqCurve is None:
                self.freqCurve = PlottedTrace(self.trace, self.plotDict[self.settings.frequencyPlot]['view'], pen=-1, style=PlottedTrace.Styles.points, name="Repetition rate", #@UndefinedVariable
                                              xColumn='x', yColumn='freq', topColumn='freqTop', bottomColumn='freqBottom')  
                self.freqCurve.plot()
                self.traceui.addTrace( self.freqCurve, pen=-1 )
            else:
                self.freqCurve.replot()                        
             
    def onClear(self):
        if self.trace:
            self.trace.x = numpy.array( [] )
            self.trace.y = numpy.array( [] )
            self.trace.bottom = numpy.array( [] )
            self.trace.top = numpy.array( [] )
            self.trace.freq = numpy.array( [] )
            self.trace.freqBottom = numpy.array( [] )
            self.trace.freqTop = numpy.array( [] )
           
    def onAddTrace(self):
        self.trace = None
        self.errorSigCurve = None
        self.freqCurve = None
        
    def saveConfig(self):
        self.config["LockStatus.settings"] = self.settings
        
