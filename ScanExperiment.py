# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 17:25:13 2012

Experiment code to scan a parameter that is controlled by the FPGA.

The Pulse Program for each point od the scan, the Pulse Program receives the
address and value of the scanned parameter on its pipe input. It is expected to
echo those on the pipe output followed by the measurement results.
It is expected to send an endlabel (0xffffffff) when finished.


@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore
from Trace import Trace
import numpy
import pens
import Traceui
import MainWindowWidget
import FitUi
from modules import enum
from pyqtgraph.dockarea import DockArea, Dock
import pyqtgraph
from modules import DataDirectory
import time
from CoordinatePlotWidget import CoordinatePlotWidget
import functools
from modules import stringutilit
from datetime import datetime, timedelta
from ui import StyleSheets
import RawData
from modules import MagnitudeUtilit
import random
import ScanControl
from AverageView import AverageView
     
ScanExperimentForm, ScanExperimentBase = PyQt4.uic.loadUiType(r'ui\ScanExperiment.ui')

class ParameterScanGenerator:
    def __init__(self, scan):
        self.scan = scan
        
    def prepare(self, pulseProgramUi ):
        print self.scan.scanParameter
        self.scan.code = pulseProgramUi.pulseProgram.variableScanCode(self.scan.scanParameter, self.scan.list)
        return ( self.scan.code, [])
        
    def restartCode(self,currentIndex):
        mycode = self.scan.code[currentIndex*2:]
        print "original length", len(self.scan.code), "remaining", len(mycode)
        return mycode
        
    def xValue(self, index):
        return self.scan.list[index].ounit(self.scan.xUnit).toval()
        
    def dataNextCode(self, experiment):
        return []
        
    def dataOnFinal(self, experiment):
        if self.scan.scanRepeat == 1:
            experiment.startScan()
        else:
            experiment.onStop()                   
    
    def xRange(self):
        return self.scan.start.ounit(self.scan.xUnit).toval(), self.scan.stop.ounit(self.scan.xUnit).toval()
                                     
    def appendData(self,trace,x,y,raw,error):                                     
        trace.x = numpy.append(trace.x, x)
        trace.y = numpy.append(trace.y, y)
        trace.raw = numpy.append(trace.raw, raw)
        if error and self.scan.evalAlgo.settings['errorBars']:
            trace.bottom = numpy.append(trace.bottom, error[0])
            trace.top = numpy.append(trace.top, error[1])
                
class StepInPlaceGenerator:
    def __init__(self, scan):
        self.scan = scan
        
    def prepare(self, pulseProgramUi ):
        #self.stepInPlaceValue = pulseProgramUi.getVariableValue(self.scan.scanParameter)
        self.stepInPlaceValue = 0
        self.scan.code = [4095, 0] # writing the last memory location
        #self.scan.code = pulseProgramUi.pulseProgram.variableScanCode(self.scan.scanParameter, [self.stepInPlaceValue])
        return (self.scan.code*5, []) # write 5 points to the fifo queue at start,
                        # this prevents the Step in Place from stopping in case the computer lags behind evaluating by up to 5 points

    def restartCode(self,currentIndex):
        return self.scan.code * 5
        
    def dataNextCode(self, experiment):
        return self.scan.code
        
    def xValue(self,index):
        return index

    def xRange(self):
        return []

    def appendData(self,trace,x,y,raw,error):                                   
        if len(trace.x)<self.scan.steps or self.scan.steps==0:
            trace.x = numpy.append(trace.x, x)
            trace.y = numpy.append(trace.y, y)
            trace.raw = numpy.append(trace.raw, raw)
            if error and self.scan.evalAlgo.settings['errorBars']:
                trace.bottom = numpy.append(trace.bottom, error[0])
                trace.top = numpy.append(trace.top, error[1])
        else:
            steps = int(self.scan.steps)
            trace.x = numpy.append(trace.x[-steps+1:], x)
            trace.y = numpy.append(trace.y[-steps+1:], y)
            trace.raw = numpy.append(trace.raw[-steps+1:], raw)
            if error and self.scan.evalAlgo.settings['errorBars']:
                trace.bottom = numpy.append(trace.bottom[-steps+1:], error[0]) 
                trace.top = numpy.append(trace.top[-steps+1:], error[1]) 

    def dataOnFinal(self, experiment):
        experiment.onStop()                   

