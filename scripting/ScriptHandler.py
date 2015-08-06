'''
Created on Aug 6, 2015

@author: jmizrahi
'''

from PyQt4 import QtCore
import logging
import traceback
from modules import magnitude
from Script import ScriptException

class ScriptHandler:
    def __init__(self, script, experimentUi):
        self.experimentUi = experimentUi
        self.script = script
        
        self.script.locationSignal.connect( self.onLocation )
        self.script.exceptionSignal.connect( self.onException )
        self.script.consoleSignal.connect(self.onConsoleSignal)

        self.script.setGlobalSignal.connect(self.onSetGlobal)
        self.script.addGlobalSignal.connect(self.onAddGlobal)
        self.script.pauseScriptSignal.connect(self.onPauseScriptFromScript)
        self.script.stopScriptSignal.connect(self.onStopScriptFromScript)
        self.script.startScanSignal.connect(self.onStartScan)
        self.script.setScanSignal.connect(self.onSetScan)
        self.script.setEvaluationSignal.connect(self.onSetEvaluation)
        self.script.setAnalysisSignal.connect(self.onSetAnalysis)
        self.script.plotPointSignal.connect(self.onPlotPoint)
        self.script.addPlotSignal.connect(self.onAddPlot)
        self.script.pauseScanSignal.connect(self.onPauseScan)
        self.script.stopScanSignal.connect(self.onStopScan)
        self.script.abortScanSignal.connect(self.onAbortScan)

    def scriptCommand(func):#@NoSelf
        """Decorator for script commands. 
        
        Catches exceptions, sets the script exception variables, and wakes the script after the
        specified action has been completed.
        """
        def baseScriptCommand(self, *args, **kwds):
            logger = logging.getLogger(__name__)
            try:
                message = func(self, *args, **kwds)
                if message:
                    logger.debug(message)
                    self.writeToConsole(message)
            except Exception as e:
                with QtCore.QMutexLocker(self.script.mutex):
                    self.script.exception = e
                    print traceback.print_exc()
            finally:
                self.script.commandWait.wakeAll()
        baseScriptCommand.func_name = func.func_name
        baseScriptCommand.func_doc = func.func_doc
        return baseScriptCommand
    
    @QtCore.pyqtSlot(str, float, str)
    @scriptCommand
    def onAddGlobal(self, name, value, unit):
        """Add a global 'name' and set it to 'value, unit'"""
        name = str(name) #signal is passed as a QString
        value = float(value)
        unit = str(unit)
        magValue = magnitude.mg(value, unit)
        doesNotExist = name not in self.experimentUi.globalVariablesUi.keys()
        message1 = ''
        if doesNotExist:
            self.experimentUi.globalVariablesUi.model.addVariable(name)
            message1 = "Global variable {0} created\n".format(name)
        self.experimentUi.globalVariablesUi.model.update([('Global', name, magValue)])
        message2 =  "Global variable {0} set to {1} {2}".format(name, value, unit)
        return message1+message2

    @QtCore.pyqtSlot(str, float, str)
    @scriptCommand
    def onSetGlobal(self, name, value, unit):
        """Set global 'name' to 'value, unit'"""
        name = str(name) #signal is passed as a QString
        value = float(value)
        unit = str(unit)
        logger = logging.getLogger(__name__)
        magValue = magnitude.mg(value, unit)
        doesNotExist = (name not in self.experimentUi.globalVariablesUi.keys())
        if doesNotExist:
            message = "Global variable {0} does not exist.".format(name)
            logger.error(message)
            self.writeToConsole(message, noError=False)
            raise ScriptException(message)
        self.experimentUi.globalVariablesUi.model.update([('Global', name, magValue)])
        return "Global variable {0} set to {1} {2}".format(name, value, unit)
    
    @QtCore.pyqtSlot()
    @scriptCommand
    def onStartScan(self):
        """Start the scan"""
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.scanRunning = True
        self.experimentUi.actionStart.trigger()
