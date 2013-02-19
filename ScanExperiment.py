# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 17:25:13 2012

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore
import Trace
import random
import numpy
import pens
import Traceui
import PulserHardware
import struct
import MainWindowWidget
import FitUi
import ScanParameters
import sys, os
sys.path.append(os.path.abspath(r'modules'))
import enum
        
ScanExperimentForm, ScanExperimentBase = PyQt4.uic.loadUiType(r'ui\ScanExperiment.ui')

class Data:
    def __init__(self):
        self.count = [list()]*8
        self.timestamp = [list()]*8
        self.timestampZero = [0]*8
        self.scanvalue = None

class Worker(QtCore.QThread):
    dataAvailable = QtCore.pyqtSignal( 'PyQt_PyObject' )
    
    def __init__(self, pulserHardware, pulseProgramUi, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.exiting = False
        self.pulserHardware = pulserHardware
        self.pulseProgramUi = pulseProgramUi
        self.Mutex = QtCore.QMutex()          # the mutex is to protect the ok library
        self.activated = False
        self.running = False
        
    def __enter__(self):
        return self
        
    def __exit__(self, type, value, traceback):
        self.pulserHardware.ppStop()
        
    def onReload(self,scandata):
        self.stopScan()
        self.startScan()

    def startScan(self,scandata):
        with QtCore.QMutexLocker(self.Mutex):
            self.pulserHardware.ppUpload(self.pulseProgramUi.getPulseProgramBinary())
            self.pulserHardware.ppWriteData(scandata)
            print "Starting"
            self.pulserHardware.ppStart()
            self.running = True
            
    def stopScan(self):
        with QtCore.QMutexLocker(self.Mutex):
            if self.running:
                self.pulserHardware.ppStop()
                self.running = False

    def finish(self):
        with QtCore.QMutexLocker(self.Mutex):
            self.exiting = True

    analyzingState = enum.enum('normal','scanparameter')
    def run(self):
        """ run is responsible for reading the data back from the FPGA
        next experiment marker is 0xffff0xxx where xxx is the address of the overwritten parameter
        end marker is 0xffffffff
        """
        try:
            with self:
                state = self.analyzingState.normal
                self.data = Data()
                self.timestampOffset = 0
                while not self.exiting:
                    with QtCore.QMutexLocker(self.Mutex):
                        data = self.pulserHardware.ppReadData(4,1.0)
                    #print len(data)
                    for s in PulserHardware.sliceview(data,4):
                        (token,) = struct.unpack('I',s)
                        print hex(token)
                        if state == self.analyzingState.scanparameter:
                            if self.data.scanvalue is None:
                                self.data.scanvalue = token
                            else:
                                self.dataAvailable.emit( self.data )
                                print "emit"
                                self.data = Data()
                                self.data.scanvalue = token
                            state = self.analyzingState.normal
                        elif token & 0xff000000 == 0xff000000:
                            if token == 0xffffffff:    # end of run
                                #self.exiting = True
                                self.dataAvailable.emit( self.data )
                                print "emit"
                                self.data = Data()
                            elif token == 0xff000000:
                                self.timestampOffset += 1<<28
                            elif token & 0xffff0000 == 0xffff0000:  # new scan parameter
                                state = self.analyzingState.scanparameter
                        else:
                            key = token >> 28
                            channel = (token >>24) & 0xf
                            value = token & 0xffffff
                            if key==1:   # count
                                self.data.count[channel].append(value)
                            elif key==2:  # timestamp
                                self.data.timstampZero[channel] = self.timestampOffset + value
                                self.data.timestamp[channel].append(0)
                            elif key==3:
                                self.data.timestamp[channel].append(self.timestampOffset + value - self.data.timstampZero[channel])
                if self.data.scanvalue is not None:
                    self.dataAvailable.emit( self.data )
                self.data = Data()
            with QtCore.QMutexLocker(self.Mutex):
                self.pulserHardware.ppStop()
                print "PP Stopped"
        except Exception as err:
            print "Scan Experiment worker exception:", err
            


class ScanExperiment(ScanExperimentForm, MainWindowWidget.MainWindowWidget):
    StatusMessage = QtCore.pyqtSignal( str )
    ClearStatusMessage = QtCore.pyqtSignal()
    OpStates = enum.enum('idle','running','paused')

    def __init__(self,settings,parent=None):
        MainWindowWidget.MainWindowWidget.__init__(self,parent)
        ScanExperimentForm.__init__(self)
        self.deviceSettings = settings
        self.pulserHardware = PulserHardware.PulserHardware(self.deviceSettings.xem)
        self.currentTrace = None
        self.currentIndex = 0
        self.activated = False

    def setupUi(self,MainWindow,config):
        ScanExperimentForm.setupUi(self,MainWindow)
        self.config = config
        self.graphicsView = self.graphicsLayout.graphicsView
        self.penicons = pens.penicons().penicons()
        self.traceui = Traceui.Traceui(self.penicons)
        self.traceui.setupUi(self.traceui)
        self.dockWidget.setWidget( self.traceui )
        self.dockWidgetList.append(self.dockWidget)
        self.fitWidget = FitUi.FitUi(self.traceui)
        self.fitWidget.setupUi(self.fitWidget)
        self.dockWidgetFitUi.setWidget( self.fitWidget )
        self.dockWidgetList.append(self.dockWidgetFitUi )
        self.scanParametersWidget = ScanParameters.ScanParameters(config,"ScanExperiment")
        self.scanParametersWidget.setupUi(self.scanParametersWidget)
        self.scanParametersUi.setWidget(self.scanParametersWidget )
        self.dockWidgetList.append(self.scanParametersUi)
        if 'ScanExperiment.MainWindow.State' in self.config:
            QtGui.QMainWindow.restoreState(self,self.config['ScanExperiment.MainWindow.State'])

    def setPulseProgramUi(self,pulseProgramUi):
        self.pulseProgramUi = pulseProgramUi.addExperiment('Scan Sequence')
        self.scanParametersWidget.setVariables( self.pulseProgramUi.pulseProgram.variabledict )

    def onClear(self):
        self.dockWidget.setShown(True)
        self.StatusMessage.emit("test Clear not implemented")
    
    def onSave(self):
        self.StatusMessage.emit("test Save not implemented")
    
    def onStart(self):
        self.state = self.OpStates.running
        # get parameter to scan and scanrange
        self.scan = self.scanParametersWidget.getScan()
        self.scan.code = self.pulseProgramUi.pulseProgram.variableScanCode(self.scan.name, self.scan.list)
        self.worker.startScan(self.scan.code)
        self.currentIndex = 0
        self.currentTrace = None
    
    def onPause(self):
        self.StatusMessage.emit("test Pause not implemented")
    
    def onStop(self):
        self.worker.stopScan()
        
    def startData(self):
        """ Initialize necessary data structures
        """
        pass
    
    def onData(self, data ):
        """ Called by worker with new data
        """
        print "onData", len(data.count[0])
        mean = numpy.mean( data.count[0] )
        x = self.scan.list[self.currentIndex].ounit('ms').toval()
        if self.currentTrace is None:
            self.currentTrace = Trace.Trace()
            self.currentTrace.x = numpy.array([x])
            self.currentTrace.y = numpy.array([mean])
            self.currentTrace.name = self.scan.name
            self.currentTrace.vars.comment = ""
            self.plottedTrace = Traceui.PlottedTrace(self.currentTrace,self.graphicsView,pens.penList)
            self.traceui.addTrace(self.plottedTrace,pen=-1)
        else:
            self.currentTrace.x = numpy.append(self.currentTrace.x, x)
            self.currentTrace.y = numpy.append(self.currentTrace.y, mean)
            self.plottedTrace.replot()
        self.currentIndex += 1
            
        
    def activate(self):
        MainWindowWidget.MainWindowWidget.activate(self)
        if (self.deviceSettings is not None) and (not self.activated):
            try:
                print "Scan activated", self.activated
                self.startData()
                self.worker = Worker(self.pulserHardware,self.pulseProgramUi)
                self.worker.dataAvailable.connect(self.onData)
                self.worker.start()
                self.activated = True
            except Exception as ex:
                print ex
                self.StatusMessage.emit( ex.message )
    
    def deactivate(self):
        MainWindowWidget.MainWindowWidget.deactivate(self)
        if self.activated and hasattr( self, 'worker'):
            print "Scan deactivated"
            self.worker.finish()
            self.worker.wait()
            self.activated = False
            self.state = self.OpStates.idle
                
    def onClose(self):
        self.config['ScanExperiment.MainWindow.State'] = QtGui.QMainWindow.saveState(self)
        self.scanParametersWidget.onClose()

    def updateSettings(self,settings,active=False):
        """ Main program settings have changed
        """
        self.deviceSettings = settings
        if active:
            self.deactivate()
            self.pulserHardware = PulserHardware.PulserHardware(self.deviceSettings.xem)
            self.activate()
        