import logging
from PyQt4 import QtCore

class QtLoggingHandler(logging.Handler, QtCore.QObject):    
    textWritten = QtCore.pyqtSignal(str)
    def __init__(self):
        logging.Handler.__init__(self)
        QtCore.QObject.__init__(self)

    def emit(self, record):
        self.textWritten.emit(self.format(record))


logger = logging.getLogger("")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(name)s %(levelname)s (%(filename)s:%(lineno)d %(funcName)s) %(message)s')

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)

qtHandler = QtLoggingHandler()
qtHandler.setFormatter(formatter)

logger.addHandler(consoleHandler)
logger.addHandler(qtHandler)

pyqtlogger = logging.getLogger("PyQt4")
pyqtlogger.setLevel(logging.ERROR)
del pyqtlogger
