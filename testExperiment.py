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
import FitUi
import functools
from modules import DataDirectory
from AverageView import AverageView

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
        self.traceui = Traceui.Traceui(self.penicons,self.config,"testExperiment",self.graphicsView)
        self.traceui.setupUi(self.traceui)
        self.dockWidget.setWidget( self.traceui )
        self.dockWidgetList.append(self.dockWidget)
        self.fitWidget = FitUi.FitUi(self.traceui,self.config,"testExperiment")
        self.fitWidget.setupUi(self.fitWidget)
        self.dockWidgetFitUi.setWidget( self.fitWidget )
        self.dockWidgetList.append(self.dockWidgetFitUi )
        self.displayUi = AverageView(self.config,"testExperiment")
        self.displayUi.setupUi(self.displayUi)
        self.displayDock = QtGui.QDockWidget("Average")
        self.displayDock.setObjectName("Average")
        self.displayDock.setWidget( self.displayUi )
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea , self.displayDock)
        self.dockWidgetList.append(self.displayDock )
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
        self.trace = Trace.Trace()
        self.x = 0
        self.phase = random.uniform(0,2*numpy.pi)
        self.trace.x = numpy.array([self.x])
        self.trace.y = numpy.array([random.gauss(numpy.sin( self.x + self.phase),0.1)])
        self.trace.top = numpy.array([0.1])
        self.trace.bottom = numpy.array([0.1])
        self.trace.name = "test trace"
        self.trace.vars.comment = "My Comment"
        self.trace.filenameCallback = functools.partial( self.traceFilename, '' )
        self.plottedtrace = Traceui.PlottedTrace(self.trace,self.graphicsView,pens.penList)
        self.traceui.addTrace(self.plottedtrace ,pen=-1)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(300)
        self.timer.timeout.connect( self.onData )
        self.timer.start(300)
        self.displayUi.onClear()
        
    def onData(self):
        self.x += 0.1
        self.trace.x = numpy.append( self.trace.x, self.x )
        value = random.gauss(numpy.sin( self.x + self.phase),0.1)
        self.trace.y = numpy.append( self.trace.y, value )
        self.trace.top = numpy.append( self.trace.top, 0.1)
        self.trace.bottom = numpy.append( self.trace.bottom, 0.1)
        self.displayUi.add( value )
        self.plottedtrace.replot()
        
    def onStop(self):
        if hasattr(self, 'timer'):
            self.timer.stop()
    
    def onPause(self):
        self.StatusMessage.emit("test Pause not implemented")
     
    def activate(self):
        self.StatusMessage.emit("test active")
        MainWindowWidget.MainWindowWidget.activate(self)
        
    def deactivate(self):
        self.StatusMessage.emit("test not active")
        MainWindowWidget.MainWindowWidget.deactivate(self)
        
    def onClose(self):
        self.config['testWidget.MainWindow.State'] = QtGui.QMainWindow.saveState(self)
        self.traceui.onClose()

    def traceFilename(self, pattern):
        directory = DataDirectory.DataDirectory()
        path = str(QtGui.QFileDialog.getSaveFileName(self, 'Save file',directory.path()))
        return path
