'''
Created on Jul 27, 2015

@author: jmizrahi
'''
import os
import logging
from PyQt4 import QtCore
import inspect
import traceback
import time

class ScriptException(Exception):
    pass

class Script(QtCore.QThread):
    """Encapsulates a running script together with all the scripting functions. Script executes in separate thread.
    
    Note that the script thread does not have an event loop. This means that it cannot respond to emitted signals,
    and calls like Script.quit and Script.exit do not work. Instead, the script emits signals indicating what to
    change, and then enters a QWaitCondition. The ScriptingUi responds to the signal, and tells the script to exit
    the wait condition once the action has been done. 
    """
    locationSignal = QtCore.pyqtSignal(list)  # arg: line numbers
    consoleSignal = QtCore.pyqtSignal(str, bool, str) #args: String to write, whether an error occurred, color to use
    exceptionSignal = QtCore.pyqtSignal(list, str) #arg: line numbers, exception message
    
    setGlobalSignal = QtCore.pyqtSignal(str, float, str) #args: name, value, unit
    addGlobalSignal = QtCore.pyqtSignal(str, float, str) #args: name, value, unit
    pauseScriptSignal = QtCore.pyqtSignal()
    stopScriptSignal = QtCore.pyqtSignal()
    startScanSignal = QtCore.pyqtSignal(bool) #arg: wait or don't wait for scan to finish before continuing script
    
    def __init__(self, fullname='', code='', parent=None):
        super(Script,self).__init__(parent)
        self.fullname = fullname #Full name, with path
        self.shortname = os.path.basename(fullname)
        self.code = code #The code in the script
        self.currentLines = []
        
        self.mutex = QtCore.QMutex()
        self.waitCondition = QtCore.QWaitCondition()
        self.repeat = False
        self.paused = False
        self.stopped = False
        self.slow = False
        self.scanRunning = False
        self.waitForScan = False
        self.exception = None
        
    def run(self):
        """run the script"""
        for name in scriptFunctions: #Define the script functions to be the corresponding class functions
            globals()[name] = getattr(self, name)
        logger = logging.getLogger(__name__)
        try:
            while True:
                execfile(self.fullname) #run the script
                if not self.repeat:
                    break
        except Exception as e:
            message = traceback.format_exc()
            logger.error(message)
            self.exceptionSignal.emit(self.currentLines, e.message)
            self.consoleSignal.emit(message, False, '')

    def emitLocation(self):
        """Emits a signal containing the current script location"""
        logger = logging.getLogger(__name__)
        frame = inspect.currentframe()
        stack_trace = traceback.extract_stack(frame) #Gets the full stack trace
        del frame #Getting rid of captured frames is recommended
        locs = [loc for loc in stack_trace if loc[0] == self.fullname] #Find the locations that match the script name
        if locs != []:
            self.currentLines= [loc[1] for loc in locs]
            for loc in locs:
                message = "Executing {0} in {1} at line {2}".format( loc[3], os.path.basename(loc[0]), loc[1] )
                logger.debug(message)
                self.consoleSignal.emit(message, True, '')
                self.locationSignal.emit(self.currentLines) #Emit a signal containing the script location
        else: #This should never execute
            message = "Emit location called while not executing script"
            logger.warning(message)
            self.consoleSignal.emit(message, False, '')

    def scriptFunction(func): #@NoSelf
        """Decorator for script functions.
        
        This decorator performs all the functions that are common to all the script functions. It checks
        whether the script has been stopped or paused, and emits the current location in the script. Once
        the function has executed, it waits to be told to continue by the main GUI. Exceptions that occur
        during execution are sent back to the script thread and raised here."""
        def baseScriptFunction(self, *args, **kwds):
            with QtCore.QMutexLocker(self.mutex): #Acquire mutex before inspecting any variables
                if not self.stopped: #if stopped, don't do anything
                    if self.paused or (self.scanRunning and self.waitForScan): #if paused or waiting on scan, wait on waitCondition
                        self.waitCondition.wait(self.mutex) #This releases the mutex and waits until the waitCondition is woken
                    self.emitLocation()
                    if self.slow:
                        self.mutex.unlock()
                        time.sleep(0.4)
                        self.mutex.lock() 
                    func(self, *args, **kwds)
                    self.waitCondition.wait(self.mutex)
                    if self.exception:
                        raise self.exception
        baseScriptFunction.isScriptFunction = True
        baseScriptFunction.func_name = func.func_name
        baseScriptFunction.func_doc = func.func_doc
        return baseScriptFunction

    @scriptFunction
    def setGlobal(self, name, value, unit):
        """set the global "name" to "value" with the given unit. This is equivalent to typing in a value+unit in the globals GUI."""
        self.setGlobalSignal.emit(name, value, unit)
         
    @scriptFunction
    def addGlobal(self, name, value, unit):
        """add the global "name" to the list of globals, and set its value to "value" with the given unit."""
        self.addGlobalSignal.emit(name, value, unit)
        
    @scriptFunction
    def pauseScript(self):
        """Pause the script. This is equivalent to clicking the "pause script" button."""
        self.pauseScriptSignal.emit()
        
    @scriptFunction
    def stopScript(self):
        """Stop the script. This is equivalent to clicking the "stop script" button."""
        self.stopScriptSignal.emit()

    @scriptFunction
    def startScan(self, wait=True):
        """Start the scan. This is equivalent to clicking the "start" button on the experiment GUI.
        
        If wait=True, script will not continue until scan has finished."""
        self.startScanSignal.emit(wait)
#     
#     @scriptFunction
#     def pauseScript(self):
#         """pause the script"""
#         self.emitLocation()
#         self.pausedSignal.emit()
#         self.paused = True
#         
#     @scriptFunction
#     def setScan(self, name):
#         """set the scan interface to "name." This is equivalent to selecting "name" from the scan dropdown menu."""
#         pass
#     
#     @scriptFunction
#     def setEvaluation(self, name):
#         """set the evaluation interface to "name." This is equivalent to selecting "name" from the evaluation dropdown menu."""
#         pass
#     
#     @scriptFunction
#     def setAnalysis(self, name):
#         """set the analysis interface to "name." This is equivalent to selecting "name" from the analysis dropdown."""
#         pass
      
def checkScripting(func):
    """Check whether a function has been marked"""
    return hasattr(func, 'isScriptFunction')

scriptFunctions = [a[0] for a in inspect.getmembers(Script, checkScripting)] #Get the names of the scripting functions
# scriptFunctionDocs = dict(zip(scriptFunctions,[getattr(Script, name).__doc__ for name in scriptFunctions])) #docstrings of the scripting functions
