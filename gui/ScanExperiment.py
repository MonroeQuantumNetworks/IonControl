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

from datetime import datetime, timedelta
import functools
import logging
import random
import time
from trace import Traceui
from trace import pens
import os.path

from PyQt4 import QtGui, QtCore
import PyQt4.uic
import numpy
from pyqtgraph.dockarea import DockArea, Dock
from pyqtgraph.graphicsItems.ViewBox import ViewBox
from pyqtgraph.exporters.ImageExporter import ImageExporter

from AverageViewTable import AverageViewTable
import MainWindowWidget
from trace import RawData
from scan.ScanControl import ScanControl
from scan.EvaluationControl import EvaluationControl
from ScanProgress import ScanProgress
from fit.FitUi import FitUi
from modules import DataDirectory
from modules import enum
from modules import stringutilit
from modules import magnitude
from trace.PlottedTrace import PlottedTrace
from trace.Trace import Trace
from uiModules.CoordinatePlotWidget import CoordinatePlotWidget
from modules import WeakMethod
import copy
from modules.Expression import Expression
from modules.SceneToPrint import SceneToPrint
from collections import defaultdict

ScanExperimentForm, ScanExperimentBase = PyQt4.uic.loadUiType(r'ui\ScanExperiment.ui')

ExpectedLoopkup = { 'd': 0, 'u' : 1, '1':0.5, '-1':0.5, 'i':0.5, '-i':0.5 }

class ScanException(Exception):
    pass

class ParameterScanGenerator:
    expression = Expression()
    def __init__(self, scan):
        self.scan = scan
        self.nextIndexToWrite = 0
        self.numUpdatedVariables = 1
        
    def prepare(self, pulseProgramUi, maxUpdatesToWrite=None ):
        if self.scan.gateSequenceUi.settings.enabled:
            _, data, self.gateSequenceSettings = self.scan.gateSequenceUi.gateSequenceScanData()    
        else:
            data = []
        self.scan.code, self.numVariablesPerUpdate = pulseProgramUi.variableScanCode(self.scan.scanParameter, self.scan.list, extendedReturn=True)
        self.numUpdatedVariables = len(self.scan.code)/2/len(self.scan.list)
        maxWordsToWrite = 2040 if maxUpdatesToWrite is None else 2*self.numUpdatedVariables*maxUpdatesToWrite
        self.maxUpdatesToWrite = maxUpdatesToWrite
        if len(self.scan.code)>maxWordsToWrite:
            self.nextIndexToWrite = maxWordsToWrite
            return ( self.scan.code[:maxWordsToWrite], data)
        self.nextIndexToWrite = len(self.scan.code)
        return ( self.scan.code, data)
        
    def restartCode(self,currentIndex ):
        maxWordsToWrite = 2040 if self.maxUpdatesToWrite is None else 2*self.numUpdatedVariables*self.maxUpdatesToWrite
        currentWordCount = 2*self.numUpdatedVariables*currentIndex
        if len(self.scan.code)-currentWordCount>maxWordsToWrite:
            self.nextIndexToWrite = maxWordsToWrite+currentWordCount
            return ( self.scan.code[currentWordCount:self.nextIndexToWrite])
        self.nextIndexToWrite = len(self.scan.code)
        return self.scan.code[currentWordCount:]
        
    def xValue(self, index):
        value = self.scan.list[index]
        if self.scan.xExpression:
            value = self.expression.evaluate( self.scan.xExpression, {"x": value} )
        if (not self.scan.xUnit and not value.dimensionless()) or not value.has_dimension(self.scan.xUnit):
            self.scan.xUnit = value.suggestedUnit() 
        return value.ounit(self.scan.xUnit).toval()
        
    def dataNextCode(self, experiment ):
        if self.nextIndexToWrite<len(self.scan.code):
            start = self.nextIndexToWrite
            self.nextIndexToWrite = min( len(self.scan.code)+1, self.nextIndexToWrite + 2*self.numUpdatedVariables )
            return self.scan.code[start:self.nextIndexToWrite]
        return []
        
    def dataOnFinal(self, experiment, currentState):
        if self.scan.scanRepeat == 1 and currentState == ScanExperiment.OpStates.running:
            experiment.startScan()
        else:
            experiment.onStop()                   
    
    def xRange(self):
        return self.scan.start.ounit(self.scan.xUnit).toval(), self.scan.stop.ounit(self.scan.xUnit).toval()
                                     
    def appendData(self,traceList,x,evaluated):
        if evaluated and traceList:
            traceList[0].x = numpy.append(traceList[0].x, x)
        for trace, (y, error, raw) in zip(traceList, evaluated):                                  
            trace.y = numpy.append(trace.y, y)
            trace.raw = numpy.append(trace.raw, raw)
            if error is not None:
                trace.bottom = numpy.append(trace.bottom, error[0])
                trace.top = numpy.append(trace.top, error[1])
                
    def expected(self, index):
        return None
                
