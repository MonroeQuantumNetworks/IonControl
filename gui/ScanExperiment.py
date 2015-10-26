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
from pyqtgraph.exporters.SVGExporter import SVGExporter

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
from trace.TraceCollection import TraceCollection
from uiModules.CoordinatePlotWidget import CoordinatePlotWidget
from modules import WeakMethod
from modules.SceneToPrint import SceneToPrint
from collections import defaultdict
from gui.ScanMethods import ScanMethodsDict, ScanException
from gui.ScanGenerators import GeneratorList
from modules.magnitude import is_magnitude
from persist.MeasurementLog import  Measurement, Parameter, Result
from scan.AnalysisControl import AnalysisControl   #@UnresolvedImport
from modules.Utility import join
import pytz
from PyQt4.QtGui import QApplication
from ProjectConfig.Project import getProject
from copy import copy

uipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\ScanExperiment.ui')
ScanExperimentForm, ScanExperimentBase = PyQt4.uic.loadUiType(uipath)

ExpectedLoopkup = { 'd': 0, 'u' : 1, '1':0.5, '-1':0.5, 'i':0.5, '-i':0.5 }

FifoDepth = 1020

class ScanExperiment(ScanExperimentForm, MainWindowWidget.MainWindowWidget):
    StatusMessage = QtCore.pyqtSignal( str )
    ClearStatusMessage = QtCore.pyqtSignal()
    NeedsDDSRewrite = QtCore.pyqtSignal()
    plotsChanged = QtCore.pyqtSignal()
    ppStartSignal = QtCore.pyqtSignal()
    ppStopSignal = QtCore.pyqtSignal()
    OpStates = enum.enum('idle','running','paused','starting','stopping', 'interrupted')
    experimentName = 'Scan Sequence'
    statusChanged = QtCore.pyqtSignal( object )
    scanConfigurationListChanged = None
    evaluationConfigurationChanged = None
    analysisConfigurationChanged = None
    evaluatedDataSignal = QtCore.pyqtSignal( dict ) #key is the eval name, val is (x, y)
    allDataSignal = QtCore.pyqtSignal( dict ) #key is the eval name, val is (xlist, ylist)
    def __init__(self,settings,pulserHardware,globalVariablesUi, experimentName,toolBar=None,parent=None, measurementLog=None, callWhenDoneAdjusting=None):
        MainWindowWidget.MainWindowWidget.__init__(self,toolBar=toolBar,parent=parent)
        ScanExperimentForm.__init__(self)
        self.deviceSettings = settings
        self.pulserHardware = pulserHardware
        self.plottedTraceList = list()
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
        self.scanTargetDict = dict()     
        self.measurementLog = measurementLog 
        self.callWhenDoneAdjusting = callWhenDoneAdjusting
        self.rawDataFile = None
        self.dataFinalized = False
        self.accumulatedTimingViolations = set()
        self.project = getProject()
        self.timestampsEnabled = self.project.isEnabled('software', 'Timestamps')
        self.unsavedTraceCount = 0

    def setupUi(self,MainWindow,config):
        logger = logging.getLogger(__name__)
        ScanExperimentForm.setupUi(self,MainWindow)
        self.config = config
        self.area = DockArea()
        self.setCentralWidget(self.area)
        self.plotDict = dict()
        axesType = self.config.get( self.experimentName+'.axesType', defaultdict( lambda: False ))

        self.requiredPlotNames = ["Scan Data", "Histogram", "Timestamps"] if self.timestampsEnabled else ["Scan Data", "Histogram"]
        if self.experimentName+'.plotNames' in self.config:
            plotNames = self.config[self.experimentName+'.plotNames']
            for name in self.requiredPlotNames: #make sure required plots are present
                if name not in plotNames:
                    plotNames.append(name)
        else:
            plotNames = copy(self.requiredPlotNames)
        # initialize all the plot windows we want
        self.createPlotWindows(plotNames, axesType)
        try:
            if self.experimentName+'.pyqtgraph-dockareastate' in self.config:
                self.area.restoreState(self.config[self.experimentName+'.pyqtgraph-dockareastate'])
        except Exception as e: #If an except occurs, we have to completely rebuild the DockArea
            logger.warning("Cannot restore dock state in experiment {0}. Exception occurred: ".format(self.experimentName) + str(e))
            self.area.deleteLater()
            self.area = DockArea()
            self.setCentralWidget(self.area)
            self.plotDict=dict()
            self.createPlotWindows(plotNames, axesType)
        del plotNames #I don't want to leave this list around, as it is not updated and may cause confusion.

        # Traceui
        self.penicons = pens.penicons().penicons()
        self.traceui = Traceui.Traceui(self.penicons,self.config,self.experimentName,self.plotDict,hasMeasurementLog=True)
        self.traceui.setupUi(self.traceui)
        self.measurementLog.addTraceui( 'Scan', self.traceui )
        self.measurementLog.traceuiLookup['Script'] = self.traceui
        self.traceui.model.traceModelDataChanged.connect(self.measurementLog.measurementModel.onTraceModelDataChanged)
        self.measurementLog.measurementModel.measurementModelDataChanged.connect(self.traceui.model.onMeasurementModelDataChanged)
        self.traceui.model.traceRemoved.connect(self.measurementLog.measurementModel.onTraceRemoved)
        self.traceui.openMeasurementLog.connect(self.measurementLog.onOpenMeasurementLog)
        # traceui for timestamps
        if self.timestampsEnabled:
            self.timestampTraceui = Traceui.Traceui(self.penicons,self.config,self.experimentName+"-timestamps",self.plotDict)
            self.timestampTraceui.setupUi(self.timestampTraceui)
            self.timestampTraceuiDock = self.setupAsDockWidget(self.timestampTraceui, "Timestamp traces", QtCore.Qt.LeftDockWidgetArea)
        # new fit widget
        self.fitWidget = FitUi(self.traceui,self.config,self.experimentName, globalDict = self.globalVariablesUi.variables )
        self.fitWidget.setupUi(self.fitWidget)
        self.globalVariablesUi.valueChanged.connect( self.fitWidget.evaluate )
        self.fitWidgetDock = self.setupAsDockWidget(self.fitWidget, "Fit", QtCore.Qt.LeftDockWidgetArea,
                                                    stackAbove=self.timestampTraceuiDock if self.timestampsEnabled else None)
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
        self.scanControlWidget = ScanControl(config, self.globalVariablesUi, self.experimentName)
        self.scanControlWidget.currentScanChanged.connect( self.progressUi.setScanLabel )
        self.scanControlWidget.setupUi(self.scanControlWidget)
        self.scanControlDock = self.setupAsDockWidget(self.scanControlWidget, "Scan Control", QtCore.Qt.RightDockWidgetArea)
        self.scanConfigurationListChanged = self.scanControlWidget.scanConfigurationListChanged
        # EvaluationControl
        self.evaluationControlWidget = EvaluationControl(config, self.globalVariablesUi, self.experimentName, self.plotDict.keys(), analysisNames=self.fitWidget.analysisNames() )
        self.evaluationControlWidget.currentEvaluationChanged.connect( self.progressUi.setEvaluationLabel )
        self.evaluationControlWidget.setupUi(self.evaluationControlWidget)
        self.fitWidget.analysisNamesChanged.connect( self.evaluationControlWidget.setAnalysisNames )
        self.evaluationControlDock = self.setupAsDockWidget( self.evaluationControlWidget, "Evaluation Control", QtCore.Qt.RightDockWidgetArea, stackAbove=self.scanControlDock)
        self.evaluationConfigurationChanged = self.evaluationControlWidget.evaluationConfigurationChanged
        # Analysis Control
        self.analysisControlWidget = AnalysisControl(config, self.globalVariablesUi, self.experimentName, self.evaluationControlWidget.evaluationNames )
        self.analysisControlWidget.currentAnalysisChanged.connect( self.progressUi.setAnalysisLabel )
        self.analysisControlWidget.setupUi(self.analysisControlWidget)
        self.analysisControlDock = self.setupAsDockWidget( self.analysisControlWidget, "Analysis Control", QtCore.Qt.RightDockWidgetArea, stackAbove=self.evaluationControlDock)
        self.globalVariablesUi.valueChanged.connect( self.analysisControlWidget.evaluate )
        self.analysisConfigurationChanged = self.analysisControlWidget.analysisConfigurationChanged

        #toolBar actions
        self.copyHistogram = QtGui.QAction( QtGui.QIcon(":/openicon/icons/office-chart-bar.png"), "Copy histogram to traces", self ) 
        self.copyHistogram.setToolTip("Copy histogram to traces")
        self.copyHistogram.triggered.connect( self.onCopyHistogram )
        self.actionList.append( self.copyHistogram )
        
        self.saveHistogram = QtGui.QAction( QtGui.QIcon(":/openicon/icons/office-chart-bar-save.png"), "Save histograms", self ) 
        self.saveHistogram.setToolTip("Save histograms for last run to file")
        self.saveHistogram.triggered.connect( self.onSaveHistogram )
        self.actionList.append( self.saveHistogram )

        self.actionAddPlot = QtGui.QAction( QtGui.QIcon(":/openicon/icons/add-plot.png"), "Add new plot", self)
        self.actionAddPlot.setToolTip("Add new plot")
        self.actionAddPlot.triggered.connect(self.onAddPlot)
        self.actionList.append(self.actionAddPlot)
        
        self.removePlot = QtGui.QAction( QtGui.QIcon(":/openicon/icons/remove-plot.png"), "Remove a plot", self)
        self.removePlot.setToolTip("Remove a plot")
        self.removePlot.triggered.connect(self.onRemovePlot)
        self.actionList.append(self.removePlot)

        self.renamePlot = QtGui.QAction( QtGui.QIcon(":/openicon/icons/rename-plot.png"), "Rename a plot", self)
        self.renamePlot.setToolTip("Rename a plot")
        self.renamePlot.triggered.connect(self.onRenamePlot)
        self.actionList.append(self.renamePlot)
        
        self.analysisControlWidget.addPushDestination('Global', self.globalVariablesUi )

    def createPlotWindows(self, plotNames, axesType):
        for name in plotNames:
            dock = Dock(name)
            widget = CoordinatePlotWidget(self, name=name)
            if hasattr(axesType, name):
                widget.setTimeAxis(axesType[name])
            view = widget._graphicsView
            self.area.addDock(dock, "bottom")
            dock.addWidget(widget)
            self.plotDict[name] = {"dock":dock, "widget":widget, "view":view}
            del dock, widget, view #This is probably unnecessary, but can't hurt
        self.plotDict["Histogram"]["widget"].autoRange()
        if self.timestampsEnabled: self.plotDict["Timestamps"]["widget"].autoRange()

    def exportXml(self, element):
        self.scanControlWidget.onExportXml(element)
        self.analysisControlWidget.onExportXml(element)
        self.evaluationControlWidget.onExportXml(element)
        self.pulseProgramUi.onExportXml(element)
        
    def importXml(self, element, mode):
        self.scanControlWidget.importXml(element, mode=mode)
        self.analysisControlWidget.importXml(element, mode=mode)
        self.evaluationControlWidget.importXml(element, mode=mode)
        self.pulseProgramUi.importXml(element, mode=mode)
        
    def reAnalyze(self, plottedTrace):
        self.analysisControlWidget.analyze( dict( ( (evaluation.name,plottedTrace) for evaluation, plottedTrace in zip(self.evaluation.evalList, self.plottedTraceList) ) ) )
        
    def printTargets(self):
        return self.plotDict.keys()

    def addPushDestination(self, name, destination):
        self.analysisControlWidget.addPushDestination(name, destination)
        
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
        pass
    
    def setTimeLabel(self):
        elapsed = time.time()-self.startTime
        expected = elapsed / ((self.currentIndex)/float(max(len(self.scan.list),1))) if self.currentIndex>0 else 0
        self.scanControlWidget.timeLabel.setText( "{0} / {1}".format(timedelta(seconds=round(elapsed)),
                                                 timedelta(seconds=round(expected)))) 
 
    def onStart(self):
        self.accumulatedTimingViolations = set()
        self.pulseProgramUi.setTimingViolations( [] )
        self.scan = self.scanControlWidget.getScan()
        self.evaluation = self.evaluationControlWidget.getEvaluation()
        self.displayUi.setNames( [evaluation.name for evaluation in self.evaluation.evalList ])
        self.scanMethod = ScanMethodsDict[self.scan.scanTarget](self)
        self.progressUi.setStarting()
        self.ppStartSignal.emit()
        if self.callWhenDoneAdjusting is None:
            self.startScan()
        else:
            self.callWhenDoneAdjusting(self.startScan)
        if self.scan.saveRawData and self.scan.rawFilename:
            self.rawDataFile = open(DataDirectory.DataDirectory().sequencefile(self.scan.rawFilename)[0],'w')
        self.dataFinalized = False

    def startScan(self):
        logger = logging.getLogger(__name__)
        if self.progressUi.state in [self.OpStates.idle, self.OpStates.starting, self.OpStates.stopping, self.OpStates.running, self.OpStates.paused, self.OpStates.interrupted]:
            self.startTime = time.time()
            self.pulserHardware.ppStop()
            
            override = dict()
            scanParam = None

            AWGEnabled = self.project.isEnabled('software', 'AWG')
            if AWGEnabled:
                AWGdevice = self.scanTargetDict["AWG"]["Duration"].device
                if AWGdevice.parent.parameters.enabled and self.scan.scanMode == 0: # 0 = Parameter Scan
                    logging.getLogger(__name__).info("AWG active!")
                    (setScanParam, scanParam) = AWGdevice.scanParam()
                    # don't scan over scanParam if not a duration scan. instead override scanParam if necessary and program the AWG
                    if not (self.scan.scanMode == 0 and self.scan.scanTarget == "AWG" and self.scan.scanParameter == "Duration"):
                        if setScanParam:
                            override = {scanParam: AWGdevice._waveform.vars['Duration']['value']}
                            scanParam = None
                        AWGdevice.program(False)
            
            PulseProgramBinary = self.pulseProgramUi.getPulseProgramBinary(override=override) # also overwrites the current variable values
            if self.scan.scanMode == 0:
                self.generator = GeneratorList[self.scan.scanMode](self.scan, scanParam=scanParam)
            else:
                self.generator = GeneratorList[self.scan.scanMode](self.scan)
            
            (mycode, data) = self.generator.prepare(self.pulseProgramUi, self.scanMethod.maxUpdatesToWrite )
            if self.pulseProgramUi.writeRam and self.pulseProgramUi.ramData:
                data = self.pulseProgramUi.ramData #Overwrites anything set above by the gate sequence ui
            if data:
                logging.getLogger(__name__).info("Writing {0} bytes to RAM ({1}%)".format(len(data)*8, 100*len(data)/(2**24) ))
                self.pulserHardware.ppWriteRamWordList(data,0, check=True)
                datacopy = [0]*len(data)
                datacopy = self.pulserHardware.ppReadRamWordList(datacopy,0)
                if data!=datacopy:
                    logger.info("original: {0}".format(data) if len(data)<202 else "original {0} ... {1}".format(data[0:100], data[-100:]) )
                    logger.info("received: {0}".format(datacopy) if len(datacopy)<202 else "received {0} ... {1}".format(datacopy[0:100], datacopy[-100:]) )
                    raise ScanException("Ram write unsuccessful datalength {0} checked length {1}".format(len(data),len(datacopy)))
                if self.scan.gateSequenceSettings.debug:
                    with open("debug.bin",'w') as f:
                        f.write( ' '.join(map(str,data)) )
            self.pulserHardware.ppFlushData()
            self.pulserHardware.ppClearWriteFifo()
            self.pulserHardware.ppUpload(PulseProgramBinary)
            self.pulserHardware.ppWriteData(mycode)
            self.displayUi.onClear()
            self.timestampsNewRun = True
            if self.plottedTraceList and self.traceui.unplotLastTrace:
                for plottedTrace in self.plottedTraceList:
                    plottedTrace.plot(0) #unplot previous trace
            if self.plottedTraceList and self.traceui.collapseLastTrace:
                self.traceui.collapse(self.plottedTraceList[0])
            self.plottedTraceList = list() #reset plotted trace list
            self.otherDataFile = None
            self.histogramBuffer = defaultdict( list )
            self.scanMethod.startScan()

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
    
    def onStop(self, reason='stopped'):
        if self.progressUi.state in [self.OpStates.starting, self.OpStates.running, self.OpStates.paused, self.OpStates.interrupted, self.OpStates.stopping ]:
            self.pulserHardware.ppStop()
            self.pulserHardware.ppClearWriteFifo()
            self.pulserHardware.ppFlushData()
            self.NeedsDDSRewrite.emit()
            QApplication.processEvents()
            try:
                if self.scan:
                    self.finalizeData(reason=reason)
            except Exception as e:
                logging.getLogger(__name__).warning("Analysis failed: {0}".format(str(e)))
            self.scanMethod.onStop()
            self.ppStopSignal.emit()

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
            logger.warning( "Read Pipe Overrun" )
            self.onInterrupt("Read Pipe Overrun")
        if data.timingViolations:
            oldlength = len(self.accumulatedTimingViolations)
            self.accumulatedTimingViolations.update(data.timingViolations)
            if len(self.accumulatedTimingViolations)>oldlength:
                self.pulseProgramUi.setTimingViolations( [self.pulseProgramUi.lineOfInstruction(l) for l in self.accumulatedTimingViolations])
                lineInPP = self.pulseProgramUi.lineOfInstruction(data.timingViolations[0])
                logger.warning( "PP Timing violation at address {0}".format(lineInPP))
        if data.final and data.exitcode not in [0,0xffff]:
            self.onInterrupt( self.pulseProgramUi.exitcode(data.exitcode) )
        else:
            logger.info( "onData {0} {1} {2}".format( self.currentIndex, dict((i,len(data.count[i])) for i in sorted(data.count.keys())), data.scanvalue ) )
            x = self.generator.xValue(self.currentIndex, data)
            self.scanMethod.onData( data, queuesize, x )
            if self.rawDataFile is not None:
                self.rawDataFile.write( data.dataString() )
                self.rawDataFile.write( '\n' )
                self.rawDataFile.flush()
                
        
    def dataMiddlePart(self, data, queuesize, x):
        if is_magnitude(x):
            x = x.ounit(self.scan.xUnit).toval()
        logger = logging.getLogger(__name__)
        evaluated = list()
        expected = self.generator.expected( self.currentIndex )
        replacementDict = dict(self.pulseProgramUi.currentContext.parameters.valueView.iteritems()) 
        for evaluation, algo in zip(self.evaluation.evalList,self.evaluation.evalAlgorithmList):
            evaluated.append( algo.evaluate( data, evaluation, expected=expected, ppDict=replacementDict, globalDict=self.globalVariables) ) # returns mean, error, raw
        if len(evaluated)>0:
            self.displayUi.add(  [ e[0] for e in evaluated ] )
            self.updateMainGraph(x, evaluated, data.timeinterval, data.timeTickOffset, queuesize  )
            self.showHistogram(data, self.evaluation.evalList, self.evaluation.evalAlgorithmList )
        if data.other:
            logger.info( "Other: {0}".format( data.other ) )
        self.currentIndex += 1
        if self.evaluation.enableTimestamps and self.timestampsEnabled:
            self.showTimestamps(data)
        self.scanMethod.prepareNextPoint(data)
        names = [self.evaluation.ev.name for self.evaluation.ev in self.evaluation.evalList]
        results = [(x,res[0]) for res in evaluated]
        self.evaluatedDataSignal.emit(dict(zip(names, results)))
        
    def updateMainGraph(self, x, evaluated, timeinterval, timeTickOffset, queuesize): # evaluated is list of mean, error, raw
        if not self.plottedTraceList:
            traceCollection = TraceCollection(record_timestamps=True)
            traceCollection.recordTimeinterval(timeTickOffset)
            self.plottedTraceList = list()
            for index, result in enumerate(evaluated):
                if result is not None:  # result is None if there were no counter results
                    (_, error, _) = result
                    showerror = error is not None
                    yColumnName = 'y{0}'.format(index) 
                    rawColumnName = 'raw{0}'.format(index)
                    traceCollection.addColumn( yColumnName )
                    traceCollection.addColumn( rawColumnName )
                    if showerror:
                        topColumnName = 'top{0}'.format(index)
                        bottomColumnName = 'bottom{0}'.format(index)
                        traceCollection.addColumn( topColumnName )
                        traceCollection.addColumn( bottomColumnName )
                        plottedTrace = PlottedTrace(traceCollection, self.plotDict[self.evaluation.evalList[index].plotname]["view"] if self.evaluation.evalList[index].plotname != 'None' else None,
                                                    pens.penList, xColumn=self.evaluation.evalList[index].abszisse.columnName,
                                                    yColumn=yColumnName, topColumn=topColumnName, bottomColumn=bottomColumnName, 
                                                    rawColumn=rawColumnName, name=self.evaluation.evalList[index].name, xAxisUnit = self.scan.xUnit,
                                                    xAxisLabel = self.scan.scanParameter, windowName=self.evaluation.evalList[index].plotname) 
                    else:                
                        plottedTrace = PlottedTrace(traceCollection, self.plotDict[self.evaluation.evalList[index].plotname]["view"] if self.evaluation.evalList[index].plotname != 'None' else None,
                                                    pens.penList, xColumn=self.evaluation.evalList[index].abszisse.columnName, yColumn=yColumnName, rawColumn=rawColumnName, name=self.evaluation.evalList[index].name,
                                                    xAxisUnit = self.scan.xUnit, xAxisLabel = self.scan.scanParameter, windowName=self.evaluation.evalList[index].plotname)               
                    xRange = self.generator.xRange() if isinstance(self.scan.start, magnitude.Magnitude) and magnitude.mg(self.scan.xUnit).dimension()==self.scan.start.dimension() else None
                    if xRange:
                        self.plotDict["Scan Data"]["view"].setXRange( *xRange )
                    else:
                        self.plotDict["Scan Data"]["view"].enableAutoRange(axis=ViewBox.XAxis)     
                    self.plottedTraceList.append( plottedTrace )
            self.plottedTraceList[0].traceCollection.name = self.scan.settingsName
            self.plottedTraceList[0].traceCollection.description["comment"] = ""
            self.plottedTraceList[0].traceCollection.description["PulseProgram"] = self.pulseProgramUi.description()
            self.plottedTraceList[0].traceCollection.description["Scan"] = self.scan.description()
            self.plottedTraceList[0].traceCollection.autoSave = self.scan.autoSave
            self.plottedTraceList[0].traceCollection.filenamePattern = self.scan.filename
            for plottedTrace in self.plottedTraceList:
                plottedTrace.category = plottedTrace.traceCollection.fileleaf if self.scan.autoSave else "UNSAVED_"+plottedTrace.traceCollection.filenamePattern+"_{0}".format(self.unsavedTraceCount)
            if not self.scan.autoSave: self.unsavedTraceCount+=1
            self.generator.appendData( self.plottedTraceList, x, evaluated, timeinterval )
            for index, plottedTrace in reversed(list(enumerate(self.plottedTraceList))):
                self.traceui.addTrace(plottedTrace, pen=-1)
            if self.traceui.expandNew:
                self.traceui.expand(self.plottedTraceList[0])
            self.traceui.resizeColumnsToContents()
        else:
            self.generator.appendData(self.plottedTraceList, x, evaluated, timeinterval )
            if queuesize<2:
                for plottedTrace in self.plottedTraceList:
                    plottedTrace.replot()

    def finalizeData(self, reason='end of scan'):
        if not self.dataFinalized:  # is not yet finalized
            logger = logging.getLogger(__name__)
            logger.info( "finalize Data reason: {0}".format(reason) )
            saveData = reason != 'aborted'
            if self.otherDataFile is not None:
                self.otherDataFile.close()
                self.otherDataFile = None
            if self.rawDataFile is not None:
                self.rawDataFile.close()
                self.rawDataFile = None
                logging.getLogger(__name__).info("Closed raw data file")
            for trace in ([self.currentTimestampTrace]+[self.plottedTraceList[0].traceCollection] if self.plottedTraceList else[]):
                if trace:
                    trace.description["traceFinalized"] = datetime.now(pytz.utc)
                    if trace.autoSave:
                        trace.save()
            if saveData:
                failedList = self.dataAnalysis()
                self.registerMeasurement(failedList)
            if self.scan.histogramSave:
                self.onSaveHistogram(self.scan.histogramFilename if self.scan.histogramFilename else None)
            self.dataFinalized = reason
            allData = {self.p.name:(self.p.x, self.p.y) for self.p in self.plottedTraceList}
            self.allDataSignal.emit(allData)
        
    def dataAnalysis(self):
        return self.analysisControlWidget.analyze( dict( ( (evaluation.name,plottedTrace) for evaluation, plottedTrace in zip(self.evaluation.evalList, self.plottedTraceList) ) ) )
                
            
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
            self.currentTimestampTrace = TraceCollection()
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
                y, x, function = algo.histogram( data, evaluation, self.evaluation.histogramBins ) 
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
            self.histogramTrace = TraceCollection()
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
                self.histogramTrace.filenamePattern = "Hist_"+self.scan.filename
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
        self.histogramTrace = TraceCollection()
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
            self.addPlot(name)
            
    def addPlot(self, name):
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
            if name not in self.requiredPlotNames:
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
            if name not in self.requiredPlotNames:
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
        self.config[self.experimentName+".axesType"] = dict( ((key,value["widget"].timeAxis) for key, value in self.plotDict.iteritems()) )
        self.scanControlWidget.saveConfig()
        self.evaluationControlWidget.saveConfig()
        self.traceui.saveConfig()
        self.displayUi.saveConfig()
        self.fitWidget.saveConfig()
        self.analysisControlWidget.saveConfig()
        
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
        
        with SceneToPrint(widget, 1, 1):
            exporter = SVGExporter(widget._graphicsView.scene()) 
            exporter.export(fileName = DataDirectory.DataDirectory().sequencefile(target+".svg")[0])
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

    def updateScanTarget(self, target, parameterdict ):
        self.scanTargetDict[target] = parameterdict
        self.scanControlWidget.updateScanTarget(target, parameterdict.keys() )

    def registerMeasurement(self, failedList):
        failedEntry = ", ".join((name for target, name in failedList)) if failedList else None
        measurement = Measurement(scanType= 'Scan', scanName=self.scan.settingsName, scanParameter=self.scan.scanParameter, scanTarget=self.scan.scanTarget,
                                  scanPP = self.scan.loadPPName,
                                  evaluation=self.evaluation.settingsName, 
                                  startDate=self.plottedTraceList[0].traceCollection.description['traceCreation'] if self.plottedTraceList else datetime.now(pytz.utc),
                                  duration=None, filename=self.plottedTraceList[0].traceCollection.filename if self.plottedTraceList else "none",
                                  comment=None, longComment=None, failedAnalysis=failedEntry)
        # add parameters
        space = self.measurementLog.container.getSpace('PulseProgram')
        for var in  self.pulseProgramUi.variableTableModel.variabledict.values():
            measurement.parameters.append( Parameter(name=var.name, value=var.outValue(), definition=var.strvalue, space=space) )
        space = self.measurementLog.container.getSpace('GlobalVariables')
        for name, value in self.globalVariables.iteritems():
            measurement.parameters.append( Parameter(name=name, value=value, space=space) )
        
        for targetname, target in self.scanTargetDict.iteritems():
            space = self.measurementLog.container.getSpace(targetname)
            for obj in target.values():
                measurement.parameters.append( Parameter(name=obj.name, value=obj.value, definition=obj.strValue if hasattr(obj,'strValue') else None, space=space) )
        # add results
        for evaluationElement in self.analysisControlWidget.analysisDefinition:
            fit = evaluationElement.fitfunction.fitfunction()
            for name, value, confidence in zip( fit.parameterNames, fit.parameters, fit.parametersConfidence ):
                fullName = join( '_', [evaluationElement.name, name] )
                measurement.results.append( Result(name=fullName, value=value, bottom=confidence, top=confidence))
            for result in fit.results.itervalues():
                fullName = join( '_', [evaluationElement.name, result.name] )
                measurement.results.append( Result(name=fullName, value=result.value))
            for pushvar in evaluationElement.pushVariables.itervalues():
                fullName = join( '_', [evaluationElement.name, pushvar.variableName] )
                measurement.results.append( Result(name=fullName, value=pushvar.value, bottom=pushvar.minimum if pushvar.minimum else None,
                                                                                       top=pushvar.maximum if pushvar.maximum else None))   
        # add Plots
        measurement.plottedTraceList = self.plottedTraceList              
        self.measurementLog.container.addMeasurement( measurement )
            
                