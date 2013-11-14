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

class ExternalScanExperiment( ScanExperiment.ScanExperiment ):
    def __init__(self,settings,pulserHardware,experimentName,parent=None):
        super(ExternalScanExperiment,self).__init__(settings,pulserHardware,experimentName,parent)
        self.state = self.OpStates.idle      
        
    def setupUi(self,MainWindow,config):
        super(ExternalScanExperiment,self).setupUi(MainWindow,config)
        self.scanControlWidget.setScanNames(ExternalScannedParameters.ExternalScannedParameters.keys())
               
    def updateEnabledParameters(self, enabledParameters ):
        self.enabledParameters = enabledParameters
        
    def startScan(self):
        if self.state in [self.OpStates.idle, self.OpStates.stopping, self.OpStates.running]:
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
            self.state = self.OpStates.starting
            self.plottedTrace = None #reset plotted trace
            if self.plottedTraceList:
                for plottedTrace in self.plottedTraceList:
                    plottedTrace.plot(0) #unplot previous trace
            self.plottedTraceList = list() #reset plotted trace
           
    def startBottomHalf(self):
        if self.state == self.OpStates.starting:
            if self.externalParameter.setValue( self.scan.list[self.externalParameterIndex]):
                """We are done adjusting"""
                self.pulserHardware.ppStart()
                self.currentIndex = 0
                self.updateProgressBar(0,max(len(self.scan.list),1))
                self.timestampsNewRun = True
                print "elapsed time", time.time()-self.startTime
                self.state = self.OpStates.running
                print "Status -> Running"
                self.updateProgressBar(self.currentIndex+1,max(len(self.scan.list),1))
            else:
                QtCore.QTimer.singleShot(100,self.startBottomHalf)

    def onStop(self):
        print "Old Status", self.state
        if self.state in [self.OpStates.starting, self.OpStates.running]:
            ScanExperiment.ScanExperiment.onStop(self)
            self.state = self.OpStates.stopping
            print "Status -> Stopping"
            self.stopBottomHalf()
            self.finalizeData(reason='stopped')
            self.updateProgressBar(self.currentIndex+1,max(len(self.scan.list),1))

                    
    def stopBottomHalf(self):
        if self.state==self.OpStates.stopping:
            if not self.externalParameter.restoreValue():
                QtCore.QTimer.singleShot(100,self.stopBottomHalf)
            else:
                self.state = self.OpStates.idle
                self.updateProgressBar(0,max(len(self.scan.list),1))
                print "Status -> Idle"

    def onData(self, data ):
        """ Called by worker with new data
        """

        if data.overrun:
            print "Read Pipe Overrun"
            self.onPause()
        else:
            print "NewExternalScan onData", len(data.count[self.scan.counterChannel]), data.scanvalue
            x = self.generator.xValue(self.externalParameterIndex)
            evaluated = list()
            for eval, algo in zip(self.scan.evalList,self.scan.evalAlgorithmList):
                if data.count[eval.counter]:
                    evaluated.append( (algo.evaluate( data.count[eval.counter]),algo.settings['errorBars'] ) ) # returns mean, error, raw
                else:
                    print "No data for counter {0}, ignoring it.".format(eval.counter)
            if len(evaluated)>0:
                self.displayUi.add( evaluated[0][0][0] )
                self.updateMainGraph(x, evaluated )
                self.showHistogram(data, self.scan.evalList[0].counter )
            self.currentIndex += 1
            self.externalParameterIndex += 1
            if self.scan.enableTimestamps: 
                self.showTimestamps(data)
            if self.externalParameterIndex<len(self.scan.list) and self.state==self.OpStates.running:
                self.externalParameter.setValue( self.scan.list[self.externalParameterIndex])
                self.pulserHardware.ppStart()
                print "External Value:" , self.scan.list[self.externalParameterIndex]
            else:
                self.finalizeData(reason='end of scan')
                if self.externalParameterIndex >= len(self.scan.list):
                    self.generator.dataOnFinal(self)
            self.updateProgressBar(self.externalParameterIndex+1,max(len(self.scan.list),1))