class GateSetScanGenerator:
    def __init__(self, scan):
        self.scan = scan
        
    def prepare(self, pulseProgramUi):
        address, data, self.gateSetSettings = self.scan.gateSetUi.gateSetScanData()
        parameter = self.gateSetSettings.startAddressParam
        if self.gateSetSettings.debug:
            print "GateSetScan", address, parameter
        self.scan.list = address
        self.scan.index = range(len(self.scan.list))
        if self.scan.scantype == 1:
            self.scan.list.reverse()
            self.scan.index.reverse()
        elif self.scan.scantype == 2:
            zipped = zip(self.scan.index,self.scan.list)
            random.shuffle(zipped)
            self.scan.index, self.scan.list = zip( *zipped )
        self.scan.code = pulseProgramUi.pulseProgram.variableScanCode(parameter, self.scan.list)
        if self.gateSetSettings.debug:
            print "GateSetScanCode", self.scan.list, self.scan.code
        return (self.scan.code, data)

    def restartCode(self,currentIndex):
        mycode = self.scan.code[currentIndex*2:]
        if self.gateSetSettings.debug:
            print "original length", len(self.scan.code), "remaining", len(mycode)
        return mycode

    def xValue(self,index):
        return self.scan.index[index]

    def dataNextCode(self, experiment):
        return []
        
    def xRange(self):
        return [0, len(self.scan.list)]

    def appendData(self,trace,x,y,raw,error):                                     
        trace.x = numpy.append(trace.x, x)
        trace.y = numpy.append(trace.y, y)
        trace.raw = numpy.append(trace.raw, raw)
        if error and self.scan.evalAlgo.settings['errorBars']:
            trace.bottom = numpy.append(trace.bottom, error[0])
            trace.top = numpy.append(trace.top, error[1])

    def dataOnFinal(self, experiment):
        if self.scan.scanRepeat == 1:
            experiment.startScan()
        else:
            experiment.onStop()                   
        
GeneratorList = [ParameterScanGenerator, StepInPlaceGenerator, GateSetScanGenerator]   
    
    


