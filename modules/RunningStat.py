# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 07:25:59 2013

@author: pmaunz
"""
import math

# see Donald Knuth's Art of Computer Programming, Vol 2, page 232, 3rd edition
class RunningStat(object):
    def __init__(self, zero=0):  # giving zero should allow to pass numpy arrays to be averaged
        self.zero = zero
        self.clear()
        
    def clear(self):
        self.mOld = self.zero
        self.mNew = self.zero
        self.sOld = self.zero
        self.sNew = self.zero
        self.count = 0
        
    @property
    def mean(self):
        return self.mNew
        
    @property
    def variance(self):
        return self.sNew/(self.count-1) if self.count>1 else 0.0
        
    @property
    def stddev(self):
        return math.sqrt( self.variance )
        
    @property
    def stderr(self):
        return self.stddev / math.sqrt(self.count-1) if self.count>1 else 0
        
    def add(self, value):
        if not( value is None or math.isnan(value) or math.isinf(value) ):
            self.count += 1
            if self.count == 1:
                self.mOld = value
                self.mNew = value
                self.sOld = 0
                self.sNew = 0
            else:
                self.mNew = self.mOld + ( value - self.mOld )/self.count
                self.sNew = self.sOld + ( value - self.mOld ) * ( value - self.mNew )
                
                self.mOld = self.mNew
                self.sOld = self.sNew
        
