# -*- coding: utf-8 -*-
"""
Created on Tue Apr 09 13:34:39 2013

@author: wolverine
"""

import numpy
import math

class MeanEvaluation:
    def __init__(self):
        self.parameters = dict()
        self.name = "Mean"
        self.tooltip = "Mean of observed counts"
        
    def evaluate(self, countarray, timestamps=None ):
        mean = numpy.mean( countarray )
        stderror = math.sqrt( mean/len(countarray))
        return mean, stderror

class ThresholdEvaluation:
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

