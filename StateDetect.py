# -*- coding: utf-8 -*-
"""
Created on Tue Apr 09 13:34:39 2013

@author: wolverine
"""


class 


class ThresholdEvaluation:
    def __init__(self):
        self.parameters = { 'threshold':1 }        
        
    def evaluate(self, countarray, timestamps=None ):
        threshold = self.parameters['threshold']
        return [ 1 if count > threshold else 0 for count in countarray ]
    
StateDetectAlgorithms = { 'Threshold': ThresholdStateDetect }

