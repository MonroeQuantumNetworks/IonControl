# -*- coding: utf-8 -*-
"""
Algorithms to evaluate the observed counts from a sequence of experiments:
This is used for simple averaging but also for different state detection algorithms

algorithms are expected to defined the fileds as stated in MeanEvaluation

"""
import numpy
import math

class MeanEvaluation:
    """
    returns mean and shot noise error
    """
    def __init__(self):
        self.parameters = dict()      # parameters (can be edited in the gui)
        self.name = "Mean"            # name (used by gui)
        self.tooltip = "Mean of observed counts"  # tooltip (used by gui)
        
    def evaluate(self, countarray, timestamps=None ):
        mean = numpy.mean( countarray )
        stderror = math.sqrt( mean/len(countarray))
        return mean, stderror

class ThresholdEvaluation:
    """
    simple threshold state detection: if more than threshold counts are observed 
    the ion is considered bright. For threshold photons or less it is considered
    dark.
    """
    def __init__(self):
        self.parameters = { 'threshold':1 }
        self.name = "Threshold"
        self.tooltip = "Obove threshold is bright"
        
    def evaluate(self, countarray, timestamps=None ):
        threshold = self.parameters['threshold']
        descriminated = [ 1 if count > threshold else 0 for count in countarray ]
        mean = numpy.mean( descriminated )
        N = len(countarray)
        error = mean*(1-mean)/N/math.sqrt(N)
        return mean, error
    
EvaluationAlgorithms = { 'Mean': MeanEvaluation, 'Threshold': ThresholdEvaluation }

