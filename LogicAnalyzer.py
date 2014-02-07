import PyQt4.uic
from modules.enum import enum
import logging 
from pens import penList
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
from pyqtgraph.graphicsItems.TextItem import TextItem
from itertools import chain, izip
from modules.Utility import flatten
from LogicAnalyzerSignalTableModel import LogicAnalyzerSignalTableModel

from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
from pycallgraph import Config

import cProfile

def do_cprofile(func):
    def profiled_func(*args, **kwargs):
        profile = cProfile.Profile()
        try:
            profile.enable()
            result = func(*args, **kwargs)
            profile.disable()
            return result
        finally:
            profile.print_stats()
    return profiled_func

def get_number():
    for x in xrange(5000000):
        yield x


Form, Base = PyQt4.uic.loadUiType(r'ui\LogicAnalyzer.ui')

class Settings:
    def __init__(self):
        self.numChannels = 38
        self.height = 0.75
        self.scaling = 0.000020
        self.numTriggerChannels = 7
        self.triggerWidth = 0.0001   # only rising edge counts
        self.numAuxChannels = 4
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault('numChannels', 38 )
        self.__dict__.setdefault('height', 0.75 )
        self.__dict__.setdefault('scaling', 0.000020 )
        self.__dict__.setdefault('numTriggerChannels', 7 )
        self.__dict__.setdefault('triggerWidth', 0.0001 )
        self.__dict__.setdefault('numAuxChannels', 4 )
        self.numTriggerChannels = 7
                

class LogicAnalyzer(Form, Base ):
    OpStates = enum('stopped','running','single','idle') #added idle in response to exception
    def __init__(self,config,pulserHardware,channelNameData, parent=None):
        Form.__init__(self)
        Base.__init__(self,parent)
        self.state = self.OpStates.idle
        self.config = config
        self.pulserHardware = pulserHardware
        self.settings = self.config.get( "LogicAnalyzerSettings", Settings() )
        self.pulserHardware.logicAnalyzerDataAvailable.connect( self.onData )
        self.curveBundle = None
        self.curveTriggerBundle = None
        self.xTrigger = None
        self.yTrigger = None
        self.yTriggerBundle = None
        self.xData = None
        self.yData = None
        self.yDataBundle = None
        self.xAuxData = None
        self.yAuxData = None
        self.yAuxDataBundle = None
        self.curveAuxBundle = None
        self.channelNameData = channelNameData
        self.lastEnabledChannels = None
        self.textItems = list()

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        self.actionRun.triggered.connect( self.onRun )
        self.actionStop.triggered.connect( self.onStop )
        self.actionSingle.triggered.connect( self.onSingle )
        self.graphicsView = self.graphicsLayout.graphicsView
        self.signalTableModel = LogicAnalyzerSignalTableModel(self.config, self.channelNameData)
        self.signalTableView.setModel(self.signalTableModel)
        self.signalTableView.resizeColumnsToContents()
        if 'LogicAnalyzer.State' in self.config:
            self.restoreState(self.config['LogicAnalyzer.State'])
        self.signalTableModel.enableChanged.connect( self.refresh )
        
