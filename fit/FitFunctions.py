# -*- coding: utf-8 -*-
"""
Created on Sat Jan 19 10:47:59 2013

@author: pmaunz
"""
import numpy

from FitFunctionBase import ResultRecord, fitFunctionMap
from fit.FitFunctionBase import FitFunctionBase
from modules import MagnitudeParser
from modules.XmlUtilit import stringToStringOrNone

class CosFit(FitFunctionBase):
    name = "Cos"
    labelIcon = ":/latex/icons/cos.png"
    def __init__(self):
        FitFunctionBase.__init__(self)
        self.functionString =  'A*cos(2*pi*k*x+theta)+O'
        self.parameterNames = [ 'A', 'k', 'theta', 'O' ]
        self.parameters = [1,1,0,0]
        self.startParameters = [1,1,0,0]
        self.parameterEnabled = [True]*4
        self.parametersConfidence = [None]*4
        
    def residuals(self,p, y, x, sigma):
        A, k , theta, O = self.allFitParameters(p)
        if sigma is not None:
            return (y-A*numpy.cos(2*numpy.pi*k*x+theta)-O)/sigma
        else:
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
        self.parameterEnabled = [True]*4
        self.parametersConfidence = [None]*4
       
    def residuals(self,p, y, x, sigma):
        A,T,theta,O = self.allFitParameters(p)
        if sigma is not None:
            return (y-A*numpy.square(numpy.cos(numpy.pi/2/T*x+theta))-O)/sigma
        else:            
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
        self.parameterEnabled = [True]*4
        self.parametersConfidence = [None]*4
        
    def residuals(self,p, y, x, sigma):
        A,T,theta,O = self.allFitParameters(p)
        if sigma is not None:
            return (y-A*numpy.square(numpy.sin(numpy.pi/2/T*x+theta))-O)/sigma
        else:
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
        self.parameterEnabled = [True]*4
        self.parametersConfidence = [None]*4
        
    def residuals(self,p, y, x, sigma):
        A,x0,s,O = self.allFitParameters(p)
        if sigma is not None:
            return (y-(A*numpy.exp(-numpy.square((x-x0)/s))+O))/sigma
        else:
            return y-(A*numpy.exp(-numpy.square((x-x0)/s))+O)
        
    def value(self,x,p=None):
        A,x0,s,O = self.parameters if p is None else p
        return A*numpy.exp(-numpy.square((x-x0)/s))+O

class SquareRabiFit(FitFunctionBase):
    name = "Square Rabi"
    def __init__(self):
        FitFunctionBase.__init__(self)
        self.functionString =  'A*R**2/(R**2+(x-C)**2) *sin**2(sqrt(R**2+(x-C)**2)*t/2)+O where R=2*pi/T'
        self.parameterNames = [ 'T', 'C', 'A', 'O', 't' ]
        self.parameters = [0]*4
        self.startParameters = [1,42,1,0,100]
        self.parameterEnabled = [True]*5
        self.parametersConfidence = [None]*5
        
    def residuals(self,p, y, x, sigma):
        T, C, A, O, t = self.allFitParameters(p)
        Rs = numpy.square(2*numpy.pi/T)
        Ds = numpy.square(2*numpy.pi*(x-C))
        if sigma is not None:
            return (y-(A*Rs/(Rs+Ds)*numpy.square(numpy.sin(numpy.sqrt(Rs+Ds)*t/2.)))-O)/sigma
        else:
            return (y-(A*Rs/(Rs+Ds)*numpy.square(numpy.sin(numpy.sqrt(Rs+Ds)*t/2.)))-O)
        
    def value(self,x,p=None):
        T, C, A, O, t = self.parameters if p is None else p
        Rs = numpy.square(2*numpy.pi/T)
        Ds = numpy.square(2*numpy.pi*(x-C))
        return (A*Rs/(Rs+Ds)*numpy.square(numpy.sin(numpy.sqrt(Rs+Ds)*t/2.)))+O
    

