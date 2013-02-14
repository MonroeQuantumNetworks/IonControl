# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 17:25:13 2012

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtCore, QtGui
import numpy
import struct
import Queue
from functools import partial
import sys
import os.path
sys.path.append(os.path.abspath(r'modules'))
import enum
import CountrateConversion
import PulserHardware
import time

MessageQueue = Queue.Queue()

step = 0.3

curvecolors = [ 'b', 'g', 'y', 'm' ]

class Task():
    pass

def hexprint(st):
    return ":".join("{0:0>2x}".format(ord(ch)) for ch in st)
    
    
class Worker(QtCore.QThread):
    data = QtCore.pyqtSignal( int, float, float )
    notifierfloat = QtCore.pyqtSignal(float)
    notifierint = QtCore.pyqtSignal(int)
    
    def __init__(self, pulserHardware, pulseProgramUi, initial_tick=0, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.exiting = False
        self.pulserHardware = pulserHardware
        self.pulseProgramUi = pulseProgramUi
        self.Mutex = QtCore.QMutex()
        self.activated = False
        self.tick = initial_tick
        
    def __enter__(self):
        self.integration_time = 100.0;
        return self
        
    def __exit__(self, type, value, traceback):
        self.wait()

    def run(self):
        try:
            self.tick_counter = 0
            print "Starting"
            self.pulserHardware.ppStart()
            with self:
                while not self.exiting:
                    if not MessageQueue.empty():
                        task = MessageQueue.get()
                        print "setting counter_mask", task.counter_mask
                        self.tick_counter = self.min_counter(task.counter_mask)
                    self.pulserHardware.ppReadData()
                    time.sleep(0.1)
                    #data = self.Connection.read(5)
#                    if len(data)==5:
#                        result = struct.unpack(">Lb", data)
#                        counter = result[0]>>24
#                        if (counter==self.tick_counter):
#                            self.tick += 1
#                        self.data.emit( counter, self.tick, result[0] & 0xffffff )
#                    else:
#                        pass
                        #print self.Connection.getStatus(), len(data)
            self.pulserHardware.ppStop()
            print "PP Stopped"
        except Exception as err:
            print err

    def min_counter(self,mask):
        cmin = 3
        if (mask & 0x04 == 0x04):
            cmin = 2
        if (mask & 0x02 == 0x02):
            cmin = 1
        if (mask & 0x01 == 0x01):
            cmin = 0
        return cmin
             
    def stop(self):
        with QtCore.QMutexLocker(self.Mutex):
            self.exiting = True

CounterForm, CounterBase = PyQt4.uic.loadUiType(r'ui\CounterWidget.ui')
           
class CounterWidget(CounterForm, CounterBase):
    StatusMessage = QtCore.pyqtSignal( str )
    ClearStatusMessage = QtCore.pyqtSignal()
    OpStates = enum.enum('idle','running','paused')
    
    def __init__(self,settings,parent=None):
        CounterBase.__init__(self,parent)
        CounterForm.__init__(self)
        self.MaxElements = 400;
        self.integration_time = 100.0;
        self.state = self.OpStates.idle
        self.initial_tick = 0
        self.unit = CountrateConversion.DisplayUnit()
        self.deviceSettings = settings
        self.pulserHardware = PulserHardware.PulserHardware(self.deviceSettings.xem)

    def setupUi(self, MainWindow, config):
        self.config = config        
        self.curves = [None]*4
        super(CounterWidget,self).setupUi(MainWindow)
        
        self.MaxElements = self.config.get('counter.MaxElements', default=self.MaxElements )
        self.counter_mask = self.config.get('counter.counter_mask', default=1 )
        self.unit.unit = self.config.get('counter.DisplayUnit',1)
        self.DisplayUnit.setCurrentIndex(self.unit.unit)
        
        self.remember_points_box.setValue(self.MaxElements)
        self.remember_points_box.valueChanged.connect(self.on_update_displaysettings)        
        
        self.counter_enable_box_1.stateChanged.connect( partial(self.on_counter_update,0) )
        self.counter_enable_box_2.stateChanged.connect( partial(self.on_counter_update,1) )
        self.counter_enable_box_3.stateChanged.connect( partial(self.on_counter_update,2) )
        self.counter_enable_box_4.stateChanged.connect( partial(self.on_counter_update,3) )

        self.counter_enable_box_1.setChecked( self.counter_mask & 0x01 == 0x01 )
        self.counter_enable_box_2.setChecked( self.counter_mask & 0x02 == 0x02 )
        self.counter_enable_box_3.setChecked( self.counter_mask & 0x04 == 0x04 )
        self.counter_enable_box_4.setChecked( self.counter_mask & 0x08 == 0x08 )

        self.curves = list()
        for mypen in curvecolors:
            #self.curves.append(self.plotview.plot(pen=mypen))
            self.curves.append(None)
        self.DisplayUnit.currentIndexChanged[int].connect(self.onUnitChange)

    def setPulseProgramUi(self,pulseProgramSetUi):
        self.pulseProgramUi = pulseProgramSetUi.addExperiment('Simple Counter')
    
    def onSave(self):
        print "CounterWidget Save not implemented"
    
    def onStart(self):
        print "CounterWidget Start not implemented"
    
    def onPause(self):
        if self.state == self.OpStates.paused:
            self.state = self.OpStates.running
        elif self.state == self.OpStates.running:
            self.state = self.OpStates.paused
        self.on_update()
    
    def onStop(self):
        print "CounterWidget Stop not implemented"
        
    def startData(self):
        if not hasattr(self, 'xData'):
            self.xData = [numpy.array([])]*4 
        if not hasattr(self, 'yData'):
            self.yData = [numpy.array([])]*4 
        #self.max_tick = 0
 
    def on_update(self):
        task = Task()
        task.counter_mask = 0 if self.state == self.OpStates.paused else self.counter_mask 
        interval = self.time_box.value()
        task.counter_interval = int( interval* 50000)
        self.integration_time = interval;
        MessageQueue.put(task)
        print "task", self.counter_mask, int( interval* 50000)
        self.config['counter.integration_time'] = self.integration_time
        self.config['counter.counter_mask'] = self.counter_mask

    def on_update_displaysettings(self):
        self.MaxElements = self.remember_points_box.value()
        self.config['counter.MaxElements'] = self.MaxElements
        
    def onData(self, counter, x, y ):
        if counter<4:
            self.initial_tick = x   
            y = self.unit.convert(y,self.integration_time) 
            Start = max( 1+len(self.xData[counter])-self.MaxElements, 0)
            self.yData[counter] = numpy.append(self.yData[counter][Start:], y)
            self.xData[counter] = numpy.append(self.xData[counter][Start:], x)
            if self.curves[counter] is not None:
                self.curves[counter].setData(self.xData[counter],self.yData[counter])
            else:
                print "ignoring result for counter", counter
                
    def onClear(self):
        for i,x in enumerate(self.xData):
            self.xData[i] = numpy.array([])
        for i,y in enumerate(self.yData):
            self.yData[i] = numpy.array([])
                
    def on_counter_update(self, index, i):
        print "i is", i, "index is", index
        self.counter_mask = 0
        self.counter_mask = ( self.counterPlotUpdate(0,self.counter_enable_box_1.isChecked()) |
                              self.counterPlotUpdate(1,self.counter_enable_box_2.isChecked()) |
                              self.counterPlotUpdate(2,self.counter_enable_box_3.isChecked()) |
                              self.counterPlotUpdate(3,self.counter_enable_box_4.isChecked()) )
        self.on_update()
        print "counter_mask", self.counter_mask    

    def counterPlotUpdate(self, index, show ):
        if show and self.curves[index] is None:
            self.curves[index] =  self.plotview.plot(pen=curvecolors[index])
        elif (not show) and (self.curves[index] is not None):
            self.plotview.removeItem( self.curves[index] )
            self.curves[index] = None
        if show:
            return 1<<index
        return 0
        
    def onUnitChange(self,unit):
        self.unit.unit = unit


    def activate(self):
        self.activated = False
        if self.deviceSettings is not None:
            try:
                self.deviceSettings.xem
                self.worker = Worker(self.pulserHardware,self.pulseProgramUi,self.initial_tick)
                self.worker.data.connect(self.onData)
                self.worker.start()
                self.startData()
                self.activated = True
                self.state = self.OpStates.running
                self.on_counter_update(0, 0)
                print "counter activated"
                self.pulserHardware.ppUpload(self.pulseProgramUi.getPulseProgramBinary())
            except Exception as ex:
                print ex
                self.StatusMessage.emit( ex.message )
    
    def deactivate(self):
        if self.activated and hasattr( self, 'worker'):
            self.worker.stop()
            self.worker.wait()
            self.activated = False
            self.state = self.OpStates.idle
        
    def onClose(self):
        self.config['counter.DisplayUnit'] = self.unit.unit

    def updateSettings(self,settings,active=False):
        self.deviceSettings = settings
        self.deactivate()
        self.pulserHardware = PulserHardware.PulserHardware(self.deviceSettings.xem)
        self.activate()
        