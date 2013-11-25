import logging
from PyQt4 import QtCore
import sys

class QtLoggingHandler(logging.Handler, QtCore.QObject):    
    textWritten = QtCore.pyqtSignal(str)
    def __init__(self):
        logging.Handler.__init__(self)
        QtCore.QObject.__init__(self)

    def emit(self, record):
        self.textWritten.emit(self.format(record).rstrip()+"\n")

class LevelThresholdFilter(logging.Filter):
    def __init__(self, passlevel, reject):
        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record):
        if self.reject:
            return (record.levelno >= self.passlevel)
        else:
            return (record.levelno < self.passlevel)


logger = logging.getLogger("")
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(levelname)s %(name)s(%(filename)s:%(lineno)d %(funcName)s) %(message)s')

stdoutHandler = logging.StreamHandler(sys.stdout)
stdoutHandler.setFormatter(formatter)
stdoutHandler.addFilter(LevelThresholdFilter(logging.ERROR,False))

stderrHandler = logging.StreamHandler(sys.stderr)
stderrHandler.setFormatter(formatter)
stderrHandler.addFilter(LevelThresholdFilter(logging.ERROR,True))

fileHandler = logging.FileHandler("messages")
fileHandler.setFormatter(formatter)
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
