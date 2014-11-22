'''
Created on Nov 6, 2014

@author: pmaunz
'''
import logging
import time
from PyQt4 import QtCore

from _functools import partial

class ScanException(Exception):
    pass

class ScanNotAvailableException(Exception):
    pass

class InternalScanMethod(object):
    name = 'Internal'
    def __init__(self, experiment):
        self.experiment = experiment
        self.maxUpdatesToWrite = None
    
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
        
    def prepareNextPoint(self, data):
        if data.final:
            self.experiment.finalizeData(reason='end of scan')
            logging.getLogger(__name__).info( "current index {0} expected {1}".format(self.experiment.currentIndex, len(self.experiment.scan.list) ) )
            if self.experiment.currentIndex >= len(self.experiment.scan.list):    # if all points were taken
                self.experiment.generator.dataOnFinal(self, self.experiment.progressUi.state )
            else:
                self.experiment.onInterrupt( self.experiment.pulseProgramUi.exitcode(data.exitcode) )
        else:
            mycode = self.experiment.generator.dataNextCode(self )
            if mycode:
                self.experiment.pulserHardware.ppWriteData(mycode)
            self.experiment.progressUi.onData( self.experiment.currentIndex )  
   
class ExternalScanMethod(InternalScanMethod):
    name = 'External'
    def __init__(self, experiment):
        super( ExternalScanMethod, self).__init__(experiment)
        self.maxUpdatesToWrite = 1
        self.parameter = None
    
    def startScan(self):
        if self.experiment.scan.scanParameter not in self.experiment.scanTargetDict[self.experiment.scan.scanTarget]:
            message = "External Scan Parameter '{0}' is not enabled.".format(self.experiment.scan.scanParameter)
            logging.getLogger(__name__).error(message)
            raise ScanNotAvailableException(message) 
        if self.experiment.scan.scanMode==0:
            self.parameter = self.experiment.scanTargetDict['External'][self.experiment.scan.scanParameter]
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
            if self.experiment.scan.scanMode==0 and self.parameter and not self.parameter.restoreValue():
                QtCore.QTimer.singleShot(100,self.stopBottomHalf)
            else:
                self.experiment.progressUi.setIdle()
                logger.info( "Status -> Idle" )
             
    def onData(self, data, queuesize, x ):
        if not self.parameter.useExternalValue():
            x = self.experiment.generator.xValue(self.index)
            self.experiment.dataMiddlePart(data, queuesize, x)
        else:
            self.parameter.asyncCurrentExternalValue( partial( self.experiment.dataMiddlePart, data, queuesize) )
            
    def prepareNextPoint(self, data):
        self.index += 1
        if self.experiment.progressUi.state == self.experiment.OpStates.running:
            if data.final and data.exitcode not in [0,0xffff]:
                self.experiment.onInterrupt( self.experiment.pulseProgramUi.exitcode(data.exitcode) )
            elif self.index < len(self.experiment.scan.list):
                mycode = self.experiment.generator.dataNextCode(self )
                if mycode:
                    self.experiment.pulserHardware.ppWriteData(mycode)
                self.dataBottomHalf()
                self.experiment.progressUi.onData( self.index )  
            else:
                self.experiment.finalizeData(reason='end of scan')
                self.experiment.generator.dataOnFinal(self.experiment, self.experiment.progressUi.state )
                logging.getLogger(__name__).info("Scan Completed")               

        
    def dataBottomHalf(self):
        logger = logging.getLogger(__name__)
        if self.experiment.progressUi.state == self.experiment.OpStates.running:
            if self.experiment.scan.scanMode!=0 or self.parameter.setValue( self.experiment.scan.list[self.index]):
                """We are done adjusting"""
                self.experiment.pulserHardware.ppStart()
                logger.info( "External Value: {0}".format(self.experiment.scan.list[self.index]) )
            else:
                QtCore.QTimer.singleShot(100,self.dataBottomHalf)

   
class GlobalScanMethod(ExternalScanMethod):
    name = 'Global'
    def __init__(self, experiment):
        super( GlobalScanMethod, self).__init__(experiment)
    
class VoltageScanMethod(object):
    name = 'Voltage'
    def  __init(self):
        pass


ScanMethodsDict = { InternalScanMethod.name: InternalScanMethod,
                    ExternalScanMethod.name: ExternalScanMethod,
                    GlobalScanMethod.name: GlobalScanMethod,
                    VoltageScanMethod.name: VoltageScanMethod }