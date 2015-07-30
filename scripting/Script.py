'''
Created on Jul 27, 2015

@author: jmizrahi
'''
import os
import logging
import modules.magnitude as magnitude
from PyQt4 import QtCore
import inspect
import traceback
import time

def longWait(): #DELETE THIS FUNCTION
    time.sleep(1)

class ScriptException(Exception):
    pass

def scriptFunction(func):
    """Mark a function as a scripting function"""
    func.isScriptFunction = True
    return func

def checkScripting(func):
    """Check whether a function has been marked"""
    return hasattr(func, 'isScriptFunction')

class Script(QtCore.QThread):
    """Encapsulates a running script together with all the scripting functions. Script executes in separate thread."""
    locationSignal = QtCore.pyqtSignal(int)
    consoleSignal = QtCore.pyqtSignal(str, bool)
    completed = QtCore.pyqtSignal()
    pausedSignal = QtCore.pyqtSignal()
    def __init__(self, globalVariablesUi, fullname='', code='', parent=None):
        super(Script,self).__init__(parent)
        self.fullname = fullname #Full name, with path
        self.shortname = os.path.basename(fullname)
        self.code = code #The code in the script
        self.paused = False
        self.scriptFunctions = []
        self.globalVariablesUi = globalVariablesUi

    def run(self):
        """run the script"""
        #Name local functions with the same names as the class functions, so that the script can call them by name directly
        for name in self.scriptFunctions:
            locals()[name] = getattr(self, name)
        execfile(self.fullname) #run the script
        self.completed.emit()
        
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
        
    @scriptFunction
    def startScan(self):
        """Start the scan. This is equivalent to clicking the "start" button on the GUI."""
        pass
    
    @scriptFunction
    def pauseScript(self):
        """pause the script"""
        self.emitLocation()
        self.pausedSignal.emit()
        self.paused = True

    @scriptFunction
    def setGlobal(self, name, value, unit):
        """set the global "name" to "value" with the given unit. This is equivalent to typing in a value+unit in the globals GUI."""
        if self.paused:
            self.exec_()
        logger = logging.getLogger(__name__)
        self.emitLocation()
        longWait()
        doesNotExist = (name not in self.globalVariablesUi.keys())
        if doesNotExist:
            message = "Global variable {0} does not exist.".format(name)
            logger.error(message)
            self.consoleSignal.emit(message, False)
            raise ScriptException(message)
        self.globalVariablesUi.update([('Global', name, magnitude.mg(value,unit))])
        message = "Global variable {0} set to {1} {2}".format(name, value, unit)
        self.consoleSignal.emit(message, True)
        logger.info(message)
        
    @scriptFunction
    def addGlobal(self, name, value, unit):
        """add the global "name" to the list of globals, and set its value to "value" with the given unit."""
        if self.paused:
            self.exec_()
        logger = logging.getLogger(__name__)
        self.emitLocation()
        doesNotExist = name not in self.globalVariablesUi.keys()
        if doesNotExist:
            self.globalVariablesUi.model.addVariable(name)
            message = "Global variable {0} created".format(name)
            logger.info(message)
            self.consoleSignal.emit(message, True)
        self.setGlobal(name, value, unit)

    @scriptFunction
    def setScan(self, name):
        """set the scan interface to "name." This is equivalent to selecting "name" from the scan dropdown menu."""
        pass
    
    @scriptFunction
    def setEvaluation(self, name):
        """set the evaluation interface to "name." This is equivalent to selecting "name" from the evaluation dropdown menu."""
        pass
    
    @scriptFunction
    def setAnalysis(self, name):
        """set the analysis interface to "name." This is equivalent to selecting "name" from the analysis dropdown."""
        pass
    
scriptFunctions = [a[0] for a in inspect.getmembers(Script, checkScripting)] #Get the names of the scripting functions
scriptFunctionDocs = dict(zip(scriptFunctions,[getattr(Script, name).__doc__ for name in scriptFunctions])) #docstrings of the scripting functions
