# -*- coding: utf-8 -*-
"""
Created on Sat Jan 19 10:47:59 2013

@author: pmaunz
"""
import numpy
from scipy.optimize import leastsq


class FitFunction(object):
    def __init__(self):
        self.epsfcn=0.0

    def leastsq(self, x, y, parameters=None):
        if parameters is None:
            parameters = self.parameters
        print parameters
        self.parameters, self.n = leastsq(self.residuals, parameters, args=(y,x), epsfcn=self.epsfcn)
        return self.parameters

class CosFit(FitFunction):
    def __init__(self):
        FitFunction.__init__(self)
        self.functionString =  'A*cos(2*pi*k*x+theta)'
        self.parameterNames = [ 'A', 'k', 'theta' ]
        self.parameters = [1,1,0]
        self.startParameters = [1,1,0]
        self.name = "Cos"
        
    def residuals(self,p, y, x):
        A,k,theta = p
        return y-A*numpy.cos(2*numpy.pi*k*x+theta)
        
    def value(self,x,p=None):
        A,k,theta = self.parameters if p is None else p
        return A*numpy.cos(2*numpy.pi*k*x+theta)
        
class GaussianFit(FitFunction):
    def __init__(self):
        FitFunction.__init__(self)
        self.functionString =  'A*exp(-(x-x0)**2/s**2)+O'
        self.parameterNames = [ 'A', 'x0', 's', 'O' ]
        self.parameters = [0]*4
        self.startParameters = [1,0,1,0]
        self.name = "Gaussian"
        
    def residuals(self,p, y, x):
        A,x0,s,O = p
        return y-(A*numpy.exp(-numpy.square((x-x0)/s))+O)
        
    def value(self,x,p=None):
        A,x0,s,O = self.parameters if p is None else p
        return A*numpy.exp(-numpy.square((x-x0)/s))+O


class LorentzianFit(FitFunction):
    def __init__(self):
        FitFunction.__init__(self)
        self.functionString =  'A*s**2*1/(s**2+(x-x0)**2)+O'
        self.parameterNames = [ 'A', 's', 'x0', 'O' ]
        self.parameters = [0]*4
        self.startParameters = [1,1,0,0]
        self.name = "Lorentzian"
        
    def residuals(self,p, y, x):
        A,s,x0,O = p
        s2 = numpy.square(s)
        return y-(A*s2/(s2+numpy.square(x-x0))+O)
        
    def value(self,x,p=None):
        A,s,x0,O  = self.parameters if p is None else p
        s2 = numpy.square(s)
        return A*s2/(s2+numpy.square(x-x0))+O
        
class TruncatedLorentzianFit(FitFunction):
    def __init__(self):
        FitFunction.__init__(self)
        self.functionString =  'A*s**2*1/(s**2+(x-x0)**2)+O'
        self.parameterNames = [ 'A', 's', 'x0', 'O' ]
        self.parameters = [0]*4
        self.startParameters = [1,1,0,0]
        self.name = " Truncated Lorentzian"
        self.epsfcn=10.0
        
    def residuals(self,p, y, x):
        A,s,x0,O = p
        s2 = numpy.square(s)
        return y-(A*s2/(s2+numpy.square(x-x0))*(1-numpy.sign(x-x0))/2+O)
        
    def value(self,x,p=None):
        A,s,x0,O  = self.parameters if p is None else p
        s2 = numpy.square(s)
        return (A*s2/(s2+numpy.square(x-x0)))*(1-numpy.sign(x-x0))/2+O
        
        
        
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