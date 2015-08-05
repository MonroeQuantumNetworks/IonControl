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
from collections import OrderedDict

class ScriptException(Exception):
    pass

class Script(QtCore.QThread):
    """Encapsulates a running script together with all the scripting functions. Script executes in separate thread.
    
    Note that the script thread does not have an event loop. This means that it cannot respond to emitted signals,
    and calls like Script.quit and Script.exit do not work. Instead, the script emits signals indicating what to
    change, and then enters a QWaitCondition. The ScriptingUi responds to the signal, and tells the script to exit
    the wait condition once the action has been done. 
    """
    #Signals to send information to the main thread
    locationSignal = QtCore.pyqtSignal(list)  # arg: line numbers
    consoleSignal = QtCore.pyqtSignal(str, bool, str) #args: String to write, True if no error occurred, color to use
    exceptionSignal = QtCore.pyqtSignal(list, str) #arg: line numbers, exception message
    
    #Signals to send instructions to the main thread
    pauseScriptSignal = QtCore.pyqtSignal()
    stopScriptSignal = QtCore.pyqtSignal()
    pauseScanSignal = QtCore.pyqtSignal()
    stopScanSignal = QtCore.pyqtSignal()
    
    setGlobalSignal = QtCore.pyqtSignal(str, float, str) #args: name, value, unit
    addGlobalSignal = QtCore.pyqtSignal(str, float, str) #args: name, value, unit
    startScanSignal = QtCore.pyqtSignal()
    setScanSignal = QtCore.pyqtSignal(str) #arg: scan name
    setEvaluationSignal = QtCore.pyqtSignal(str) #arg: evaluation name
    setAnalysisSignal = QtCore.pyqtSignal(str) #arg: analysis name
    plotPointSignal = QtCore.pyqtSignal(float, float, str, str, bool) #args: x, y, plotname, tracename, save if True
    addPlotSignal = QtCore.pyqtSignal(str) #arg: plot name
    abortScanSignal = QtCore.pyqtSignal()
    helpSignal = QtCore.pyqtSignal()
    
    def __init__(self, fullname='', code='', parent=None):
        super(Script,self).__init__(parent)
        self.fullname = fullname #Full name, with path
        self.shortname = os.path.basename(fullname)
        self.code = code #The code in the script
        self.currentLines = []
        
        self.mutex = QtCore.QMutex() #used to control access to class variables that are accessed by ScriptingUi
        self.pauseWait = QtCore.QWaitCondition() #Used to wait while script is paused
        self.scanWait = QtCore.QWaitCondition() #Used to wait for end of scan
        self.dataWait = QtCore.QWaitCondition() #Used to wait for data
        self.commandWait = QtCore.QWaitCondition() #Used to wait for command to be completed
        #These are all class elements that are modified directly during operation by ScriptingUi
        self.repeat = False
        self.paused = False
        self.stopped = False
        self.slow = False
        self.scanRunning = False
        self.waitOnScan = False
        self.waitOnData = False
        self.exception = None
        self.data = None
        for name in scriptFunctions: #Define the script functions to be the corresponding class functions
            globals()[name] = getattr(self, name)
        
    def run(self):
        """run the script"""
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
                    if self.scanRunning:
                        if self.waitOnScan:
                            self.scanWait.wait(self.mutex)
                        elif self.waitOnData:
                            self.dataWait.wait(self.mutex)
                    if self.paused:
                        self.pauseWait.wait(self.mutex)
                    self.emitLocation()
                    if self.slow:
                        self.mutex.unlock()
                        time.sleep(0.4)
                        self.mutex.lock() 
                    func(self, *args, **kwds)
                    self.commandWait.wait(self.mutex)
                    if self.exception:
                        raise self.exception
        baseScriptFunction.isScriptFunction = True
        baseScriptFunction.func_name = func.func_name
        baseScriptFunction.func_doc = func.func_doc
        return baseScriptFunction
    
    def scriptInternalFunction(func): #@NoSelf
        """Decorator for script internal functions. These are functions which do not interface with the GUI."""
        func.isScriptFunction = True
        return func
        
    @scriptFunction
    def setGlobal(self, name, value, unit):
        """setGlobal(name, value, unit):
        set a global to a given value.
        
        This is equivalent to typing in a value in the globals table.
        
        Parameters
        ----------
        name : str
               The name of the global to set
        value : float
                The value to set the global to
        unit : str
                The unit to associate with the specified value"""
        self.setGlobalSignal.emit(name, value, unit)
         
    @scriptFunction
    def addGlobal(self, name, value, unit):
        """addGlobal(name, value, unit):
        add a global with a specified value.
        
        This is equivalent to adding a global via the globals UI, and then setting its value in the globals table.
        
        Parameters
        ----------
        name : str
               The name of the global to set
        value : float
                The value to set the global to
        unit : str
               The unit to associate with the specified value"""
        self.addGlobalSignal.emit(name, value, unit)
        
    @scriptFunction
    def pauseScript(self):
        """pauseScript():
        Pause the script.
        
        This is equivalent to clicking the "pause script" button."""
        self.pauseScriptSignal.emit()
        
    @scriptFunction
    def stopScript(self):
        """stopScript():
        Stop the script.
        
        This is equivalent to clicking the "stop script" button."""
        self.stopScriptSignal.emit()

    @scriptFunction
    def startScan(self, waitOnScan=True, waitOnData=True):
        """startScan(waitOnScan=True, waitOnData=True):
        Start the scan.
        
        This is equivalent to clicking "start" on the experiment GUI.
        
        Parameters
        ----------        
        waitOnScan : bool, optional
                      If True, the script will not continue until scan has finished.
        waitOnData : bool, optional
                      If True, the script will not continue until the first data point arrives."""
        self.waitOnScan = waitOnScan
        self.waitOnData = waitOnData
        self.startScanSignal.emit()
        
    @scriptFunction
    def setScan(self, name):
        """setScan(name):
        set the scan interface to "name."
        
        This is equivalent to selecting "name" from the scan drop down menu.
        
        Parameters
        ----------
        name : str
               The name of the scan from the scan context menu"""
        self.setScanSignal.emit(name)
     
    @scriptFunction
    def setEvaluation(self, name):
        """setEvaluation(name):
        set the evaluation interface to "name."
        
        This is equivalent to selecting "name" from the evaluation drop down menu.
        
        Parameters
        ----------
        name : str
               The name of the evaluation from the scan context menu"""
        self.setEvaluationSignal.emit(name)
     
    @scriptFunction
    def setAnalysis(self, name):
        """setAnalysis(name):
        set the analysis interface to "name."
        
        This is equivalent to selecting "name" from the analysis drop down menu.
        
        Parameters
        ----------
        name : str
               The name of the analysis from the analysis context menu"""
        self.setAnalysisSignal.emit(name)

    @scriptInternalFunction
    def waitForScan(self):
        """waitForScan():
        Wait for scan to finish before continuing script.
        
        If startScan is run with waitOnScan=True, this function is unnecessary"""
        with QtCore.QMutexLocker(self.mutex):
            self.waitOnScan = True
    
    @scriptInternalFunction
    def waitForData(self):
        """waitForData():
        Wait for data to arrive before continuing script."""
        with QtCore.QMutexLocker(self.mutex):
            self.waitOnData = True
 
    @scriptInternalFunction
    def getData(self):
        """getData():
        Get the data from a running scan"""
        with QtCore.QMutexLocker(self.mutex):
            return self.data
    
    @scriptFunction
    def plotPoint(self, x, y, plotName, traceName='', save=True):
        """plotPoint(x, y, plotName, traceName='', save=True):
        Plot a point.
        
        Plot a given point to a specified plot.
        
        Parameters
        ----------
        x : float
            the x coordinate of the point to plot
        y : float
            the y coordinate of the point to plot
        plotName : str
            the name of the plot to use
        traceName: str, optional
            the name of the trace to add to the tracelist. The default is plotName
        save: bool, optional
            If true, save the resulting trace to a file. The default is True."""
        traceName = plotName if traceName == '' else traceName
        self.plotPointSignal.emit(x, y, plotName, traceName, save)
        
    @scriptFunction
    def addPlot(self, name):
        """addPlot(name):
        Add a plot. 
        
        This is equivalent to clicking "add plot" on the experiment GUI.
        
        Parameters
        ----------
        name : str
               The name of the plot to add"""
        self.addPlotSignal.emit(name)

    @scriptFunction
    def pauseScan(self):
        """pauseScan():
        Pause the scan.
        
        This is equivalent to clicking "pause" on the experiment GUI."""
        self.pauseScanSignal.emit()
        
    @scriptFunction
    def stopScan(self):
        """stopScan():
        Stop the scan.
        
        This is equivalent to clicking "stop" on the experiment GUI."""
        self.stopScanSignal.emit()
    
    @scriptFunction    
    def abortScan(self):
        """abortScan():
        Abort the scan.
        
        This is equivalent to clicking "abort" on the experiment GUI."""
        self.abortScanSignal.emit()
        
    @scriptFunction
    def help(self):
        """help():
        Get a list of all script commands and their documentation."""
        self.helpSignal.emit()

def checkScripting(func):
    """Check whether a function has been marked"""
    return hasattr(func, 'isScriptFunction')

scriptFunctions = [a[0] for a in inspect.getmembers(Script, checkScripting)] #Get the names of the scripting functions
scriptFunctionDocs = OrderedDict(zip(scriptFunctions, [getattr(Script, name).__doc__ for name in scriptFunctions])) #docstrings of the scripting functions
