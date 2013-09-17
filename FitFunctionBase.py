# -*- coding: utf-8 -*-
"""
Created on Thu May 16 20:53:03 2013

@author: pmaunz
"""

from scipy.optimize import leastsq

class FitFunctionBase(object):
    name = 'None'
    def __init__(self):
        self.epsfcn=0.0
        self.parameterNames = []
        self.parameters = []
        self.constantNames = []
        self.resultNames = []

    def leastsq(self, x, y, parameters=None):
        if parameters is None:
            parameters = self.parameters
        self.parameters, self.n = leastsq(self.residuals, parameters, args=(y,x), epsfcn=self.epsfcn)
        print self.parameters
        self.finalize(self.parameters)
        return self.parameters
        
    def __str__(self):
         return "; ".join([", ".join([self.name, self.functionString] + [ "{0}={1}".format(name, value) for name, value in zip(self.parameterNames,self.parameters)]),
                          ", ".join([ "{0}={1}".format(name,getattr(self,name)) for name in self.constantNames ])])

    def setConstant(self, name, value):
        setattr(self,name,value)
        
    def finalize(self,parameters):
        pass