#        return "Scan started with scan = {0}, evaluation = {1}".format()

    @QtCore.pyqtSlot()
    @scriptCommand
    def onPauseScan(self):
        self.experimentUi.actionPause.trigger()
        return "Scan paused"
        
    @QtCore.pyqtSlot()
    @scriptCommand
    def onStopScan(self):
        self.experimentUi.actionStop.trigger()
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.scanRunning = False
        return "Scan stopped"
        
    @QtCore.pyqtSlot()
    @scriptCommand
    def onAbortScan(self):
        self.experimentUi.actionAbort.trigger()
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.scanRunning = False
        return "Scan aborted"

    @QtCore.pyqtSlot(str)
    @scriptCommand
    def onSetScan(self, name):
        pass
    
    @QtCore.pyqtSlot(str)
    @scriptCommand
    def onSetEvaluation(self, name):
        pass
    
    @QtCore.pyqtSlot(str)
    @scriptCommand
    def onSetAnalysis(self, name):
        pass
    
    @QtCore.pyqtSlot(float, float, str, str, bool)
    @scriptCommand
    def onPlotPoint(self, x, y, plotName, traceName, save):
        pass
    
    @QtCore.pyqtSlot(str)
    @scriptCommand
    def onAddPlot(self, name):
        pass
    
    @QtCore.pyqtSlot()
    @scriptCommand
    def onPauseScriptFromScript(self):
        self.onPauseScript(True)
        return 'script paused'

    @QtCore.pyqtSlot()
    @scriptCommand
    def onStopScriptFromScript(self):
        self.onStopScript()
        return 'script stopped'        
    
    @QtCore.pyqtSlot(list)        
    def onLocation(self, currentLines):
        """Mark where the script currently is"""
        self.experimentUi.scriptingWindow.markLocation(currentLines)

    def onStartScript(self):
        """Runs when start script button clicked. Starts the script and disables some aspects of the script GUI"""
        if not self.script.isRunning():
            with QtCore.QMutexLocker(self.script.mutex):
                self.script.paused = False
                self.script.stopped = False
                self.script.exceptionLine = -1
                self.script.exception = None
                self.script.start()

    def onPauseScript(self, paused):
        """Runs when pause script button clicked. Sets paused variable and wakes up script if unpaused."""
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.paused = paused
            if not paused:
                self.script.pauseWait.wakeAll()
        
    def onStopScript(self):
        """Runs when stop script button is clicked. Sets stopped variable and wakes up all waitConditions.""" 
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.stopped = True
            self.script.paused = False
            self.script.repeat = False
            self.script.commandWait.wakeAll()
            self.script.pauseWait.wakeAll()
            self.script.scanWait.wakeAll()
            self.script.dataWait.wakeAll()
            
    def onPauseScriptAndScan(self):
        """Runs when pause script and scan button is clicked."""
        self.onPauseScript(True)
        self.experimentUi.actionPause.trigger()
        
    def onStopScriptAndScan(self):
        """Runs when stop script and scan button is clicked."""
        self.onStopScript()
        self.experimentUi.actionStop.trigger()

    @QtCore.pyqtSlot(str, bool, str)
    def onConsoleSignal(self, message, noError, color):
        """Runs when script emits a console signal. Writes message to console."""
        self.writeToConsole(message, noError=noError, color=color)
    
    @QtCore.pyqtSlot(int, str)
    def onException(self, currentLines, message):
        """Runs when script emits exception signal. Highlights error."""
        self.experimentUi.scriptingWindow.markError(currentLines, message)
                
    def onRepeat(self, repeat):
        """Runs when repeat button is clicked. Set repeat variable."""
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.repeat = repeat

    def onSlow(self, slow):
        """Runs when slow button is clicked. Set slow variable."""
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.slow = slow

    def writeToConsole(self, message, noError=True, color=''):
        """write a message to the console."""
        self.experimentUi.scriptingWindow.writeToConsole(message, noError, color)