# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 17:25:13 2012

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore
import os.path
import numpy
import pens
import Traceui
import pyqtgraph
import MainWindowWidget
import Trace
import string
        
testForm, testBase = PyQt4.uic.loadUiType(r'ui\FromFile.ui')


class FileTrace(Trace.Trace):
    def __init__(self):
        Trace.Trace.__init__(self)
        
    def saveTrace(self,filename):
        of = open(filename,'w')
        self.saveTraceHeader(of)
        print >>of, "# histogram data: time [ms] counts"
        for x,y in zip(self.x, self.y):
            print >>of, x, y
        of.close()
        
    def readTrace(self,filename):
        infile = open(filename,'r')
        self.x = []
        self.y = []
        with infile:
            for line in infile:
                line = line.lstrip()
                if line[0]=='#':
                    a = line.split(None,2)
                    if len(a)>2:
                        self.vars.__dict__[a[1]] = a[2]  
                else:
                    a = line.split(None,2)
                    if len(a)>1:
                        self.x.append(float(a[0]))
                        self.y.append(float(a[1]))
        

class configuration:                    
    def __init__(self):
        self.directory = os.path.expanduser('~')

class FromFile(testForm, MainWindowWidget.MainWindowWidget):
    StatusMessage = QtCore.pyqtSignal( str )
    ClearStatusMessage = QtCore.pyqtSignal()

    def __init__(self,parent=None):
        MainWindowWidget.MainWindowWidget.__init__(self,parent)
        testForm.__init__(self)
        pyqtgraph.setConfigOption('background', 'w')
        pyqtgraph.setConfigOption('foreground', 'k')
        self.conf = configuration()

    def setupUi(self,MainWindow,config):
        testForm.setupUi(self,MainWindow)
        self.config = config
        self.graphicsView = self.graphicsLayout.graphicsView
        self.penicons = pens.penicons().penicons()
        self.traceui = Traceui.Traceui(self.penicons)
        self.traceui.setupUi(self.traceui)
        self.dockWidget.setWidget( self.traceui )
        self.dockWidgetList.append(self.dockWidget)
        self.conf = config.get('FromFile.configuration',configuration())

    def onClear(self):
        self.dockWidget.setShown(True)
        self.StatusMessage.emit("test Clear not implemented")
    
    def onSave(self):
        self.StatusMessage.emit("test Save not implemented")
    
    def onStart(self):
        fnames = QtGui.QFileDialog.getOpenFileNames(self, 'Open files', self.conf.directory)
        for fname in fnames:
            trace = FileTrace()
            trace.filename = str(fname)
            self.conf.directory, trace.name = os.path.split(str(fname))
            trace.readTrace(fname)
            self.traceui.addTrace(Traceui.PlottedTrace(trace,self.graphicsView,pens.penList,-1))
    
    def onPause(self):
        self.StatusMessage.emit("From File Pause not implemented")
    
    def onStop(self):
        self.StatusMessage.emit("From File Stop not implemented")
        
    def activate(self):
        self.StatusMessage.emit("From File active")
        MainWindowWidget.MainWindowWidget.activate(self)
        
    def deactivate(self):
        self.StatusMessage.emit("From File not active")
        MainWindowWidget.MainWindowWidget.deactivate(self)
        
    def onClose(self):
        self.config['FromFile.configuration'] = self.conf
