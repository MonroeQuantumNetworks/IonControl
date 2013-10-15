# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtGui, QtCore
import os.path
import functools
import modules.magnitude as magnitude
       
VoltageAdjustForm, VoltageAdjustBase = PyQt4.uic.loadUiType(r'ui\VoltageAdjust.ui')
ShuttlingEdgeForm, ShuttlingEdgeBase = PyQt4.uic.loadUiType(r'ui\ShuttlingEdge.ui')

class ShuttlingEdge:
    def __init__(self):
        self.fromLine = 0
        self.toLine = 0
        self.steps = 2
    
class ShuttlingEdgeUi( ShuttlingEdgeForm, ShuttlingEdgeBase ):
    def __init__(self, parent=None):
        ShuttlingEdgeForm.__init__(self)
        ShuttlingEdgeBase.__init__(self,parent)
        self.definition = ShuttlingEdge()
        
    def setupUi(self, parent):
        ShuttlingEdgeForm.setupUi(self,parent)
        self.fromBox.valueChanged.connect( functools.partial(self.onValueChanged, 'fromLine') )
        self.toBox.valueChanged.connect( functools.partial(self.onValueChanged, 'toLine') )
        self.stepsBox.valueChanged.connect( functools.partial(self.onValueChanged, 'steps') )
        self.fromBox.setValue(self.definition.fromLine)
        self.toBox.setValue(self.definition.toLine)
        self.stepsBox.setValue(self.definition.steps)
        
        
    def onValueChanged(self, attr, value):
        setattr( self.definition, attr, value.toval() if isinstance( value, magnitude.Magnitude) else value )
    
class Adjust:
    def __init__(self):
        self.line = 0.0
        self.lineGain = 1.0
        self.globalGain = 1.0
        
class Settings:
    def __init__(self):
        self.adjust = Adjust()
        
class ShuttlingException(Exception):
    pass
    
class VoltageAdjust(VoltageAdjustForm, VoltageAdjustBase ):
    updateOutput = QtCore.pyqtSignal(object)
    shuttleOutput = QtCore.pyqtSignal(object, object)
    
    def __init__(self,config,parent=None):
        VoltageAdjustForm.__init__(self)
        VoltageAdjustBase.__init__(self,parent)
        self.config = config
        self.configname = 'VoltageAdjust.Settings'
        self.settings = self.config.get(self.configname,Settings())
        self.adjust = self.settings.adjust
        self.shuttlingEdges = list()
        self.shuttlingDefinitions = list()

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
        self.startShuttlingSeqFiniteButton.clicked.connect( self.onShuttleSequence )
        self.startShuttlingSeqContButton.clicked.connect( functools.partial(self.onShuttleSequence, cont=True) )
#        self.edgesVerticalLayout = QtGui.QVBoxLayout(self.shuttlingEdgesWidget)
#        self.edgesVerticalLayout.setSpacing(0)
#        self.shuttlingEdgesWidget.setLayout(self.edgesVerticalLayout)
        
        for index in range(2):
            edge = ShuttlingEdgeUi()
            edge.setupUi(edge)
            edge.goButton.clicked.connect( functools.partial(self.onShuttleEdge, index) )
            self.shuttlingEdges.append(edge)
            self.verticalLayout.addWidget(edge)
            
#        AONumberVoltageAction = QtGui.QAction( "AO Number/10 voltage")
#        AONumberVoltageAction.triggered.connect( self.applyAONumberVoltage )
#        self.lineLabel.addAction( AONumberVoltageAction )
#        DSubNumberVoltageAction = QtGui.QAction( "DSub Number/10 voltage")
#        DSubNumberVoltageAction.triggered.connect( self.applyDSubNumberVoltage )
#        self.lineLabel.addAction( DSubNumberVoltageAction )

    def onShuttleSequence(self, cont=False):
        print "ShuttleSequence"
        first = self.shuttlingEdges[0].definition.fromLine
        last = self.shuttlingEdges[-1].definition.toLine
        if self.adjust.line==first:
            reverse = False
        elif self.adjust.line==last:
            reverse = True
        else:
            raise ShuttlingException("Current Line has to be either first line or last line of shuttling definition")
        definitionlist = [edgeui.definition for edgeui in self.shuttlingEdges]
        for item in definitionlist:
            item.lineGain = self.adjust.lineGain
            item.globalGain = self.adjust.globalGain
            item.reverse = reverse
        self.shuttleOutput.emit( definitionlist, cont )

    def onShuttlingDone(self,currentline):
        self.lineBox.setValue(currentline)
        self.adjust.line = currentline

    def onShuttleEdge(self, index):
        print "ShuttleEdge", index
        definition = self.shuttlingEdges[index].definition
        if self.adjust.line==definition.fromLine:
            definition.reverse = False
        elif self.adjust.line==definition.toLine:
            definition.reverse = True
        else:
            raise ShuttlingException("Current Line has to be either first line or last line of shuttling definition")
        definition.lineGain = self.adjust.lineGain
        definition.globalGain = self.adjust.globalGain
        self.shuttleOutput.emit( [self.shuttlingEdges[index].definition], False )
        
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
        