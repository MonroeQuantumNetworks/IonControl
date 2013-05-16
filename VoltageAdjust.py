# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtGui, QtCore
import os.path
import functools
import magnitude
       
VoltageAdjustForm, VoltageAdjustBase = PyQt4.uic.loadUiType(r'ui\VoltageAdjust.ui')
ShuttlingEdgeForm, ShuttlingEdgeBase = PyQt4.uic.loadUiType(r'ui\ShuttlingEdge.ui')
    
class ShuttlingEdge( ShuttlingEdgeForm, ShuttlingEdgeBase ):
    def __init__(self, parent=0):
        ShuttlingEdgeForm.__init__(self,parent)
        QtGui.QListWidgetItem.__init__(self)
    
class Adjust:
    def __init__(self):
        self.line = 0.0
        self.lineGain = 1.0
        self.globalGain = 1.0

class Settings:
    def __init__(self):
        self.adjust = Adjust()
    
class VoltageAdjust(VoltageAdjustForm, VoltageAdjustBase ):
    updateOutput = QtCore.pyqtSignal(object)
    
    def __init__(self,config,parent=None):
        VoltageAdjustForm.__init__(self)
        VoltageAdjustBase.__init__(self,parent)
        self.config = config
        self.configname = 'VoltageAdjust.Settings'
        self.settings = self.config.get(self.configname,Settings())
        self.adjust = self.settings.adjust
        self.shuttlingEdges = list()
        self.activeShuttlingEdges = 0

    def setupUi(self, parent):
        VoltageAdjustForm.setupUi(self,parent)
        self.lineBox.setValue( self.adjust.line )
        self.lineGainBox.setValue( self.adjust.lineGain )
        self.globalGainBox.setValue( self.adjust.globalGain )
        self.lineBox.valueChanged.connect( functools.partial(self.onValueChanged,"line") )
        self.lineGainBox.valueChanged.connect( functools.partial(self.onValueChanged,"lineGain") )
        self.globalGainBox.valueChanged.connect( functools.partial(self.onValueChanged,"globalGain") )
        # Shuttling
        self.addEdgeButton.clicked.connect( self.addShuttlingEdge )
        self.removeEdgeButton.clicked.connect( self.removeShuttlingEdge )
        
    def addShuttlingEdge(self):
#        if len(self.shuttlingEdges)>self.activeShuttlingEdges:
#            self.shuttlingEdges[self.activeShuttlingEdges].setVisible(True)
#            self.activeShuttlingEdges += 1
#        else:
#            EdgeWidget = ShuttlingEdgeForm( ShuttlingEdgeBase() )
        e = ShuttlingEdge()
        e.setupUi(e)
        self.listWidget.setIndexWidget( )

    def removeShuttlingEdge(self):
        pass        
        
    def onValueChanged(self, attribute, value):
        setattr(self.adjust,attribute,value.toval() if isinstance( value, magnitude.Magnitude) else value) 
        self.updateOutput.emit(self.adjust)
    
    def onClose(self):
        self.config[self.configname] = self.settings
        