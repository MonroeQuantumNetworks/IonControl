# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtCore
from modules import enum
import magnitude
import DedicatedCountersSettings
import numpy
import DedicatedDisplay
       
DedicatedCountersForm, DedicatedCountersBase = PyQt4.uic.loadUiType(r'ui\DedicatedCounters.ui')

curvecolors = [ 'b', 'g', 'r', 'b', 'c', 'm', 'y', 'g' ]

class Settings:
    pass

class DedicatedCounters(DedicatedCountersForm,DedicatedCountersBase ):
    OpStates = enum.enum('idle','running','paused')
    def __init__(self,config,pulserHardware,parent=0):
        DedicatedCountersForm.__init__(self,parent)
        DedicatedCountersBase.__init__(self)
        self.config = config
        self.settings = self.config.get('DedicatedCounter.Settings',Settings())
        self.pulserHardware = pulserHardware
        self.state = self.OpStates.idle
        self.xData = [numpy.array([])]*8
        self.yData = [numpy.array([])]*8
        self.integrationTime = 0
        self.integrationTimeLookup = dict()
        self.tick = 0

    def setupUi(self, parent):
        DedicatedCountersForm.setupUi(self,parent)
        self.actionSave.triggered.connect( self.onSave )
        self.actionClear.triggered.connect( self.onClear )
        self.actionPause.triggered.connect( self.onPause )
        self.actionStart.triggered.connect( self.onStart )
        self.actionStop.triggered.connect( self.onStop )
        self.settingsUi = DedicatedCountersSettings.DedicatedCountersSettings(self.config)
        self.settingsUi.setupUi(self.settingsUi)
        self.settingsDock.setWidget( self.settingsUi )
        self.settingsUi.valueChanged.connect( self.onSettingsChanged )
        self.settings = self.settingsUi.settings
        self.displayUi = DedicatedDisplay.DedicatedDisplay(self.config)
        self.displayUi.setupUi(self.displayUi)
        self.displayDock.setWidget( self.displayUi )
        self.curves = [None]*8
        self.graphicsView = self.graphicsLayout.graphicsView
        
    def onSettingsChanged(self):
        self.pulserHardware.integrationTime = self.settings.integrationTime
        self.integrationTimeLookup[ self.pulserHardware.integrationTimeBinary & 0xffffff] = self.settings.integrationTime
        self.settings = self.settingsUi.settings
        if self.state==self.OpStates.running:
            self.pulserHardware.counterMask = self.settings.counterMask
            self.pulserHardware.adcMask = self.settings.adcMask
        for index in range(8): 
            show = self.settings.counterMask & (1<<index)
            if  show and self.curves[index] is None:
                self.curves[index] = self.graphicsView.plot(pen=curvecolors[index])
            elif (not show) and (self.curves[index] is not None):
                self.graphicsView.removeItem( self.curves[index] )
                self.curves[index] = None
                
    def onClose(self):
        self.config['DedicatedCounter.Settings'] = self.settings            
        
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
        self.pulserHardware.dedicatedDataAvailable.connect( self.onData )
        
    def onStart(self):
        self.pulserHardware.counterMask = self.settings.counterMask
        self.pulserHardware.adcMask = self.settings.adcMask
        self.state = self.OpStates.running

    def onStop(self):
        self.pulserHardware.counterMask = 0
        self.pulserHardware.adcMask = 0
        self.state = self.OpStates.idle
                
    def onSave(self):
        pass
    
    def onClear(self):
        self.xData = [numpy.array([])]*8
        self.yData = [numpy.array([])]*8
        self.tick = 0        
    
    def onPause(self):
        if self.state in [self.OpStates.running, self.OpStates.paused]:
            self.state = self.OpStates.paused if self.actionPause.isChecked() else self.OpStates.running
        
    def onData(self, data):
        self.tick += 1
        self.displayUi.values = data.data
        if data.data[12] is not None:
            self.dataIntegrationTime = self.integrationTimeLookup[ data.data[12] ]
        for counter in range(8):
            if data.data[counter] is not None:
                y = self.settings.displayUnit.convert(data.data[counter],self.dataIntegrationTime.ounit('ms').toval()) 
                Start = max( 1+len(self.xData[counter])-self.settings.pointsToKeep, 0)
                self.yData[counter] = numpy.append(self.yData[counter][Start:], y)
                self.xData[counter] = numpy.append(self.xData[counter][Start:], self.tick )
                if self.curves[counter] is not None:
                    self.curves[counter].setData(self.xData[counter],self.yData[counter])
 