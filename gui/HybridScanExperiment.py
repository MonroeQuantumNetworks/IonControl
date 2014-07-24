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

import ExternalScanExperiment
import ScanExperiment
from functools import partial
from modules.magnitude import Magnitude
from modules import DataDirectory

class ScanNotAvailableException(Exception):
    pass

class HybridScanExperiment( ExternalScanExperiment.ExternalScanExperiment ):
    def __init__(self,settings,pulserHardware,experimentName,toolBar=None,parent=None):
        super(HybridScanExperiment,self).__init__(settings,pulserHardware,experimentName,toolBar=toolBar,parent=parent)
        self.enableParameter = True
        self.enableExternalParameter = True
        
    def setupUi(self,MainWindow,config):
        super(HybridScanExperiment,self).setupUi(MainWindow,config)
        
    def updatePulseProgram(self):
        self.scanControlWidget.setPulseProgramUi( self.pulseProgramUi )

    def setPulseProgramUi(self,pulseProgramUi):
        self.pulseProgramUi = pulseProgramUi.addExperiment(self.experimentName, self.globalVariables, self.globalVariablesChanged )
        self.pulseProgramUi.pulseProgramChanged.connect( self.updatePulseProgram )
        self.scanControlWidget.setPulseProgramUi( self.pulseProgramUi )
        
    def updateEnabledParameters(self, enabledParameters ):
        self.enabledParameters = enabledParameters
        self.scanControlWidget.setScanNames( self.enabledParameters.keys() )
        
