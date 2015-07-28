'''
Created on Jul 27, 2015

@author: jmizrahi
'''
import os

def scriptingFunction(func):
    """Mark a function as a scripting function"""
    func.isScriptingFunction = True
    return func

def checkScripting(func):
    """Check whether a function has been marked"""
    return hasattr(func, 'isScriptingFunction')

class Script:
    """Encapsulates a script together with all the scripting functions."""
    def __init__(self, fullname='', code=''):
        self.fullname = fullname #Full name, with path
        self.shortname = os.path.basename(fullname)
        self.code = code #The code in the script
        
    @scriptingFunction
    def startScan(self):
        """Start the scan. This is equivalent to clicking the "start" button on the GUI."""
        pass
    
    @scriptingFunction
    def setGlobal(self, name, value, create=False):
        """set the global "name" to "value." This is equivalent to typing in a value in the globals GUI.
        If create=True, global will be created if name does not exist.
        If create=False, ScriptingException will be raised if name does not exist."""
        pass

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
    
import inspect
scriptingFunctionNames = [a[0] for a in inspect.getmembers(Script, checkScripting)] #Get the names of the scripting functions
scriptingFunctionDocs = [getattr(Script, name).__doc__ for name in scriptingFunctionNames] #docstrings of the scripting functions
scriptingFunctions = zip(scriptingFunctionNames, scriptingFunctionDocs) #dict of the form name:docstring, for each scripting function
