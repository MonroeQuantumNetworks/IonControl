# -*- coding: utf-8 -*-
"""
Algorithms to evaluate the observed counts from a sequence of experiments:
This is used for simple averaging but also for different state detection algorithms

algorithms are expected to defined the fileds as stated in MeanEvaluation

"""
import numpy
import math
from modules import dictutil

class EvaluationBase(object):
    def __init__(self):
        self.parameters = dict()               
        
    def setParameter(self, name, value):
        self.parameters[name] = value
        self.saveParam()

    def saveParam(self):
        pass

class MeanEvaluation:
    """
    returns mean and shot noise error
    """
    def __init__(self,config):
        self.parameters = dict()      # parameters (can be edited in the gui)
        self.name = "Mean"            # name (used by gui)
        self.tooltip = "Mean of observed counts"  # tooltip (used by gui)
        
    def evaluate(self, countarray, timestamps=None ):
        mean = numpy.mean( countarray )
        stderror = math.sqrt( mean/len(countarray))
        return mean, (stderror/2., stderror/2. )

class ThresholdEvaluation(EvaluationBase):
    """
    simple threshold state detection: if more than threshold counts are observed 
    the ion is considered bright. For threshold photons or less it is considered
    dark.
    """
    def __init__(self,config):
        self.config = config
        self.parameters = self.config.get('ThresholdEvaluation.Parameters',dict())
        dictutil.setdefault( self.parameters, { 'threshold':1, 'invert':0 })
        self.name = "Threshold"
        self.tooltip = "Obove threshold is bright"
        self.saveParam()
        
    def evaluate(self, countarray, timestamps=None ):
        if not countarray:
            return None, None
        N = len(countarray)
        threshold = self.parameters['threshold']
        if bool(self.parameters['invert']):
            descriminated = [ 0 if count > threshold else 1 for count in countarray ]
        else:
            descriminated = [ 1 if count > threshold else 0 for count in countarray ]
        summe = numpy.sum( descriminated )
        bottom = summe*(N-summe)
        top = bottom
        print N, summe
        if summe==0:
            print "summe==0"
            top = (N-1)/2.
        elif summe==N:
            print "summe==N"
            bottom = (N-1)/2.
            print bottom
        norm = pow(N,-3.5)
        return summe/N, (bottom*norm, top*norm)
        
    def saveParam(self):
        self.config['ThresholdEvaluation.Parameters'] = self.parameters

    
EvaluationAlgorithms = { 'Mean': MeanEvaluation, 'Threshold': ThresholdEvaluation }

