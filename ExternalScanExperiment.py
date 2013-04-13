# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 21:36:17 2013
Scan that varies a parameter outside the FPGA
it uses ScanExperiment and only overwrites procedures that need to handle
stuff differently.
@author: pmaunz
"""

import ScanExperiment 
import time
import numpy
import Trace
import functools
import Traceui
import pens
import ExternalScannedParameters
from PyQt4 import QtCore

class ExternalScanExperiment( ScanExperiment.ScanExperiment ):
    def setupUi(self,MainWindow,config):
        super(ExternalScanExperiment,self).setupUi(MainWindow,config)
        self.scanParametersWidget.setScanNames(ExternalScannedParameters.ExternalScannedParameters.keys())
        
    def setPulseProgramUi(self,pulseProgramUi):
        self.pulseProgramUi = pulseProgramUi.addExperiment(self.experimentName)
        
    def onStart(self):
        if not self.running:
            self.running = True
            self.start = time.time()
            self.state = self.OpStates.running
            self.scanSettings = self.scanSettingsWidget.settings
            self.scan = self.scanParametersWidget.getScan()
            self.externalParameter = ExternalScannedParameters.ExternalScannedParameters[self.scan.name]()
            self.externalParameter.saveValue()
            self.externalParameterIndex = 0
                    
            self.pulserHardware.ppFlushData()
            self.pulserHardware.ppClearWriteFifo()
            self.pulserHardware.ppUpload(self.pulseProgramUi.getPulseProgramBinary())
            QtCore.QTimer.singleShot(100,self.startBottomHalf)
        
    def startBottomHalf(self):
        if self.externalParameter.setValue( self.scan.list[self.externalParameterIndex]):
            """We are done adjusting"""
            self.pulserHardware.ppStart()
            self.currentIndex = 0
            if self.currentTrace is not None:
                self.currentTrace.header = self.pulseProgramUi.pulseProgram.currentVariablesText("#")
                if self.scan.autoSave:
                    self.currentTrace.resave()
                self.currentTrace = None
            self.scanParametersWidget.progressBar.setRange(0,float(len(self.scan.list)))
            self.scanParametersWidget.progressBar.setValue(0)
            self.scanParametersWidget.progressBar.setVisible( True )
            self.timestampsNewRun = True
            print "elapsed time", time.time()-self.start
        else:
            QtCore.QTimer.singleShot(100,self.startBottomHalf)

    def onStop(self):
        super(ExternalScanExperiment,self).onStop()
        self.externalParameter.restoreValue()


    def onData(self, data ):
        """ Called by worker with new data
        """
        print "NewExternalScan onData", len(data.count[self.scanSettings.counter]), data.scanvalue
        mean, error = self.scanSettings.evalAlgo.evaluate( data.count[self.scanSettings.counter] )
        if self.scan.scanMode == self.scanParametersWidget.ScanModes.StepInPlace:
            x = self.currentIndex
        else:
            x = self.externalParameter.currentExternalValue() 
        print "data", x, mean 
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
        self.externalParameterIndex += 1
        self.showHistogram(data)
        if self.timestampSettingsWidget.settings.enable: 
            self.showTimestamps(data)
        if self.externalParameterIndex<len(self.scan.list):
            self.externalParameter.setValue( self.scan.list[self.externalParameterIndex])
            self.pulserHardware.ppStart()
            print "External Value:" , self.scan.list[self.externalParameterIndex]
        else:
            self.finalizeData()
        self.scanParametersWidget.progressBar.setValue(float(self.externalParameterIndex))
