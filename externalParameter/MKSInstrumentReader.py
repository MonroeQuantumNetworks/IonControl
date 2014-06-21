'''
Created on Jun 21, 2014

@author: pmaunz
'''

from modules import magnitude
from InstrumentLoggingReader import InstrumentLoggingReader
from Queue import Queue
from MKSReader import MKSReader
from ExternalParameterBase import ExternalParameterBase

class MKSInstrumentReader( ExternalParameterBase ):
    """test """
    className = "MKS Vacuum Gauge"
    def __init__(self, name, settings, instrument):
        ExternalParameterBase(self, name, settings)
        port = int(instrument)
        reader = MKSReader(port=port)
        reader.open()
        self.commandQueue = Queue()
        self.reader = InstrumentLoggingReader(reader, self.commandQueue)
        self.newData = self.reader.newData
         
    def close(self):
        self.reader.close()
        del self.reader
        
    def setDefaults(self):
        self.settings.__dict__.setdefault('timeout', magnitude.mg(100,'ms') )      # s delay between subsequent updates
        
    def currentValue(self):
        return self.reader.value()
    
    def currentExternalValue(self):
        """
        if the value is determined externally, return the external value, otherwise return value
        """
        return self.reader.value()

    def paramDef(self):
        """
        return the parameter definition used by pyqtgraph parametertree to show the gui
        """
        return [{'name': 'timeout', 'type': 'magnitude', 'value': self.settings.timeout, 'tip': "wait time for result"},
                {'name': 'readWait', 'type': 'magnitude', 'value': self.settings.readWait, 'tip': "time to wait between readings"}]

a = MKSInstrumentReader.className