#     def onData(self, logicData ):
#         config = Config(max_depth=5)
#         with PyCallGraph(output=GraphvizOutput()):
#             self.onDataProfile(logicData)
        
    @do_cprofile
    def onData(self, logicData):
        self.logicData = logicData
        offset = 0
        if logicData.data:
            self.xData, self.yData = zip( *logicData.data )
            self.xData = [ x * self.settings.scaling for x in self.xData ]  # convert tuple to list
            self.xData.append( logicData.stopMarker * self.settings.scaling )
            self.yDataBundle = [list() for _ in range(self.settings.numChannels)]
            for i in range(self.settings.numChannels):
                if self.signalTableModel.enabledList[i]:
                    for value in self.yData:
                        self.yDataBundle[i].append(offset+self.settings.height if value&(1<<i) else offset )
                    offset += 1
        nextChannel = self.settings.numChannels
        if logicData.auxData:
            self.xAuxData, self.yAuxData = zip( *logicData.auxData )
            self.xAuxData = [ x * self.settings.scaling for x in self.xAuxData ]  # convert tuple to list
            self.xAuxData.append( logicData.stopMarker * self.settings.scaling )
            self.yAuxDataBundle = [list() for _ in range(self.settings.numAuxChannels)]
            for i in range(self.settings.numAuxChannels):
                if self.signalTableModel.enabledList[nextChannel+i]:
                    for value in self.yAuxData:
                        self.yAuxDataBundle[i].append(offset+self.settings.height if value&(1<<i) else offset )
                    offset += 1
        nextChannel += self.settings.numAuxChannels
        if logicData.trigger:
            self.xTrigger, self.yTrigger = zip( *logicData.trigger )
            self.xTrigger = list(flatten([ (x* self.settings.scaling,x* self.settings.scaling+self.settings.triggerWidth)  for x in self.xTrigger ]))  # convert tuple to list
            self.yTrigger = list(flatten([ (y,0) for y in self.yTrigger ]))
            self.xTrigger.append( logicData.stopMarker * self.settings.scaling )
            self.yTriggerBundle = [list() for _ in range(self.settings.numTriggerChannels)]
            for i in range(self.settings.numTriggerChannels):
                if self.signalTableModel.enabledList[nextChannel+i]:
                    for value in self.yTrigger:
                        self.yTriggerBundle[i].append(offset+self.settings.height if value&(1<<i) else offset )
                    offset += 1
        self.plotData()
        if self.state==self.OpStates.single:
            self.setStatusStopped()
           
    def plotData(self):
        offset = 0
        if self.lastEnabledChannels and self.lastEnabledChannels!=self.signalTableModel.enabledList:
            for curve in self.curveBundle + self.curveAuxBundle + self.curveTriggerBundle:
                if curve:
                    self.graphicsView.removeItem(curve)
                self.curveBundle = None
                self.curveAuxBundle = None
                self.curveTriggerBundle = None
            if self.textItems:
                for item in self.textItems:
                    self.graphicsView.removeItem(item)
        if self.yDataBundle:
            if self.curveBundle is None:
                self.curveBundle = list()
                for i, yData in enumerate(self.yDataBundle):
                    if yData:
                        curve = PlotCurveItem(self.xData, yData, stepMode=True, fillLevel=offset, brush=penList[1][4], pen=penList[1][0]) 
                        self.graphicsView.addItem( curve )
                        self.curveBundle.append( curve )
                        textItem = TextItem( self.signalTableModel.primaryChannelName(i), anchor=(1,1), color=(0,0,0) )
                        textItem.setPos( 0, offset )
                        self.graphicsView.addItem(textItem)
                        self.textItems.append(textItem)
                        offset += 1
                    else:
                        self.curveBundle.append( None )
            else:
                for curve, yData in zip(self.curveBundle, self.yDataBundle):
                    if yData:
                        if curve:
                            curve.setData(x=self.xData,y=yData)
                            
        nextChannel = self.settings.numChannels
        if self.yAuxDataBundle:
            if self.curveAuxBundle is None:
                self.curveAuxBundle = list()
                for i, yAuxData in enumerate(self.yAuxDataBundle):
                    if yAuxData:
                        curve = PlotCurveItem(self.xAuxData, yAuxData, stepMode=True, fillLevel=offset, brush=penList[2][4], pen=penList[2][0])
                        self.graphicsView.addItem( curve )
                        self.curveBundle.append( curve )
                        textItem = TextItem( self.signalTableModel.auxChannelName(i), anchor=(1,1), color=(0,0,0) )
                        textItem.setPos( 0, offset )
                        self.graphicsView.addItem(textItem)
                        self.textItems.append(textItem)
                        offset += 1 
                    else:
                        self.curveBundle.append( None )
                        
            else:
                for curve, yData in zip(self.curveBundle, self.yDataBundle):
                    if yData:
                        if curve:
                            curve.setData(x=self.xData,y=yData)
        nextChannel += self.settings.numAuxChannels
        if self.yTriggerBundle:
            if self.curveTriggerBundle is None:
                self.curveTriggerBundle = list()
                for i, yTrigger in enumerate(self.yTriggerBundle):
                    if yTrigger:
                        curve = PlotCurveItem(self.xTrigger, yTrigger, stepMode=True, fillLevel=offset, brush=penList[3][4], pen=penList[3][0]) 
                        self.graphicsView.addItem( curve )
                        self.curveTriggerBundle.append( curve )
                        textItem = TextItem( self.signalTableModel.triggerChannelName(i), anchor=(1,1), color=(0,0,0) )
                        textItem.setPos( 0, offset )
                        self.graphicsView.addItem(textItem)
                        self.textItems.append(textItem)
                        offset += 1 
                    else:
                        self.curveTriggerBundle.append( None )
                        
            else:
                for curve, yTrigger in zip(self.curveTriggerBundle, self.yTriggerBundle):
                    if yTrigger:
                        if curve:
                            curve.setData(x=self.xTrigger,y=yTrigger)
        self.lastEnabledChannels = list( self.signalTableModel.enabledList )
             
    def refresh(self):
        self.onData(self.logicData)
                
    def onRun(self):
        logger = logging.getLogger(__name__)
        logger.debug("Starting Logic Analyzer")
        self.pulserHardware.enableLogicAnalyzer(True)
        self.setStatusRunning()
        
    def onStop(self):
        logger = logging.getLogger(__name__)
        logger.debug("Stopping Logic Analyzer")
        self.pulserHardware.enableLogicAnalyzer(False)
        self.setStatusStopped()
        
    def onSingle(self):
        logger = logging.getLogger(__name__)
        logger.debug("Logic Analyzer Single Shot")
        self.pulserHardware.enableLogicAnalyzer(False)
        self.pulserHardware.logicAnalyzerTrigger()
        self.setStatusSingle()
        
    def setStatusStopped(self):
        self.state = self.OpStates.idle
        self.statusBar.showMessage("Stopped")
        
    def setStatusRunning(self):
        self.state = self.OpStates.idle
        self.statusBar.showMessage("Running")

    def setStatusSingle(self):
        self.state = self.OpStates.idle
        self.statusBar.showMessage("Single shot")
        
    def saveConfig(self):
        self.config["LogicAnalyzerSettings"] = self.settings
        self.signalTableModel.saveConfig()
        self.config['LogicAnalyzer.State'] = self.saveState()

    
    def onClose(self):
        pass

    def closeEvent(self,e):
        self.onClose()
        
