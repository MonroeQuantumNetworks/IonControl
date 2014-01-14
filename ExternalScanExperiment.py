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
import ExternalScannedParameters
from PyQt4 import QtCore
from modules import enum
import logging

class ScanNotAvailableException(Exception):
    pass

class ExternalScanExperiment( ScanExperiment.ScanExperiment ):
    def __init__(self,settings,pulserHardware,experimentName,toolBar=None,parent=None):
        super(ExternalScanExperiment,self).__init__(settings,pulserHardware,experimentName,toolBar=toolBar,parent=parent)
        self.state = self.OpStates.idle      
        
    def setupUi(self,MainWindow,config):
        super(ExternalScanExperiment,self).setupUi(MainWindow,config)
        
    def updatePulseProgram(self):
        self.scanControlWidget.setPulseProgramUi( self.pulseProgramUi )

    def setPulseProgramUi(self,pulseProgramUi):
        self.pulseProgramUi = pulseProgramUi.addExperiment(self.experimentName, self.globalVariables, self.globalVariablesChanged )
        self.pulseProgramUi.pulseProgramChanged.connect( self.updatePulseProgram )
        self.scanControlWidget.setPulseProgramUi( self.pulseProgramUi )
        
    def updateEnabledParameters(self, enabledParameters ):
        self.enabledParameters = enabledParameters
        self.scanControlWidget.setScanNames( self.enabledParameters.keys() )
        
    def startScan(self):
        logger = logging.getLogger(__name__)
        if self.state in [self.OpStates.idle, self.OpStates.stopping, self.OpStates.running, self.OpStates.paused]:
            self.startTime = time.time()
            self.state = self.OpStates.running
            if self.scan.scanParameter not in self.enabledParameters:
                message = "External Scan Parameter '{0}' is not enabled.".format(self.scan.scanParameter)
                logger.error(message)
                raise ScanNotAvailableException(message) 
            self.externalParameter = self.enabledParameters[self.scan.scanParameter]
            self.externalParameter.saveValue()
            self.externalParameterIndex = 0
            self.generator = ScanExperiment.GeneratorList[self.scan.scanMode](self.scan)
                    
            self.pulserHardware.ppFlushData()
            self.pulserHardware.ppClearWriteFifo()
            self.pulserHardware.ppUpload(self.pulseProgramUi.getPulseProgramBinary())
            self.displayUi.onClear()
            self.state = self.OpStates.starting
            self.plottedTrace = None #reset plotted trace
            if self.plottedTraceList:
                for plottedTrace in self.plottedTraceList:
                    plottedTrace.plot(0) #unplot previous trace
            self.plottedTraceList = list() #reset plotted trace
            QtCore.QTimer.singleShot(100,self.startBottomHalf)
           
    def startBottomHalf(self):
        logger = logging.getLogger(__name__)
        if self.state == self.OpStates.starting:
            if self.externalParameter.setValue( self.scan.list[self.externalParameterIndex]):
                """We are done adjusting"""
                self.pulserHardware.ppStart()
                self.currentIndex = 0
                self.updateProgressBar(0,max(len(self.scan.list),1))
                self.timestampsNewRun = True
                logger.info( "elapsed time {0}".format( time.time()-self.startTime ) )
                self.state = self.OpStates.running
                logger.info( "Status -> Running" )
                self.updateProgressBar(self.currentIndex+1,max(len(self.scan.list),1))
            else:
                QtCore.QTimer.singleShot(100,self.startBottomHalf)

    def onStop(self):
        logger = logging.getLogger(__name__)
        logger.debug( "Old Status {0}".format( self.state ) )
        if self.state in [self.OpStates.starting, self.OpStates.running, self.OpStates.paused]:
            ScanExperiment.ScanExperiment.onStop(self)
            logger.info( "Status -> Stopping" )
            self.stopBottomHalf()
            self.updateProgressBar(self.currentIndex+1,max(len(self.scan.list),1))
            self.state = self.OpStates.stopping

                    
    def stopBottomHalf(self):
        logger = logging.getLogger(__name__)
        if self.state==self.OpStates.stopping:
            if not self.externalParameter.restoreValue():
                QtCore.QTimer.singleShot(100,self.stopBottomHalf)
            else:
                self.state = self.OpStates.idle
                self.updateProgressBar(0,max(len(self.scan.list),1))
                logger.info( "Status -> Idle" )

    def onData(self, data ):
        """ Called by worker with new data
        """
        logger = logging.getLogger(__name__)

        if data.overrun:
            logger.error( "Read Pipe Overrun" )
            self.onPause()
        else:
            logger.info( "NewExternalScan onData {0}".format( data.scanvalue ) )
            x = self.generator.xValue(self.externalParameterIndex)
            evaluated = list()
            for eval, algo in zip(self.scan.evalList,self.scan.evalAlgorithmList):
                if data.count[eval.counter]:
                    evaluated.append( (algo.evaluate( data.count[eval.counter]),algo.settings['errorBars'] ) ) # returns mean, error, raw
                else:
                    logger.info( "No data for counter {0}, ignoring it.".format(eval.counter) )
            if len(evaluated)>0:
                self.displayUi.add( evaluated[0][0][0] )
                self.updateMainGraph(x, evaluated )
                self.showHistogram(data, self.scan.evalList[0].counter )
            self.currentIndex += 1
            self.externalParameterIndex += 1
            if self.scan.enableTimestamps: 
                self.showTimestamps(data)
            if self.state == self.OpStates.running:
                if self.externalParameterIndex < len(self.scan.list):
                    self.externalParameter.setValue( self.scan.list[self.externalParameterIndex])
                    self.pulserHardware.ppStart()
                    logger.info( "External Value: {0}".format(self.scan.list[self.externalParameterIndex]) )
                else:
                    self.finalizeData(reason='end of scan')
                    self.generator.dataOnFinal(self)
                    logger.info("Scan Completed")
            self.updateProgressBar(self.externalParameterIndex+1,max(len(self.scan.list),1))

