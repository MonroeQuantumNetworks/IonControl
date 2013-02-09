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
import pyqtgraph
import MainWindowWidget
import Trace
import FitUi
        
testForm, testBase = PyQt4.uic.loadUiType(r'ui\testExperiment.ui')

class test(testForm, MainWindowWidget.MainWindowWidget):
    StatusMessage = QtCore.pyqtSignal( str )
    ClearStatusMessage = QtCore.pyqtSignal()

    def __init__(self,parent=None):
        MainWindowWidget.MainWindowWidget.__init__(self,parent)
        testForm.__init__(self)
        pyqtgraph.setConfigOption('background', 'w')
        pyqtgraph.setConfigOption('foreground', 'k')

    def setupUi(self,MainWindow,config):
        testForm.setupUi(self,MainWindow)
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
        if 'testWidget.MainWindow.State' in self.config:
            QtGui.QMainWindow.restoreState(self,self.config['testWidget.MainWindow.State'])
            print "restoreState"

    def setPulseProgramUi(self,pulseProgramUi):
        self.pulseProgramUi = pulseProgramUi
        self.pulseProgramUi.addExperiment('Sequence')

    def onClear(self):
        self.dockWidget.setShown(True)
        self.StatusMessage.emit("test Clear not implemented")
    
    def onSave(self):
        self.StatusMessage.emit("test Save not implemented")
    
    def onStart(self):
        trace = Trace.Trace()
        phase = random.uniform(0,2*numpy.pi)
        trace.x = numpy.arange(0,5,5/200.)
        trace.y = numpy.sin( numpy.arange(0,5,5/200.) + phase)
        trace.height = 0.2
        for index, elem in enumerate(trace.y):
            trace.y[index] = random.gauss(elem,0.1)
        trace.name = "test trace"
        trace.vars.comment = "My Comment"
        self.traceui.addTrace(Traceui.PlottedTrace(trace,self.graphicsView,pens.penList),pen=-1)
    
    def onPause(self):
        self.StatusMessage.emit("test Pause not implemented")
    
    def onStop(self):
        self.StatusMessage.emit("test Stop not implemented")
        
    def activate(self):
        self.StatusMessage.emit("test active")
        MainWindowWidget.MainWindowWidget.activate(self)
        
    def deactivate(self):
        self.StatusMessage.emit("test not active")
        MainWindowWidget.MainWindowWidget.deactivate(self)
        
    def onClose(self):
        self.config['testWidget.MainWindow.State'] = QtGui.QMainWindow.saveState(self)
