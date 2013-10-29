# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 21:36:17 2013

Scan that varies a parameter outside the FPGA
it uses ScanExperiment and only overwrites procedures that need to handle
stuff differently.

External parameters that can be scanned in this way are defined in ExternalScannedParameters

The pulse program is expected to run the experiment necessary for one external parameter setting.
It reports the count values during each experiment and finishes by sending the end marker (0xffffffff).

@author: pmaunz
"""

import ScanExperiment 
import time
from PyQt4 import QtCore
from modules import enum

class VoltageScanExperiment( ScanExperiment.ScanExperiment ):
    Status = enum.enum('Idle','Starting','Running','Stopping')
    def __init__(self,settings,pulserHardware,experimentName,parent=None):
        super(VoltageScanExperiment,self).__init__(settings,pulserHardware,experimentName,parent)
        self.status = self.Status.Idle        
        
    def setupUi(self,MainWindow,config):
        super(VoltageScanExperiment,self).setupUi(MainWindow,config)
        #self.scanControlWidget.setScanNames()
        
    def setPulseProgramUi(self,pulseProgramUi):
        self.pulseProgramUi = pulseProgramUi.addExperiment(self.experimentName)
        
    def updateEnabledParameters(self, enabledParameters ):
        self.enabledParameters = enabledParameters
        
    def startScan(self):
        if self.status in [self.Status.Idle, self.Status.Stopping, self.Status.Running]:
            self.startTime = time.time()
            self.state = self.OpStates.running
            self.externalParameter = self.enabledParameters[self.scan.scanParameter]
            self.externalParameter.saveValue()
            self.externalParameterIndex = 0
            self.generator = ScanExperiment.GeneratorList[self.scan.scanMode](self.scan)
                    
            self.pulserHardware.ppFlushData()
            self.pulserHardware.ppClearWriteFifo()
            self.pulserHardware.ppUpload(self.pulseProgramUi.getPulseProgramBinary())
            QtCore.QTimer.singleShot(100,self.startBottomHalf)
            self.displayUi.onClear()
            self.status = self.Status.Starting
            if self.plottedTrace is not None:
                self.plottedTrace.plot(0) #unplot previous trace
                if self.scan.autoSave:
                    self.plottedTrace.trace.resave()
            self.plottedTrace = None #reset plotted trace
        
    def startBottomHalf(self):
        if self.status == self.Status.Starting:
            if self.externalParameter.setValue( self.scan.list[self.externalParameterIndex]):
                """We are done adjusting"""
                self.pulserHardware.ppStart()
                self.currentIndex = 0
                self.updateProgressBar(0,max(len(self.scan.list),1))
                self.timestampsNewRun = True
                print "elapsed time", time.time()-self.startTime
                self.status = self.Status.Running
                print "Status -> Running"
            else:
                QtCore.QTimer.singleShot(100,self.startBottomHalf)

    def onStop(self):
        print "Old Status", self.status
        if self.status in [self.Status.Starting, self.Status.Running]:
            ScanExperiment.ScanExperiment.onStop(self)
            self.status = self.Status.Stopping
            self.stopBottomHalf()
            print "Status -> Stopping"
            self.finalizeData(reason='stopped')
            self.updateProgressBar(self.currentIndex+1,max(len(self.scan.list),1))

                    
    def stopBottomHalf(self):
        if self.status==self.Status.Stopping:
            if not self.externalParameter.restoreValue():
                QtCore.QTimer.singleShot(100,self.stopBottomHalf)
            else:
                self.status = self.Status.Idle
                self.updateProgressBar(0,max(len(self.scan.list),1))

    def onData(self, data ):
        """ Called by worker with new data
        """
        print "NewExternalScan onData", len(data.count[self.scan.counterChannel]), data.scanvalue
        mean, error, raw = self.scan.evalAlgo.evaluate( data.count[self.scan.counterChannel] )
        self.displayUi.add( mean )
        x = self.generator.xValue(self.externalParameterIndex)
        print "data", x, mean 
        if mean is not None:
            self.updateMainGraph(x, mean, error, raw)
        self.currentIndex += 1
        self.externalParameterIndex += 1
        self.showHistogram(data)
        if self.scan.enableTimestamps: 
            self.showTimestamps(data)
        if self.externalParameterIndex<len(self.scan.list) and self.status==self.Status.Running:
            self.externalParameter.setValue( self.scan.list[self.externalParameterIndex])
            self.pulserHardware.ppStart()
            print "External Value:" , self.scan.list[self.externalParameterIndex]
        else:
            self.finalizeData(reason='end of scan')
            if self.externalParameterIndex >= len(self.scan.list):
                self.generator.dataOnFinal(self)
        self.updateProgressBar(self.externalParameterIndex+1,max(len(self.scan.list),1))

