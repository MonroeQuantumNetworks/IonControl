# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 17:25:13 2012

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
import ScanParameters
from modules import enum
from pyqtgraph.dockarea import DockArea, Dock
import pyqtgraph
import ScanExperimentSettings
from modules import DataDirectory
import TimestampSettings
import time
import CoordinatePlotWidget
import functools
from modules import stringutilit
        
ScanExperimentForm, ScanExperimentBase = PyQt4.uic.loadUiType(r'ui\ScanExperiment.ui')

class ScanExperiment(ScanExperimentForm, MainWindowWidget.MainWindowWidget):
    StatusMessage = QtCore.pyqtSignal( str )
    ClearStatusMessage = QtCore.pyqtSignal()
    NeedsDDSRewrite = QtCore.pyqtSignal()
    OpStates = enum.enum('idle','running','paused')
    experimentName = 'Scan Sequence'

    def __init__(self,settings,pulserHardware,parent=None):
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
            if 'ScanExperiment.pyqtgraph-dokareastate' in self.config:
                self.area.restoreState(self.config['ScanExperiment.pyqtgraph-dokareastate'])
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
        self.fitWidget = FitUi.FitUi(self.traceui,self.config,"ScanExperiment")
        self.fitWidget.setupUi(self.fitWidget)
        self.dockWidgetFitUi.setWidget( self.fitWidget )
        self.dockWidgetList.append(self.dockWidgetFitUi )
        self.scanParametersWidget = ScanParameters.ScanParameters(config,"ScanExperiment")
        self.scanParametersWidget.setupUi(self.scanParametersWidget)
        self.scanParametersUi.setWidget(self.scanParametersWidget )
        self.scanSettingsWidget = ScanExperimentSettings.ScanExperimentSettings(config,"ScanExperiment")
        self.scanSettingsWidget.setupUi(self.scanSettingsWidget)
        self.scanSettingsUi.setWidget(self.scanSettingsWidget)
        self.timestampSettingsWidget = TimestampSettings.TimestampSettings(config,"ScanExperiment")
        self.timestampSettingsWidget.setupUi(self.timestampSettingsWidget)
        self.timestampSettingsUi.setWidget(self.timestampSettingsWidget)
        self.dockWidgetList.append(self.scanParametersUi)
        self.dockWidgetList.append(self.scanSettingsUi)
        self.dockWidgetList.append(self.timestampSettingsUi)
        if 'ScanExperiment.MainWindow.State' in self.config:
            QtGui.QMainWindow.restoreState(self,self.config['ScanExperiment.MainWindow.State'])

    def setPulseProgramUi(self,pulseProgramUi):
        self.pulseProgramUi = pulseProgramUi.addExperiment(self.experimentName)
        self.scanParametersWidget.setVariables( self.pulseProgramUi.pulseProgram.variabledict )

    def onClear(self):
        self.dockWidget.setShown(True)
        self.StatusMessage.emit("test Clear not implemented")
    
    def onSave(self):
        self.StatusMessage.emit("test Save not implemented")
    
    def onStart(self):
        start = time.time()
        self.state = self.OpStates.running
        self.scanSettings = self.scanSettingsWidget.settings
        # get parameter to scan and scanrange
        self.scan = self.scanParametersWidget.getScan()
        if self.scan.scanMode == self.scanParametersWidget.ScanModes.StepInPlace:
            self.scan.code = self.pulseProgramUi.pulseProgram.variableScanCode(self.scan.name, [self.scan.list[0]])
            mycode = self.pulseProgramUi.pulseProgram.variableScanCode(self.scan.name, [self.scan.list[0]]*2)
        else:
            self.scan.code = self.pulseProgramUi.pulseProgram.variableScanCode(self.scan.name, self.scan.list)
            mycode = self.scan.code
        self.pulserHardware.ppFlushData()
        self.pulserHardware.ppClearWriteFifo()
        self.pulserHardware.ppUpload(self.pulseProgramUi.getPulseProgramBinary())
        self.pulserHardware.ppWriteData(mycode)
        print "Starting"
        self.pulserHardware.ppStart()
        self.running = True
        self.currentIndex = 0
        if self.currentTrace is not None:
            self.currentTrace.header = self.pulseProgramUi.pulseProgram.currentVariablesText("#")
            if self.scan.autoSave:
                self.currentTrace.resave()
            self.currentTrace = None
        self.scanParametersWidget.progressBar.setRange(0,len(self.scan.list))
        self.scanParametersWidget.progressBar.setValue(0)
        self.scanParametersWidget.progressBar.setVisible( True )
        self.timestampsNewRun = True
        print "elapsed time", time.time()-start
    
    def onPause(self):
        self.StatusMessage.emit("test Pause not implemented")
    
    def onStop(self):
        if self.running:
            self.pulserHardware.ppStop()
            self.pulserHardware.ppClearWriteFifo()
            self.pulserHardware.ppFlushData()
            self.running = False
            if self.scan.rewriteDDS:
                self.NeedsDDSRewrite.emit()
        self.scanParametersWidget.progressBar.setVisible( False )
        
    def startData(self):
        """ Initialize necessary data structures
        """
        pass
    
    def traceFilename(self, pattern):
        directory = DataDirectory.DataDirectory( self.scanSettings.project )
        if pattern and pattern!='':
            filename, components = directory.sequencefile( pattern )
            return filename
        else:
            path = str(QtGui.QFileDialog.getSaveFileName(self, 'Save file',directory.path()))
            return path
            
    def onData(self, data ):
        """ Called by worker with new data
        """
        print "onData", len(data.count[self.scanSettings.counter]), data.scanvalue
        mean = numpy.mean( data.count[self.scanSettings.counter] )
        if self.scan.scanMode == self.scanParametersWidget.ScanModes.StepInPlace:
            x = self.currentIndex
        else:
            x = self.scan.list[self.currentIndex].ounit(self.scan.start.out_unit).toval()
        if self.currentTrace is None:
            self.currentTrace = Trace.Trace()
            self.currentTrace.x = numpy.array([x])
            self.currentTrace.y = numpy.array([mean])
            self.currentTrace.name = self.scan.name
            self.currentTrace.vars.comment = ""
            self.currentTrace.filenameCallback = functools.partial( self.traceFilename, self.scan.filename )
            self.plottedTrace = Traceui.PlottedTrace(self.currentTrace,self.graphicsView,pens.penList)
            if not self.scan.scanMode == self.scanParametersWidget.ScanModes.StepInPlace:
                self.graphicsView.setXRange( self.scan.start.toval(), self.scan.stop.ounit(self.scan.start.out_unit).toval() )
            self.traceui.addTrace(self.plottedTrace,pen=-1)
        else:
            if self.scan.scanMode == self.scanParametersWidget.ScanModes.StepInPlace and len(self.currentTrace.x)>=self.scan.steps:
                self.currentTrace.x = numpy.append(self.currentTrace.x[-self.scan.steps+1:], x)
                self.currentTrace.y = numpy.append(self.currentTrace.y[-self.scan.steps+1:], mean)
            else:
                self.currentTrace.x = numpy.append(self.currentTrace.x, x)
                self.currentTrace.y = numpy.append(self.currentTrace.y, mean)
            self.plottedTrace.replot()
        self.currentIndex += 1
        self.showHistogram(data)
        if self.timestampSettingsWidget.settings.enable: 
            self.showTimestamps(data)
        if data.final:
            self.finalizeData()
        else:
            if self.scan.scanMode == self.scanParametersWidget.ScanModes.StepInPlace:
                self.pulserHardware.ppWriteData(self.scan.code)     
        self.scanParametersWidget.progressBar.setValue(self.currentIndex)

    def finalizeData(self):
        pulseProgramHeader = self.pulseProgramUi.pulseProgram.currentVariablesText("#")
        scanHeader = stringutilit.commentarize( repr(self.scan) )
        self.currentTrace.header = '\n'.join((pulseProgramHeader, scanHeader)) 
        if self.scan.autoSave:
            self.currentTrace.resave()
        if self.scan.scanMode == self.scanParametersWidget.ScanModes.RepeatedScan:
            self.onStart()
        else:
            self.onStop()
        
    def showTimestamps(self,data):
        settings = self.timestampSettingsWidget.settings
        bins = int( (settings.roiWidth/settings.binwidth).toval() )
        myrange = (settings.roiStart.toval('ms'),(settings.roiStart+settings.roiWidth).toval('ms'))
        y, x = numpy.histogram( [ (timestamp * self.pulserHardware.timestep).toval('ms') for timestamp in data.timestamp[settings.channel]], 
                                range=myrange,
                                bins=bins)
        x = x[0:-1]
                                
        if self.currentTimestampTrace and numpy.array_equal(self.currentTimestampTrace.x,x) and (
            settings.integrate == self.timestampSettingsWidget.integrationMode.IntegrateAll or 
                (settings.integrate == self.timestampSettingsWidget.integrationMode.IntegrateRun and not self.timestampsNewRun) ) :
            self.currentTimestampTrace.y += y
            self.plottedTimestampTrace.replot()
        else:    
            self.currentTimestampTrace = Trace.Trace()
            self.currentTimestampTrace.x = x
            self.currentTimestampTrace.y = y
            self.currentTimestampTrace.name = self.scan.name
            self.currentTimestampTrace.vars.comment = ""
            self.currentTimestampTrace.filenameCallback = functools.partial( self.traceFilename, "Timestamp_"+self.scan.filename )
            self.plottedTimestampTrace = Traceui.PlottedTrace(self.currentTimestampTrace,self.timestampView,pens.penList)
            self.timestampTraceui.addTrace(self.plottedTimestampTrace,pen=-1)              
        self.timestampsNewRun = False                       
        
    def showHistogram(self, data):
        settings = self.scanSettingsWidget.settings
        y, x = numpy.histogram( data.count[settings.counter] , range=(0,settings.histogramBins), bins=settings.histogramBins)
        if settings.integrate and hasattr(self,'histx') and numpy.array_equal(self.histx,x):
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
                self.startData()
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
        self.config['ScanExperiment.MainWindow.State'] = QtGui.QMainWindow.saveState(self)
        self.config['ScanExperiment.pyqtgraph-dokareastate'] = self.area.saveState()
        self.scanParametersWidget.onClose()
        self.scanSettingsWidget.onClose()
        self.timestampSettingsWidget.onClose()
        self.traceui.onClose()

    def updateSettings(self,settings,active=False):
        """ Main program settings have changed
        """
        self.deviceSettings = settings
        