# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 17:25:13 2012

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtCore, QtGui
import numpy
import struct
from functools import partial
import sys
import os.path
sys.path.append(os.path.abspath(r'modules'))
import enum
import CountrateConversion
import PulserHardware

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
        return self
        
    def __exit__(self, type, value, traceback):
        pass
#        self.wait()
        
    def onReload(self):
        with QtCore.QMutexLocker(self.Mutex):
            if self.running:
                self.pulserHardware.ppStop()
                self.pulserHardware.ppUpload(self.pulseProgramUi.getPulseProgramBinary())
                self.pulserHardware.ppStart()

    def run(self):
        try:
            with QtCore.QMutexLocker(self.Mutex):
                self.tick_counter = 0
                self.pulserHardware.ppUpload(self.pulseProgramUi.getPulseProgramBinary())
                print "Starting"
                self.pulserHardware.ppStart()
                self.running = True
            with self:
                while not self.exiting:
                    with QtCore.QMutexLocker(self.Mutex):
                        data = self.pulserHardware.ppReadData(4,0.1)
                    for s in PulserHardware.sliceview(data,4):
                        (token,) = struct.unpack('I',s)
                        count = token & 0xffffff
                        tokentype = (token >> 28)
                        counter = (token>>24) & 0xf
                        if (counter==self.tick_counter):
                            self.tick += 1
                        self.data.emit( counter, self.tick, count )
            with QtCore.QMutexLocker(self.Mutex):
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
        self.remember_points_box.valueChanged.connect(self.onUpdateDisplaysettings)        
        
        self.counter_enable_box_1.stateChanged.connect( partial(self.onCounterUpdate,0) )
        self.counter_enable_box_2.stateChanged.connect( partial(self.onCounterUpdate,1) )
        self.counter_enable_box_3.stateChanged.connect( partial(self.onCounterUpdate,2) )
        self.counter_enable_box_4.stateChanged.connect( partial(self.onCounterUpdate,3) )

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
        """ Main program save button
        """
        print "CounterWidget Save not implemented"
    
    def onStart(self):
        """ Main program Start button
        """
        print "CounterWidget Start not implemented"
    
    def onPause(self):
        """ Main program Pause button
        """
        if self.state == self.OpStates.paused:
            self.state = self.OpStates.running
        elif self.state == self.OpStates.running:
            self.state = self.OpStates.paused
    
    def onStop(self):
        """ Main program Stop button
        """
        print "CounterWidget Stop not implemented"
        
    def onClear(self):
        """ Main program Clear button
        """
        for i,x in enumerate(self.xData):
            self.xData[i] = numpy.array([])
        for i,y in enumerate(self.yData):
            self.yData[i] = numpy.array([])
        
    def onReload(self):
        """ Main program reload button
        """
        if self.activated:
            self.worker.onReload()
            
    def startData(self):
        """ Initialize local data
        """
        if not hasattr(self, 'xData'):
            self.xData = [numpy.array([])]*4 
        if not hasattr(self, 'yData'):
            self.yData = [numpy.array([])]*4 
        #self.max_tick = 0
 
    def onUpdateDisplaysettings(self):
        self.MaxElements = self.remember_points_box.value()
        self.config['counter.MaxElements'] = self.MaxElements
        
    def onData(self, counter, x, y ):
        if counter<4:
            self.initial_tick = x   
            y = self.unit.convert(y,self.pulseProgramUi.pulseProgram.variable("coolingTime").ounit('ms').toval()) 
            Start = max( 1+len(self.xData[counter])-self.MaxElements, 0)
            self.yData[counter] = numpy.append(self.yData[counter][Start:], y)
            self.xData[counter] = numpy.append(self.xData[counter][Start:], x)
            if self.curves[counter] is not None:
                self.curves[counter].setData(self.xData[counter],self.yData[counter])
            else:
                print "ignoring result for counter", counter
                
    def onCounterUpdate(self, index, i):
        """ called when the counter enable check boxes change state
        """
        print "i is", i, "index is", index
        self.counter_mask = 0
        self.counter_mask = ( self.counterPlotUpdate(0,self.counter_enable_box_1.isChecked()) |
                              self.counterPlotUpdate(1,self.counter_enable_box_2.isChecked()) |
                              self.counterPlotUpdate(2,self.counter_enable_box_3.isChecked()) |
                              self.counterPlotUpdate(3,self.counter_enable_box_4.isChecked()) )
        self.config['counter.counter_mask'] = self.counter_mask

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
                self.onCounterUpdate(0, 0)
                self.worker = Worker(self.pulserHardware,self.pulseProgramUi,self.initial_tick)
                self.worker.data.connect(self.onData)
                self.worker.start()
                self.startData()
                self.activated = True
                self.state = self.OpStates.running
                print "counter activated"
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
        """ Main program settings have changed
        """
        self.deviceSettings = settings
        self.deactivate()
        self.pulserHardware = PulserHardware.PulserHardware(self.deviceSettings.xem)
        self.activate()
        