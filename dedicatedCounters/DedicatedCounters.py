# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz

DedicatedCounters reads and displays the counts from the simple counters and ADCs.

"""
from PyQt4 import QtCore, QtGui
import PyQt4.uic
import numpy
import logging

from dedicatedCounters import AutoLoad
from dedicatedCounters import DedicatedCountersSettings
from dedicatedCounters import DedicatedDisplay
from dedicatedCounters import InputCalibrationUi
from modules import enum
from trace.Trace import Trace, TracePlotting
from modules.DataDirectory import DataDirectory
from trace.pens import penList
 
DedicatedCountersForm, DedicatedCountersBase = PyQt4.uic.loadUiType(r'ui\DedicatedCounters.ui')

#curvecolors = [ 'b', 'g', 'r', 'b', 'c', 'm', 'y', 'g' ]

class Settings:
    pass

class DedicatedCounters(DedicatedCountersForm,DedicatedCountersBase ):
    dataAvailable = QtCore.pyqtSignal( object )
    OpStates = enum.enum('idle','running','paused')
    def __init__(self,config,dbConnection,pulserHardware,globalVariablesUi,externalInstrumentObservable, parent=None):
        DedicatedCountersForm.__init__(self)
        DedicatedCountersBase.__init__(self,parent)
        self.dataSlotConnected = False
        self.config = config
        self.settings = self.config.get('DedicatedCounter.Settings',Settings())
        self.pulserHardware = pulserHardware
        self.state = self.OpStates.idle
        self.xData = [numpy.array([])]*8
        self.yData = [numpy.array([])]*8
        self.integrationTime = 0
        self.integrationTimeLookup = dict()
        self.tick = 0
        self.analogCalbrations = None
        self.globalVariablesUi = globalVariablesUi
        self.externalInstrumentObservable = externalInstrumentObservable
        self.dbConnection = dbConnection
#        [
#            AnalogInputCalibration.PowerDetectorCalibration(),
#            AnalogInputCalibration.PowerDetectorCalibrationTwo(),
#            AnalogInputCalibration.AnalogInputCalibration(),
#            AnalogInputCalibration.AnalogInputCalibration() ]

    def setupUi(self, parent):
        DedicatedCountersForm.setupUi(self,parent)
        self.actionSave.triggered.connect( self.onSave )
        self.actionClear.triggered.connect( self.onClear )
        self.actionStart.triggered.connect( self.onStart )
        self.actionStop.triggered.connect( self.onStop )
        self.settingsUi = DedicatedCountersSettings.DedicatedCountersSettings(self.config)
        self.settingsUi.setupUi(self.settingsUi)
        self.settingsDock.setWidget( self.settingsUi )
        self.settingsUi.valueChanged.connect( self.onSettingsChanged )
        self.settings = self.settingsUi.settings
        # Input Calibrations        
        self.calibrationUi = InputCalibrationUi.InputCalibrationUi(self.config,4)
        self.calibrationUi.setupUi(self.calibrationUi)
        self.calibrationDock = QtGui.QDockWidget("Input Calibration")
        self.calibrationDock.setObjectName("Input Calibration")
        self.calibrationDock.setWidget( self.calibrationUi )
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea , self.calibrationDock)
        self.analogCalbrations = self.calibrationUi.calibrations
        # Display Channels 0-3
        self.displayUi = DedicatedDisplay.DedicatedDisplay(self.config,"Channel 0-3")
        self.displayUi.setupUi(self.displayUi)
        self.displayDock = QtGui.QDockWidget("Channel 0-3")
        self.displayDock.setObjectName("Channel 0-3")
        self.displayDock.setWidget( self.displayUi )
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea , self.displayDock)
        # Display Channel 4-7
        self.displayUi2 = DedicatedDisplay.DedicatedDisplay(self.config,"Channel 4-7")
        self.displayUi2.setupUi(self.displayUi2)
        self.displayDock2 = QtGui.QDockWidget("Channel 4-7")
        self.displayDock2.setObjectName("Channel 4-7")
        self.displayDock2.setWidget(self.displayUi2)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea , self.displayDock2)
        # Display ADC 0-3
        self.displayUiADC = DedicatedDisplay.DedicatedDisplay(self.config,"Analog Channels")
        self.displayUiADC.setupUi(self.displayUiADC)
        self.displayDockADC = QtGui.QDockWidget("Analog Channels")
        self.displayDockADC.setObjectName("Analog Channels")
        self.displayDockADC.setWidget(self.displayUiADC)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea , self.displayDockADC)
        # Arrange the dock widgets
        self.tabifyDockWidget( self.displayDockADC, self.displayDock2)
        self.tabifyDockWidget( self.displayDock2, self.displayDock )
        self.tabifyDockWidget( self.calibrationDock, self.settingsDock )
        self.calibrationDock.hide()        
        # AutoLoad
        self.autoLoad = AutoLoad.AutoLoad(self.config, self.dbConnection, self.pulserHardware, self.dataAvailable, self.globalVariablesUi, self.externalInstrumentObservable)
        self.autoLoad.setupUi(self.autoLoad)
        self.autoLoadDock = QtGui.QDockWidget("Auto Loader")
        self.autoLoadDock.setObjectName("Auto Loader")
        self.autoLoadDock.setWidget( self.autoLoad )
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.autoLoadDock)
        
        self.curves = [None]*8
        self._graphicsView = self.graphicsLayout._graphicsView
        if 'DedicatedCounter.MainWindow.State' in self.config:
            QtGui.QMainWindow.restoreState(self,self.config['DedicatedCounter.MainWindow.State'])
        self.onSettingsChanged()
                
    def onSettingsChanged(self):
        self.integrationTimeLookup[ self.pulserHardware.getIntegrationTimeBinary(self.settings.integrationTime) & 0xffffff] = self.settings.integrationTime
        self.pulserHardware.integrationTime = self.settings.integrationTime
        self.settings = self.settingsUi.settings
        if self.state==self.OpStates.running:
            self.pulserHardware.counterMask = self.settings.counterMask
            self.pulserHardware.adcMask = self.settings.adcMask
        for index in range(8): 
            show = self.settings.counterMask & (1<<index)
            if  show and self.curves[index] is None:
                self.curves[index] = self._graphicsView.plot(pen=penList[index+1][0])
            elif (not show) and (self.curves[index] is not None):
                self._graphicsView.removeItem( self.curves[index] )
                self.curves[index] = None
                
    def saveConfig(self):
        self.config['DedicatedCounter.pos'] = self.pos()
        self.config['DedicatedCounter.size'] = self.size()
        self.config['DedicatedCounter.Settings'] = self.settings
        self.config['DedicatedCounter.MainWindow.State'] = QtGui.QMainWindow.saveState(self)
        self.autoLoad.saveConfig()
        self.calibrationUi.saveConfig()
        self.settingsUi.saveConfig()

    def onClose(self):
        self.autoLoad.onClose()

    def closeEvent(self,e):
        self.onClose()
        
    def reject(self):
        self.config['DedicatedCounter.pos'] = self.pos()
        self.config['DedicatedCounter.size'] = self.size()
        self.pulserHardware.dedicatedDataAvailable.disconnect( self.onData )
        self.hide()
        
    def show(self):
        if 'DedicatedCounter.pos' in self.config:
            self.move(self.config['DedicatedCounter.pos'])
        if 'DedicatedCounter.size' in self.config:
            self.resize(self.config['DedicatedCounter.size'])
        super(DedicatedCounters,self).show()
        if not self.dataSlotConnected:
            self.pulserHardware.dedicatedDataAvailable.connect( self.onData )
            self.dataSlotConnected = True
        
    def onStart(self):
        self.pulserHardware.counterMask = self.settings.counterMask
        self.pulserHardware.adcMask = self.settings.adcMask
        self.state = self.OpStates.running

    def onStop(self):
        self.pulserHardware.counterMask = 0
        self.pulserHardware.adcMask = 0
        self.state = self.OpStates.idle
                
    def onSave(self):
        logger = logging.getLogger(__name__)
        for counter in range(8):
            if len(self.xData[counter])>0 and len(self.yData[counter])>0:
                trace = Trace()
                trace.x = self.xData[counter]
                trace.y = self.yData[counter]
                trace.description["counter"] = counter
                filename, _ = DataDirectory().sequencefile("DedicatedCounter_{0}.txt".format(counter))
                trace.addTracePlotting( TracePlotting(name="Counter {0}".format(counter)) )
                trace.saveTrace(filename)
        logger.info("saving dedicated counters")
    
    def onClear(self):
        self.xData = [numpy.array([])]*8
        self.yData = [numpy.array([])]*8
        self.tick = 0        
    
    def onData(self, data):
        self.tick += 1
        self.displayUi.values = data.data[0:4]
        self.displayUi2.values = data.data[4:8]
        self.displayUiADC.values = self.convertAnalog(data.data[8:12])
        data.analogValues = self.displayUiADC.values
        if data.data[12] is not None and data.data[12] in self.integrationTimeLookup:
            self.dataIntegrationTime = self.integrationTimeLookup[ data.data[12] ]
        else:
            self.dataIntegrationTime = self.settings.integrationTime
        data.integrationTime = self.dataIntegrationTime 
        for counter in range(8):
            if data.data[counter] is not None:
                y = self.settings.displayUnit.convert(data.data[counter],self.dataIntegrationTime.ounit('ms').toval())
                Start = max( 1+len(self.xData[counter])-self.settings.pointsToKeep, 0)
                self.yData[counter] = numpy.append(self.yData[counter][Start:], y)
                self.xData[counter] = numpy.append(self.xData[counter][Start:], self.tick )
                if self.curves[counter] is not None:
                    self.curves[counter].setData(self.xData[counter],self.yData[counter])
        self.dataAvailable.emit(data)
 
    def convertAnalog(self,data):
        converted = list()
        for channel, cal in enumerate(self.analogCalbrations):
            converted.append( cal.convertMagnitude(data[channel]) )
        return converted
    