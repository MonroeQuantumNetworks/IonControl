'''
Created on May 18, 2014

@author: pmaunz
'''
import math
from modules.magnitude import MagnitudeError

class ScanSegmentDefinition(object):
    def __init__(self):
        self._start = 0
        self._stop = 1
        self._center = 0.5
        self._span = 1
        self._steps = 2
        self._stepsize = 1
        self._stepPreference = 'stepsize'
        self._inconsistent = False
        
    def __setstate__(self, d):
        self.__dict__ = d
        self.__dict__.setdefault('_inconsistent',False)
        
    stateFields = ['_start', '_stop', '_center', '_span', '_steps', '_stepsize', '_stepPreference'] 
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))
        
    @property
    def start(self):
        return self._start
    
    @start.setter
    def start(self, start):
        self._start = start
        self.calculateCenterSpan()
        
    @property
    def stop(self):
        return self._stop
    
    @stop.setter
    def stop(self, stop):
        self._stop = stop
        self.calculateCenterSpan()
        
    def calculateCenterSpan(self):
        try:
            self._span = abs(self._stop - self._start)
            self._center = self._start + (self._stop-self._start)/2
            if self._stepPreference=='steps' and self._steps>1:
                self._stepsize = self._span / (self._steps-1)
            else:
                self._steps = math.ceil(self._span / self._stepsize + 1) 
            self._inconsistent = False
        except MagnitudeError:
            self._inconsistent = True
          
    @property
    def center(self):
        return self._center
        
    @center.setter  
    def center(self, center):
        self._center = center
        try:
            self.calculateStartStop()
            self._inconsistent = False
        except MagnitudeError:
            self._inconsistent = True
        
    @property
    def span(self):
        return self._span
    
    @span.setter
    def span(self, span):
        self._span = span
        try:
            self.calculateStartStop()
            if self._stepPreference=='steps' and self._steps>1:
                self._stepsize = self._span / (self._steps-1)
            else:
                self._steps = math.ceil(self._span / self._stepsize) + 1
            self._inconsistent = False
        except MagnitudeError:
            self._inconsistent = True
            
        
    def calculateStartStop(self):
        self._start = self._center - self._span/2
        self._stop = self._center + self._span/2
        
    @property
    def steps(self):
        return self._steps
    
    @steps.setter
    def steps(self, steps):
        self._steps = max( steps, 2 )
        self._stepPreference = 'steps'
        self._stepsize = self._span / (self._steps-1)
        
    @property
    def stepsize(self):
        return self._stepsize
    
    @stepsize.setter
    def stepsize(self, stepsize):
        try:
            self._stepsize = stepsize
            self._stepPreference = 'stepsize'
            self._steps = math.ceil(self._span / self._stepsize+1) 
            self._inconsistent = False
        except MagnitudeError:
            self._inconsistent = True
        
    @property
    def inconsistent(self):
        return self._inconsistent