class StepInPlaceGenerator:
    def __init__(self, scan):
        self.scan = scan
        
    def prepare(self, pulseProgramUi, maxUpdatesToWrite=None ):
        if self.scan.gateSequenceUi.settings.enabled:
            _, data, self.gateSequenceSettings = self.scan.gateSequenceUi.gateSequenceScanData()    
        else:
            data = []
        #self.stepInPlaceValue = pulseProgramUi.getVariableValue(self.scan.scanParameter)
        self.stepInPlaceValue = 0
        self.scan.code = [4095, 0] # writing the last memory location
        #self.scan.code = pulseProgramUi.pulseProgram.variableScanCode(self.scan.scanParameter, [self.stepInPlaceValue])
        return (self.scan.code*5, data) # write 5 points to the fifo queue at start,
                        # this prevents the Step in Place from stopping in case the computer lags behind evaluating by up to 5 points

    def restartCode(self,currentIndex):
        return self.scan.code * 5
        
    def dataNextCode(self, experiment):
        return self.scan.code
        
    def xValue(self,index):
        return index

    def xRange(self):
        return []

    def appendData(self,traceList,x,evaluated):
        if evaluated and traceList:
            if len(traceList[0].x)<self.scan.steps or self.scan.steps==0:
                traceList[0].x = numpy.append(traceList[0].x, x)
                for trace, (y, error, raw) in zip(traceList, evaluated):                                  
                    trace.y = numpy.append(trace.y, y)
                    trace.raw = numpy.append(trace.raw, raw)
                    if error is not None:
                        trace.bottom = numpy.append(trace.bottom, error[0])
                        trace.top = numpy.append(trace.top, error[1])
            else:
                steps = int(self.scan.steps)
                traceList[0].x = numpy.append(traceList[0].x[-steps+1:], x)
                for trace, (y, error, raw) in zip(traceList, evaluated):                                  
                    trace.y = numpy.append(trace.y[-steps+1:], y)
                    trace.raw = numpy.append(trace.raw[-steps+1:], raw)
                    if error is not None:
                        trace.bottom = numpy.append(trace.bottom[-steps+1:], error[0])
                        trace.top = numpy.append(trace.top[-steps+1:], error[1])

    def dataOnFinal(self, experiment, currentState):
        experiment.onStop()                   

    def expected(self, index):
        return None

class GateSequenceScanGenerator:
    def __init__(self, scan):
        self.scan = scan
        self.nextIndexToWrite = 0
        self.numUpdatedVariables = 1
        self.maxWordsToWrite = 2040
        
    def prepare(self, pulseProgramUi, maxUpdatesToWrite=None):
        logger = logging.getLogger(__name__)
        self.maxUpdatesToWrite = maxUpdatesToWrite
        address, data, self.gateSequenceSettings = self.scan.gateSequenceUi.gateSequenceScanData()
        self.gateSequenceAttributes = self.scan.gateSequenceUi.gateSequenceAttributes()
        parameter = self.gateSequenceSettings.startAddressParam
        logger.debug( "GateSequenceScan {0} {1}".format( address, parameter ) )
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
        self.numVariablesPerUpdate = 1
        logger.debug( "GateSequenceScanCode {0} {1}".format(self.scan.list, self.scan.code) )
        if self.scan.gateSequenceSettings.debug:
            dumpFilename, _ = DataDirectory.DataDirectory().sequencefile("fpga_sdram.bin")
            with open( dumpFilename, 'wb') as f:
                f.write( bytearray(numpy.array(data, dtype=numpy.int32).view(dtype=numpy.int8)) )
            codeFilename, _ = DataDirectory.DataDirectory().sequencefile("start_address.txt")
            with open( codeFilename, 'w') as f:
                for a in self.scan.code[1::2]:
                    f.write( "{0}\n".format(a) )
            codeFilename, _ = DataDirectory.DataDirectory().sequencefile("start_address_sorted.txt")
            with open( codeFilename, 'w') as f:
                for index, a in enumerate(sorted(self.scan.code[1::2])):
                    f.write( "{0} {1}\n".format(index, a) )
        if len(self.scan.code)>self.maxWordsToWrite:
            self.nextIndexToWrite = self.maxWordsToWrite
            return ( self.scan.code[:self.maxWordsToWrite], data)
        self.nextIndexToWrite = len(self.scan.code)
        return ( self.scan.code, data)

    def restartCode(self,currentIndex):
        currentWordCount = 2*self.numUpdatedVariables*currentIndex
        if len(self.scan.code)-currentWordCount>self.maxWordsToWrite:
            self.nextIndexToWrite = self.maxWordsToWrite+currentWordCount
            return ( self.scan.code[currentWordCount:self.nextIndexToWrite])
        self.nextIndexToWrite = len(self.scan.code)
        return self.scan.code[currentWordCount:]

    def xValue(self,index):
        return self.scan.index[index]

    def dataNextCode(self, experiment):
        if self.nextIndexToWrite<len(self.scan.code):
            start = self.nextIndexToWrite
            self.nextIndexToWrite = min( len(self.scan.code)+1, self.nextIndexToWrite + 2*self.numUpdatedVariables )
            return self.scan.code[start:self.nextIndexToWrite]
        return []
        
    def xRange(self):
        return [0, len(self.scan.list)]

    def appendData(self,traceList,x,evaluated):
        if evaluated and traceList:
            traceList[0].x = numpy.append(traceList[0].x, x)
        for trace, (y, error, raw) in zip(traceList, evaluated):                                  
            trace.y = numpy.append(trace.y, y)
            trace.raw = numpy.append(trace.raw, raw)
            if error is not None:
                trace.bottom = numpy.append(trace.bottom, error[0])
                trace.top = numpy.append(trace.top, error[1])

    def dataOnFinal(self, experiment, currentState):
        if self.scan.scanRepeat == 1 and currentState==ScanExperiment.OpStates.running:
            experiment.startScan()
        else:
            experiment.onStop()                   

    def expected(self, index):
        if self.gateSequenceAttributes is not None:
            try:
                expected = ExpectedLoopkup[ self.gateSequenceAttributes[self.scan.index[index]]['expected'] ]
            except (IndexError, KeyError):
                expected = None
            return expected
        return None 
        
GeneratorList = [ParameterScanGenerator, StepInPlaceGenerator, GateSequenceScanGenerator]   

