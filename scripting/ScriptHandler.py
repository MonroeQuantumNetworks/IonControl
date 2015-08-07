'''
Created on Aug 6, 2015

@author: jmizrahi
'''

from PyQt4 import QtCore
import os
import logging
import traceback
from modules import magnitude
from Script import ScriptException

class ScriptHandler:
    def __init__(self, script, experimentUi):
        #self.experimentUi = experimentUi
        self.experimentUi = experimentUi
        self.globalVariablesUi = experimentUi.globalVariablesUi
        self.scanControlWidget = experimentUi.tabDict['Scan'].scanControlWidget
        self.evaluationControlWidget = experimentUi.tabDict['Scan'].evaluationControlWidget
        self.analysisControlWidget = experimentUi.tabDict['Scan'].analysisControlWidget
        
        self.script = script
        
        #status signals
        self.script.locationSignal.connect( self.onLocation )
        self.script.exceptionSignal.connect( self.onException )
        self.script.consoleSignal.connect(self.onConsoleSignal)

        #action signals
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
                error, message = func(self, *args, **kwds)
                
                if error and message:
                    logger.error(message)
                    self.writeToConsole(message, error=True)
                    raise ScriptException(message)
                
                elif error and (not message):
                    raise ScriptException('')
                
                elif (not error) and message:
                    logger.debug(message)
                    self.writeToConsole(message)
                    
            except Exception as e:
                with QtCore.QMutexLocker(self.script.mutex):
                    self.script.exception = e
                    logger.error(traceback.print_exc())
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
        doesNotExist = name not in self.globalVariablesUi.keys()
        if doesNotExist:
            self.globalVariablesUi.model.addVariable(name)
            message = "Global variable {0} created\n".format(name)
        else:
            message = "Global variable {0} already exists\n".format(name)
        self.globalVariablesUi.model.update([('Global', name, magValue)])
        message +=  "Global variable {0} set to {1} {2}".format(name, value, unit)
        error = False
        return (error, message)

    @QtCore.pyqtSlot(str, float, str)
    @scriptCommand
    def onSetGlobal(self, name, value, unit):
        """Set global 'name' to 'value, unit'"""
        name = str(name) #signal is passed as a QString
        value = float(value)
        unit = str(unit)
        magValue = magnitude.mg(value, unit)
        doesNotExist = name not in self.globalVariablesUi.keys()
        if doesNotExist:
            message = "Global variable {0} does not exist.".format(name)
            error = True
        else:
            self.globalVariablesUi.model.update([('Global', name, magValue)])
            message = "Global variable {0} set to {1} {2}".format(name, value, unit)
            error = False
        return (error, message)
    
    @QtCore.pyqtSlot()
    @scriptCommand
    def onStartScan(self):
        """Start the scan"""
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.scanRunning = True
        self.experimentUi.actionStart.trigger()
        #return "Scan started with scan = {0}, evaluation = {1}".format()

    @QtCore.pyqtSlot()
    @scriptCommand
    def onPauseScan(self):
        self.experimentUi.actionPause.trigger()
        error = False
        message = "Scan paused"
        return (error, message)
        
    @QtCore.pyqtSlot()
    @scriptCommand
    def onStopScan(self):
        self.experimentUi.actionStop.trigger()
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.scanRunning = False
        error = False
        message = "Scan stopped"
        return (error, message)
        
    @QtCore.pyqtSlot()
    @scriptCommand
    def onAbortScan(self):
        self.experimentUi.actionAbort.trigger()
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.scanRunning = False
        error = False
        message = "Scan aborted"
        return (error, message)

    @QtCore.pyqtSlot(str)
    @scriptCommand
    def onSetScan(self, name):
        name = str(name)
        doesNotExist = self.scanControlWidget.comboBox.findText(name)==-1
        if doesNotExist:
            message = "Scan {0} does not exist.".format(name)
            error = True
        else:
            self.scanControlWidget.loadSetting(name)
            message = "Scan set to {0}".format(name)
            error = False
        return (error, message)
    
    @QtCore.pyqtSlot(str)
    @scriptCommand
    def onSetEvaluation(self, name):
        name = str(name)
        doesNotExist = self.evaluationControlWidget.comboBox.findText(name)==-1
        if doesNotExist:
            message = "Evaluation {0} does not exist.".format(name)
            error = True
        else:
            self.evaluationControlWidget.loadSetting(name)
            message = "Evaluation set to {0}".format(name)
            error = False
        return (error, message)
    
    @QtCore.pyqtSlot(str)
    @scriptCommand
    def onSetAnalysis(self, name):
        name = str(name)
        doesNotExist = name not in self.analysisControlWidget.analysisDefinitionDict
        if doesNotExist:
            message = "Analysis {0} does not exist.".format(name)
            error = True
        else:
            self.analysisControlWidget.onLoadAnalysisConfiguration(name)
            message = "Analysis set to {0}".format(name)
            error = False
        return (error, message)
    
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
        message = 'script paused'
        error = False
        return (error, message)

    @QtCore.pyqtSlot()
    @scriptCommand
    def onStopScriptFromScript(self):
        self.onStopScript()
        message = 'script stopped'
        error = False
        return (error, message)        
    
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

    def onRepeat(self, repeat):
        """Runs when repeat button is clicked. Set repeat variable."""
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.repeat = repeat

    def onSlow(self, slow):
        """Runs when slow button is clicked. Set slow variable."""
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.slow = slow

    @QtCore.pyqtSlot(str, bool, str)
    def onConsoleSignal(self, message, error, color):
        """Runs when script emits a console signal. Writes message to console."""
        self.writeToConsole(message, error=error, color=color)
    
    @QtCore.pyqtSlot(str, str)
    def onException(self, message, trace):
        """Runs when script emits exception signal. Highlights error."""
        logger = logging.getLogger(__name__)
        message = str(message)
        trace = str(trace)
        logger.error(trace)
        self.writeToConsole(trace, error=True)
        self.experimentUi.scriptingWindow.markError(self.currentLines, message)
    
    @QtCore.pyqtSlot(list)        
    def onLocation(self, locs):
        """Mark where the script currently is"""
        logger = logging.getLogger(__name__)
        self.currentLines = []
        if locs:
            self.currentLines = [loc[1] for loc in locs]
            for loc in locs:
                message = "Executing {0} in {1} at line {2}".format( loc[3], os.path.basename(loc[0]), loc[1] )
                logger.debug(message)
                self.writeToConsole(message, False)
        else: #This should never execute
            message = "onLocation called while not executing script"
            logger.warning(message)
            self.writeToConsole(message, True)
        self.experimentUi.scriptingWindow.markLocation(self.currentLines)
        
    def writeToConsole(self, message, error=False, color=''):
        """write a message to the console."""
        self.experimentUi.scriptingWindow.writeToConsole(message, error, color)
