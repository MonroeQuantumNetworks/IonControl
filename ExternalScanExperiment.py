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
import ScanExperimentSettings
import time
import ExternalScannedParameters
from modules import enum
from modules import DataDirectory

        
ExternalScanForm, ExternalScanBase = PyQt4.uic.loadUiType(r'ui\ExternalScanExperiment.ui')

class ExternalScanExperiment(ExternalScanForm, MainWindowWidget.MainWindowWidget):
    StatusMessage = QtCore.pyqtSignal( str )
    ClearStatusMessage = QtCore.pyqtSignal()
    NeedsDDSRewrite = QtCore.pyqtSignal()
    OpStates = enum.enum('idle','running','paused')
    experimentName = 'External Scan'

    def __init__(self,settings,pulserHardware,parent=None):
        MainWindowWidget.MainWindowWidget.__init__(self,parent)
        ExternalScanForm.__init__(self)
        self.settings = settings
        self.pulserHardware = pulserHardware
        self.activated = False
        self.currentTrace = None

    def setupUi(self,MainWindow,config):
        ExternalScanForm.setupUi(self,MainWindow)
        self.config = config
        self.graphicsView = self.graphicsLayout.graphicsView
        self.penicons = pens.penicons().penicons()
        self.traceui = Traceui.Traceui(self.penicons)
        self.traceui.setupUi(self.traceui)
        self.dockWidget.setWidget( self.traceui )
        self.dockWidgetList.append(self.dockWidget)
        self.fitWidget = FitUi.FitUi(self.traceui,self.config,"ExternalScanExperiment")
        self.fitWidget.setupUi(self.fitWidget)
        self.dockWidgetFitUi.setWidget( self.fitWidget )
        self.dockWidgetList.append(self.dockWidgetFitUi )
        self.scanParametersWidget = ScanParameters.ScanParameters(config,"ScanExperiment")
        self.scanParametersWidget.setupUi(self.scanParametersWidget)
        self.scanParametersDock = QtGui.QDockWidget("Scan Parameters")
        self.scanParametersDock.setObjectName("ExternalScanParametersDock")
        self.scanParametersDock.setWidget(self.scanParametersWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea , self.scanParametersDock)
        self.scanSettingsWidget = ScanExperimentSettings.ScanExperimentSettings(config,"ExternalScanExperiment")
        self.scanSettingsWidget.setupUi(self.scanSettingsWidget)
        self.scanSettingsDock = QtGui.QDockWidget("Settings")
        self.scanSettingsDock.setObjectName("ExternalScanSettingsDock")
        self.scanSettingsDock.setWidget(self.scanSettingsWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea , self.scanSettingsDock)
        if 'ExternalScanExperiment.MainWindow.State' in self.config:
            QtGui.QMainWindow.restoreState(self,self.config['ExternalScanExperiment.MainWindow.State'])
            print "restoreState"
        self.scanParametersWidget.setScanNames(ExternalScannedParameters.ExternalScannedParameters.keys())
            

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
        directory = DataDirectory.DataDirectory( self.scanSettings.project )
        self.tracefilename, components = directory.sequencefile( self.scanSettings.filename )
        self.scan = self.scanParametersWidget.getScan()
        self.externalParameter = ExternalScannedParameters.ExternalScannedParameters[self.scan.name]()
        self.externalParameter.saveValue()
        self.externalParameterIndex = 0
        self.externalParameter.setValue( self.scan.list[self.externalParameterIndex])
                
        self.pulserHardware.ppUpload(self.pulseProgramUi.getPulseProgramBinary())
        self.pulserHardware.ppStart()
        self.running = True
        self.currentIndex = 0
        if self.currentTrace is not None:
            self.currentTrace.header = self.pulseProgramUi.pulseProgram.currentVariablesText("#")
            self.currentTrace.resave()
            self.currentTrace = None
        self.scanParametersWidget.progressBar.setRange(0,float(len(self.scan.list)))
        self.scanParametersWidget.progressBar.setValue(0)
        self.scanParametersWidget.progressBar.setVisible( True )
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
        self.externalParameter.restoreValue()
        self.scanParametersWidget.progressBar.setVisible( False )
       
    def activate(self):
        MainWindowWidget.MainWindowWidget.activate(self)
        if (self.pulserHardware is not None) and (not self.activated):
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

    def onData(self, data ):
        """ Called by worker with new data
        """
        print "onData", len(data.count[self.scanSettings.counter]), data.scanvalue
        mean = numpy.mean( data.count[self.scanSettings.counter] )
        x = self.externalParameter.currentExternalValue() #self.scan.list[self.currentIndex].ounit(self.scan.start.out_unit).toval()
        print "data", x, mean 
        if self.currentTrace is None:
            self.currentTrace = Trace.Trace()
            self.currentTrace.x = numpy.array([x])
            self.currentTrace.y = numpy.array([mean])
            self.currentTrace.name = self.scan.name
            self.currentTrace.vars.comment = ""
            self.currentTrace.filename = self.tracefilename
            print "Filename:" , self.tracefilename
            self.plottedTrace = Traceui.PlottedTrace(self.currentTrace,self.graphicsView,pens.penList)
            if not self.scan.scanMode == self.scanParametersWidget.ScanModes.StepInPlace:
                self.graphicsView.setXRange( self.scan.start.toval(), self.scan.stop.ounit(self.scan.start.out_unit).toval() )
            self.traceui.addTrace(self.plottedTrace,pen=-1)
        else:
            self.currentTrace.x = numpy.append(self.currentTrace.x, x)
            self.currentTrace.y = numpy.append(self.currentTrace.y, mean)
            self.plottedTrace.replot()
        self.externalParameterIndex += 1
#        self.showHistogram(data)
#        if self.timestampSettingsWidget.settings.enable: 
#            self.showTimestamps(data)
        if self.externalParameterIndex<len(self.scan.list):
            self.externalParameter.setValue( self.scan.list[self.externalParameterIndex])
            self.pulserHardware.ppStart()
            print "External Value:" , self.scan.list[self.externalParameterIndex]
        else:
            self.currentTrace.header = self.pulseProgramUi.pulseProgram.currentVariablesText("#")
            self.currentTrace.resave()
            if self.scan.scanMode == self.scanParametersWidget.ScanModes.RepeatedScan:
                self.onStart()
            else:
                self.onStop()
        self.scanParametersWidget.progressBar.setValue(float(self.externalParameterIndex))

           
    def onClose(self):
        self.config['ExternalScanExperiment.MainWindow.State'] = QtGui.QMainWindow.saveState(self)
        self.scanParametersWidget.onClose()
        self.scanSettingsWidget.onClose()
