import logging
import sys

from PyQt4 import QtCore


class QtLoggingHandler(logging.Handler, QtCore.QObject):    
    textWritten = QtCore.pyqtSignal(object, object)
    def __init__(self):
        logging.Handler.__init__(self)
        QtCore.QObject.__init__(self)

    def emit(self, record):
        self.textWritten.emit(self.format(record).rstrip()+"\n", record.levelno)

class LevelThresholdFilter(logging.Filter):
    def __init__(self, passlevel, reject):
        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record):
        if self.reject:
            return (record.levelno >= self.passlevel)
        else:
            return (record.levelno < self.passlevel)
        
class LevelFilter(logging.Filter):
    def __init__(self, passlevel):
        self.passlevel = passlevel
        
    def filter(self, record):
        return record.levelno == self.passlevel

traceHandler = None
def setTraceFilename(filename):
    global traceHandler
    if traceHandler is not None:
        logger.removeHandler(traceHandler)
    traceHandler = logging.FileHandler(filename)
    traceHandler.setFormatter(fileformatter)
    traceHandler.addFilter( LevelFilter(logging.TRACE))  # @UndefinedVariable
    logger.addHandler( traceHandler )


TRACE_LEVEL_NUM = 25 
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")
def trace(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        self._log(TRACE_LEVEL_NUM, message, args, **kws) 
logging.Logger.trace = trace
logging.TRACE = TRACE_LEVEL_NUM

logger = logging.getLogger("")
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(levelname)s %(name)s(%(filename)s:%(lineno)d %(funcName)s) %(message)s')

stdoutHandler = logging.StreamHandler(sys.stdout)
stdoutHandler.setFormatter(formatter)
stdoutHandler.addFilter(LevelThresholdFilter(logging.ERROR,False))

stderrHandler = logging.StreamHandler(sys.stderr)
stderrHandler.setFormatter(formatter)
stderrHandler.addFilter(LevelThresholdFilter(logging.ERROR,True))

fileformatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s(%(filename)s:%(lineno)d %(funcName)s) %(message)s')

fileHandler = logging.FileHandler("messages")
fileHandler.setFormatter(fileformatter)
fileHandler.setLevel(logging.INFO) 

qtHandler = QtLoggingHandler()
qtHandler.setFormatter(formatter)

logger.addHandler(stdoutHandler)
logger.addHandler(stderrHandler)
logger.addHandler(qtHandler)
logger.addHandler(fileHandler)

pyqtlogger = logging.getLogger("PyQt4")
pyqtlogger.setLevel(logging.ERROR)
del pyqtlogger
