import PyQt4.uic
from modules.enum import enum
import logging 
from pens import penList
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
from itertools import chain, izip
from modules.Utility import flatten

Form, Base = PyQt4.uic.loadUiType(r'ui\LogicAnalyzer.ui')

class Settings:
    def __init__(self):
        self.numChannels = 38
        self.height = 0.75
        self.scaling = 0.000020
        self.numTriggerChannels = 6
        self.triggerWidth = 0.0001   # only rising edge counts
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault('numChannels', 38 )
        self.__dict__.setdefault('height', 0.75 )
        self.__dict__.setdefault('scaling', 0.000020 )
        self.__dict__.setdefault('numTriggerChannels', 6 )
        self.__dict__.setdefault('triggerWidth', 0.0001 )
                

class LogicAnalyzer(Form, Base ):
    OpStates = enum('idle','running','single')
    def __init__(self,config,pulserHardware,parent=None):
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

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        self.actionRun.triggered.connect( self.onRun )
        self.actionStop.triggered.connect( self.onStop )
        self.actionSingle.triggered.connect( self.onSingle )
        self.graphicsView = self.graphicsLayout.graphicsView
        
    def onData(self, logicData ):
        if logicData.data:
            self.xData, self.yData = zip( *logicData.data )
            self.xData = [ x * self.settings.scaling for x in self.xData ]  # convert tuple to list
            self.xData.append( logicData.stopMarker * self.settings.scaling )
            self.yDataBundle = [list() for _ in range(self.settings.numChannels)]
            for value in self.yData:
                for i in range(self.settings.numChannels):
                    self.yDataBundle[i].append(i+self.settings.height if value&(1<<i) else i )
        if logicData.trigger:
            self.xTrigger, self.yTrigger = zip( *logicData.trigger )
            self.xTrigger = list(flatten([ (x* self.settings.scaling,x* self.settings.scaling+self.settings.triggerWidth)  for x in self.xTrigger ]))  # convert tuple to list
            self.yTrigger = flatten([ (y,0) for y in self.yTrigger ])
            self.xTrigger.append( logicData.stopMarker * self.settings.scaling )
            self.yTriggerBundle = [list() for _ in range(self.settings.numTriggerChannels)]
            for value in self.yTrigger:
                for i in range(self.settings.numTriggerChannels):
                    self.yTriggerBundle[i].append(self.settings.numChannels+i+self.settings.height if value&(1<<i) else self.settings.numChannels+i )
        self.plotData()
           
    def plotData(self):
        if self.yDataBundle:
            if self.curveBundle is None:
                self.curveBundle = list()
                for i, yData in enumerate(self.yDataBundle):
                    curve = PlotCurveItem(self.xData, yData, stepMode=True, fillLevel=i, brush=penList[1][4], pen=penList[1][0]) 
                    self.graphicsView.addItem( curve )
                    self.curveBundle.append( curve )
            else:
                for curve, yData in zip(self.curveBundle, self.yDataBundle):
                    curve.setData(x=self.xData,y=yData)
        if self.yTriggerBundle:
            if self.curveTriggerBundle is None:
                self.curveTriggerBundle = list()
                for i, yTrigger in enumerate(self.yTriggerBundle):
                    curve = PlotCurveItem(self.xTrigger, yTrigger, stepMode=True, fillLevel=i+self.settings.numChannels, brush=penList[2][4], pen=penList[2][0]) 
                    self.graphicsView.addItem( curve )
                    self.curveTriggerBundle.append( curve )
            else:
                for curve, yTrigger in zip(self.curveTriggerBundle, self.yTriggerBundle):
                    curve.setData(x=self.xTrigger,y=yTrigger)
                
    def onRun(self):
        logger = logging.getLogger(__name__)
        logger.debug("Starting Logic Analyzer")
        self.pulserHardware.enableLogicAnalyzer(True)
        
    def onStop(self):
        logger = logging.getLogger(__name__)
        logger.debug("Stopping Logic Analyzer")
        self.pulserHardware.enableLogicAnalyzer(False)
        
    def onSingle(self):
        logger = logging.getLogger(__name__)
        logger.debug("Logic Analyzer Single Shot")
        self.pulserHardware.logicAnalyzerTrigger()
        
    def saveConfig(self):
        self.config["LogicAnalyzerSettings"] = self.settings
    
    def onClose(self):
        pass

    def closeEvent(self,e):
        self.onClose()
        
