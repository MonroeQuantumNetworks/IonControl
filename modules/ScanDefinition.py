'''
Created on May 18, 2014

@author: pmaunz
'''
import math

class ScanSegmentDefinition:
    def __init__(self):
        self.start = 0
        self.stop = 1
        self.center = 0.5
        self.span = 1
        self.steps = 2
        self.stepsize = 1
        self.stepPreference = 'stepsize'
        
    def setStart(self, start):
        self.start = start
        self.calculateCenterSpan
        
    def setStop(self, stop):
        self.stop = stop
        self.calculateCenterSpan()
        
    def calculateCenterSpan(self):
        self.span = abs(self.stop - self.start)
        self.center = self.start + (self.stop-self.start)/2
        if self.stepPreference=='steps' and self.steps>1:
            self.stepsize = self.span / (self.steps-1)
        else:
            self.steps = math.ceil(self.span / self.stepsize)
            
    def setCenter(self, center):
        self.center = center
        self.calculateStartStop()
        
    def setSpan(self, span):
        self.span = span
        self.calculateStartStop()
        if self.stepPreference=='steps' and self.steps>1:
            self.stepsize = self.span / (self.steps-1)
        else:
            self.steps = math.ceil(self.span / self.stepsize)
        
    def calculateStartStop(self):
        self.start = self.center - self.span/2
        self.stop = self.center + self.span/2
        
    def setSteps(self, steps):
        self.steps = max( steps, 2 )
        self.stepPreference = 'steps'
        self.stepsize = self.span / (self.steps-1)
        
    def setStepsize(self, stepsize):
        self.stepsize = stepsize
        self.stepPreference = 'stepsize'
        self.steps = math.ceil(self.span / self.stepsize)
        
            
