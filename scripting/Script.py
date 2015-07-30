'''
Created on Jul 27, 2015

@author: jmizrahi
'''
import os
import logging
import modules.magnitude as magnitude
from PyQt4.QtCore import pyqtSignal, QThread, pyqtSlot, QEventLoop
import inspect
import traceback

class ScriptException(Exception):
    pass

def scriptingFunction(func):
    """Mark a function as a scripting function"""
    func.isScriptingFunction = True
    return func

def checkScripting(func):
    """Check whether a function has been marked"""
    return hasattr(func, 'isScriptingFunction')

class Script(QThread):
    """Encapsulates a running script together with all the scripting functions. Script executes in separate thread."""
    locationSignal = pyqtSignal(int)
    completed = pyqtSignal()
    def __init__(self, globalVariablesUi, fullname='', code='', parent=None):
        super(Script,self).__init__(parent)
        self.fullname = fullname #Full name, with path
        self.shortname = os.path.basename(fullname)
        self.code = code #The code in the script
        self.scriptingFunctionNames = []
        self.globalVariablesUi = globalVariablesUi
        
    def run(self):
        """run the script"""
        #Name local functions with the same names as the class functions, so that the script can call them by name directly
        for name in self.scriptingFunctionNames:
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
            logger.info("Executing {0} in {1} at line {2}".format( scriptLoc[3], os.path.basename(scriptLoc[0]), scriptLoc[1] ))
        else:
            logger.warning("Not executing script")
        self.locationSignal.emit(scriptLoc[1]) #Emit a signal containing the script location 
        
    @scriptingFunction
    def startScan(self):
        """Start the scan. This is equivalent to clicking the "start" button on the GUI."""
        pass
    
    @scriptingFunction
    def setGlobal(self, name, value, unit, create=False):
        """set the global "name" to "value" with the given unit. This is equivalent to typing in a value+unit in the globals GUI.
        If create=True, global will be created if name does not exist.
        If create=False, ScriptingException will be raised if name does not exist."""
        logger = logging.getLogger(__name__)
        self.emitLocation()
        doesNotExist = (name not in self.globalVariablesUi.keys())
        import time #DELETE THIS
        time.sleep(1) #DELETE THIS
        if not create and doesNotExist:
            errorMessage = "Global variable {0} does not exist.".format(name)
            logger.error(errorMessage)
            raise ScriptException(errorMessage)
        elif doesNotExist:
            self.globalVariablesUi.model.addVariable(name)
            logger.info("Global variable {0} created".format(name))
        self.globalVariablesUi.update([('Global', name, magnitude.mg(value,unit))])
        logger.info("Global variable {0} set to {1} {2}".format(name, value, unit))

    @scriptingFunction
    def setScan(self, name):
        """set the scan interface to "name." This is equivalent to selecting "name" from the scan dropdown menu."""
        pass
    
    @scriptingFunction
    def setEvaluation(self, name):
        """set the evaluation interface to "name." This is equivalent to selecting "name" from the evaluation dropdown menu."""
        pass
    
    @scriptingFunction
    def setAnalysis(self, name):
        """set the analysis interface to "name." This is equivalent to selecting "name" from the analysis dropdown."""
        pass
    
    @scriptingFunction
    def pause(self):
        """Pause the script."""
    
scriptingFunctionNames = [a[0] for a in inspect.getmembers(Script, checkScripting)] #Get the names of the scripting functions
scriptingFunctionDocs = [getattr(Script, name).__doc__ for name in scriptingFunctionNames] #docstrings of the scripting functions
scriptingFunctions = zip(scriptingFunctionNames, scriptingFunctionDocs) #dict of the form name:docstring, for each scripting function