class ScanExperiment(ScanExperimentForm, MainWindowWidget.MainWindowWidget):
    StatusMessage = QtCore.pyqtSignal( str )
    ClearStatusMessage = QtCore.pyqtSignal()
    NeedsDDSRewrite = QtCore.pyqtSignal()
    plotsChanged = QtCore.pyqtSignal()
    OpStates = enum.enum('idle','running','paused','starting','stopping', 'interrupted')
    experimentName = 'Scan Sequence'
    statusChanged = QtCore.pyqtSignal( object )
    scanConfigurationListChanged = None
    evaluationConfigurationChanged = None
    def __init__(self,settings,pulserHardware,globalVariablesUi, experimentName,toolBar=None,parent=None):
        MainWindowWidget.MainWindowWidget.__init__(self,toolBar=toolBar,parent=parent)
        ScanExperimentForm.__init__(self)
        self.deviceSettings = settings
        self.pulserHardware = pulserHardware
        self.plottedTraceList = list()
        self.averagePlottedTraceList = list()
        self.currentIndex = 0
        self.activated = False
        self.histogramCurveList = list()
        self.timestampCurve = None
        self.currentTimestampTrace = None
        self.experimentName = experimentName
        self.globalVariables = dict()
        self.histogramList = list()
        self.histogramTrace = None
        self.interruptReason = ""
        self.scan = None
        self.otherDataFile = None
        self.enableParameter = True
        self.enableExternalParameter = False
        self.histogramBuffer = defaultdict( list )
        self.globalVariables = globalVariablesUi.variables
        self.globalVariablesChanged = globalVariablesUi.valueChanged
        self.globalVariablesUi = globalVariablesUi        

    def setupUi(self,MainWindow,config):
        logger = logging.getLogger(__name__)
        ScanExperimentForm.setupUi(self,MainWindow)
        self.config = config
        self.area = DockArea()
        self.setCentralWidget(self.area)
        self.plotDict = dict()
        if self.experimentName+'.plotNames' in self.config:
            plotNames = self.config[self.experimentName+'.plotNames']
        else:
            plotNames = {"Scan Data", "Histogram", "Timestamps"}
        if "Scan Data" not in plotNames:
            plotNames.append("Scan Data")
        if "Histogram" not in plotNames:
            plotNames.append("Histogram")
        if "Timestamps" not in plotNames:
            plotNames.append("Timestamps")
        # initialize all the plot windows we want
        for name in plotNames:
            dock = Dock(name)
            widget = CoordinatePlotWidget(self, name=name)
            view = widget._graphicsView
            self.area.addDock(dock, "bottom")
            dock.addWidget(widget)
            self.plotDict[name] = {"dock":dock, "widget":widget, "view":view}
            del dock, widget, view #This is probably unnecessary, but can't hurt
        del plotNames #I don't want to leave this list around, as it is not updated and may cause confusion.
        self.plotDict["Histogram"]["widget"].autoRange()
        self.plotDict["Timestamps"]["widget"].autoRange()
        try:
            if self.experimentName+'.pyqtgraph-dockareastate' in self.config:
                self.area.restoreState(self.config[self.experimentName+'.pyqtgraph-dockareastate'])
        except Exception as e:
            logger.error("Cannot restore dock state in experiment {0}. Exception occurred: ".format(self.experimentName) + str(e))
        # Traceui
        self.penicons = pens.penicons().penicons()
        self.traceui = Traceui.Traceui(self.penicons,self.config,self.experimentName,self.plotDict)
        self.traceui.setupUi(self.traceui)
        # traceui for timestamps
        self.timestampTraceui = Traceui.Traceui(self.penicons,self.config,self.experimentName+"-timestamps",self.plotDict)
        self.timestampTraceui.setupUi(self.timestampTraceui)
        self.timestampTraceuiDock = self.setupAsDockWidget(self.timestampTraceui, "Timestamp traces", QtCore.Qt.LeftDockWidgetArea)
        # new fit widget
        self.fitWidget = FitUi(self.traceui,self.config,self.experimentName, globalDict = self.globalVariablesUi.variables )
        self.fitWidget.setupUi(self.fitWidget)
        self.globalVariablesUi.valueChanged.connect( self.fitWidget.evaluate )
        self.fitWidgetDock = self.setupAsDockWidget(self.fitWidget, "Fit", QtCore.Qt.LeftDockWidgetArea, stackAbove=self.timestampTraceuiDock)
        # TraceuiDock
        self.traceuiDock = self.setupAsDockWidget(self.traceui, "Traces", QtCore.Qt.LeftDockWidgetArea, stackAbove=self.fitWidgetDock )
        # ScanProgress
        self.progressUi = ScanProgress()
        self.progressUi.setupUi()
        self.stateChanged = self.progressUi.stateChanged
        self.setupAsDockWidget(self.progressUi, "Progress", QtCore.Qt.RightDockWidgetArea)
        # Average View
        self.displayUi = AverageViewTable(self.config)
        self.displayUi.setupUi()
        self.setupAsDockWidget(self.displayUi, "Average", QtCore.Qt.RightDockWidgetArea)
        # Scan Control
        self.scanControlWidget = ScanControl(config, self.globalVariablesUi, self.experimentName, internalParam=self.enableParameter, externalParam=self.enableExternalParameter )
        self.scanControlWidget.setupUi(self.scanControlWidget)
        self.setupAsDockWidget( self.scanControlWidget, "Scan Control", QtCore.Qt.RightDockWidgetArea)
        self.scanConfigurationListChanged = self.scanControlWidget.scanConfigurationListChanged
        # EvaluationControl
        self.evaluationControlWidget = EvaluationControl(config, self.globalVariablesUi, self.experimentName, self.plotDict.keys(), analysisNames=self.fitWidget.analysisNames() )
        self.evaluationControlWidget.setupUi(self.evaluationControlWidget)
        self.fitWidget.analysisNamesChanged.connect( self.evaluationControlWidget.setAnalysisNames )
        self.setupAsDockWidget( self.evaluationControlWidget, "Evaluation Control", QtCore.Qt.RightDockWidgetArea)
        self.evaluationConfigurationChanged = self.evaluationControlWidget.evaluationConfigurationChanged

        if self.experimentName+'.MainWindow.State' in self.config:
            QtGui.QMainWindow.restoreState(self,self.config[self.experimentName+'.MainWindow.State'])
        
        #toolBar actions
        self.copyHistogram = QtGui.QAction( QtGui.QIcon(":/openicon/icons/office-chart-bar.png"), "Copy histogram to traces", self ) 
        self.copyHistogram.setToolTip("Copy histogram to traces")
        self.copyHistogram.triggered.connect( self.onCopyHistogram )
        self.actionList.append( self.copyHistogram )
        
        self.saveHistogram = QtGui.QAction( QtGui.QIcon(":/openicon/icons/office-chart-bar-save.png"), "Save histograms", self ) 
        self.saveHistogram.setToolTip("Save histograms for last run to file")
        self.saveHistogram.triggered.connect( self.onSaveHistogram )
        self.actionList.append( self.saveHistogram )

        self.addPlot = QtGui.QAction( QtGui.QIcon(":/openicon/icons/add-plot.png"), "Add new plot", self)
        self.addPlot.setToolTip("Add new plot")
        self.addPlot.triggered.connect(self.onAddPlot)
        self.actionList.append(self.addPlot)
        
        self.removePlot = QtGui.QAction( QtGui.QIcon(":/openicon/icons/remove-plot.png"), "Remove a plot", self)
        self.removePlot.setToolTip("Remove a plot")
        self.removePlot.triggered.connect(self.onRemovePlot)
        self.actionList.append(self.removePlot)

        self.renamePlot = QtGui.QAction( QtGui.QIcon(":/openicon/icons/rename-plot.png"), "Rename a plot", self)
        self.renamePlot.setToolTip("Rename a plot")
        self.renamePlot.triggered.connect(self.onRenamePlot)
        self.actionList.append(self.renamePlot)
        
        self.fitWidget.addPushDestination('Global', self.globalVariablesUi )

        
    def printTargets(self):
        return self.plotDict.keys()

    def addPushDestination(self, name, destination):
        self.fitWidget.addPushDestination(name, destination)
        
    def setupAsDockWidget(self, widget, name, area=QtCore.Qt.RightDockWidgetArea, stackAbove=None, stackBelow=None ):
        dock = QtGui.QDockWidget(name)
        dock.setObjectName(name)
        dock.setWidget( widget )
        self.addDockWidget(area , dock )
        self.dockWidgetList.append( dock )
        if stackAbove is not None:
            self.tabifyDockWidget( stackAbove, dock )
        elif stackBelow is not None:
            self.tabifyDockWidget( dock, stackBelow )
        return dock           

    def setPulseProgramUi(self,pulseProgramUi):
        self.pulseProgramUi = pulseProgramUi.addExperiment(self.experimentName, self.globalVariables, self.globalVariablesChanged )
        self.scanControlWidget.setVariables( self.pulseProgramUi.pulseProgram.variabledict )
        self.pulseProgramUi.pulseProgramChanged.connect( self.updatePulseProgram )
        self.scanControlWidget.setPulseProgramUi( self.pulseProgramUi )
        
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
        expected = elapsed / ((self.currentIndex)/float(max(len(self.scan.list),1))) if self.currentIndex>0 else 0
        self.scanControlWidget.timeLabel.setText( "{0} / {1}".format(timedelta(seconds=round(elapsed)),
                                                 timedelta(seconds=round(expected)))) 
 
    def onStart(self):
        self.scan = self.scanControlWidget.getScan()
        self.evaluation = self.evaluationControlWidget.getEvaluation()
        self.displayUi.setNames( [evaluation.name for evaluation in self.evaluation.evalList ])
        if (self.scan.scanRepeat == 1) and (self.scan.scanMode != 1): #scanMode == 1 corresponds to step in place.
            self.createAverageTrace(self.evaluation.evalList)
            self.progressUi.setAveraged(0)
        else:
            self.progressUi.setAveraged(None)
        self.startScan()

    def createAverageTrace(self,evalList):
        trace = Trace()
        self.averagePlottedTraceList = list()
        for index, evaluation in enumerate(evalList):
            yColumnName = 'y{0}'.format(index)
