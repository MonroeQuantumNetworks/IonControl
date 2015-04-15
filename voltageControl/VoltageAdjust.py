# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import functools
import logging

from PyQt4 import QtCore
import PyQt4.uic

from voltageControl.ShuttleEdgeTableModel import ShuttleEdgeTableModel
from voltageControl.ShuttlingDefinition import ShuttlingGraph, ShuttleEdge
from modules.PyqtUtility import updateComboBoxItems, BlockSignals
from modules.firstNotNone import firstNotNone
from modules.Utility import unique
from modules.GuiAppearance import restoreGuiState, saveGuiState
from xml.etree import ElementTree 
from xml.dom import minidom
import os.path
from modules.Expression import Expression
from gui.ExpressionValue import ExpressionValue
from modules.magnitude import mg
import re


VoltageAdjustForm, VoltageAdjustBase = PyQt4.uic.loadUiType(r'ui\VoltageAdjust.ui')
ShuttlingEdgeForm, ShuttlingEdgeBase = PyQt4.uic.loadUiType(r'ui\ShuttlingEdge.ui')

    
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
        self.shuttlingRoute = ""
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault('shuttlingRoute',"")
        
class ShuttlingException(Exception):
    pass

def triplet_iterator(iterable):
    i = 0
    while i+2<len(iterable):
        yield iterable[i:i+3]
        i += 2
    
class VoltageAdjust(VoltageAdjustForm, VoltageAdjustBase ):
    updateOutput = QtCore.pyqtSignal(object)
    shuttleOutput = QtCore.pyqtSignal(object, object)
    
    def __init__(self, config, voltageBlender, globalDict, parent=None):
        VoltageAdjustForm.__init__(self)
        VoltageAdjustBase.__init__(self,parent)
        self.config = config
        self.configname = 'VoltageAdjust.Settings'
        self.settings = self.config.get(self.configname,Settings())
        self.settings.adjust.globalDict = globalDict
        self.adjust = self.settings.adjust
        self.shuttlingGraph = ShuttlingGraph()
        self.voltageBlender = voltageBlender
        self.shuttlingDefinitionFile = None

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
        self.shuttleEdgeTableModel = ShuttleEdgeTableModel(self.config, self.shuttlingGraph)
        self.edgeTableView.setModel(self.shuttleEdgeTableModel)
        self.currentPositionLabel.setText( firstNotNone( self.shuttlingGraph.currentPositionName, "" ) )
        self.shuttlingGraph.currentPositionObservable.subscribe( self.onCurrentPositionEvent )
        self.shuttlingGraph.graphChangedObservable.subscribe( self.setupGraphDependent )
        self.setupGraphDependent()
        self.uploadDataButton.clicked.connect( self.onUploadData )
        self.uploadEdgesButton.clicked.connect( self.onUploadEdgesButton )
        restoreGuiState(self, self.config.get('VoltageAdjust.GuiState'))
        self.destinationComboBox.currentIndexChanged[QtCore.QString].connect( self.onShuttleSequence )
        self.shuttlingRouteEdit.setText( " ".join(self.settings.shuttlingRoute) )
        self.shuttlingRouteEdit.editingFinished.connect( self.onSetShuttlingRoute )
        self.shuttlingRouteButton.clicked.connect( self.onShuttlingRoute )
        
    def onSetShuttlingRoute(self):
        self.settings.shuttlingRoute = re.split(r'\s*(-|,)\s*', str(self.shuttlingRouteEdit.text()) )
        
    def onShuttlingRoute(self):
        if self.settings.shuttlingRoute:
            path = list()
            for start, transition, stop in triplet_iterator(self.settings.shuttlingRoute):
                if transition=="-":
                    path.extend( self.shuttlingGraph.shuttlePath(start, stop) )
            if path:
                self.shuttleOutput.emit( path, False )                               
        
    def onUploadData(self):
        self.voltageBlender.writeData()
    
    def onUploadEdgesButton(self):
        self.writeShuttleLookup()
        
    def writeShuttleLookup(self):
        self.voltageBlender.writeShuttleLookup(self.shuttlingGraph)
    
    def setupGraphDependent(self):
        updateComboBoxItems( self.destinationComboBox, sorted(self.shuttlingGraph.nodes()) )

    def onCurrentPositionEvent(self, event):
        with BlockSignals(self.lineBox):
            self.adjust.line = event.line
            self.lineBox.setValue( self.adjust.line )          
        self.currentPositionLabel.setText( firstNotNone(event.text, "") )           

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
        edge = self.shuttlingGraph.getValidEdge()
        self.shuttleEdgeTableModel.add(edge)

    def removeShuttlingEdge(self):
        for index in sorted(unique([ i.row() for i in self.edgeTableView.selectedIndexes() ]),reverse=True):
            self.shuttleEdgeTableModel.remove(index)
        
    def onExpressionChanged(self, attribute, value):
        setattr(self.adjust,attribute,value) 
        self.updateOutput.emit(self.adjust)
    
    def setLine(self, line):
        self.shuttlingGraph.setPosition( line )
        
    def setCurrentPositionLabel(self, event ):
        self.currentPositionLabel.setText( event.text )
    
    def saveConfig(self):
        self.config[self.configname] = self.settings
        self.config['VoltageAdjust.GuiState'] = saveGuiState(self)
        root = ElementTree.Element('VoltageAdjust')
        self.shuttlingGraph.toXmlElement(root)
        if self.shuttlingDefinitionFile:
            with open(self.shuttlingDefinitionFile,'w') as f:
                f.write(self.prettify(root))
            
    def prettify(self, elem):
        """Return a pretty-printed XML string for the Element.
        """
        rough_string = ElementTree.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def loadShuttleDef(self, filename):
        if filename is not None:
            self.shuttlingDefinitionFile = filename
            if os.path.exists(filename):
                tree = ElementTree.parse(filename)
                root = tree.getroot()
                
                # load pulse definition
                ShuttlingGraphElement = root.find("ShuttlingGraph")
                self.shuttlingGraph = ShuttlingGraph.fromXmlElement(ShuttlingGraphElement)
                self.shuttleEdgeTableModel.setShuttlingGraph(self.shuttlingGraph)
                self.currentPositionLabel.setText( firstNotNone( self.shuttlingGraph.currentPositionName, "" ) )
                self.shuttlingGraph.currentPositionObservable.subscribe( self.onCurrentPositionEvent )
                self.shuttlingGraph.graphChangedObservable.subscribe( self.setupGraphDependent )
                self.setupGraphDependent()
        