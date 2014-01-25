import PyQt4.uic
from PyQt4 import QtCore, QtGui
from modules.enum import enum
import logging 

Form, Base = PyQt4.uic.loadUiType(r'ui\LogicAnalyzer.ui')

class Settings:
    pass

class LogicAnalyzer(Form, Base ):
    dataAvailable = QtCore.pyqtSignal( object )
    OpStates = enum('idle','running','single')
    def __init__(self,config,pulserHardware,parent=None):
        Form.__init__(self)
        Base.__init__(self,parent)
        self.state = self.OpStates.idle
        self.config = config
        self.pulserHardware = pulserHardware
        self.settings = self.config.get( "LogicAnalyzerSettings", Settings() )

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        self.actionRun.triggered.connect( self.onRun )
        self.actionStop.triggered.connect( self.onStop )
        self.actionSingle.triggered.connect( self.onSingle )
        
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
        pass
        
    def saveConfig(self):
        self.config["LogicAnalyzerSettings"] = self.settings
    
    def onClose(self):
        self.autoLoad.onClose()

    def closeEvent(self,e):
        self.onClose()
        