#             rawColumnName = 'raw{0}'.format(index)
            trace.addColumn( yColumnName )
            thisAveragePlottedTrace = PlottedTrace(trace, self.plotDict[evaluation.plotname]["view"], pens.penList, yColumn=yColumnName, xAxisUnit = self.scan.xUnit,
                                                    xAxisLabel = self.scan.scanParameter, windowName=evaluation.plotname)
            thisAveragePlottedTrace.trace.name = self.scan.settingsName + " Average"
            thisAveragePlottedTrace.trace.description["comment"] = "Average Trace"
            thisAveragePlottedTrace.trace.filenameCallback = functools.partial( thisAveragePlottedTrace.traceFilename, self.scan.filename)
            self.averagePlottedTraceList.append( thisAveragePlottedTrace  )                
            self.traceui.addTrace(thisAveragePlottedTrace, pen=0)
        
    def startScan(self):
        logger = logging.getLogger(__name__)
        self.startTime = time.time()
        PulseProgramBinary = self.pulseProgramUi.getPulseProgramBinary() # also overwrites the current variable values            
        self.generator = GeneratorList[self.scan.scanMode](self.scan)
        (mycode, data) = self.generator.prepare(self.pulseProgramUi)
        self.progressUi.setRunning( max(len(self.scan.list),1) ) 
        if data:
            self.pulserHardware.ppWriteRamWordList(data,0, check=True)
            datacopy = [0]*len(data)
            datacopy = self.pulserHardware.ppReadRamWordList(datacopy,0)
            if data!=datacopy:
                logger.info("original: {0}".format(data) if len(data)<202 else "original {0} ... {1}".format(data[0:100], data[-100:]) )
                logger.info("received: {0}".format(datacopy) if len(datacopy)<202 else "received {0} ... {1}".format(datacopy[0:100], datacopy[-100:]) )
                raise ScanException("Ram write unsuccessful datalength {0} checked length {1}".format(len(data),len(datacopy)))
        self.pulserHardware.ppFlushData()
        self.pulserHardware.ppClearWriteFifo()
        self.pulserHardware.ppUpload(PulseProgramBinary)
        self.pulserHardware.ppWriteData(mycode)
        logger.info( "Starting" )
        self.pulserHardware.ppStart()
        self.currentIndex = 0
        self.timestampsNewRun = True
        self.displayUi.onClear()
        logger.info( "elapsed time {0}".format( time.time()-self.startTime ) )
        if self.plottedTraceList and self.traceui.unplotLastTrace():
            for plottedTrace in self.plottedTraceList:
                plottedTrace.plot(0) #unplot previous trace
        self.plottedTraceList = list() #reset plotted trace
        self.otherDataFile = None
        self.histogramBuffer = defaultdict( list )
    
    def onContinue(self):
        if self.progressUi.state == self.OpStates.interrupted:
            logging.getLogger(__name__).info("Received ion reappeared signal, will continue.")
            self.onPause()
    
    def onPause(self):
        logger = logging.getLogger(__name__)
        if self.progressUi.state in [self.OpStates.paused,self.OpStates.interrupted]:
            self.pulserHardware.ppFlushData()
            self.pulserHardware.ppClearWriteFifo()
            self.pulserHardware.ppWriteData(self.generator.restartCode(self.currentIndex))
            logger.info( "Starting" )
            self.pulserHardware.ppStart()
            self.progressUi.resumeRunning(self.currentIndex)
            self.timestampsNewRun = False
            logger.info( "continued" )
        elif self.progressUi.state == self.OpStates.running:
            self.pulserHardware.ppStop()
            self.progressUi.setPaused()
    
    def onInterrupt(self, reason):
        self.pulserHardware.ppStop()
        self.progressUi.setInterrupted(reason)       
    
    def onStop(self, setProgress=True):
        if self.progressUi.state in [self.OpStates.starting, self.OpStates.running, self.OpStates.paused, self.OpStates.interrupted]:
            self.pulserHardware.ppStop()
            self.pulserHardware.ppClearWriteFifo()
            self.pulserHardware.ppFlushData()
            self.NeedsDDSRewrite.emit()
        if setProgress:
            self.progressUi.setIdle()
        if self.scan:
            self.finalizeData(reason='stopped')

    def traceFilename(self, pattern):
        directory = DataDirectory.DataDirectory()
        if pattern and pattern!='':
            filename, _ = directory.sequencefile(pattern)
            return filename
        else:
            path = str(QtGui.QFileDialog.getSaveFileName(self, 'Save file',directory.path()))
            return path
            
    def onData(self, data, queuesize ):
        """ Called by worker with new data
        queuesize is the size of waiting messages, dont't do expensive unnecessary stuff if queue is deep
        """
        logger = logging.getLogger(__name__)
        if data.other and self.scan.gateSequenceSettings.debug:
            if self.otherDataFile is None:
                dumpFilename, _ = DataDirectory.DataDirectory().sequencefile("other_data.bin")
                self.otherDataFile = open( dumpFilename, "wb" )
            self.otherDataFile.write( self.pulserHardware.wordListToBytearray(data.other))
        if data.overrun:
            logger.error( "Read Pipe Overrun" )
            self.onInterrupt("Read Pipe Overrun")
        elif data.final and data.exitcode!=0:
            self.onInterrupt( self.pulseProgramUi.exitcode(data.exitcode) )
        else:
            logger.info( "onData {0} {1} {2}".format( self.currentIndex, [len(data.count[i]) for i in range(16)], data.scanvalue ) )
            # Evaluate as given in evalList
            expected = self.generator.expected( self.currentIndex )
            x = self.generator.xValue(self.currentIndex)
            evaluated = list()
            for evaluation, algo in zip(self.evaluation.evalList,self.evaluation.evalAlgorithmList):
                evaluated.append( algo.evaluate( data, counter=evaluation.counter, name=evaluation.name, expected=expected ) ) # returns mean, error, raw
            if data.other:
                logger.info( "Other: {0}".format( data.other ) )
            if len(evaluated)>0:
                self.displayUi.add( [ e[0] for e in evaluated ] )
                self.updateMainGraph(x, evaluated, 0 if data.final else queuesize )
                self.showHistogram(data, self.evaluation.evalList, self.evaluation.evalAlgorithmList )
            self.currentIndex += 1
            if self.evaluation.enableTimestamps: 
                self.showTimestamps(data)
            if data.final:
                self.finalizeData(reason='end of scan')
                logger.info( "current index {0} expected {1}".format(self.currentIndex, len(self.scan.list) ) )
                if self.currentIndex >= len(self.scan.list):    # if all points were taken
                    self.generator.dataOnFinal(self, self.progressUi.state )
                else:
                    self.onInterrupt( self.pulseProgramUi.exitcode(data.exitcode) )
            else:
                mycode = self.generator.dataNextCode(self )
                if mycode:
                    self.pulserHardware.ppWriteData(mycode)
                self.progressUi.onData( self.currentIndex )  

    def updateMainGraph(self, x, evaluated, queuesize): # evaluated is list of mean, error, raw
        if not self.plottedTraceList:
            trace = Trace(record_timestamps=True)
            self.plottedTraceList = list()
            for index, result in enumerate(evaluated):
                if result is not None:  # result is None if there were no counter results
                    (_, error, _) = result
                    showerror = error is not None
                    yColumnName = 'y{0}'.format(index) 
                    rawColumnName = 'raw{0}'.format(index)
                    trace.addColumn( yColumnName )
                    trace.addColumn( rawColumnName )
                    if showerror:
                        topColumnName = 'top{0}'.format(index)
                        bottomColumnName = 'bottom{0}'.format(index)
                        trace.addColumn( topColumnName )
                        trace.addColumn( bottomColumnName )                
                        plottedTrace = PlottedTrace(trace, self.plotDict[self.evaluation.evalList[index].plotname]["view"] if self.evaluation.evalList[index].plotname != 'None' else None, 
                                                    pens.penList, yColumn=yColumnName, topColumn=topColumnName, bottomColumn=bottomColumnName, 
                                                    rawColumn=rawColumnName, name=self.evaluation.evalList[index].name, xAxisUnit = self.scan.xUnit,
                                                    xAxisLabel = self.scan.scanParameter, windowName=self.evaluation.evalList[index].plotname) 
                    else:                
                        plottedTrace = PlottedTrace(trace, self.plotDict[self.evaluation.evalList[index].plotname]["view"] if self.evaluation.evalList[index].plotname != 'None' else None, 
                                                    pens.penList, yColumn=yColumnName, rawColumn=rawColumnName, name=self.evaluation.evalList[index].name,
                                                    xAxisUnit = self.scan.xUnit, xAxisLabel = self.scan.scanParameter, windowName=self.evaluation.evalList[index].plotname)               
                    xRange = self.generator.xRange() if isinstance(self.scan.start, magnitude.Magnitude) and magnitude.mg(self.scan.xUnit).dimension()==self.scan.start.dimension() else None
                    if xRange:
                        self.plotDict["Scan Data"]["view"].setXRange( *xRange )
                    else:
                        self.plotDict["Scan Data"]["view"].enableAutoRange(axis=ViewBox.XAxis)     
                    self.plottedTraceList.append( plottedTrace )
            self.plottedTraceList[0].trace.name = self.scan.settingsName
            self.plottedTraceList[0].trace.description["comment"] = ""
            self.plottedTraceList[0].trace.description["PulseProgram"] = self.pulseProgramUi.description() 
            self.plottedTraceList[0].trace.description["Scan"] = self.scan.description()
            self.plottedTraceList[0].trace.filenameCallback = functools.partial( WeakMethod.ref(self.plottedTraceList[0].traceFilename), self.scan.filename )
            self.generator.appendData( self.plottedTraceList, x, evaluated )
            for index, plottedTrace in reversed(list(enumerate(self.plottedTraceList))):
                if (self.scan.scanRepeat == 1) and (self.scan.scanMode != 1): #scanMode == 1 corresponds to step in place.           
                    self.traceui.addTrace( plottedTrace, pen=-1, parentTrace=self.averagePlottedTraceList[index])
                else:
                    self.traceui.addTrace( plottedTrace, pen=-1)
            self.traceui.resizeColumnsToContents()
        else:
            self.generator.appendData(self.plottedTraceList, x, evaluated)
            if queuesize<2:
                for plottedTrace in self.plottedTraceList:
                    plottedTrace.replot()

    def finalizeData(self, reason='end of scan'):
        logger = logging.getLogger(__name__)
        logger.info( "finalize Data" )
        if self.otherDataFile is not None:
            self.otherDataFile.close()
            self.otherDataFile = None
        if reason == 'end of scan':
            self.dataAnalysis()
        for trace in ([self.currentTimestampTrace]+[self.plottedTraceList[0].trace] if self.plottedTraceList else[]):
            if trace:
                trace.description["traceFinalized"] = datetime.now()
                trace.resave(saveIfUnsaved=self.scan.autoSave)
        if (self.scan.scanRepeat == 1) and (self.scan.scanMode != 1): #scanMode == 1 corresponds to step in place.
            if reason == 'end of scan': #We only re-average the data if finalizeData is called because a scan ended
                averagePlottedTrace = None
                for averagePlottedTrace in self.averagePlottedTraceList:
                    averagePlottedTrace.averageChildren()
                    averagePlottedTrace.plot(7) #average trace is plotted in black
                if averagePlottedTrace:
                    self.progressUi.setAveraged(averagePlottedTrace.childCount())
                    averagePlottedTrace.trace.resave(saveIfUnsaved=self.scan.autoSave)
        if self.scan.histogramSave:
            self.onSaveHistogram(self.scan.histogramFilename if self.scan.histogramFilename else None)
            
        
    def dataAnalysis(self):
        for evaluation, plot in zip(self.evaluation.evalList, self.plottedTraceList):
            if evaluation.analysis is not None:
                fitfunction = self.fitWidget.analysisFitfunction(evaluation.analysis)
                sigma = None
                if plot.hasHeightColumn:
                    sigma = plot.height
                elif plot.hasTopColumn and plot.hasBottomColumn:
                    sigma = abs(plot.top + plot.bottom)
                fitfunction.evaluate( self.globalVariablesUi.variables )
                fitfunction.leastsq(plot.x,plot.y,sigma=sigma)
                plot.fitFunction = copy.deepcopy(fitfunction)
                plot.plot(-2)
                self.fitWidget.pushVariables(fitfunction.pushVariableValues())
                
            
    def showTimestamps(self,data):
        bins = int( (self.evaluation.roiWidth/self.evaluation.binwidth).toval() )
        multiplier = self.pulserHardware.timestep.toval('ms')
        myrange = (self.evaluation.roiStart.toval('ms')/multiplier,(self.evaluation.roiStart+self.evaluation.roiWidth).toval('ms')/multiplier)
        y, x = numpy.histogram( data.timestamp[self.evaluation.timestampsChannel], 
                                range=myrange,
                                bins=bins)
        x = x[0:-1] * multiplier
                                
        if self.currentTimestampTrace and numpy.array_equal(self.currentTimestampTrace.x,x) and (
            self.evaluation.integrateTimestamps == self.evaluationControlWidget.integrationMode.IntegrateAll or 
                (self.evaluation.integrateTimestamps == self.evaluationControlWidget.integrationMode.IntegrateRun and not self.timestampsNewRun) ) :
            self.currentTimestampTrace.y += y
            self.plottedTimestampTrace.replot()
            if self.currentTimestampTrace.rawdata:
                self.currentTimestampTrace.rawdata.addInt(data.timestamp[self.evaluation.timestampsChannel])
        else:    
            self.currentTimestampTrace = Trace()
            if self.evaluation.saveRawData:
                self.currentTimestampTrace.rawdata = RawData()
                self.currentTimestampTrace.rawdata.addInt(data.timestamp[self.evaluation.timestampsChannel])
            self.currentTimestampTrace.x = x
            self.currentTimestampTrace.y = y
            self.currentTimestampTrace.name = self.scan.settingsName
            self.currentTimestampTrace.description["comment"] = ""
            self.currentTimestampTrace.filenameCallback = functools.partial( self.traceFilename, "Timestamp_"+self.scan.filename )
            self.plottedTimestampTrace = PlottedTrace(self.currentTimestampTrace,self.plotDict["Timestamps"]["view"],pens.penList, windowName="Timestamps")
            self.timestampTraceui.addTrace(self.plottedTimestampTrace,pen=-1)              
            pulseProgramHeader = stringutilit.commentarize( self.pulseProgramUi.documentationString() )
            scanHeader = stringutilit.commentarize( repr(self.scan) )
            self.plottedTimestampTrace.trace.header = '\n'.join((pulseProgramHeader, scanHeader)) 
        self.timestampsNewRun = False                       
        
    def showHistogram(self, data, evalList, evalAlgoList ):
        index = 0
        for evaluation, algo in zip(evalList, evalAlgoList):
            if evaluation.showHistogram:
                y, x, function = algo.histogram( data, evaluation.counter, self.evaluation.histogramBins) 
                if self.evaluation.integrateHistogram and len(self.histogramList)>index:
                    self.histogramList[index] = (self.histogramList[index][0] + y, self.histogramList[index][1], evaluation.name, None )
                elif len(self.histogramList)>index:
                    self.histogramList[index] = (y,x,evaluation.name, function )
                else:
                    self.histogramList.append( (y,x,evaluation.name, function) )
                self.histogramBuffer[evaluation.name].append(y)
                index += 1
        numberTraces = index
        del self.histogramList[numberTraces:]   # remove elements that are not needed any more
        if not self.histogramTrace:
            self.histogramTrace = Trace()            
        for index, histogram in enumerate(self.histogramList):
            if index<len(self.histogramCurveList):
                self.histogramCurveList[index].x = histogram[1]
                self.histogramCurveList[index].y = histogram[0]  
                self.histogramCurveList[index].fitFunction = histogram[3]
                self.histogramCurveList[index].replot()
            else:
                yColumnName = 'y{0}'.format(index) 
                self.histogramTrace.addColumn( yColumnName, ignoreExisting=True )
                plottedHistogramTrace = PlottedTrace(self.histogramTrace,self.plotDict["Histogram"]["view"],pens.penList,plotType=PlottedTrace.Types.steps, #@UndefinedVariable
                                                     yColumn=yColumnName, name="Histogram "+(histogram[2] if histogram[2] else ""), windowName="Histogram" )
                self.histogramTrace.filenameCallback = functools.partial( plottedHistogramTrace.traceFilename, "Hist"+self.scan.filename )
                plottedHistogramTrace.x = histogram[1]
                plottedHistogramTrace.y = histogram[0]
                plottedHistogramTrace.trace.name = self.scan.settingsName
                plottedHistogramTrace.fitFunction = histogram[3]
                self.histogramCurveList.append(plottedHistogramTrace)
                plottedHistogramTrace.plot()
        for i in range(numberTraces,len(self.histogramCurveList)):
            self.histogramCurveList[i].removePlots()
        del self.histogramCurveList[numberTraces:]

    def onCopyHistogram(self):
        for plottedtrace in self.histogramCurveList:
            self.traceui.addTrace(plottedtrace,pen=-1)   
        self.histogramTrace = Trace()    
        self.histogramCurveList = []        
             
    
    def onSaveHistogram(self, filenameTemplate="Histogram.txt"):
        tName, tExtension = os.path.splitext(filenameTemplate) if filenameTemplate else ("Histogram", ".txt")
        for name, histogramlist in self.histogramBuffer.iteritems():
            filename = DataDirectory.DataDirectory().sequencefile(tName+"_"+name+tExtension)[0]
            with open(filename,'w') as f:
                for histogram in histogramlist:
                    f.write( "\t".join(map(str,histogram)))
                    f.write("\n")
    
    def onAddPlot(self):
        name, ok = QtGui.QInputDialog.getText(self, 'Plot Name', 'Please enter a plot name: ')
        if ok:
            name = str(name)
            dock = Dock(name)
            widget = CoordinatePlotWidget(self)
            view = widget._graphicsView
            self.area.addDock(dock, "bottom")
            dock.addWidget(widget)
            self.plotDict[name] = {"dock":dock, "widget":widget, "view":view}
            self.evaluationControlWidget.plotnames.append(name)
            self.saveConfig() #In case the program suddenly shuts down
            self.plotsChanged.emit()
            
    def onRemovePlot(self):
        logger = logging.getLogger(__name__)
        names = QtCore.QStringList()
        for name in self.plotDict.keys():
            if name not in ['Scan Data', 'Histogram', 'Timestamps']:
                names.append(name)
        if names.count() > 0:
            name, ok = QtGui.QInputDialog.getItem(self, "Select Plot", "Please select which plot to remove: ", names, editable=False)
            if ok:
                name = str(name)
                self.plotDict[name]["dock"].close()
                self.evaluationControlWidget.plotnames.remove(name)
                del self.plotDict[name]
                for evaluation in self.evaluationControlWidget.settings.evalList: #Change any instance of the removed plot in the current scan evaluation to the default scan ("Scan Data")
                    if evaluation.plotname == name:
                        evaluation.plotname = "Scan Data"
                self.saveConfig() #In case the program suddenly shuts down
        else:
            logger.info("There are no plots which can be removed")
        self.saveConfig()
        self.plotsChanged.emit()

                
    def onRenamePlot(self):
        logger = logging.getLogger(__name__)
        names = QtCore.QStringList()
        for name in self.plotDict.keys():
            if name not in ['Scan Data', 'Histogram', 'Timestamps']:
                names.append(name)
        if names.count() > 0:
            name, ok = QtGui.QInputDialog.getItem(self, "Select Plot", "Please select which plot to rename: ", names, editable=False)
            if ok:
                newName, newOk = QtGui.QInputDialog.getText(self, 'New Plot Name', 'Please enter a new plot name: ')
                if newOk:
                    name = str(name)
                    newName = str(newName)
                    self.plotDict[name]["dock"].label.setText(QtCore.QString(newName))
                    self.plotDict[newName] = self.plotDict[name]
                    del self.plotDict[name]
                    self.evaluationControlWidget.plotnames.append(newName)
                    self.evaluationControlWidget.plotnames.remove(name)
                    for evaluation in self.evaluationControlWidget.settings.evalList: #Update the current evaluation plot names, whether or not it has been saved
                        if evaluation.plotname == name:
                            evaluation.plotname = newName
                    for settingsName in self.evaluationControlWidget.settingsDict.keys(): #Update all the saved evaluation plot names
                        for evaluation in self.evaluationControlWidget.settingsDict[settingsName].evalList:
                            if evaluation.plotname == name:
                                evaluation.plotname = newName
                    self.saveConfig() #In case the program suddenly shuts down
        else:
            logger.info("There are no plots which can be renamed")
        self.plotsChanged.emit()


    def activate(self):
        logger = logging.getLogger(__name__)
        MainWindowWidget.MainWindowWidget.activate(self)
        if (self.deviceSettings is not None) and (not self.activated):
            try:
                logger.info( "Scan activated" )
                self.pulserHardware.ppFlushData()
                self.pulserHardware.dataAvailable.connect(self.onData)
                self.activated = True
            except Exception as ex:
                logger.exception("activate")
                self.StatusMessage.emit( ex.message )
    
    def deactivate(self):
        logger = logging.getLogger(__name__)
        MainWindowWidget.MainWindowWidget.deactivate(self)
        if self.activated :
            logger.info( "Scan deactivated" )
            self.pulserHardware.dataAvailable.disconnect(self.onData)
            self.activated = False
            self.progressUi.setIdle()
                
    def saveConfig(self):
        self.config[self.experimentName+'.MainWindow.State'] = QtGui.QMainWindow.saveState(self)
        self.config[self.experimentName+'.pyqtgraph-dockareastate'] = self.area.saveState()
        self.config[self.experimentName+'.plotNames'] = self.plotDict.keys()
        self.scanControlWidget.saveConfig()
        self.evaluationControlWidget.saveConfig()
        self.traceui.saveConfig()
        self.displayUi.saveConfig()
        self.fitWidget.saveConfig()
        
    def onClose(self):
        pass

    def state(self):
        return self.progressUi.state
        
    def onPrint(self, target, printer, pdfPrinter, preferences):
        widget = self.plotDict[target]['widget']
        if preferences.savePdf:
            with SceneToPrint(widget):
                painter = QtGui.QPainter(pdfPrinter)
                widget.render( painter )
                del painter
        
        # create an exporter instance, as an argument give it
        # the item you wish to export
        with SceneToPrint(widget, preferences.gridLinewidth, preferences.curveLinewidth):
            exporter = ImageExporter(widget._graphicsView.scene()) 
      
            # set export parameters if needed
            pageWidth = printer.pageRect().width()
            pageHeight = printer.pageRect().height()
            exporter.parameters()['width'] = pageWidth*preferences.printWidth   # (note this also affects height parameter)
            exporter.widthChanged()
              
            # save to file
            png = exporter.export(toBytes=True)
            if preferences.savePng:
                png.save(DataDirectory.DataDirectory().sequencefile(target+".png")[0])
            
            if preferences.doPrint:
                painter = QtGui.QPainter( printer )
                painter.drawImage(QtCore.QPoint(pageWidth*preferences.printX,pageHeight*preferences.printY), png)

                
                