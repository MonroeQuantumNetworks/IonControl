# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import functools
import logging

from PyQt4 import QtCore
import PyQt4.uic

import modules.magnitude as magnitude
from modules.Expression import Expression
from gui.ExpressionValue import ExpressionValue
from modules.magnitude import mg


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
    
class Adjust(object):
    expression = Expression()
    def __init__(self, globalDict=dict()):
        self._globalDict = globalDict
        self._line = ExpressionValue( name="line", globalDict=globalDict, value=mg(0.0) )
        self._lineGain = ExpressionValue( name="lineGain", globalDict=globalDict, value=mg(1.0) )
        self._globalGain = ExpressionValue( name="globalGain", globalDict=globalDict, value=mg(1.0) )
        
    @property 
    def globalDict(self):
        return self._globalDict
    
    @globalDict.setter
    def globalDict(self, globalDict):
        self._globalDict = globalDict
        self._line.globalDict = globalDict
        self._lineGain.globalDict = globalDict
        self._globalGain.globalDict = globalDict        
        
    @property
    def line(self):
        return self._line.value
    
    @line.setter
    def line(self, value):
        self._line.value = value
    
    @property
    def lineGain(self):
        return self._lineGain.value
    
    @lineGain.setter
    def lineGain(self, value):
        self._lineGain.value = value
    
    @property
    def globalGain(self):
        return self._globalGain.value
    
    @globalGain.setter
    def globalGain(self, value):
        self._globalGain.value = value
        
    @property
    def lineString(self):
        return self._line.string
    
    @lineString.setter
    def lineString(self, s):
        self._line.string = s
    
    @property
    def lineGainString(self):
        return self._lineGain.string
    
    @lineGainString.setter
    def lineGainString(self, s):
        self._lineGain.string = s
    
    @property
    def globalGainString(self):
        return self._globalGain.value
    
    @globalGainString.setter
    def globalGainString(self, s):
        self._globalGain.string = s
        
class Settings:
    def __init__(self):
        self.adjust = Adjust()
        
class ShuttlingException(Exception):
    pass
    
class VoltageAdjust(VoltageAdjustForm, VoltageAdjustBase ):
    updateOutput = QtCore.pyqtSignal(object)
    shuttleOutput = QtCore.pyqtSignal(object, object)
    
    def __init__(self, config, globalDict, parent=None):
        VoltageAdjustForm.__init__(self)
        VoltageAdjustBase.__init__(self,parent)
        self.config = config
        self.configname = 'VoltageAdjust.Settings'
        self.settings = self.config.get(self.configname,Settings())
        self.settings.adjust.globalDict = globalDict
        self.adjust = self.settings.adjust
        self.shuttlingEdges = list()
        self.shuttlingDefinitions = list()

    def setupUi(self, parent):
        VoltageAdjustForm.setupUi(self,parent)
        self.lineBox.globalDict = self.settings.adjust.globalDict
        self.lineGainBox.globalDict = self.settings.adjust.globalDict
        self.globalGainBox.globalDict = self.settings.adjust.globalDict
        self.lineBox.setExpression( self.adjust._line )
        self.lineGainBox.setExpression( self.adjust._lineGain )
        self.globalGainBox.setExpression( self.adjust._globalGain )
        self.lineBox.expressionChanged.connect( functools.partial(self.onExpressionChanged,"_line") )
        self.lineGainBox.expressionChanged.connect( functools.partial(self.onExpressionChanged,"_lineGain") )
        self.globalGainBox.expressionChanged.connect( functools.partial(self.onExpressionChanged,"_globalGain") )
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
        logger = logging.getLogger(__name__)
        logger.info( "ShuttleSequence" )
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
        logger = logging.getLogger(__name__)
        logger.info( "ShuttleEdge {0}".format( index ) )
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
        
    def onExpressionChanged(self, attribute, value):
        setattr(self.adjust,attribute,value) 
        self.updateOutput.emit(self.adjust)
        
    def saveConfig(self):
        self.config[self.configname] = self.settings
        