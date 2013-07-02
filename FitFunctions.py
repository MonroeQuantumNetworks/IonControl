# -*- coding: utf-8 -*-
"""
Created on Sat Jan 19 10:47:59 2013

@author: pmaunz
"""
import numpy

from FitFunctionBase import FitFunctionBase
from modules import MagnitudeParser

class CosFit(FitFunctionBase):
    name = "Cos"
    def __init__(self):
        FitFunctionBase.__init__(self)
        self.functionString =  'A*cos(2*pi*k*x+theta)+O'
        self.parameterNames = [ 'A', 'k', 'theta', 'O' ]
        self.parameters = [1,1,0,0]
        self.startParameters = [1,1,0,0]
        
    def residuals(self,p, y, x):
        A,k,theta,O = p
        return y-A*numpy.cos(2*numpy.pi*k*x+theta)-O
        
    def value(self,x,p=None):
        A,k,theta, O = self.parameters if p is None else p
        return A*numpy.cos(2*numpy.pi*k*x+theta)+O

class CosSqFit(FitFunctionBase):
    name = "Cos2"
    def __init__(self):
        FitFunctionBase.__init__(self)
        self.functionString =  'A*cos^2(pi*x/(2*T)+theta)+O'
        self.parameterNames = [ 'A', 'T', 'theta', 'O' ]
        self.parameters = [1,100,0,0]
        self.startParameters = [1,1,0,0]
       
    def residuals(self,p, y, x):
        A,T,theta,O = p
        return y-A*numpy.square(numpy.cos(numpy.pi/2/T*x+theta))-O
        
    def value(self,x,p=None):
        A,T,theta, O = self.parameters if p is None else p
        return A*numpy.square(numpy.cos(numpy.pi/2/T*x+theta))+O
        

class SinSqFit(FitFunctionBase):
    name = "Sin2"
    def __init__(self):
        FitFunctionBase.__init__(self)
        self.functionString =  'A*sin^2(pi/(2*T)*x+theta)+O'
        self.parameterNames = [ 'A', 'T', 'theta', 'O' ]
        self.parameters = [1,100,0,0]
        self.startParameters = [1,100,0,0]
        
    def residuals(self,p, y, x):
        A,T,theta,O = p
        return y-A*numpy.square(numpy.sin(numpy.pi/2/T*x+theta))-O
        
    def value(self,x,p=None):
        A,T,theta, O = self.parameters if p is None else p
        return A*numpy.square(numpy.sin(numpy.pi/2/T*x+theta))+O
        
class GaussianFit(FitFunctionBase):
    name = "Gaussian"
    def __init__(self):
        FitFunctionBase.__init__(self)
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

class SquareRabiFit(FitFunctionBase):
    name = "Square Rabi"
    def __init__(self):
        FitFunctionBase.__init__(self)
        self.functionString =  'A*R**2/(R**2+(x-C)**2) *sin**2(sqrt(R**2+(x-C)**2)*t/2)+O where R=2*pi/T'
        self.parameterNames = [ 'T', 'C', 'A', 'O' ]
        self.parameters = [0]*4
        self.startParameters = [1,42,1,0]
        self.constantNames = ['t']
        self.t = 100
        
    def residuals(self,p, y, x):
        T, C, A, O = p
        Rs = numpy.square(2*numpy.pi/T)
        Ds = numpy.square(2*numpy.pi*(x-C))
        return y-(A*Rs/(Rs+Ds)*numpy.square(numpy.sin(numpy.sqrt(Rs+Ds)*self.t/2)))-O
        
    def value(self,x,p=None):
        T, C, A, O = self.parameters if p is None else p
        Rs = numpy.square(2*numpy.pi/T)
        Ds = numpy.square(2*numpy.pi*(x-C))
        return (A*Rs/(Rs+Ds)*numpy.square(numpy.sin(numpy.sqrt(Rs+Ds)*self.t/2)))+O
    

class LorentzianFit(FitFunctionBase):
    name = "Lorentzian"
    def __init__(self):
        FitFunctionBase.__init__(self)
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
        
class TruncatedLorentzianFit(FitFunctionBase):
    name = "Truncated Lorentzian"
    def __init__(self):
        FitFunctionBase.__init__(self)
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
        
from RabiCarrierFunction import RabiCarrierFunction, FullRabiCarrierFunction       
        
fitFunctionMap = { GaussianFit.name: GaussianFit, 
                   CosFit.name: CosFit, 
                   CosSqFit.name: CosSqFit,
                   SinSqFit.name: SinSqFit,
                   SquareRabiFit.name: SquareRabiFit,
                   LorentzianFit.name: LorentzianFit,
                   TruncatedLorentzianFit.name: TruncatedLorentzianFit,
                   RabiCarrierFunction.name: RabiCarrierFunction,
                   FullRabiCarrierFunction.name: FullRabiCarrierFunction }

def fitFunctionFactory(text):
    """
    Creates a FitFunction Object from a saved string representation
    """
    parts = text.split(';')
    components = parts[0].split(',')
    name = components[0].strip()
    function = fitFunctionMap[name]()
    for index, arg in enumerate(components[2:]):
        value = float(arg.split('=')[1].strip())
        function.parameters[index] = value
    print parts
    if len(parts)>1 and len(parts[1])>0:
        components = parts[1].split(',')
        for item in components:
            print item
            name, value = item.split('=')
            print "'{0}' '{1}' '{2}'".format(item,name.strip(),value.strip())
            setattr(function, name.strip(), MagnitudeParser.parse(value.strip()))
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