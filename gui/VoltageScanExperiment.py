# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 21:36:17 2013

Scan that varies a parameter outside the FPGA
it uses ScanExperiment and only overwrites procedures that need to handle
stuff differently.

External parameters that can be scanned in this way are defined in ExternalParameter

The pulse program is expected to run the experiment necessary for one external parameter setting.
It reports the count values during each experiment and finishes by sending the end marker (0xffffffff).

@author: pmaunz
"""

import logging
import time

from PyQt4 import QtCore

import ScanExperiment
from modules import enum


class VoltageScanExperiment( ScanExperiment.ScanExperiment ):
    Status = enum.enum('Idle','Starting','Running','Stopping')
    def __init__(self,settings,pulserHardware,globalVariablesUi,experimentName,toolBar=None,parent=None):
        super(VoltageScanExperiment,self).__init__(settings,pulserHardware,globalVariablesUi,experimentName,toolBar=toolBar,parent=parent)
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
            if self.plottedTrace is not None and self.traceui.unplotLastTrace():
                self.plottedTrace.plot(0) #unplot previous trace
                if self.scan.autoSave:
                    self.plottedTrace.trace.resave()
            self.plottedTrace = None #reset plotted trace
        
    def startBottomHalf(self):
        logger = logging.getLogger(__name__)
        if self.status == self.Status.Starting:
            if self.externalParameter.setValue( self.scan.list[self.externalParameterIndex]):
                """We are done adjusting"""
                self.pulserHardware.ppStart()
                self.currentIndex = 0
                self.updateProgressBar(0,max(len(self.scan.list),1))
                self.timestampsNewRun = True
                logger.info( "elapsed time {0}".format( time.time()-self.startTime ) )
                self.status = self.Status.Running
                logger.info( "Status -> Running" )
            else:
                QtCore.QTimer.singleShot(100,self.startBottomHalf)

    def onStop(self):
        logger = logging.getLogger(__name__)        
        logger.debug( "Old Status {0}".format( self.status ) )
        if self.status in [self.Status.Starting, self.Status.Running]:
            ScanExperiment.ScanExperiment.onStop(self)
            self.status = self.Status.Stopping
            self.stopBottomHalf()
            logger.info( "Status -> Stopping" )
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
        logger = logging.getLogger(__name__)
        logger.info( "NewExternalScan onData {0}".format( data.scanvalue ) )
        mean, error, raw = self.scan.evalAlgo.evaluate( data.count[0] )
        self.displayUi.add( mean )
        x = self.generator.xValue(self.externalParameterIndex)
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
            logger.info( "External Value: {0}".format( self.scan.list[self.externalParameterIndex] ) )
        else:
            self.finalizeData(reason='end of scan')
            if self.externalParameterIndex >= len(self.scan.list):
                self.generator.dataOnFinal(self)
        self.updateProgressBar(self.externalParameterIndex+1,max(len(self.scan.list),1))

