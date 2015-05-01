'''
Created on Feb 4, 2015

@author: pmaunz
'''

from FitFunctionBase import FitFunctionBase
from modules import MagnitudeUtilit
import numpy

class SelectLast(FitFunctionBase):
    name = "SelectLastValue"
    functionString =  'Choose last value'
    parameterNames = [ 'value' ]
    def __init__(self):
        FitFunctionBase.__init__(self)
        self.parameters = [0.0]
        self.startParameters = [0.0]
        
    def residuals(self,p, y, x, sigma):
        value = self.allFitParameters(p)
        if sigma is not None:
            return (y-value)/sigma
        else:
            return y-value
        
    def value(self,x,p=None):
        v,  = self.parameters if p is None else p
        return numpy.array( [v for _ in range(len(x))] )

    def leastsq(self, x, y, parameters=None, sigma=None):
        if parameters is None:
            parameters = [MagnitudeUtilit.value(param) for param in self.startParameters]
        self.parameters = [ y[-1] ]
        return self.parameters