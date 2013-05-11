# -*- coding: utf-8 -*-
"""
Created on Sat Jan 19 10:47:59 2013

@author: pmaunz
"""
import numpy
from scipy.optimize import leastsq


class FitFunction(object):
    name = 'None'
    def __init__(self):
        self.epsfcn=0.0
        self.parameterNames = []
        self.parameters = []

    def leastsq(self, x, y, parameters=None):
        if parameters is None:
            parameters = self.parameters
        self.parameters, self.n = leastsq(self.residuals, parameters, args=(y,x), epsfcn=self.epsfcn)
        print self.parameters
        return self.parameters
        
    def __str__(self):
         return ", ".join([self.name, self.functionString] + [ "{0}={1}".format(name, value) for name, value in zip(self.parameterNames,self.parameters)])

class CosFit(FitFunction):
    name = "Cos"
    def __init__(self):
        FitFunction.__init__(self)
        self.functionString =  'A*cos(2*pi*k*x+theta)'
        self.parameterNames = [ 'A', 'k', 'theta' ]
        self.parameters = [1,1,0]
        self.startParameters = [1,1,0]
        
    def residuals(self,p, y, x):
        A,k,theta = p
        return y-A*numpy.cos(2*numpy.pi*k*x+theta)
        
    def value(self,x,p=None):
        A,k,theta = self.parameters if p is None else p
        return A*numpy.cos(2*numpy.pi*k*x+theta)
        
class GaussianFit(FitFunction):
    name = "Gaussian"
    def __init__(self):
        FitFunction.__init__(self)
        self.functionString =  'A*exp(-(x-x0)**2/s**2)+O'
        self.parameterNames = [ 'A', 'x0', 's', 'O' ]
        self.parameters = [0]*4
        self.startParameters = [1,0,1,0]
        
    def residuals(self,p, y, x):
        A,x0,s,O = p
        return y-(A*numpy.exp(-numpy.square((x-x0)/s))+O)
        
    def value(self,x,p=None):
        A,x0,s,O = self.parameters if p is None else p
        return A*numpy.exp(-numpy.square((x-x0)/s))+O


class LorentzianFit(FitFunction):
    name = "Lorentzian"
    def __init__(self):
        FitFunction.__init__(self)
        self.functionString =  'A*s**2*1/(s**2+(x-x0)**2)+O'
        self.parameterNames = [ 'A', 's', 'x0', 'O' ]
        self.parameters = [0]*4
        self.startParameters = [1,1,0,0]
        
    def residuals(self,p, y, x):
        A,s,x0,O = p
        s2 = numpy.square(s)
        return y-(A*s2/(s2+numpy.square(x-x0))+O)
        
    def value(self,x,p=None):
        A,s,x0,O  = self.parameters if p is None else p
        s2 = numpy.square(s)
        return A*s2/(s2+numpy.square(x-x0))+O
        
class TruncatedLorentzianFit(FitFunction):
    name = " Truncated Lorentzian"
    def __init__(self):
        FitFunction.__init__(self)
        self.functionString =  'A*s**2*1/(s**2+(x-x0)**2)+O'
        self.parameterNames = [ 'A', 's', 'x0', 'O' ]
        self.parameters = [0]*4
        self.startParameters = [1,1,0,0]
        self.epsfcn=10.0
        
    def residuals(self,p, y, x):
        A,s,x0,O = p
        s2 = numpy.square(s)
        return y-(A*s2/(s2+numpy.square(x-x0))*(1-numpy.sign(x-x0))/2+O)
        
    def value(self,x,p=None):
        A,s,x0,O  = self.parameters if p is None else p
        s2 = numpy.square(s)
        return (A*s2/(s2+numpy.square(x-x0)))*(1-numpy.sign(x-x0))/2+O
        
fitFunctionMap = { GaussianFit.name: GaussianFit, 
                   CosFit.name: CosFit, 
                   LorentzianFit.name: LorentzianFit,
                   TruncatedLorentzianFit.name: TruncatedLorentzianFit }

def fitFunctionFactory(text):
    """
    Creates a FitFunction Object from a saved string representation
    """
    components = text.split(',')
    name = components[0].strip()
    function = fitFunctionMap[name]()
    for index, arg in enumerate(components[2:]):
        value = float(arg.split('=')[1].strip())
        function.parameters[index] = value
    return function
        
        
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