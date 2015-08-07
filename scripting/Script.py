'''
Created on Jul 27, 2015

@author: jmizrahi
'''
import os
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
    #Signals to send information to the main thread
    locationSignal = QtCore.pyqtSignal(list)  # arg: trace locations corresponding to the script
    consoleSignal = QtCore.pyqtSignal(str, bool, str) #args: String to write, True if no error occurred, color to use
    exceptionSignal = QtCore.pyqtSignal(str, str) #args: exception message, traceback
    
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
    
    def __init__(self, fullname='', code='', parent=None):
        super(Script,self).__init__(parent)
        self.fullname = fullname #Full name, with path
        self.shortname = os.path.basename(fullname)
        self.code = code #The code in the script
        
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
        self.exception = None
        self.data = None
        for name in scriptFunctions: #Define the script functions to be the corresponding class functions
            globals()[name] = getattr(self, name)
        
    def run(self):
        """run the script"""
        try:
            while True:
                execfile(self.fullname) #run the script
                if not self.repeat:
                    break
        except Exception as e:
            trace = traceback.format_exc()
            with QtCore.QMutexLocker(self.mutex):
                self.exceptionSignal.emit(e.message, trace)

    def emitLocation(self):
        """Emits a signal containing the current script location"""
        frame = inspect.currentframe()
        stack_trace = traceback.extract_stack(frame) #Gets the full stack trace
        del frame #Getting rid of captured frames is recommended
        locs = [loc for loc in stack_trace if loc[0] == self.fullname] #Find the locations that match the script name
        self.locationSignal.emit(locs)

    def scriptFunction(func): #@NoSelf
        """Decorator for script functions.
        
        This decorator performs all the functions that are common to all the script functions. It checks
        whether the script has been stopped or paused, and emits the current location in the script. Once
        the function has executed, it waits to be told to continue by the main GUI. Exceptions that occur
        during execution are sent back to the script thread and raised here."""
        def baseScriptFunction(self, *args, **kwds):
            with QtCore.QMutexLocker(self.mutex): #Acquire mutex before inspecting any variables
                if not self.stopped: #if stopped, don't do anything
                    if self.scanRunning and self.waitOnScan:
                        self.scanWait.wait(self.mutex)
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
        """setGlobal(name, value, unit)
        set global name to (value, unit).
        This is equivalent to typing in a value in the globals table."""
        self.setGlobalSignal.emit(name, value, unit)
         
    @scriptFunction
    def addGlobal(self, name, value, unit):
        """addGlobal(name, value, unit)
        add a global name, set to (value, unit).      
        This is equivalent to adding a global via the globals UI, and then setting its value in the globals table."""
        self.addGlobalSignal.emit(name, value, unit)
        
    @scriptFunction
    def pauseScript(self):
        """pauseScript()
        Pause the script.
        This is equivalent to clicking the "pause script" button."""
        self.pauseScriptSignal.emit()
        
    @scriptFunction
    def stopScript(self):
        """stopScript()
        Stop the script.
        This is equivalent to clicking the "stop script" button."""
        self.stopScriptSignal.emit()

    @scriptFunction
    def startScan(self, wait=True):
        """startScan(wait=True)
        Start the scan.
        This is equivalent to clicking "start" on the experiment GUI.
        
        If wait=True, the script will not continue until the scan is finished.
        """
        self.waitOnScan = wait
        self.startScanSignal.emit()
        
    @scriptFunction
    def setScan(self, name):
        """setScan(name)
        set the scan interface to "name."
        This is equivalent to selecting "name" from the scan drop down menu."""
        self.setScanSignal.emit(name)
     
    @scriptFunction
    def setEvaluation(self, name):
        """setEvaluation(name)
        set the evaluation interface to "name."
        This is equivalent to selecting "name" from the evaluation drop down menu."""
        self.setEvaluationSignal.emit(name)
     
    @scriptFunction
    def setAnalysis(self, name):
        """setAnalysis(name)
        set the analysis interface to "name."
        This is equivalent to selecting "name" from the analysis drop down menu."""
        self.setAnalysisSignal.emit(name)

    @scriptFunction
    def plotPoint(self, x, y, plotName, traceName='', save=True):
        """plotPoint(x, y, plotName, traceName='', save=True)
        Plot a point (x, y) to plot "plotName", save trace/file under "traceName", and save to file if save=True"""
        traceName = plotName if traceName == '' else traceName
        self.plotPointSignal.emit(x, y, plotName, traceName, save)
        
    @scriptFunction
    def addPlot(self, name):
        """addPlot(name)
        Add a plot named "name". 
        This is equivalent to clicking "add plot" on the experiment GUI."""
        self.addPlotSignal.emit(name)

    @scriptFunction
    def pauseScan(self):
        """pauseScan()
        Pause the scan.
        This is equivalent to clicking "pause" on the experiment GUI."""
        self.pauseScanSignal.emit()
        
    @scriptFunction
    def stopScan(self):
        """stopScan()
        Stop the scan.
        This is equivalent to clicking "stop" on the experiment GUI."""
        self.stopScanSignal.emit()
    
    @scriptFunction    
    def abortScan(self):
        """abortScan()
        Abort the scan.
        This is equivalent to clicking "abort" on the experiment GUI."""
        self.abortScanSignal.emit()
        
    @scriptInternalFunction
    def waitForScan(self):
        """waitForScan()
        Wait for scan to finish before continuing script.
        If startScan is run with waitOnScan=True, this function is unnecessary."""
        with QtCore.QMutexLocker(self.mutex):
            self.waitOnScan = True
    
    @scriptInternalFunction
    def waitForData(self):
        """waitForData()
        Wait for data to arrive before continuing script."""
        with QtCore.QMutexLocker(self.mutex):
            self.waitOnData = True
 
    @scriptInternalFunction
    def getData(self):
        """getData()
        Get the data from a running scan."""
        with QtCore.QMutexLocker(self.mutex):
            return self.data

    @scriptInternalFunction
    def scanIsRunning(self):
        """scanIsRunning()
        Return True if the scan is running. Otherwise, False."""
        with QtCore.QMutexLocker(self.mutex):
            return self.scanRunning

def checkScripting(func):
    """Check whether a function has been marked"""
    return hasattr(func, 'isScriptFunction')

scriptFunctions = [a[0] for a in inspect.getmembers(Script, checkScripting)] #Get the names of the scripting functions
scriptDocs = [getattr(Script, name).__doc__ for name in scriptFunctions] #Get the doc strings