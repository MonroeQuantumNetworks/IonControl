# -*- coding: utf-8 -*-
"""
Created on Wed Apr 10 21:36:17 2013

@author: pmaunz
"""

import ScanExperiment 
import time

class NewExternalScanExperiment( ScanExperiment.ScanExperiment ):
    def onStart(self):
        start = time.time()
        self.state = self.OpStates.running
        self.scanSettings = self.scanSettingsWidget.settings
        # get parameter to scan and scanrange
        self.scan = self.scanParametersWidget.getScan()
        if self.scan.scanMode == self.scanParametersWidget.ScanModes.StepInPlace:
            self.scan.code = self.pulseProgramUi.pulseProgram.variableScanCode(self.scan.name, [self.scan.list[0]])
            mycode = self.pulseProgramUi.pulseProgram.variableScanCode(self.scan.name, [self.scan.list[0]]*2)
        else:
            self.scan.code = self.pulseProgramUi.pulseProgram.variableScanCode(self.scan.name, self.scan.list)
            mycode = self.scan.code
        self.pulserHardware.ppFlushData()
        self.pulserHardware.ppClearWriteFifo()
        self.pulserHardware.ppUpload(self.pulseProgramUi.getPulseProgramBinary())
        self.pulserHardware.ppWriteData(mycode)
        print "Starting"
        self.pulserHardware.ppStart()
        self.running = True
        self.currentIndex = 0
        if self.currentTrace is not None:
            self.currentTrace.header = self.pulseProgramUi.pulseProgram.currentVariablesText("#")
            if self.scan.autoSave:
                self.currentTrace.resave()
            self.currentTrace = None
        self.scanParametersWidget.progressBar.setRange(0,len(self.scan.list))
        self.scanParametersWidget.progressBar.setValue(0)
        self.scanParametersWidget.progressBar.setVisible( True )
        self.timestampsNewRun = True
        print "elapsed time", time.time()-start
    
    def onStop(self):
        if self.running:
            self.pulserHardware.ppStop()
            self.pulserHardware.ppClearWriteFifo()
            self.pulserHardware.ppFlushData()
            self.running = False
            if self.scan.rewriteDDS:
                self.NeedsDDSRewrite.emit()
        self.scanParametersWidget.progressBar.setVisible( False )
    
    def onData(self, data ):
        """ Called by worker with new data
        """
        print "onData", len(data.count[self.scanSettings.counter]), data.scanvalue
        mean, error = self.scanSettings.evalAlgo.evaluate( data.count[self.scanSettings.counter] )
        #mean = numpy.mean( data.count[self.scanSettings.counter] )
        if self.scan.scanMode == self.scanParametersWidget.ScanModes.StepInPlace:
            x = self.currentIndex
        else:
            x = self.scan.list[self.currentIndex].ounit(self.scan.start.out_unit).toval()
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
        self.currentIndex += 1
        self.showHistogram(data)
        if self.timestampSettingsWidget.settings.enable: 
            self.showTimestamps(data)
        if data.final:
            self.finalizeData()
        else:
            if self.scan.scanMode == self.scanParametersWidget.ScanModes.StepInPlace:
                self.pulserHardware.ppWriteData(self.scan.code)     
        self.scanParametersWidget.progressBar.setValue(self.currentIndex)
