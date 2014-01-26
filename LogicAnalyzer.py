import PyQt4.uic
from PyQt4 import QtCore, QtGui
from modules.enum import enum
import logging 
from pens import penList
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem

Form, Base = PyQt4.uic.loadUiType(r'ui\LogicAnalyzer.ui')

class Settings:
    pass

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

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        self.actionRun.triggered.connect( self.onRun )
        self.actionStop.triggered.connect( self.onStop )
        self.actionSingle.triggered.connect( self.onSingle )
        self.graphicsView = self.graphicsLayout.graphicsView
        
    def onData(self, logicData ):
        if logicData.data:
            self.xData, self.yData = zip( *logicData.data )
            self.xData = [ x * 0.000020 for x in self.xData ]  # convert tuple to list
            self.xData.append( logicData.stopMarker * 0.000020 )
            self.yDataBundle = [list() for _ in range(32)]
            for value in self.yData:
                for i in range(32):
                    self.yDataBundle[i].append(i+0.75 if value&(1<<i) else i )
            self.plotData()
            
    def plotData(self):
        if self.curveBundle is None:
            self.curveBundle = list()
            for i, yData in enumerate(self.yDataBundle):
                curve = PlotCurveItem(self.xData, yData, stepMode=True, fillLevel=i, brush=penList[1][4], pen=penList[1][0]) 
                self.graphicsView.addItem( curve )
                self.curveBundle.append( curve )
        else:
            for curve, yData in zip(self.curveBundle, self.yDataBundle):
                curve.setData(x=self.xData,y=yData)
                
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
        