class ScanExperiment(ScanExperimentForm, MainWindowWidget.MainWindowWidget):
    StatusMessage = QtCore.pyqtSignal( str )
    ClearStatusMessage = QtCore.pyqtSignal()
    NeedsDDSRewrite = QtCore.pyqtSignal()
    OpStates = enum.enum('idle','running','paused')
    experimentName = 'Scan Sequence'

    def __init__(self,settings,pulserHardware,experimentName,parent=None):
        MainWindowWidget.MainWindowWidget.__init__(self,parent)
        ScanExperimentForm.__init__(self)
        self.deviceSettings = settings
        self.pulserHardware = pulserHardware
        self.plottedTraceList = list()
        self.averagePlottedTraceList = list()
        self.currentIndex = 0
        self.activated = False
        self.histogramCurve = None
        self.timestampCurve = None
        self.running = False
        self.currentTimestampTrace = None
        self.experimentName = experimentName
        self.globalVariables = dict()
        self.state = self.OpStates.idle

    def setupUi(self,MainWindow,config):
        ScanExperimentForm.setupUi(self,MainWindow)
        self.config = config
        self.area = DockArea()
        self.setCentralWidget(self.area)
        # initialize all the plot windows we want
        self.mainDock = Dock("Scan data")
        self.histogramDock = Dock("Histogram")
        self.timestampDock = Dock("timestamps")
        self.area.addDock(self.mainDock,'left')
        self.area.addDock(self.histogramDock,'right')
        self.area.addDock(self.timestampDock,'bottom',self.histogramDock)
        self.graphicsWidget = CoordinatePlotWidget(self) # self.graphicsLayout.graphicsView
        self.mainDock.addWidget(self.graphicsWidget)
        self.graphicsView = self.graphicsWidget.graphicsView
        self.histogramWidget = CoordinatePlotWidget(self)
        self.histogramDock.addWidget(self.histogramWidget)
        self.histogramView = self.histogramWidget.graphicsView        
        self.histogramWidget.autoRange()
        self.timestampWidget = CoordinatePlotWidget(self) # pyqtgraph.PlotWidget()
        self.timestampDock.addWidget( self.timestampWidget )
        self.timestampView = self.timestampWidget.graphicsView
        self.timestampWidget.autoRange()
        try:
            if self.experimentName+'.pyqtgraph-dokareastate' in self.config:
                self.area.restoreState(self.config[self.experimentName+'.pyqtgraph-dokareastate'])
        except:
            pass # Ignore errors on restoring the state. This might happen after a new dock is added
        self.penicons = pens.penicons().penicons()
        self.traceui = Traceui.Traceui(self.penicons,self.config,self.experimentName,self.graphicsView)
        self.traceui.setupUi(self.traceui)
        self.dockWidget.setWidget( self.traceui )
        self.dockWidgetList.append(self.dockWidget)
        # traceui for timestamps
        self.timestampTraceui = Traceui.Traceui(self.penicons,self.config,self.experimentName+"-timestamps",self.timestampView)
        self.timestampTraceui.setupUi(self.timestampTraceui)
        self.timestampDockWidget.setWidget( self.timestampTraceui )
        self.dockWidgetList.append(self.timestampDockWidget)       
        self.fitWidget = FitUi.FitUi(self.traceui,self.config,self.experimentName)
        self.fitWidget.setupUi(self.fitWidget)
        self.dockWidgetFitUi.setWidget( self.fitWidget )
        self.dockWidgetList.append(self.dockWidgetFitUi )
        self.scanControlWidget = ScanControl.ScanControl(config,self.experimentName)
        self.scanControlWidget.setupUi(self.scanControlWidget)
        self.scanControlUi.setWidget(self.scanControlWidget )
        self.scanControlWidget.scansAveraged.hide()
        self.dockWidgetList.append(self.scanControlUi)
        self.tabifyDockWidget( self.scanControlUi, self.dockWidgetFitUi )
        self.tabifyDockWidget( self.timestampDockWidget, self.dockWidget)
        # Average View
        self.displayUi = AverageView(self.config,"testExperiment")
        self.displayUi.setupUi(self.displayUi)
        self.displayDock = QtGui.QDockWidget("Average")
        self.displayDock.setObjectName("Average")
        self.displayDock.setWidget( self.displayUi )
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea , self.displayDock)
        self.dockWidgetList.append(self.displayDock )
        if self.experimentName+'.MainWindow.State' in self.config:
            QtGui.QMainWindow.restoreState(self,self.config[self.experimentName+'.MainWindow.State'])
        self.updateProgressBar(0,1)

    def setPulseProgramUi(self,pulseProgramUi):
        self.pulseProgramUi = pulseProgramUi.addExperiment(self.experimentName, self.globalVariables, self.globalVariablesChanged )
        self.scanControlWidget.setVariables( self.pulseProgramUi.pulseProgram.variabledict )
        self.pulseProgramUi.pulseProgramChanged.connect( self.updatePulseProgram )
        self.scanControlWidget.setPulseProgramUi( self.pulseProgramUi )
        
    def setGlobalVariablesUi(self, globalVariablesUi ):
        self.globalVariables = globalVariablesUi.variables
        self.globalVariablesChanged = globalVariablesUi.valueChanged
        
    def updatePulseProgram(self):
        self.scanControlWidget.setVariables( self.pulseProgramUi.pulseProgram.variabledict )
        self.scanControlWidget.setPulseProgramUi( self.pulseProgramUi )

    def onClear(self):
        self.dockWidget.setShown(True)
        self.StatusMessage.emit("test Clear not implemented")
    
    def onSave(self):
        self.StatusMessage.emit("test Save not implemented")
    
    def setTimeLabel(self):
        elapsed = time.time()-self.startTime
        expected = elapsed / ((self.currentIndex)/float(len(self.scan.list))) if self.currentIndex>0 else 0
        self.scanControlWidget.timeLabel.setText( "{0} / {1}".format(timedelta(seconds=round(elapsed)),
                                                 timedelta(seconds=round(expected)))) 
 
    def updateProgressBar(self, value, range=None):
        if self.state == self.OpStates.idle:
            self.scanControlWidget.progressBar.setFormat("Idle")            
            self.scanControlWidget.progressBar.setValue(0)
        elif self.state == self.OpStates.running:
            if range:
                self.scanControlWidget.progressBar.setRange(0,range)
            self.scanControlWidget.progressBar.setValue(value)
            self.scanControlWidget.progressBar.setStyleSheet("")
            self.scanControlWidget.progressBar.setFormat("%p%")            
            self.setTimeLabel()
        elif self.state == self.OpStates.paused:
            self.scanControlWidget.progressBar.setStyleSheet(StyleSheets.RedProgressBar)
            self.scanControlWidget.progressBar.setFormat("Paused")            
            self.setTimeLabel()
    
    def onStart(self):
        self.scan = self.scanControlWidget.getScan()
        if (self.scan.scanRepeat == 1) and (self.scan.scanMode != 1): #scanMode == 1 corresponds to step in place.
            self.createAverageTrace()
            self.scanControlWidget.scansAveraged.setText("Scans averaged: 0")
            self.scanControlWidget.scansAveraged.show()
        else:
            self.scanControlWidget.scansAveraged.hide()
        self.startScan()

    def createAverageTrace(self):
        trace = Trace()
        self.averagePlottedTraceList = list()
        for index, result in enumerate(evaluated):
            yColumnName = 'y{0}'.format(index)
            rawColumnName = 'raw{0}'.fromat(index)
            trace.addColumn( yColumnName )
            thisAveragePlottedTrace = Traceui.PlottedTrace(trace, self.graphicsView, pens.penList, yColumnName=yColumnName)
            self.averagePlottedTraceList.append( thisAveragePlottedTrace  )                
            self.traceui.addTrace(thisAveragePlottedTrace, pen=0)
            thisAveragePlottedTrace.trace.name = self.scan.settingsName + " Average"
            thisAveragePlottedTrace.trace.vars.comment = "Average Trace"
            thisAveragePlottedTrace.trace.filenameCallback = functools.partial( thisAveragePlottedTrace.traceFilename, self.scan.filename)
        
    def startScan(self):
        self.startTime = time.time()
        self.state = self.OpStates.running
        PulseProgramBinary = self.pulseProgramUi.getPulseProgramBinary() # also overwrites the current variable values            
        self.generator = GeneratorList[self.scan.scanMode](self.scan)
        (mycode, data) = self.generator.prepare(self.pulseProgramUi)
        if data:
            self.pulserHardware.ppWriteRamWordlist(data,0)
        self.pulserHardware.ppFlushData()
        self.pulserHardware.ppClearWriteFifo()
        self.pulserHardware.ppUpload(PulseProgramBinary)
        self.pulserHardware.ppWriteData(mycode)
        print "Starting"
        self.pulserHardware.ppStart()
        self.running = True
        self.currentIndex = 0
        self.timestampsNewRun = True
        self.displayUi.onClear()
        self.updateProgressBar(0,max(len(self.scan.list),1))
        print "elapsed time", time.time()-self.startTime
        if self.plottedTrace is not None:
            self.plottedTrace.plot(0) #unplot previous trace
        self.plottedTrace = None #reset plotted trace
    
    def onPause(self):
        if self.state == self.OpStates.paused:
            self.state = self.OpStates.running
            self.pulserHardware.ppFlushData()
            self.pulserHardware.ppClearWriteFifo()
            self.pulserHardware.ppWriteData(self.generator.restartCode(self.currentIndex))
            print "Starting"
            self.pulserHardware.ppStart()
            self.running = True
            self.updateProgressBar(self.currentIndex,max(len(self.scan.list),1))
            self.timestampsNewRun = False
            print "continued"
        elif self.state == self.OpStates.running:
            self.pulserHardware.ppStop()
            self.updateProgressBar(self.currentIndex,max(len(self.scan.list),1))
            self.state = self.OpStates.paused
    
    def onStop(self):
        if self.running:
            self.pulserHardware.ppStop()
            self.pulserHardware.ppClearWriteFifo()
            self.pulserHardware.ppFlushData()
            self.running = False
            if self.scan.rewriteDDS:
                self.NeedsDDSRewrite.emit()
            self.state = self.OpStates.idle
        self.updateProgressBar(self.currentIndex+1,max(len(self.scan.list),1))
        self.finalizeData(reason='stopped')

    def traceFilename(self, pattern):
        directory = DataDirectory.DataDirectory()
        if pattern and pattern!='':
            filename, components = directory.sequencefile(pattern)
            return filename
        else:
            path = str(QtGui.QFileDialog.getSaveFileName(self, 'Save file',directory.path()))
            return path
            
    def onData(self, data ):
        """ Called by worker with new data
        """
        if data.overrun:
            print "Read Pipe Overrun"
            self.onPause()
        else:
            print "onData", [len(data.count[i]) for i in range(16)], data.scanvalue
            print self.scan.evalAlgo.evaluate( data.count[self.scan.counterChannel] )
            # Evaluate as given in evalList
            x = self.generator.xValue(self.currentIndex)
            evaluated = list()
            for eval, algo in zip(self.scan.evalList,self.scan.evalAlgorithmList):
                evaluated.append( algo.evaluate( data.count[eval.counter])) # returns mean, error, raw
            if data.other:
                print "Other:", data.other
            if len(evaluated)>0:
                self.displayUi.add( evaluated[0][0] )
                self.updateMainGraph(x, evaluated )
                self.showHistogram(data, self.scan.evalList[0].counter )
            self.currentIndex += 1
            if self.scan.enableTimestamps: 
                self.showTimestamps(data)
            if data.final:
                self.finalizeData(reason='end of scan')
                print "current index", self.currentIndex, "expected", len(self.scan.list)
                if self.currentIndex >= len(self.scan.list):    # if all points were taken
                    self.generator.dataOnFinal(self)
                else:
                    self.state = self.OpStates.paused
            else:
                mycode = self.generator.dataNextCode(self)
                if mycode:
                    self.pulserHardware.ppWriteData(mycode)     
            self.updateProgressBar(self.currentIndex,max(len(self.scan.list),1))

    def updateMainGraph(self, x, evaluated): # evaluated is list of mean, error, raw
        print x, mean, error
        if not self.plottedTraceList:
            trace = Trace()
            self.plottedTraceList = list()
            for index, result in enumerate(evaluated):
                mean, error, raw = result
                yColumnName = 'y{0}'.format(index)
                rawColumnName = 'raw{0}'.fromat(index)
                trace.addColumn( yColumnName )
                if error and self.scan.evalAlgo.settings['errorBars']:
                    topColumnName = 'top{0}'.format(index)
                    bottomColumnName = 'bottom{0}'.format(index)
                    trace.addColumn( topColumnName )
                    trace.addColumn( bottomColumnName )                
                self.plottedTraceList.append(  Traceui.PlottedTrace(trace, self.graphicsView, pens.penList, 
                                                            yColumnName=yColumnName, topColumnName=topColumnName, bottomColumnName=bottomColumnName) )                
                self.plottedTrace.trace.name = self.scan.settingsName
                self.plottedTrace.trace.vars.comment = ""
                self.plottedTrace.trace.filenameCallback = functools.partial( self.plottedTrace.traceFilename, self.scan.filename )
                self.generator.appendData(self.plottedTrace, x, mean, raw, error)
                xRange = self.generator.xRange()
                if xRange:
                    self.graphicsView.setXRange( *xRange )     
                if (self.scan.scanRepeat == 1) and (self.scan.scanMode != 1): #scanMode == 1 corresponds to step in place.           
                    self.traceui.addTrace(self.plottedTrace, pen=-1, parentTrace=self.averagePlottedTraceList[index])
                else:
                    self.traceui.addTrace(self.plottedTrace, pen=-1)
                pulseProgramHeader = stringutilit.commentarize( self.pulseProgramUi.documentationString() )
                scanHeader = stringutilit.commentarize( self.scan.documentationString() )
                self.plottedTrace.trace.header = '\n'.join((pulseProgramHeader, scanHeader))
        else:
            for plottedTrace, result in zip(self.plottedTraceList, evaluated):
                mean, error, raw = result
                self.generator.appendData(plottedTrace, x, mean, raw, error)
                plottedTrace.replot()

    def finalizeData(self, reason='end of scan'):
        print "finalize Data"
        for trace in [self.plottedTrace.trace, self.currentTimestampTrace]:
            if trace:
                trace.vars.traceFinalized = datetime.now()
                trace.resave(saveIfUnsaved=self.scan.autoSave)
        if (self.scan.scanRepeat == 1) and (self.scan.scanMode != 1): #scanMode == 1 corresponds to step in place.
            if reason == 'end of scan': #We only re-average the data if finalizeData is called because a scan ended
                averagePlottedTrace = None
                for averagePlottedTrace in self.averagePlottedTraceList:
                    averagePlottedTrace.averageChildren()
                    averagePlottedTrace.plot(7) #average trace is plotted in black
                if averagePlottedTrace:
                    self.scanControlWidget.scansAveraged.setText("Scans averaged: {0}".format(averagePlottedTrace.childCount()))
                    averagePlottedTrace.trace.resave(saveIfUnsaved=self.scan.autoSave)
            
    def showTimestamps(self,data):
        bins = int( (self.scan.roiWidth/self.scan.binwidth).toval() )
        multiplier = self.pulserHardware.timestep.toval('ms')
        myrange = (self.scan.roiStart.toval('ms')/multiplier,(self.scan.roiStart+self.scan.roiWidth).toval('ms')/multiplier)
        y, x = numpy.histogram( data.timestamp[self.scan.timestampsChannel], 
                                range=myrange,
                                bins=bins)
        x = x[0:-1] * multiplier
                                
        if self.currentTimestampTrace and numpy.array_equal(self.currentTimestampTrace.x,x) and (
            self.scan.integrateTimestamps == self.scanControlWidget.integrationMode.IntegrateAll or 
                (self.scan.integrateTimestamps == self.scanControlWidget.integrationMode.IntegrateRun and not self.timestampsNewRun) ) :
            self.currentTimestampTrace.y += y
            self.plottedTimestampTrace.replot()
            if self.currentTimestampTrace.rawdata:
                self.currentTimestampTrace.rawdata.addInt(data.timestamp[self.scan.timestampsChannel])
        else:    
            self.currentTimestampTrace = Trace.Trace()
            if self.scan.saveRawData:
                self.currentTimestampTrace.rawdata = RawData()
                self.currentTimestampTrace.rawdata.addInt(data.timestamp[self.scan.timestampsChannel])
            self.currentTimestampTrace.x = x
            self.currentTimestampTrace.y = y
            self.currentTimestampTrace.name = self.scan.settingsName
            self.currentTimestampTrace.vars.comment = ""
            self.currentTimestampTrace.filenameCallback = functools.partial( self.traceFilename, "Timestamp_"+self.scan.filename )
            self.plottedTimestampTrace = Traceui.PlottedTrace(self.currentTimestampTrace,self.timestampView,pens.penList)
            self.timestampTraceui.addTrace(self.plottedTimestampTrace,pen=-1)              
            pulseProgramHeader = stringutilit.commentarize( self.pulseProgramUi.documentationString() )
            scanHeader = stringutilit.commentarize( repr(self.scan) )
            self.plottedTimestampTrace.trace.header = '\n'.join((pulseProgramHeader, scanHeader)) 
        self.timestampsNewRun = False                       
        
    def showHistogram(self, data, channel):
        y, x = numpy.histogram( data.count[channel] , range=(0,self.scan.histogramBins), bins=self.scan.histogramBins)
        if self.scan.integrateHistogram and hasattr(self,'histx') and numpy.array_equal(self.histx,x):
            self.histy += y
        else:
            self.histx, self.histy = x, y
        if self.histogramCurve is None:
            self.histogramCurve = pyqtgraph.PlotCurveItem(self.histx, self.histy, stepMode=True, fillLevel=0, brush=(0, 0, 255, 80))
            self.histogramView.addItem(self.histogramCurve)
        else:
            self.histogramCurve.setData( self.histx, self.histy )
        
        
    def activate(self):
        MainWindowWidget.MainWindowWidget.activate(self)
        if (self.deviceSettings is not None) and (not self.activated):
            try:
                print "Scan activated"
                self.pulserHardware.ppFlushData()
                self.pulserHardware.dataAvailable.connect(self.onData)
                self.activated = True
            except Exception as ex:
                print ex
                self.StatusMessage.emit( ex.message )
    
    def deactivate(self):
        MainWindowWidget.MainWindowWidget.deactivate(self)
        if self.activated :
            print "Scan deactivated",
            self.pulserHardware.dataAvailable.disconnect(self.onData)
            self.activated = False
            self.state = self.OpStates.idle
                
    def onClose(self):
        self.config[self.experimentName+'.MainWindow.State'] = QtGui.QMainWindow.saveState(self)
        self.config[self.experimentName+'.pyqtgraph-dokareastate'] = self.area.saveState()
        self.scanControlWidget.onClose()
        self.traceui.onClose()

        
