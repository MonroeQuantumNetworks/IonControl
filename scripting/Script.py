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

def longWait(): #DELETE THIS FUNCTION
    time.sleep(1)

class ScriptException(Exception):
    pass

# def scriptFunction(func):
#     """Mark a function as a scripting function"""
#     func.isScriptFunction = True
#     return func
# 
def checkScripting(func):
    """Check whether a function has been marked"""
    return hasattr(func, 'isScriptFunction')

class Script(QtCore.QThread):
    """Encapsulates a running script together with all the scripting functions. Script executes in separate thread.
    
    Note that the script thread does not have an event loop. This means that it cannot respond to emitted signals,
    and calls like Script.quit and Script.exit do not work. Instead, the script emits signals indicating what to
    change, and then enters a QWaitCondition. The ScriptingUi responds to the signal, and tells the script to exit
    the wait condition once the action has been done. 
    """
    locationSignal = QtCore.pyqtSignal(int)
    consoleSignal = QtCore.pyqtSignal(str, bool)
    
    setGlobalSignal = QtCore.pyqtSignal(str, float, str)
    addGlobalSignal = QtCore.pyqtSignal(str, float, str)
    
    def __init__(self, fullname='', code='', parent=None):
        super(Script,self).__init__(parent)
        self.fullname = fullname #Full name, with path
        self.shortname = os.path.basename(fullname)
        self.code = code #The code in the script

        self.mutex = QtCore.QMutex()
        self.waitCondition = QtCore.QWaitCondition()
        self.repeat = False
        self.paused = False
        self.stopped = False
        self.exceptionOccurred = False
        self.exception = None
        
    def run(self):
        """run the script"""
        #Define the script functions
        setGlobal = self.setGlobal #@UnusedVariable
        addGlobal = self.addGlobal #@UnusedVariable
        logger = logging.getLogger(__name__)
        try:
            while True:
                execfile(self.fullname) #run the script
                if not self.repeat:
                    break
        except Exception:
            message = traceback.format_exc()
            logger.error(message)
            self.consoleSignal.emit(message, False)

#     def scriptFunction(func):
#         def magic(self, *args, **kwds):
#             print 'magic'
#             func(self, *args, **kwds)
#         magic.isScriptFunction = True
#         magic.__name__ = func.__name__
#         return magic

    def emitLocation(self):
        """Emits a signal containing the current script location"""
        logger = logging.getLogger(__name__)
        frame = inspect.currentframe()
        stack_trace = traceback.extract_stack(frame) #Gets the full stack trace
        del frame #Getting rid of captured frames is recommended
        locs = [loc for loc in stack_trace if loc[0] == self.fullname] #Find the locations that match the script name
        scriptLoc = locs[0] if locs != [] else (None, -1, None, None)
        if scriptLoc[1] >= 0:
            message = "Executing {0} in {1} at line {2}".format( scriptLoc[3], os.path.basename(scriptLoc[0]), scriptLoc[1] )
            logger.debug(message)
            self.consoleSignal.emit(message, True)
        else:
            message = "Not executing script"
            logger.warning(message)
            self.consoleSignal.emit(message, False)
        self.locationSignal.emit(scriptLoc[1]) #Emit a signal containing the script location

    def scriptFunction(func): #@NoSelf
        def baseScriptFunction(self, *args):
            if not self.stopped: #if stopped, don't do anything
                if self.paused: #if paused, wait on waitCondition
                    with QtCore.QMutexLocker(self.mutex):
                        self.waitCondition.wait(self.mutex)
                self.emitLocation()
                longWait()
                func(self, *args)
                with QtCore.QMutexLocker(self.mutex):
                    self.waitCondition.wait(self.mutex)
                    if self.exceptionOccurred:
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
          
#     @scriptFunction
#     def startScan(self):
#         """Start the scan. This is equivalent to clicking the "start" button on the GUI."""
#         pass
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
      
scriptFunctions = [a[0] for a in inspect.getmembers(Script, checkScripting)] #Get the names of the scripting functions
# scriptFunctionDocs = dict(zip(scriptFunctions,[getattr(Script, name).__doc__ for name in scriptFunctions])) #docstrings of the scripting functions
