# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 17:25:13 2012

@author: pmaunz
"""

import sys
import os.path
sys.path.append(os.path.abspath(r'modules'))
import PyQt4.uic
from PyQt4 import QtGui, QtCore
import Trace
import Traceui
import pens
import numpy
import timestamper
import struct
import enum
import DataDirectory
from MainWindowWidget import MainWindowWidget

class TDCTrace(Trace.Trace):
    def __init__(self):
        Trace.Trace.__init__(self)
        
    def saveTrace(self,filename):
        of = open(filename,'w')
        self.saveTraceHeader(of)
        print >>of, "# histogram data: time [ms] counts"
        for x,y in zip(self.x, self.y):
            print >>of, x, y
        of.close()

        
TDCWidgetForm, TDCWidgetBase = PyQt4.uic.loadUiType(r'ui\TDCWidget.ui')

class TDCWidget(TDCWidgetForm, MainWindowWidget):
    StatusMessage = QtCore.pyqtSignal( str )
    ClearStatusMessage = QtCore.pyqtSignal()
    OpStates = enum.enum('idle','running','paused')

    def __init__(self,parent=None):
        MainWindowWidget.__init__(self,parent)
        TDCWidgetForm.__init__(self)
        self.dockWidgets = list()
        self.state = self.OpStates.idle
        self.activated = False
        
    def addDockWidget(self, Area, Widget ):
        QtGui.QMainWindow.addDockWidget(self, Area, Widget)
        self.dockWidgets.append(Widget)
        
    def setupUi(self, Form, config ):
        self.config = config
        TDCWidgetForm.setupUi(self, Form)
        self.penicons = pens.penicons().penicons()
        self.traceui = Traceui.Traceui(self.penicons)
        self.traceui.setupUi(self.traceui)
        self.dockWidget.setWidget( self.traceui )
        if 'TDCWidget.MainWindow.State' in self.config:
            QtGui.QMainWindow.restoreState(self,self.config['TDCWidget.MainWindow.State'])
        
        self.channel = self.config.get('TDCWidget.channel',0)
        self.channel_edit.setValue(self.channel)
        self.channel_edit.valueChanged.connect(self.on_update)

        self.trigger = self.config.get('TDCWidget.trigger',4)
        self.trigger_edit.setValue(self.trigger)
        self.trigger_edit.valueChanged.connect(self.on_update)

        self.roi_start = self.config.get('TDCWidget.roi_start',-2)
        self.roi_start_edit.setValue(self.roi_start)
        self.roi_start_edit.valueChanged.connect(self.on_update)

        self.roi_stop = self.config.get('TDCWidget.roi_stop',2)
        self.roi_stop_edit.setValue(self.roi_stop)
        self.roi_stop_edit.valueChanged.connect(self.on_update)

        self.binwidth = self.config.get('TDCWidget.binwidth',0.01)
        self.binwidth_edit.setValue(self.binwidth)
        self.binwidth_edit.valueChanged.connect(self.on_update)

        self.filename = str(self.config.get('TDCWidget.filename',"tdc"))
        self.filename_edit.setText("{0:s}".format(self.filename))
        self.filename_edit.editingFinished.connect(self.on_update)  

        self.project = str(self.config.get('TDCWidget.project',"tdc"))
        self.project_edit.setText("{0:s}".format(self.project))
        self.project_edit.editingFinished.connect(self.on_update)  
              
        self.ontime = self.config.get('TDCWidget.ontime',1000.)
        self.ontime_edit.setValue(self.ontime)

        self.offtime = self.config.get('TDCWidget.offtime',1000.)
        self.offtime_edit.setValue(self.offtime)
        
        self.sequence_enable = False
        self.sequence_enable_box.stateChanged.connect( self.on_sequence_enable )
         
        self.sequenceUpdateButton.clicked.connect(self.on_sequence_update )        
        self.deviceSerial = self.config.get('TDCWidget.deviceSerial')
        
        self.dockWidgetList.extend( [ self.SequenceGeneratorWidget, self.dockWidget ] )
        self.refreshInterval = self.config.get('TDCWidget.refreshInterval',1000)
        self.doubleSpinBoxRefresh.setValue(self.refreshInterval )
        self.doubleSpinBoxRefresh.valueChanged.connect(self.onrefreshInterval)
        
    def onrefreshInterval(self):
        self.refreshInterval = self.doubleSpinBoxRefresh.value()
        if self.activated:
            self.timer.setInterval(self.refreshInterval)
        
    def updateSettings(self,settings,active=False):
        if settings.deviceSerial != self.deviceSerial:
            if self.state > self.OpStates.idle:
                self.onStop()
            self.deviceSerial = settings.deviceSerial
        
    def onClear(self):
        self.StatusMessage.emit("TDC Clear not implemented")
    
    def onSave(self):
        self.StatusMessage.emit("TDC Save not implemented")
    
    def onPause(self):
        self.StatusMessage.emit("TDC Pause not implemented")
    
    def activate(self):
        if self.deviceSerial is not None:
            self.StatusMessage.emit("TDC active")
            self.ts = timestamper.timestamper(self.channel,self.trigger,self.binwidth,self.roi_start,self.roi_stop,filename=self.filename+".bin",FPGASerial=self.deviceSerial)
            self.xData = numpy.copy( self.ts.readXValues() )
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.onDataUpdate)
            self.timer.start(2000)
            self.currentTrace = Traceui.PlottedTrace(TDCTrace(),self.graphicsView,pens.penList)
            self.activated = True
        else:
            print "No Instrument selected"
            self.activated = False
        MainWindowWidget.activate(self)
        
    def deactivate(self):
        if self.activated:
            print "TDC deactivated"
            self.onStop()
            self.timer.stop()
            self.ts.stop()
            self.ts.wait()
            del self.ts
            self.activated = False
        MainWindowWidget.deactivate(self)
        
    def on_update(self):
        self.channel = self.channel_edit.value()    
        self.trigger = self.trigger_edit.value()        
        self.roi_start = self.roi_start_edit.value()        
        self.roi_stop = self.roi_stop_edit.value()        
        self.binwidth = self.binwidth_edit.value()        
        newname = str(self.filename_edit.text())
        if newname=="":
            self.filename = "tdc"
        else:
            self.filename = newname
        print self.filename
        self.project = str(self.project_edit.text())
        
    def on_sequence_update(self):
        print "on_sequence_update()"
        self.sequence_enable = self.sequence_enable_box.isChecked()
        self.ontime = self.ontime_edit.value()
        self.offtime = self.offtime_edit.value()
        ontime = int( round(self.ontime/timestamper.clockcycle))
        offtime = int( round(self.offtime/timestamper.clockcycle))
        self.ontime = ontime*timestamper.clockcycle
        self.offtime = offtime*timestamper.clockcycle
        self.ontime_edit.setValue(self.ontime)
        self.offtime_edit.setValue(self.offtime)
        enable = 0x00
        ontime += 1  # to compensate for the hardware omitting one cycle
        offtime += 1
        if self.sequence_enable:
            enable = 0x01
        self.ts.sendCommand( struct.pack('>BIIB', 0x13, ontime , offtime , enable )  ) 
        self.config['TDCWidget.offtime'] = self.offtime
        self.config['TDCWidget.ontime'] = self.ontime
  
    def on_sequence_enable(self, state):
        print "on_sequence_enable()"
        self.on_sequence_update()
  
    def on_update_displaysettings(self):
        self.MaxElements = int(self.remember_points_box.text())        
        self.remember_points_box.setText("{0:d}".format(self.MaxElements))
        
    def onData(self, counter, x, y ):   
        pass            

    def onDataUpdate(self):
        if self.state == self.OpStates.running:
            self.currentTrace.trace.y = self.ts.readHistogram()
            self.currentTrace.replot()
            status = self.ts.readStatus()
            self.triggerrate_label.setText( "{0:f}".format(status.triggerrate/1000.) )
            self.photonrate_label.setText( "{0:f}".format(status.photonrate/1000.) )
            self.labelIntegratedCounts.setText( "{0:d}".format(int(numpy.sum(self.currentTrace.trace.y))))
            self.badcrc_label.setText("{0:d}".format(status.badcrc))
            print status.triggerrate/1000., status.photonrate/1000., status.badcrc, status.goodcrc, status.triggercount, status.photoncount
            
    def onStart(self):
        if not self.activated:
            self.activate()
        if (self.state>self.OpStates.idle):
            self.onStop()
        directory = DataDirectory.DataDirectory( str(self.project) )
        filename, components = directory.sequencefile( str(self.filename) )
        name, extension = os.path.splitext(filename)
        self.ts.startNewRecording(self.channel,self.trigger,self.binwidth,self.roi_start,self.roi_stop,filename=name+".bin")
        print "started recording with filename",name+".bin"
        self.currentTrace = Traceui.PlottedTrace(TDCTrace(),self.graphicsView,pens.penList)
        self.currentTrace.trace.y = self.ts.readHistogram()
        self.currentTrace.trace.x = self.ts.readXValues()
        self.currentTrace.trace.filename = filename
        self.currentTrace.trace.name = ''.join( components[1:] )
        self.traceui.addTrace(self.currentTrace)
        self.currentTrace.plot( -1 )
        self.state = self.OpStates.running
    
    def onStop(self):
        self.ts.stopRecording()
        self.onDataUpdate()
        self.currentTrace.trace.vars.ontime_ms = self.ontime
        self.currentTrace.trace.vars.offtime_ms = self.offtime
        status = self.ts.readStatus()
        self.currentTrace.trace.vars.triggers = status.triggercount
        self.currentTrace.trace.vars.photons = status.photoncount
        self.currentTrace.trace.vars.read_errors = status.badcrc
        self.currentTrace.trace.resave()   
        self.state = self.OpStates.idle
        
    
    def onClose(self):
        self.config['TDCWidget.channel'] = self.channel
        self.config['TDCWidget.trigger'] = self.trigger
        self.config['TDCWidget.roi_start'] = self.roi_start       
        self.config['TDCWidget.roi_stop'] = self.roi_stop  
        self.config['TDCWidget.binwidth'] = self.binwidth       
        self.config['TDCWidget.filename'] = self.filename
        self.config['TDCWidget.project'] = self.project
        self.config['TDCWidget.MainWindow.State'] = QtGui.QMainWindow.saveState(self)
        self.config['TDCWidget.deviceSerial'] = self.deviceSerial
        self.config['TDCWidget.refreshInterval'] = self.refreshInterval

        self.deactivate()
                