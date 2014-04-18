# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 17:25:13 2012

@author: pmaunz
"""

import functools
import random
from trace import pens

from PyQt4 import QtGui, QtCore
import PyQt4.uic
import numpy

from AverageViewTable import AverageViewTable
import MainWindowWidget
from scan.ScanControl import ScanControl
from fit.FitUi import FitUi
from modules import DataDirectory
from trace.PlottedTrace import PlottedTrace
from trace.Trace import Trace
from trace.Traceui import Traceui


testForm, testBase = PyQt4.uic.loadUiType(r'ui\testExperiment.ui')

class test(testForm, MainWindowWidget.MainWindowWidget):
    StatusMessage = QtCore.pyqtSignal( str )
    ClearStatusMessage = QtCore.pyqtSignal()
    experimentName = 'Test Scan'

    def __init__(self,parent=None):
        MainWindowWidget.MainWindowWidget.__init__(self,parent)
        testForm.__init__(self)
#        pyqtgraph.setConfigOption('background', 'w')
#        pyqtgraph.setConfigOption('foreground', 'k')

    def setupUi(self,MainWindow,config):
        testForm.setupUi(self,MainWindow)
        self.config = config
        self.plottedTrace = None
        self.graphicsView = self.graphicsLayout.graphicsView
        self.penicons = pens.penicons().penicons()
        self.traceui = Traceui(self.penicons,self.config,"testExperiment",self.graphicsView)
        self.traceui.setupUi(self.traceui)
        self.dockWidget.setWidget( self.traceui )
        self.dockWidgetList.append(self.dockWidget)
        self.fitWidget = FitUi(self.traceui,self.config,"testExperiment")
        self.fitWidget.setupUi(self.fitWidget)
        self.dockWidgetFitUi.setWidget( self.fitWidget )
        self.dockWidgetList.append(self.dockWidgetFitUi )
        self.displayUi = AverageViewTable(self.config)
        self.displayUi.setupUi()
        self.displayDock = QtGui.QDockWidget("Average")
        self.displayDock.setObjectName("Average")
        self.displayDock.setWidget( self.displayUi )
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea , self.displayDock)
        self.dockWidgetList.append(self.displayDock )
        if 'testWidget.MainWindow.State' in self.config:
            QtGui.QMainWindow.restoreState(self,self.config['testWidget.MainWindow.State'])
#start added
        self.scanControlWidget = ScanControl(config,self.experimentName)
        self.scanControlWidget.setupUi(self.scanControlWidget)
        self.scanControlUi.setWidget(self.scanControlWidget )
        self.dockWidgetList.append(self.scanControlUi)
#end added
        self.tabifyDockWidget( self.dockWidgetFitUi, self.scanControlUi )

    def setPulseProgramUi(self,pulseProgramUi):
        self.pulseProgramUi = pulseProgramUi
        self.pulseProgramUi.addExperiment('Sequence')

    def onClear(self):
        self.dockWidget.setShown(True)
        self.StatusMessage.emit("test Clear not implemented")
    
    def onSave(self):
        self.StatusMessage.emit("test Save not implemented")

    def onStart(self):
        self.scanType = self.scanControlWidget.scanRepeatComboBox.currentIndex()
#start added
        if self.scanType == 0:
            self.startScan()
        elif self.scanType == 1:
            self.createAverageScan()
            self.startScan()
#end added
        self.timer = QtCore.QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect( self.onData )
        self.timer.start(10)
        self.displayUi.onClear()

#start added
    def createAverageScan(self):
        self.averagePlottedTrace = PlottedTrace(Trace(), self.graphicsView, pens.penList)
        self.averagePlottedTrace.trace.name = "test average trace"
        self.averagePlottedTrace.trace.vars.comment = "average trace comment"
        self.averagePlottedTrace.trace.filenameCallback = functools.partial(self.traceFilename, '')
        self.traceui.addTrace(self.averagePlottedTrace, pen=0)
#end added

    def startScan(self):
        if self.plottedTrace is not None:
            self.plottedTrace.plot(0)
        self.plottedTrace = PlottedTrace(Trace(),self.graphicsView,pens.penList)
        self.xvalue = 0
        self.phase = 0 #random.uniform(0,2*numpy.pi)
        self.plottedTrace.trace.x = numpy.array([self.xvalue])
        c = numpy.sin( self.xvalue + self.phase)**2
        self.plottedTrace.trace.y = numpy.array([random.gauss(c, 0.1)])#c*(1-c))])
        self.plottedTrace.trace.top = numpy.array([0.05])
        self.plottedTrace.trace.bottom = numpy.array([0.05])
        self.plottedTrace.trace.filenameCallback = functools.partial( self.traceFilename, '' )
        if self.scanType == 0:
            self.plottedTrace.trace.name = "test trace"
            self.plottedTrace.trace.vars.comment = "My Comment"
            self.traceui.addTrace(self.plottedTrace, pen=-1)
#start added
        elif self.scanType == 1:
            self.traceui.addTrace(self.plottedTrace, pen=-1, parentTrace=self.averagePlottedTrace)
            self.plottedTrace.trace.name = "test trace {0}".format(self.averagePlottedTrace.childCount())
            self.plottedTrace.trace.vars.comment = "My Comment {0}".format(self.averagePlottedTrace.childCount())
#end added

    def onData(self):
        self.xvalue += 0.05
        self.plottedTrace.trace.x = numpy.append( self.plottedTrace.trace.x, self.xvalue )
        c = numpy.sin( self.xvalue + self.phase)**2
        value = random.gauss(c, 0.1)#c*(1-c))
        self.plottedTrace.trace.y = numpy.append( self.plottedTrace.trace.y, value )
        self.plottedTrace.trace.top = numpy.append( self.plottedTrace.trace.top, 0.05)
        self.plottedTrace.trace.bottom = numpy.append( self.plottedTrace.trace.bottom, 0.05)
        self.displayUi.add( [value] )
        self.plottedTrace.replot()
        if self.xvalue > 500:
            if self.scanType == 0:
                self.onStop()
#start added
            elif self.scanType == 1:
                self.averagePlottedTrace.averageChildren()
                self.averagePlottedTrace.plot(7) #average plot is in black
                self.startScan()
#end added
                
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
        
    def saveConfig(self):
        self.config['testWidget.MainWindow.State'] = QtGui.QMainWindow.saveState(self)
        self.traceui.saveConfig()
        self.fitWidget.saveConfig()
        
    def traceFilename(self, pattern):
        directory = DataDirectory.DataDirectory()
        path = str(QtGui.QFileDialog.getSaveFileName(self, 'Save file',directory.path()))
        return path

    def setGlobalVariablesUi(self, globalVariablesUi ):
        self.globalVariables = globalVariablesUi.variables
        self.globalVariablesChanged = globalVariablesUi.valueChanged
        self.globalVariablesUi = globalVariablesUi
        self.fitWidget.setGlobalVariablesUi( globalVariablesUi )
