# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 17:25:13 2012

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtCore
import numpy
import struct
from functools import partial
from modules import enum
from modules import CountrateConversion
import PulserHardware

step = 0.3

curvecolors = [ 'b', 'g', 'y', 'm' ]

class Task():
    pass

def hexprint(st):
    return ":".join("{0:0>2x}".format(ord(ch)) for ch in st)
    
    
CounterForm, CounterBase = PyQt4.uic.loadUiType(r'ui\CounterWidget.ui')
           
class CounterWidget(CounterForm, CounterBase):
    StatusMessage = QtCore.pyqtSignal( str )
    ClearStatusMessage = QtCore.pyqtSignal()
    OpStates = enum.enum('idle','running','paused')
    
    def __init__(self,settings,pulserHardware,parent=None):
        CounterBase.__init__(self,parent)
        CounterForm.__init__(self)
        self.MaxElements = 400;
        self.state = self.OpStates.idle
        self.initial_tick = 0
        self.unit = CountrateConversion.DisplayUnit()
        self.deviceSettings = settings
        self.pulserHardware = pulserHardware
        self.activated = False

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
        if self.running:
            self.pulserHardware.ppStop()
            self.pulserHardware.ppUpload(self.pulseProgramUi.getPulseProgramBinary())
            self.pulserHardware.ppStart()
            
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
        
    def onData(self, data ):
        if len(data.count[0])>0:
            counter = 0
            self.initial_tick += 1   
            print data.count[0]
            y = self.unit.convert(data.count[counter][0],self.pulseProgramUi.pulseProgram.variable("coolingTime").ounit('ms').toval()) 
            Start = max( 1+len(self.xData[counter])-self.MaxElements, 0)
            self.yData[counter] = numpy.append(self.yData[counter][Start:], y)
            self.xData[counter] = numpy.append(self.xData[counter][Start:], self.initial_tick)
            if self.curves[counter] is not None:
                self.curves[counter].setData(self.xData[counter],self.yData[counter])
            else:
                print "ignoring result for counter", counter
        else:
            print data.count[0]
                
    def onCounterUpdate(self, index, i):
        """ called when the counter enable check boxes change state
        """
        # print "i is", i, "index is", index
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
        if self.deviceSettings is not None:
            try:
                #self.deviceSettings.xem
                self.onCounterUpdate(0, 0)
                self.startData()
                self.pulserHardware.dataAvailable.connect(self.onData)
                self.tick_counter = 0
                binary = self.pulseProgramUi.getPulseProgramBinary()
                print "binary size", len(binary)
                self.pulserHardware.ppUpload(binary)
                print "Starting"
                self.pulserHardware.ppStart()
                self.running = True

                self.activated = True
                self.state = self.OpStates.running
                print "counter activated"
            except Exception as ex:
                print ex
                self.StatusMessage.emit( ex.message )
    
    def deactivate(self):
        if self.activated:
            self.pulserHardware.ppStop()
            print "PP Stopped"
            self.pulserHardware.dataAvailable.disconnect(self.onData)
            self.activated = False
            self.state = self.OpStates.idle
        
    def onClose(self):
        self.config['counter.DisplayUnit'] = self.unit.unit

    def updateSettings(self,settings,active=False):
        """ Main program settings have changed
        """
        self.deviceSettings = settings
       