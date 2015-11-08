'''
Created on Nov 6, 2014

@author: pmaunz
'''
import logging
import time
from PyQt4 import QtCore

from functools import partial

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
        self.experiment.progressUi.setRunning( max(len(self.experiment.context.scan.list),1) if self.experiment.context.scan.list is not None else 100)
        logger.info( "Starting" )
        self.experiment.pulserHardware.ppStart()
        self.experiment.context.currentIndex = 0
        logger.info( "elapsed time {0}".format( time.time()-self.experiment.context.startTime ) )

    def onStop(self):
        self.experiment.progressUi.setIdle()            

    def onData(self, data, queuesize, x ):
        self.experiment.dataMiddlePart( data, queuesize, x )
        
    def prepareNextPoint(self, data):
        if data.final:
            self.experiment.finalizeData(reason='end of scan')
            if self.experiment.context.scan.list is None:
                self.experiment.conetxt.generator.dataOnFinal(self.experiment, self.experiment.progressUi.state )
            elif self.experiment.context.currentIndex >= len(self.experiment.context.scan.list):    # if all points were taken
                logging.getLogger(__name__).info( "current index {0} expected {1}".format(self.experiment.context.currentIndex, len(self.experiment.context.scan.list) ) )
                self.experiment.context.generator.dataOnFinal(self.experiment, self.experiment.progressUi.state )
            else:
                logging.getLogger(__name__).error( "current index {0} expected {1}".format(self.experiment.context.currentIndex, len(self.experiment.context.scan.list) ) )
                self.experiment.onInterrupt( self.experiment.pulseProgramUi.exitcode(data.exitcode) )
        else:
            mycode = self.experiment.context.generator.dataNextCode(self )
            if mycode:
                self.experiment.pulserHardware.ppWriteData(mycode)
            self.experiment.progressUi.onData( self.experiment.context.currentIndex )
   
class ExternalScanMethod(InternalScanMethod):
    name = 'External'
    def __init__(self, experiment):
        """ Initialize with a given experiment.
        experiment :: ScanExperiment
        """
        super( ExternalScanMethod, self).__init__(experiment)
        self.maxUpdatesToWrite = 1
        self.parameter = None
    
    def startScan(self):
        if self.experiment.context.scan.scanParameter not in self.experiment.scanTargetDict[self.experiment.context.scan.scanTarget]:
            message = "{0} Scan Parameter '{1}' is not enabled.".format(self.name,self.experiment.context.scan.scanParameter)
            logging.getLogger(__name__).warning(message)
            raise ScanNotAvailableException(message) 
        if self.experiment.context.scan.scanMode==0:
            self.parameter = self.experiment.scanTargetDict[self.name][self.experiment.context.scan.scanParameter]
            self.parameter.saveValue(overwrite=False)
            self.index = 0                 
        self.experiment.progressUi.setStarting()
        QtCore.QTimer.singleShot(100,self.startBottomHalf)

    def startBottomHalf(self):
        logger = logging.getLogger(__name__)
        if self.experiment.progressUi.is_starting:
            if self.experiment.context.scan.scanMode!=0 or self.parameter.setValue( self.experiment.context.scan.list[self.index]):
                """We are done adjusting"""
                self.experiment.pulserHardware.ppStart()
                self.experiment.context.currentIndex = 0
                self.experiment.context.timestampsNewRun = True
                logger.info( "elapsed time {0}".format( time.time()-self.experiment.context.startTime ) )
                logger.info( "Status -> Running" )
                self.experiment.progressUi.setRunning( max(len(self.experiment.context.scan.list),1) )
            else:
                QtCore.QTimer.singleShot(100,self.startBottomHalf)

    def onStop(self):
        self.experiment.progressUi.setStopping()
        self.stopBottomHalf()
                  
    def stopBottomHalf(self):
        logger = logging.getLogger(__name__)
        if self.experiment.progressUi.is_stopping:
            if self.experiment.context.scan.scanMode==0 and self.parameter and not self.parameter.restoreValue():
                QtCore.QTimer.singleShot(100,self.stopBottomHalf)
            else:
                self.experiment.progressUi.setIdle()
                logger.info( "Status -> Idle" )
             
    def onData(self, data, queuesize, x ):
        if not self.parameter.useExternalValue:
            x = self.experiment.context.generator.xValue(self.index, data)
            self.experiment.dataMiddlePart(data, queuesize, x)
        else:
            self.parameter.asyncCurrentExternalValue( partial( self.experiment.dataMiddlePart, data, queuesize) )
            
    def prepareNextPoint(self, data):
        self.index += 1
        if self.experiment.progressUi.is_running:
            if data.final and data.exitcode not in [0,0xffff]:
                self.experiment.onInterrupt( self.experiment.pulseProgramUi.exitcode(data.exitcode) )
            elif self.index < len(self.experiment.context.scan.list):
                mycode = self.experiment.context.generator.dataNextCode(self )
                if mycode:
                    self.experiment.pulserHardware.ppWriteData(mycode)
                self.dataBottomHalf()
                self.experiment.progressUi.onData( self.index )  
            else:
                self.experiment.finalizeData(reason='end of scan')
                self.experiment.context.generator.dataOnFinal(self.experiment, self.experiment.progressUi.state )
                logging.getLogger(__name__).info("Scan Completed")               

        
    def dataBottomHalf(self):
        logger = logging.getLogger(__name__)
        if self.experiment.progressUi.is_running:
            if self.experiment.context.scan.scanMode!=0 or self.parameter.setValue( self.experiment.context.scan.list[self.index]):
                """We are done adjusting"""
                self.experiment.pulserHardware.ppStart()
                logger.info( "{0} Value: {1}".format(self.name, self.experiment.context.scan.list[self.index]) )
            else:
                QtCore.QTimer.singleShot(100,self.dataBottomHalf)
   
class AWGScanMethod(ExternalScanMethod):
    name = 'AWG'
    def __init__(self, experiment):
        super( AWGScanMethod, self).__init__(experiment)
   
class GlobalScanMethod(ExternalScanMethod):
    name = 'Global'
    def __init__(self, experiment):
        super( GlobalScanMethod, self).__init__(experiment)
    
class VoltageScanMethod(ExternalScanMethod):
    name = 'Voltage'
    def __init__(self, experiment):
        super( VoltageScanMethod, self).__init__(experiment)

class VoltageLocalAdjustScanMethod(ExternalScanMethod):
    name = 'Voltage Local Adjust'
    def __init__(self, experiment):
        super( VoltageLocalAdjustScanMethod, self).__init__(experiment)


ScanMethodsDict = { InternalScanMethod.name: InternalScanMethod,
                    AWGScanMethod.name: AWGScanMethod,
                    ExternalScanMethod.name: ExternalScanMethod,
                    GlobalScanMethod.name: GlobalScanMethod,
                    VoltageScanMethod.name: VoltageScanMethod,
                    VoltageLocalAdjustScanMethod.name: VoltageLocalAdjustScanMethod }
