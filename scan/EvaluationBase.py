'''
Created on Nov 3, 2015

@author: wolverine
'''
from modules.Observable import Observable
from pyqtgraph.parametertree import Parameter
from PyQt4 import QtCore
import logging
import copy
import numpy

EvaluationAlgorithms = {}

class EvaluationException(Exception):
    pass

class EvaluationMeta(type):
    def __new__(self, name, bases, dct):
        evalclass = super(EvaluationMeta, self).__new__(self, name, bases, dct)
        if name!='EvaluationBase':
            if 'name' not in dct:
                raise EvaluationException("Evaluation class needs to have class attribute 'name'")
            EvaluationAlgorithms[dct['name']] = evalclass
        return evalclass


class EvaluationBase(Observable):
    __metaclass__ = EvaluationMeta
    hasChannel = True
    def __init__(self, globalDict, settings= None):
        Observable.__init__(self)
        self.settings = settings if settings else dict()
        self.globalDict = globalDict
        self.setDefault()
        self._parameter = Parameter.create(name='params', type='group',children=self.children())
        try:
            self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        except TypeError:
            # connection already exists, just ignore it
            logging.getLogger(__name__).warning("EvaluationBase parameter connection already exists")
        self.settingsName = None
               
    def update(self, param, changes):
        for param, _, data in changes:
            self.settings[param.name()] = data
        self.firebare()
            
    def children(self):
        return []    
    
    def setSettings(self, settings, settingsName):
        try:
            for name, value in self.settings.iteritems():
                settings.setdefault(name, value)
            self.settings = settings
            for name, value in settings.items():
                try:
                    self._parameter[name] = value
                except Exception:
                    settings.pop(name)
            self.settingsName = settingsName if settingsName else "unnamed"
        except Exception as ex:
            logging.getLogger(__name__).exception(ex)
        
    def setSettingsName(self, settingsName):
        self.settingsName = settingsName

    @property
    def parameter(self):
        # re-create to prevent exception for signal not connected
        self._parameter = Parameter.create(name=self.settingsName, type='group',children=self.children())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        return self._parameter
    
    def __deepcopy__(self, memo=None):
        return type(self)( copy.deepcopy(self.settings,memo) )
  
    def histogram(self, data, evaluation, histogramBins=50 ):
        countarray = evaluation.getChannelData(data)
        y, x = numpy.histogram( countarray , range=(0,histogramBins), bins=histogramBins)
        return y, x, None   # third parameter is optional function 
    