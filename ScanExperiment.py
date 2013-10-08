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
import Trace
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
import CoordinatePlotWidget
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
            experiment.onStart()
        else:
            experiment.onStop()                   
    
    def xRange(self):
        return self.scan.start.ounit(self.scan.xUnit).toval(), self.scan.stop.ounit(self.scan.xUnit).toval()
                                     
    def appendData(self,trace,x,y,raw,error):                                     
        trace.x = numpy.append(trace.x, x)
        trace.y = numpy.append(trace.y, y)
        trace.raw = numpy.append(trace.raw, raw)
        if error and self.scan.errorBars:
            trace.bottom = numpy.append(trace.bottom, error[0])
            trace.top = numpy.append(trace.top, error[1])
                
class StepInPlaceGenerator:
    def __init__(self, scan):
        self.scan = scan
        
    def prepare(self, pulseProgramUi ):
        self.stepInPlaceValue = pulseProgramUi.getVariableValue(self.scan.scanParameter)
        self.scan.code = pulseProgramUi.pulseProgram.variableScanCode(self.scan.scanParameter, [self.stepInPlaceValue])
        return (pulseProgramUi.pulseProgram.variableScanCode(self.scan.scanParameter, [self.stepInPlaceValue]*5) , [])

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
            if error and self.scan.errorBars:
                trace.bottom = numpy.append(trace.bottom, error[0])
                trace.top = numpy.append(trace.top, error[1])
        else:
            steps = int(self.scan.steps)
            trace.x = numpy.append(trace.x[-steps+1:], x)
            trace.y = numpy.append(trace.y[-steps+1:], y)
            trace.raw = numpy.append(trace.raw[-steps+1:], raw)
            if error and self.scan.errorBars:
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
        if error and self.scan.errorBars:
            trace.bottom = numpy.append(trace.bottom, error[0])
            trace.top = numpy.append(trace.top, error[1])

    def dataOnFinal(self, experiment):
        if self.scan.scanRepeat == 1:
            experiment.onStart()
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
        self.currentTrace = None
        self.currentIndex = 0
        self.activated = False
        self.histogramCurve = None
        self.timestampCurve = None
        self.running = False
        self.currentTimestampTrace = None
        self.experimentName = experimentName
        self.globalVariables = dict()

    def setupUi(self,MainWindow,config):
        ScanExperimentForm.setupUi(self,MainWindow)
        self.config = config
        self.area = DockArea()
        self.setCentralWidget(self.area)
        # initialize all the plot windows we want
        self.mainDock = Dock("Scan data")
        self.histogramDock = Dock("Histogram")
        self.averageDock = Dock("average")
        self.timestampDock = Dock("timestamps")
        self.area.addDock(self.mainDock,'left')
        self.area.addDock(self.histogramDock,'right')
        self.area.addDock(self.averageDock,'bottom',self.histogramDock)
        self.area.addDock(self.timestampDock,'bottom',self.averageDock)
        self.graphicsWidget = CoordinatePlotWidget.CoordinatePlotWidget(self) # self.graphicsLayout.graphicsView
        self.mainDock.addWidget(self.graphicsWidget)
        self.graphicsView = self.graphicsWidget.graphicsView
        self.histogramView = pyqtgraph.PlotWidget()
        self.histogramDock.addWidget( self.histogramView)
        self.averageView = pyqtgraph.PlotWidget()       
        self.averageDock.addWidget( self.averageView )
        self.timestampWidget = CoordinatePlotWidget.CoordinatePlotWidget(self) # pyqtgraph.PlotWidget()
        self.timestampDock.addWidget( self.timestampWidget )
        self.timestampView = self.timestampWidget.graphicsView
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
        expected = elapsed / (self.currentIndex/float(len(self.scan.list))) if self.currentIndex>0 else 0
        self.scanControlWidget.timeLabel.setText( "{0} / {1}".format(timedelta(seconds=round(elapsed)),
                                                 timedelta(seconds=round(expected)))) 
    
    def onStart(self):
        self.startTime = time.time()
        self.state = self.OpStates.running
        PulseProgramBinary = self.pulseProgramUi.getPulseProgramBinary() # also overwrites the current variable values            
        self.scan = self.scanControlWidget.getScan()
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
        if self.currentTrace is not None:
            if self.scan.autoSave:
                self.currentTrace.resave()
            self.currentTrace = None
        self.scanControlWidget.progressBar.setRange(0,len(self.scan.list))
        self.scanControlWidget.progressBar.setValue(0)
        self.scanControlWidget.progressBar.setStyleSheet("")
        self.scanControlWidget.progressBar.setVisible( True )
        self.scanControlWidget.timeLabel.setVisible( True )
        self.setTimeLabel()
        self.timestampsNewRun = True
        self.displayUi.onClear()
        print "elapsed time", time.time()-self.startTime
    
    def onPause(self):
        if self.state == self.OpStates.paused:
            self.state = self.OpStates.running
            self.pulserHardware.ppFlushData()
            self.pulserHardware.ppClearWriteFifo()
            self.pulserHardware.ppWriteData(self.generator.restartCode(self.currentIndex))
            print "Starting"
            self.pulserHardware.ppStart()
            self.running = True
            self.scanControlWidget.progressBar.setRange(0,len(self.scan.list))
            self.scanControlWidget.progressBar.setValue(self.currentIndex)
            self.scanControlWidget.progressBar.setStyleSheet("")
            self.scanControlWidget.progressBar.setVisible( True )
            self.scanControlWidget.timeLabel.setVisible( True )
            self.setTimeLabel()
            self.timestampsNewRun = False
            print "continued"
        elif self.state == self.OpStates.running:
            self.pulserHardware.ppStop()
            self.scanControlWidget.progressBar.setStyleSheet(StyleSheets.RedProgressBar)
            self.state = self.OpStates.paused
            
    
    def onStop(self):
        if self.running:
            self.pulserHardware.ppStop()
            self.pulserHardware.ppClearWriteFifo()
            self.pulserHardware.ppFlushData()
            self.running = False
            if self.scan.rewriteDDS:
                self.NeedsDDSRewrite.emit()
        self.scanControlWidget.progressBar.setVisible( False )
        self.scanControlWidget.timeLabel.setVisible( False )
        self.finalizeData()

    def traceFilename(self, pattern):
        directory = DataDirectory.DataDirectory()
        if pattern and pattern!='':
            filename, components = directory.sequencefile( pattern )
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
            mean, error, raw = self.scan.evalAlgo.evaluate( data.count[self.scan.counterChannel] )
            self.displayUi.add( mean )
            if data.other:
                print "Other:", data.other
            #mean = numpy.mean( data.count[self.scan.counterChannel] )
            x = self.generator.xValue(self.currentIndex)
            if mean is not None:
                self.updateMainGraph(x, mean, error, raw)
            self.currentIndex += 1
            self.showHistogram(data)
            if self.scan.enableTimestamps: 
                self.showTimestamps(data)
            if data.final:
                self.finalizeData()
                print "current index", self.currentIndex, "expected", len(self.scan.list)
                if self.currentIndex >= len(self.scan.list):
                    self.generator.dataOnFinal(self)
                else:
                    self.state = self.OpStates.paused
                    self.scanControlWidget.progressBar.setStyleSheet(StyleSheets.RedProgressBar)
            else:
                mycode = self.generator.dataNextCode(self)
                if mycode:
                    self.pulserHardware.ppWriteData(mycode)     
            self.scanControlWidget.progressBar.setValue(self.currentIndex)
            self.setTimeLabel()


    def updateMainGraph(self, x, mean, error, raw):
        print x, mean, error
        if self.currentTrace is None:
            self.currentTrace = Trace.Trace()
            self.currentTrace.x = numpy.array([x])
            self.currentTrace.y = numpy.array([mean])
            self.currentTrace.raw = numpy.array([raw])
            if error and self.scan.errorBars:
                self.currentTrace.bottom = numpy.array([error[0]])
                self.currentTrace.top = numpy.array([error[1]])
            self.currentTrace.name = self.scan.scanParameter
            self.currentTrace.vars.comment = ""
            self.currentTrace.filenameCallback = functools.partial( self.traceFilename, self.scan.filename )
            self.plottedTrace = Traceui.PlottedTrace(self.currentTrace,self.graphicsView,pens.penList)
            xRange = self.generator.xRange()
            if xRange:
                self.graphicsView.setXRange( *xRange )                
            self.traceui.addTrace(self.plottedTrace,pen=-1)
            pulseProgramHeader = stringutilit.commentarize( self.pulseProgramUi.documentationString() )
            scanHeader = stringutilit.commentarize( repr(self.scan) )
            self.currentTrace.header = '\n'.join((pulseProgramHeader, scanHeader)) 
        else:
            self.generator.appendData(self.currentTrace, x, mean, raw, error)
            self.plottedTrace.replot()

    def finalizeData(self):
        print "finalize Data"
        for trace in [self.currentTrace, self.currentTimestampTrace]:
            if trace:
                trace.vars.traceFinalized = datetime.now()
                trace.resave(saveIfUnsaved=self.scan.autoSave)
            
        
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
            self.currentTimestampTrace.name = self.scan.name
            self.currentTimestampTrace.vars.comment = ""
            self.currentTimestampTrace.filenameCallback = functools.partial( self.traceFilename, "Timestamp_"+self.scan.filename )
            self.plottedTimestampTrace = Traceui.PlottedTrace(self.currentTimestampTrace,self.timestampView,pens.penList)
            self.timestampTraceui.addTrace(self.plottedTimestampTrace,pen=-1)              
            pulseProgramHeader = stringutilit.commentarize( self.pulseProgramUi.documentationString() )
            scanHeader = stringutilit.commentarize( repr(self.scan) )
            self.currentTrace.header = '\n'.join((pulseProgramHeader, scanHeader)) 
        self.timestampsNewRun = False                       
        
    def showHistogram(self, data):
        y, x = numpy.histogram( data.count[self.scan.counterChannel] , range=(0,self.scan.histogramBins), bins=self.scan.histogramBins)
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

    def updateSettings(self,settings,active=False):
        """ Main program settings have changed
        """
        self.deviceSettings = settings
        