# -*- coding: utf-8 -*-
"""
Created on Sat Jan 19 10:47:59 2013

@author: pmaunz
"""
import numpy
from scipy.optimize import leastsq


class FitFunction(object):
    def __init__(self):
        pass

    def leastsq(self, x, y, parameters=None):
        if parameters is None:
            parameters = self.parameters
        print parameters
        self.parameters, self.n = leastsq(self.residuals, parameters, args=(y,x))
        return self.parameters

class CosFit(FitFunction):
    def __init__(self):
        FitFunction.__init__(self)
        self.functionString =  'A*cos(2*pi*k*x+theta)'
        self.parameterNames = [ 'A', 'k', 'theta' ]
        self.parameters = [0]*3
        self.startParameters = [0]*3
        self.name = "Cos"
        
    def residuals(self,p, y, x):
        A,k,theta = p
        return y-A*numpy.cos(2*numpy.pi*k*x+theta)
        
    def value(self,x,p=None):
        A,k,theta = self.parameters if p is None else p
        return A*numpy.cos(2*numpy.pi*k*x+theta)
        
        
if __name__ == "__main__":
    x = numpy.arange(0,6e-2,6e-2/30)
    A,k,theta = 10, 1.0/3e-2, numpy.pi/6
    y_true = A*numpy.sin(2*numpy.pi*k*x+theta)
    y_meas = y_true + 2*numpy.random.randn(len(x))
    
    f = CosFit()
    p = [8, 1/2.3e-2, 1]
    ls, n = f.leastsq(x, y_meas, p )
    
    import matplotlib.pyplot as plt
    plt.plot(x,f.value(x,ls),x,y_meas,'o',x,y_true)
    plt.title('Least-squares fit to noisy data')
    plt.legend(['Fit', 'Noisy', 'True'])
    plt.show() 