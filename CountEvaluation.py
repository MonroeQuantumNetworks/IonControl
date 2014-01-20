# -*- coding: utf-8 -*-
"""
Algorithms to evaluate the observed counts from a sequence of experiments:
This is used for simple averaging but also for different state detection algorithms

algorithms are expected to defined the fileds as stated in MeanEvaluation

"""
import numpy
import math
from pyqtgraph.parametertree import Parameter
from PyQt4 import QtCore
from Observable import Observable
from modules.enum import enum 
import copy

class EvaluationBase(Observable):
    def __init__(self,settings =  None):
        Observable.__init__(self)
        self.settings = settings if settings else dict()
        self.setDefault()
        self._parameter = Parameter.create(name='params', type='group',children=self.children())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        self.settingsName = None
               
    def update(self, param, changes):
        for param, _, data in changes:
            self.settings[param.name()] = data
        self.firebare()
            
    def children(self):
        return []    
    
    def setSettings(self, settings, settingsName):
        for name, value in self.settings.iteritems():
            settings.setdefault(name, value)
        self.settings = settings
        for name, value in settings.iteritems():
            self._parameter[name] = value
        self.settingsName = settingsName if settingsName else "unnamed"
        
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
  

class MeanEvaluation(EvaluationBase):
    """
    returns mean and shot noise error
    """
    name = 'Mean'
    tooltip = "Mean of observed counts" 
    errorBarType = enum('shotnoise','statistical')
    def __init__(self,settings=None):
        EvaluationBase.__init__(self,settings)
        self.errorBarTypeLookup = [ self.evaluateShotnoise, self.evaluateStatistical ]
        
    def setDefault(self):
        self.settings.setdefault('errorBars',False)
        self.settings.setdefault('errorBarType',0)
         
    def evaluateShotnoise(self, countarray ):
        summe = numpy.sum( countarray )
        l = float(len(countarray))
        mean = summe/l
        stderror = math.sqrt( max(summe,1) )/l
        return mean, (stderror/2. if summe>0 else 0, stderror/2. ), summe

    def evaluateStatistical(self, countarray):
        mean = numpy.mean( countarray )
        stderr = numpy.std( countarray, ddof=1 ) / math.sqrt( max( len(countarray)-1, 1) )
        return mean, (stderr/2.,stderr/2.), numpy.sum( countarray )
    
    def evaluate(self, countarray, timestamps=None ):
        if not countarray:
            return 0, (0,0), 0
        return self.errorBarTypeLookup[self.settings['errorBarType']](countarray)

    def children(self):
        return [{'name':'errorBars', 'type': 'bool', 'value':self.settings['errorBars'] },
                {'name':'errorBarType', 'type': 'list', 'values':self.errorBarType.mapping, 'value': self.settings['errorBarType'] } ]     

class NumberEvaluation(EvaluationBase):
    """
    returns mean and shot noise error
    """
    name = 'Number'
    tooltip = "Number of results" 
    def __init__(self,settings=None):
        EvaluationBase.__init__(self,settings)
        
    def setDefault(self):
        self.settings.setdefault('errorBars',False)
         
    def evaluate(self, countarray, timestamps=None ):
        if not countarray:
            return 0, (0,0), 0
        return len(countarray), (0,0), len(countarray)

    def children(self):
        return [{'name':'errorBars', 'type': 'bool', 'value':self.settings['errorBars'], 'readonly':True }]     


class ThresholdEvaluation(EvaluationBase):
    """
    simple threshold state detection: if more than threshold counts are observed 
    the ion is considered bright. For threshold photons or less it is considered
    dark.
    """
    name = "Threshold"
    tooltip = "Obove threshold is bright"
    def __init__(self,settings=None):
        EvaluationBase.__init__(self,settings)
        
    def setDefault(self):
        self.settings.setdefault('threshold',1)
        self.settings.setdefault('invert',False)
        self.settings.setdefault('errorBars',False)
        
    def evaluate(self, countarray, timestamps=None ):
        if not countarray:
            return None, None, None
        N = float(len(countarray))
        if self.settings['invert']:
            descriminated = [ 0 if count > self.settings['threshold'] else 1 for count in countarray ]
        else:
            descriminated = [ 1 if count > self.settings['threshold'] else 0 for count in countarray ]
        x = numpy.sum( descriminated )
        p = x/N
        # Wilson score interval with continuity correction
        # see http://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
        rootp = 3-1/N -4*p+4*N*(1-p)*p
        top = min( 1, (2 + 2*N*p + math.sqrt(rootp))/(2*(N+1)) ) if rootp>=0 else 1
        rootb = -1-1/N +4*p+4*N*(1-p)*p
        bottom = max( 0, (2*N*p - math.sqrt(rootb))/(2*(N+1)) ) if rootb>=0 else 0            
        return p, (p-bottom, top-p), x
        
    def children(self):
        return [{'name':'threshold','type':'int','value':self.settings['threshold']},
                {'name':'errorBars', 'type': 'bool', 'value':self.settings['errorBars'] },
                {'name':'invert', 'type': 'bool', 'value':self.settings['invert'] }]     
        
   
EvaluationAlgorithms = { MeanEvaluation.name: MeanEvaluation, 
                         ThresholdEvaluation.name: ThresholdEvaluation,
                         NumberEvaluation.name: NumberEvaluation }

