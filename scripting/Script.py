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
    
    The script behavior is as follows: each script function that manipulates a GUI element does so by emitting a
    signal, followed by entering  QWaitCondition. The ScriptHandler responds to the signal, and wakes up the 
    QWaitCondition. For access to GUI data, the script waits at a QWaitCondition until the data is available.
    When the data is available, the ScriptHandler sets the script data variables appropriately, and then wakes the
    wait condition. This back-and-forth handoff between the Script thread and the ScriptHandler (which lives in the
    main GUI thread) is what ensures synchronicity and avoids race conditions.

    Note that the script thread does not have an event loop. This means that it cannot respond to emitted signals,
    and calls like Script.quit and Script.exit do not work. Instead, the script emits signals indicating what to
    change, and then enters a QWaitCondition. The ScriptingUi responds to the signal, and tells the script to exit
    the wait condition once the action has been done. 
    
    All the script functions are executed via the script function decorator, which simplifies the code.
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
    plotPointSignal = QtCore.pyqtSignal(float, float, str) #args: x, y, tracename
    plotListSignal = QtCore.pyqtSignal(list, list, str) #args: xList, yList, tracename
    addPlotSignal = QtCore.pyqtSignal(str) #arg: plot name
    abortScanSignal = QtCore.pyqtSignal()
    createTraceSignal = QtCore.pyqtSignal(list) #arg: trace creation data
    
    def __init__(self, fullname='', code='', parent=None):
        super(Script,self).__init__(parent)
        self.fullname = fullname #Full name, with path
        self.code = code #The code in the script
        
        self.mutex = QtCore.QMutex() #used to control access to class variables that are accessed by ScriptHandler
        
        self.pauseWait = QtCore.QWaitCondition() #Used to wait while script is paused
        self.scanWait = QtCore.QWaitCondition() #Used to wait for end of scan
        
        self.dataWait = QtCore.QWaitCondition() #Used to wait for single data point
        self.allDataWait = QtCore.QWaitCondition() #Used to wait for full data set
        self.analysisWait = QtCore.QWaitCondition() #Used to wait for analysis results
        self.guiWait = QtCore.QWaitCondition() #Used to wait for gui to execute command

        for name in scriptFunctions: #Define global functions corresponding to the scripting functions
            globals()[name] = getattr(self, name)
        
        #Below are all class elements that are modified directly during operation by ScriptHandler
        #All access to these parameters is mutex protected while the script is running
        
        #parameters that control the script execution process
        self.repeat = False
        self.paused = False
        self.stopped = False
        self.slow = False
        
        #parameters that control synchronization with the gui
        self.scanStatus = 'idle'
        self.scanIsRunning = False
        self.waitOnScan = False
        self.analysisReady = False
        self.allDataReady = False
        self.dataReady = False
        
        #parameters to send information from the gui to the script
        self.analysisResults = dict()
        self.data = dict()
        self.allData = dict()
        self.exception = None

    @QtCore.pyqtProperty(str)
    def shortname(self):
        return os.path.basename(self.fullname)

    def run(self):
        """run the script"""
        try:
            d = dict(locals(), **globals()) #Executing in this scope allows a function defined in the script to call another function defined in the script
            while True:
                execfile(self.fullname, d, d) #run the script
                if not self.repeat:
                    break
        except Exception as e:
            trace = traceback.format_exc()
            with QtCore.QMutexLocker(self.mutex):
                self.exceptionSignal.emit(type(e).__name__+": "+str(e.message), trace)

    def emitLocation(self):
        """Emits a signal containing the current script location"""
        frame = inspect.currentframe()
        stack_trace = traceback.extract_stack(frame) #Gets the full stack trace
        del frame #Getting rid of captured frames is recommended
        locs = [loc for loc in stack_trace if loc[0] == self.fullname] #Find the locations that match the script name
        self.locationSignal.emit(locs)

    def scriptFunction(waitForGui=True, waitForAnalysis=False, waitForData=False, waitForAllData=False, runIfStopped=False): #@NoSelf
        """Decorator for script functions.
        
        This decorator performs all the functions that are common to all the script functions. It checks
        whether the script has been stopped or paused, and emits the current location in the script. Once
        the function has executed, it waits to be told to continue by the main GUI. Exceptions that occur
        during execution are sent back to the script thread and raised here."""
        def realScriptFunction(func):
            """The decorator without arguments (returned by the decorator with arguments)"""
            def baseScriptFunction(self, *args, **kwds):
                """The base script function that wraps all the other script functions"""
                with QtCore.QMutexLocker(self.mutex): #Acquire mutex before inspecting any variables
                    if (not self.stopped) or (self.stopped and runIfStopped): #if stopped, don't do anything
                        if self.scanIsRunning and self.waitOnScan:
                            self.scanWait.wait(self.mutex)
                        if self.paused:
                            self.pauseWait.wait(self.mutex)
                        self.emitLocation()
                        if self.slow:
                            self.mutex.unlock()
                            time.sleep(0.4) #On slow, we wait on each line for 0.4 s 
                            self.mutex.lock() 
                        if waitForAnalysis and not self.analysisReady:
                            self.analysisWait.wait(self.mutex)
                        if waitForAllData and not self.allDataReady:
                            self.allDataWait.wait(self.mutex)
                        if waitForData and not self.dataReady:
                            self.dataWait.wait(self.mutex)
                        returnData = func(self, *args, **kwds) #This is the actual function
                        if waitForGui:
                            self.guiWait.wait(self.mutex)
                        if self.exception:
                            raise self.exception
                        return returnData
            baseScriptFunction.isScriptFunction = True
            baseScriptFunction.func_name = func.func_name
            baseScriptFunction.func_doc = func.func_doc
            return baseScriptFunction
        return realScriptFunction
        
    @scriptFunction()
    def setGlobal(self, name, value, unit):
        """setGlobal(name, value, unit)
        set global 'name' to (value, unit).

        This is equivalent to typing in a value/unit in the globals table.
        If there is not a global with the given name, an exception is raised.
        This is to avoid typos leading to unexpected behavior. To add a global,
        use 'addGlobal'
         
        name: str
        value: float
        unit: str"""
        self.setGlobalSignal.emit(name, value, unit)
         
    @scriptFunction()
    def addGlobal(self, name, value, unit):
        """addGlobal(name, value, unit)
        add a global 'name', set to (value, unit).     
         
        This is equivalent to adding a global via the globals UI,and
        then setting its value in the globals table.
        
        name: str
        value: float
        unit: str"""
        self.addGlobalSignal.emit(name, value, unit)
        
    @scriptFunction()
    def pauseScript(self):
        """pauseScript()
        Pause the script.
        
        This is equivalent to clicking the "pause script" button."""
        self.pauseScriptSignal.emit()
        
    @scriptFunction()
    def stopScript(self):
        """stopScript()
        Stop the script.
        
        This is equivalent to clicking the "stop script" button."""
        self.stopScriptSignal.emit()

    @scriptFunction()
    def startScan(self, wait=True):
        """startScan(wait=True)
        Start the scan.
        
        This is equivalent to clicking "start" on the experiment GUI. If
        wait=True, the script will not continue until the scan is finished.
        
        wait: bool"""
        self.waitOnScan = wait
        self.startScanSignal.emit()
        
    @scriptFunction()
    def setScan(self, name):
        """setScan(name)
        set the scan interface to "name."
        
        This is equivalent to selecting "name" from the scan drop down menu.
        If there is no scan by that name, an exception is raised.
        
        name: str"""
        self.setScanSignal.emit(name)
     
    @scriptFunction()
    def setEvaluation(self, name):
        """setEvaluation(name)
        set the evaluation interface to "name."
        
        This is equivalent to selecting "name" from the evaluation drop down menu.
        If there is no evaluation by that name, an exception is raised.
        
        name: str"""
        self.setEvaluationSignal.emit(name)
     
    @scriptFunction()
    def setAnalysis(self, name):
        """setAnalysis(name)
        set the analysis interface to "name."
        
        This is equivalent to selecting "name" from the analysis drop down menu.
        If there is no analysis by that name, an exception is raised.
        
        name: str"""
        self.setAnalysisSignal.emit(name)

    @scriptFunction()
    def plotPoint(self, x, y, traceName):
        """plotPoint(x, y, traceName)
        Plot a single point (x, y) to trace traceName.
        
        x: float
        y: float
        traceName: str"""
        self.plotPointSignal.emit(x, y, traceName)

    @scriptFunction()
    def plotList(self, xList, yList, traceName):
        """plotList(xList, yList, traceName)
        Plot a set of points given in xList, yList to trace traceName.
        
        x: list
        y: list
        traceName: str"""
        if type(xList).__module__ == 'numpy':
            xList = xList.tolist()
        if type(yList).__module__ == 'numpy':
            yList = yList.tolist()
        self.plotListSignal.emit(xList, yList, traceName)
        
    @scriptFunction()
    def addPlot(self, name):
        """addPlot(name)
        Add a plot named "name".
         
        This is equivalent to clicking "add plot" on the experiment GUI.
        
        name: str"""
        self.addPlotSignal.emit(name)

    @scriptFunction()
    def pauseScan(self):
        """pauseScan()
        Pause the scan.
        
        This is equivalent to clicking "pause" on the experiment GUI."""
        self.pauseScanSignal.emit()
        
    @scriptFunction()
    def stopScan(self):
        """stopScan()
        Stop the scan.
        
        This is equivalent to clicking "stop" on the experiment GUI."""
        self.stopScanSignal.emit()
    
    @scriptFunction()  
    def abortScan(self):
        """abortScan()
        Abort the scan.
        
        This is equivalent to clicking "abort" on the experiment GUI."""
        self.abortScanSignal.emit()
        
    @scriptFunction()
    def createTrace(self, traceName, plotName, xUnit='', xLabel='', comment=''):
        """createTrace(traceName, plotName, xUnit='', xLabel='', comment='')
        
        create a new trace with name 'traceName' to be plotted on plot
        'plotName' with unit 'xUnit', label 'xLabel', and comment 'comment'.
        
        traceName: str
        plotName: str
        xUnit: str
        xLabel: str
        comment: str"""
        traceCreationData = [traceName, plotName, xUnit, xLabel, comment]
        self.createTraceSignal.emit(traceCreationData)
        
    @scriptFunction(waitForGui=False)
    def waitForScan(self):
        """waitForScan()
        Wait for scan to finish before continuing script.
        
        If startScan is run with wait=True, this function is unnecessary."""
        self.waitOnScan = True
    
    @scriptFunction(waitForGui=False, waitForData=True)
    def getData(self):
        """getData()
        Get the most recent data point from a running scan.
        
        Data is returned as a dictionary. The key corresponds to
        the name of each evaluation in the evaluation list. The value
        is a tuple (x, y)."""
        self.dataReady = False
        return self.data

    @scriptFunction(waitForGui=False, waitForAllData=True)
    def getAllData(self):
        """getAllData()
        Get the full set of data from the most recent scan.
        
        Data is returned as a dictionary. The key corresponds to
        the name of each evaluation in the evaluation list. The value
        is a tuple (xList, yList)."""
        self.allDataReady = False
        return self.allData

    @scriptFunction(waitForGui=False, waitForAnalysis=True)
    def getAnalysis(self):
        """getAnalysis()
        Get the analysis results for the most recent scan.
        
        Analysis is returned as a dictionary of dictionaries. The key corresponds
        to the name of each analysis in the analysis list. The value is another
        dictionary, whose keys correspond to the names of fit parameters in the
        specified evaluation.
        
        Example: a Gaussian fit named "myFit" in the analysis, with center parameter
        x0, would return its center value as getAnalysis()['myFit']['x0']"""
        self.analysisReady = False
        return self.analysisResults

    @scriptFunction(waitForGui=False)
    def scanRunning(self):
        """scanRunning()
        Return True if the scan is running. Otherwise, False."""
        return self.scanIsRunning
    
    @scriptFunction(waitForGui=False)
    def getScanStatus(self):
        """getScanStatus()
        Return the current state of the scan.
        
        One of 'idle', 'running', 'paused', 'starting', 'stopping', or 'interrupted'"""
        return self.scanStatus
        
    @scriptFunction(waitForGui=False, runIfStopped=True)
    def scriptIsStopped(self):
        """scriptIsStopped()
        Return True if the script has been stopped, Otherwise, False."""
        return self.stopped

def checkScripting(func):
    """Check whether a function has been marked as a script function"""
    return hasattr(func, 'isScriptFunction')

scriptFunctions = [a[0] for a in inspect.getmembers(Script, checkScripting)] #Get the names of the scripting functions
scriptDocs = [getattr(Script, name).__doc__ for name in scriptFunctions] #Get the doc strings