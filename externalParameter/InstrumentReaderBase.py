'''
Created on Jun 21, 2014

@author: pmaunz
'''
from ExternalParameterBase import ExternalParameterBase
from modules import magnitude

class InstrumentReaderBase( ExternalParameterBase ):
    """test """
    className = "MKS Vacuum Gauge"
    def __init__(self, name, settings):
        ExternalParameterBase.__init__(self, name, settings)
         
    def setDefaults(self):
        self.settings.__dict__.setdefault('timeout', magnitude.mg(100,'ms') )      # s delay between subsequent updates
        self.settings.__dict__.setdefault('readWait', magnitude.mg(100,'ms') )      # s delay between subsequent updates
        
    def paramDef(self):
        """
        return the parameter definition used by pyqtgraph parametertree to show the gui
        """
        return [{'name': 'timeout', 'type': 'magnitude', 'value': self.settings.timeout, 'tip': "wait time for result"},
                {'name': 'readWait', 'type': 'magnitude', 'value': self.settings.readWait, 'tip': "time to wait between readings"}]
