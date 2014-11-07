'''
Created on Nov 6, 2014

@author: pmaunz
'''
import logging
import time
from PyQt4 import QtCore
from collections import defaultdict
from modules import DataDirectory

from gui.ScanGenerators import GeneratorList
from _functools import partial

class ScanException(Exception):
    pass

class ScanNotAvailableException(Exception):
    pass

class InternalScanMethod(object):
    name = 'Internal'
    def __init__(self, experiment):
        self.experiment = experiment
    
    def startScan(self):
        logger = logging.getLogger(__name__)
        self.experiment.progressUi.setRunning( max(len(self.experiment.scan.list),1) ) 
        logger.info( "Starting" )
        self.experiment.pulserHardware.ppStart()
        self.experiment.currentIndex = 0
        logger.info( "elapsed time {0}".format( time.time()-self.experiment.startTime ) )

    def onStop(self):
        self.experiment.progressUi.setIdle()            

    def onData(self, data, queuesize, x ):
        self.experiment.dataMiddlePart( data, queuesize, x )
   
class ExternalScanMethod(InternalScanMethod):
    name = 'External'
    def __init__(self, experiment):
        super( ExternalScanMethod, self).__init__(experiment)
    
    def startScan(self):
        if self.experiment.scan.scanParameter not in self.experiment.scanTargetDict:
            message = "External Scan Parameter '{0}' is not enabled.".format(self.experiment.scan.scanParameter)
            logging.getLogger(__name__).error(message)
            raise ScanNotAvailableException(message) 
        if self.experiment.scan.scanMode==0:
            self.parameter = self.experiment.scanTargetDict[self.experiment.scan.scanParameter]
            self.parameter.saveValue(overwrite=False)
            self.index = 0                 
        self.experiment.progressUi.setStarting()
        QtCore.QTimer.singleShot(100,self.startBottomHalf)

    def startBottomHalf(self):
        logger = logging.getLogger(__name__)
        if self.experiment.progressUi.state == self.experiment.OpStates.starting:
            if self.experiment.scan.scanMode!=0 or self.parameter.setValue( self.experiment.scan.list[self.index]):
                """We are done adjusting"""
                self.experiment.pulserHardware.ppStart()
                self.experiment.currentIndex = 0
                self.experiment.timestampsNewRun = True
                logger.info( "elapsed time {0}".format( time.time()-self.experiment.startTime ) )
                logger.info( "Status -> Running" )
                self.experiment.progressUi.setRunning( max(len(self.experiment.scan.list),1) ) 
            else:
                QtCore.QTimer.singleShot(100,self.startBottomHalf)

    def onStop(self):
        self.experiment.progressUi.setStopping()
        self.stopBottomHalf()
                  
    def stopBottomHalf(self):
        logger = logging.getLogger(__name__)
        if self.experiment.progressUi.state==self.experiment.OpStates.stopping:
            if self.experiment.scan.scanMode==0 and not self.parameter.restoreValue():
                QtCore.QTimer.singleShot(100,self.stopBottomHalf)
            else:
                self.experiment.progressUi.setIdle()
                logger.info( "Status -> Idle" )
             
    def onData(self, data, queuesize ):
        if not self.parameter.useExternalValue():
            x = self.experiment.generator.xValue(self.index)
            self.dataMiddlePart(data, queuesize, x)
        else:
            self.parameter.asyncCurrentExternalValue( partial( self.experiment.dataMiddlePart, data, queuesize) )
            
    def prepareNextPoint(self):
        if self.index < len(self.experiment.scan.list):
            self.dataBottomHalf()
        
    def dataBottomHalf(self):
        logger = logging.getLogger(__name__)
        if self.experiment.progressUi.state == self.OpStates.running:
            if self.experiment.scan.scanMode!=0 or self.parameter.setValue( self.scan.list[self.index]):
                """We are done adjusting"""
                self.pulserHardware.ppStart()
                logger.info( "External Value: {0}".format(self.scan.list[self.externalParameterIndex]) )
            else:
                QtCore.QTimer.singleShot(100,self.dataBottomHalf)

   
class GlobalScanMethod(object):
    name = 'Global'
    def __init__(self):
        pass
    
class VoltageScanMethod(object):
    name = 'Voltage'
    def  __init(self):
        pass


ScanMethodsDict = { InternalScanMethod.name: InternalScanMethod,
                    ExternalScanMethod.name: ExternalScanMethod,
                    GlobalScanMethod.name: GlobalScanMethod,
                    VoltageScanMethod.name: VoltageScanMethod }