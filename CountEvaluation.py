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
         
    def evaluate(self, countarray, timestamps=None ):
        summe = numpy.sum( countarray )
        l = len(countarray)
        mean = summe/float(l)
        stderror = math.sqrt( mean/float(l) )
        return mean, (stderror/2., stderror/2. ), summe

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
        
    def evaluate(self, countarray, timestamps=None ):
        if not countarray:
            return None, None, None
        N = len(countarray)
        if self.settings['invert']:
            descriminated = [ 0 if count > self.settings['threshold'] else 1 for count in countarray ]
        else:
            descriminated = [ 1 if count > self.settings['threshold'] else 0 for count in countarray ]
        summe = numpy.sum( descriminated )
        bottom = summe*(N-summe)
        top = bottom
        if summe==0:
            top = (N-1)/2.
        elif summe==N:
            bottom = (N-1)/2.
        norm = pow(float(N),-3.5)
        return summe/float(N), (bottom*norm, top*norm), summe
        
    def children(self):
        return [{'name':'threshold','type':'int','value':1},
                {'name':'invert', 'type': 'bool', 'value':False }]     

   
EvaluationAlgorithms = { 'Mean': MeanEvaluation, 'Threshold': ThresholdEvaluation }