class LorentzianFit(FitFunctionBase):
    name = "Lorentzian"
    def __init__(self):
        FitFunctionBase.__init__(self)
        self.functionString =  'A*s**2*1/(s**2+(x-x0)**2)+O'
        self.parameterNames = [ 'A', 's', 'x0', 'O' ]
        self.parameters = [0]*4
        self.startParameters = [1,1,0,0]
        self.parameterEnabled = [True]*4
        self.parametersConfidence = [None]*4
        
    def residuals(self,p, y, x, sigma):
        A,s,x0,O = self.allFitParameters(p)
        s2 = numpy.square(s)
        if sigma is not None:
            return (y-(A*s2/(s2+numpy.square(x-x0))+O))/sigma
        else:
            return (y-(A*s2/(s2+numpy.square(x-x0))+O))            
        
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
        self.parameterEnabled = [True]*4
        self.parametersConfidence = [None]*4
        
    def residuals(self,p, y, x, sigma):
        A,s,x0,O = self.allFitParameters(p)
        s2 = numpy.square(s)
        if sigma is not None:
            return (y-(A*s2/(s2+numpy.square(x-x0))*(1-numpy.sign(x-x0))/2+O))/sigma
        else:
            return (y-(A*s2/(s2+numpy.square(x-x0))*(1-numpy.sign(x-x0))/2+O))

        
    def value(self,x,p=None):
        A,s,x0,O  = self.parameters if p is None else p
        s2 = numpy.square(s)
        return (A*s2/(s2+numpy.square(x-x0)))*(1-numpy.sign(x-x0))/2+O

class LinearFit(FitFunctionBase):
    """class for fitting to a line
    """
    name = "Line"
    def __init__(self):
        FitFunctionBase.__init__(self)
        self.functionString =  'm*x + b'
        self.parameterNames = [ 'm', 'b' ]
        self.parameters = [1,0]
        self.startParameters = [1,0]
        self.halfpoint = 0        
        self.parameterEnabled = [True]*2
        self.parametersConfidence = [None]*2
        self.results['halfpoint'] = ResultRecord(name='halfpoint')
        
    def residuals(self,p, y, x, sigma):
        m,b = self.allFitParameters(p)
        if sigma is not None:
            return (y - m*x - b)/sigma
        else:
            return y - m*x - b
        
    def value(self,x,p=None):
        m, b = self.parameters if p is None else p
        return m*x + b
        
    def update(self,parameters):
        m, b = parameters
        self.results['halfpoint'].value = (0.5-b)/m

from fit.RabiCarrierFunction import RabiCarrierFunction, FullRabiCarrierFunction       
        
fitFunctionMap.update({ GaussianFit.name: GaussianFit, 
                       CosFit.name: CosFit, 
                       CosSqFit.name: CosSqFit,
                       SinSqFit.name: SinSqFit,
                       SquareRabiFit.name: SquareRabiFit,
                       LorentzianFit.name: LorentzianFit,
                       TruncatedLorentzianFit.name: TruncatedLorentzianFit,
                       RabiCarrierFunction.name: RabiCarrierFunction,
                       FullRabiCarrierFunction.name: FullRabiCarrierFunction,
                       LinearFit.name: LinearFit
                 } )       
        
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
    if len(parts)>1 and len(parts[1])>0:
        components = parts[1].split(',')
        for item in components:
            name, value = item.split('=')
            setattr(function, name.strip(), MagnitudeParser.parse(value.strip()))
    return function

def fromXmlElement(element):
    """
    Creates a FitFunction Object from a saved string representation
    """
    name = element.attrib['name']
    function = fitFunctionMap[name]()
    function.parametersConfidence = [None]*len(function.parameters)
    function.parameterEnabled = [True]*len(function.parameters)
    for index, parameter in enumerate(element.findall("Parameter")):
        value = float(parameter.text)
        function.parameters[index] = value
        function.parameterNames[index] = parameter.attrib['name']
        function.parametersConfidence[index] = float(parameter.attrib['confidence'])
        function.parameterEnabled[index] = parameter.attrib['enabled'] == "True"
    for index, parameter in enumerate(element.findall("Result")):
        name= parameter.attrib['name']
        function.results[name] = ResultRecord( name=name,
                               definition = stringToStringOrNone( parameter.attrib['definition'] ),
                               globalname = stringToStringOrNone( parameter.attrib['globalname'] ),
                               push = stringToStringOrNone( parameter.attrib['globalname'] ),
                               value = MagnitudeParser.parse(parameter.text) )
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