#     def startScan(self):
#         PulseProgramBinary = self.pulseProgramUi.getPulseProgramBinary() # also overwrites the current variable values            
#         self.generator = GeneratorList[self.scan.scanMode](self.scan)
#         (mycode, data) = self.generator.prepare(self.pulseProgramUi)
#         self.progressUi.setRunning( max(len(self.scan.list),1) ) 
#         if data:
#             self.pulserHardware.ppWriteRamWordList(data,0, check=False)
#             datacopy = [0]*len(data)
#             datacopy = self.pulserHardware.ppReadRamWordList(datacopy,0)
#             if self.scan.gateSequenceSettings.debug:
#                 dumpFilename, _ = DataDirectory.DataDirectory().sequencefile("fpga_sdram.bin")
#                 with open( dumpFilename, 'wb') as f:
#                     f.write( self.pulserHardware.wordListToBytearray(datacopy))
#                 codeFilename, _ = DataDirectory.DataDirectory().sequencefile("start_address.txt")
#                 with open( codeFilename, 'w') as f:
#                     for a in mycode:
#                         f.write( "{0}\n".format(a) )
#             if data!=datacopy:
#                 raise ScanException("Ram write unsuccessful")
#         self.pulserHardware.ppFlushData()
#         self.pulserHardware.ppClearWriteFifo()
#         self.pulserHardware.ppUpload(PulseProgramBinary)
#         self.pulserHardware.ppWriteData(mycode)
#         logger.info( "Starting" )
#         self.pulserHardware.ppStart()
#         self.currentIndex = 0
#         self.timestampsNewRun = True
#         self.displayUi.onClear()
#         logger.info( "elapsed time {0}".format( time.time()-self.startTime ) )
#         if self.plottedTraceList and self.traceui.unplotLastTrace():
#             for plottedTrace in self.plottedTraceList:
#                 plottedTrace.plot(0) #unplot previous trace
#         self.plottedTraceList = list() #reset plotted trace
#         self.otherDataFile = None 

    def startScan(self):
        logger = logging.getLogger(__name__)
        if self.progressUi.state in [self.OpStates.idle, self.OpStates.stopping, self.OpStates.running, self.OpStates.paused, self.OpStates.interrupted]:
            self.startTime = time.time()
            if self.scan.externalScanParameter not in self.enabledParameters:
                message = "External Scan Parameter '{0}' is not enabled.".format(self.scan.externalScanParameter)
                logger.error(message)
                raise ScanNotAvailableException(message) 
            self.externalParameter = self.enabledParameters[self.scan.externalScanParameter]
            self.externalParameter.saveValue()
            self.externalParameterIndex = 0
            self.generator = ScanExperiment.GeneratorList[self.scan.scanMode](self.scan)
            (mycode, data) = self.generator.prepare(self.pulseProgramUi)
            if data:
                self.pulserHardware.ppWriteRamWordList(data,0, check=False)
                datacopy = [0]*len(data)
                datacopy = self.pulserHardware.ppReadRamWordList(datacopy,0)
                if self.scan.gateSequenceSettings.debug:
                    dumpFilename, _ = DataDirectory.DataDirectory().sequencefile("fpga_sdram.bin")
                    with open( dumpFilename, 'wb') as f:
                        f.write( self.pulserHardware.wordListToBytearray(datacopy))
                    codeFilename, _ = DataDirectory.DataDirectory().sequencefile("start_address.txt")
                    with open( codeFilename, 'w') as f:
                        for a in mycode:
                            f.write( "{0}\n".format(a) )
                if data!=datacopy:
                    raise ScanExperiment.ScanException("Ram write unsuccessful")
                    
            self.pulserHardware.ppFlushData()
            self.pulserHardware.ppClearWriteFifo()
            self.pulserHardware.ppUpload(self.pulseProgramUi.getPulseProgramBinary())
            self.pulserHardware.ppWriteData(mycode)     #TODO make sure only one point is written
            self.displayUi.onClear()
            self.progressUi.setStarting()
            self.plottedTrace = None #reset plotted trace
            if self.plottedTraceList and self.traceui.unplotLastTrace():
                for plottedTrace in self.plottedTraceList:
                    plottedTrace.plot(0) #unplot previous trace
            self.plottedTraceList = list() #reset plotted trace
            QtCore.QTimer.singleShot(100,self.startBottomHalf)
           
    def startBottomHalf(self):
        logger = logging.getLogger(__name__)
        if self.progressUi.state == self.OpStates.starting:
            if self.externalParameter.setValue( self.scan.list[self.externalParameterIndex]):
                """We are done adjusting"""
                self.pulserHardware.ppStart()
                self.currentIndex = 0
                self.timestampsNewRun = True
                logger.info( "elapsed time {0}".format( time.time()-self.startTime ) )
                logger.info( "Status -> Running" )
                self.progressUi.setRunning( max(len(self.scan.list),1) ) 
            else:
                QtCore.QTimer.singleShot(100,self.startBottomHalf)

    def onStop(self):
        logger = logging.getLogger(__name__)
        if self.progressUi.state in [self.OpStates.starting, self.OpStates.running, self.OpStates.paused, self.OpStates.interrupted]:
            ScanExperiment.ScanExperiment.onStop(self)
            logger.info( "Status -> Stopping" )
            self.progressUi.setStopping()
            self.stopBottomHalf()

                    
    def stopBottomHalf(self):
        logger = logging.getLogger(__name__)
        if self.progressUi.state==self.OpStates.stopping:
            if not self.externalParameter.restoreValue():
                QtCore.QTimer.singleShot(100,self.stopBottomHalf)
            else:
                self.progressUi.setIdle()
                logger.info( "Status -> Idle" )

    def onData(self, data, queuesize ):
        """ Called by worker with new data
        """
        logger = logging.getLogger(__name__)

        if data.overrun:
            logger.error( "Read Pipe Overrun" )
            self.onPause()
        else:
            logger.info( "NewExternalScan onData {0}".format( data.scanvalue ) )
            if not self.externalParameter.useExternalValue():
                x = self.generator.xValue(self.externalParameterIndex)
                self.dataMiddlePart(data, queuesize, x)
            else:
                self.externalParameter.asyncCurrentExternalValue( partial( self.dataMiddlePart, data, queuesize) )
            
    def dataMiddlePart(self, data, queuesize, x):
        if isinstance(x, Magnitude):
            x = x.ounit(self.scan.xUnit).toval()
        logger = logging.getLogger(__name__)
        evaluated = list()
        expected = self.generator.expected( self.currentIndex )
        for evaluation, algo in zip(self.scan.evalList,self.scan.evalAlgorithmList):
            evaluated.append( algo.evaluate( data, counter=evaluation.counter, name=evaluation.name, expected=expected ) ) # returns mean, error, raw
        if len(evaluated)>0:
            self.displayUi.add(  [ e[0] for e in evaluated ] )
            self.updateMainGraph(x, evaluated, queuesize if self.externalParameterIndex < len(self.scan.list) else 0 )
            self.showHistogram(data, self.scan.evalList )
        self.currentIndex += 1
        self.externalParameterIndex += 1
        if self.scan.enableTimestamps: 
            self.showTimestamps(data)
        if self.progressUi.state == self.OpStates.running:
            if data.final and data.exitcode not in [0,0xffff]:
                self.onInterrupt( self.pulseProgramUi.exitcode(data.exitcode) )
            elif self.externalParameterIndex < len(self.scan.list):
                self.dataBottomHalf()
                self.progressUi.onData( self.currentIndex )  
            else:
                self.finalizeData(reason='end of scan')
                self.generator.dataOnFinal(self, self.progressUi.state )
                logger.info("Scan Completed")

    def dataBottomHalf(self):
        logger = logging.getLogger(__name__)
        if self.progressUi.state == self.OpStates.running:
            if self.externalParameter.setValue( self.scan.list[self.externalParameterIndex]):
                """We are done adjusting"""
                self.pulserHardware.ppStart()
                logger.info( "External Value: {0}".format(self.scan.list[self.externalParameterIndex]) )
            else:
                QtCore.QTimer.singleShot(100,self.dataBottomHalf)
