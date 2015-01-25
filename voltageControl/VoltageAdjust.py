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
from voltageControl.ShuttleEdgeTableModel import ShuttleEdgeTableModel
from voltageControl.ShuttlingDefinition import ShuttlingGraph, ShuttleEdge
from modules.PyqtUtility import updateComboBoxItems
from modules.firstNotNone import firstNotNone
from modules.Utility import unique
from modules.GuiAppearance import restoreGuiState, saveGuiState


VoltageAdjustForm, VoltageAdjustBase = PyQt4.uic.loadUiType(r'ui\VoltageAdjust.ui')
ShuttlingEdgeForm, ShuttlingEdgeBase = PyQt4.uic.loadUiType(r'ui\ShuttlingEdge.ui')

    
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
    
    def __init__(self,config,voltageBlender,parent=None):
        VoltageAdjustForm.__init__(self)
        VoltageAdjustBase.__init__(self,parent)
        self.config = config
        self.configname = 'VoltageAdjust.Settings'
        self.settings = self.config.get(self.configname,Settings())
        self.adjust = self.settings.adjust
        self.shuttlingGraph = ShuttlingGraph()
        self.voltageBlender = voltageBlender

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
        self.shuttleEdgeTableModel = ShuttleEdgeTableModel(self.config, self.shuttlingGraph)
        self.edgeTableView.setModel(self.shuttleEdgeTableModel)
        self.currentPositionLabel.setText( firstNotNone( self.shuttlingGraph.currentPositionName, "" ) )
        self.shuttlingGraph.currentPositionNameObservable.subscribe( self.onCurrentPositionEvent )
        self.shuttlingGraph.graphChangedObservable.subscribe( self.setupGraphDependent )
        self.setupGraphDependent()
        self.uploadDataButton.clicked.connect( self.onUploadData )
        self.uploadEdgesButton.clicked.connect( self.onUploadEdgesButton )
        restoreGuiState(self, self.config.get('VoltageAdjust.GuiState'))
        self.shuttlingGraph.currentPositionNameObservable.subscribe( self.setCurrentPositionLabel )
        self.destinationComboBox.currentIndexChanged[QtCore.QString].connect( self.onShuttleSequence )
        
    def onUploadData(self):
        self.voltageBlender.writeData()
    
    def onUploadEdgesButton(self):
        self.writeShuttleLookup()
        
    def writeShuttleLookup(self):
        self.voltageBlender.writeShuttleLookup(self.shuttlingGraph)
    
    def setupGraphDependent(self):
        updateComboBoxItems( self.destinationComboBox, self.shuttlingGraph.nodes() )

    def onCurrentPositionEvent(self, event):
        self.currentPositionLabel.setText( firstNotNone(self.shuttlingGraph.currentPositionName, "") )           

    def onShuttleSequence(self, destination, cont=False):
        destination = str(destination)
        logger = logging.getLogger(__name__)
        logger.info( "ShuttleSequence" )
        path = self.shuttlingGraph.shuttlePath(None, destination)
        if path:
            self.shuttleOutput.emit( path, cont )

    def onShuttlingDone(self,currentline):
        self.lineBox.setValue(currentline)
        self.adjust.line = currentline

    def addShuttlingEdge(self):
        edge = ShuttleEdge()
        self.shuttleEdgeTableModel.add(edge)

    def removeShuttlingEdge(self):
        for index in sorted(unique([ i.row() for i in self.edgeTableView.selectedIndexes() ]),reverse=True):
            self.shuttleEdgeTableModel.remove(index)
        
    def onValueChanged(self, attribute, value):
        setattr(self.adjust,attribute,value.toval() if isinstance( value, magnitude.Magnitude) else value) 
        self.updateOutput.emit(self.adjust)
    
    def setLine(self, line):
        self.shuttlingGraph.setPosition( line )
        
    def setCurrentPositionLabel(self, event ):
        self.currentPositionLabel.setText( event.text )
    
    def saveConfig(self):
        self.config[self.configname] = self.settings
        self.config['VoltageAdjust.GuiState'] = saveGuiState(self)
        