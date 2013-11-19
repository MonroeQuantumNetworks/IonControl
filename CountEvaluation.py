# -*- coding: utf-8 -*-
"""
Algorithms to evaluate the observed counts from a sequence of experiments:
This is used for simple averaging but also for different state detection algorithms

algorithms are expected to defined the fileds as stated in MeanEvaluation

"""
import numpy
import math
from modules import dictutil
from pyqtgraph.parametertree import Parameter
from PyQt4 import QtCore
from Observable import Observable

class EvaluationBase(Observable):
    def __init__(self,settings =  None):
        Observable.__init__(self)
        self.settings = settings if settings else dict()
        self._parameter = Parameter.create(name='params', type='group',children=self.children())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
               
    def update(self, param, changes):
        for param, change, data in changes:
            self.settings[param.name()] = data
        self.firebare()
            
    def children(self):
        return []    
    
    def setSettings(self, settings):
        for name, value in self.settings.iteritems():
            settings.setdefault(name, value)
        self.settings = settings
        for name, value in settings.iteritems():
            self._parameter[name] = value

    @property
    def parameter(self):
        return self._parameter

class MeanEvaluation(EvaluationBase):
    """
    returns mean and shot noise error
    """
    name = 'Mean'
    tooltip = "Mean of observed counts" 
    def __init__(self,settings=None):
        EvaluationBase.__init__(self,settings)
        self.setdefault()
        
    def setdefault(self):
        self.settings.setdefault('errorBars',False)
         
    def evaluate(self, countarray, timestamps=None ):
        summe = numpy.sum( countarray )
        l = float(len(countarray))
        mean = summe/l
        stderror = math.sqrt( max(summe,1) )/l
        return mean, (stderror/2. if summe>0 else 0, stderror/2. ), summe

    def children(self):
        return [{'name':'errorBars', 'type': 'bool', 'value':False }]     

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
        self.setdefault()
        
    def setdefault(self):
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
        return [{'name':'threshold','type':'int','value':1},
                {'name':'errorBars', 'type': 'bool', 'value':False },
                {'name':'invert', 'type': 'bool', 'value':False }]     

   
EvaluationAlgorithms = { 'Mean': MeanEvaluation, 'Threshold': ThresholdEvaluation }

