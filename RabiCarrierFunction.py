# -*- coding: utf-8 -*-
"""
Created on Thu May 16 20:56:17 2013

@author: pmaunz
"""

from FitFunctionBase import FitFunctionBase
from scipy import constants
from numpy import pi, cos, sqrt, sin
from magnitude import mg

class RabiCarrierFunction(FitFunctionBase):
    name = "RabiCarrier"
    def __init__(self):
        FitFunctionBase.__init__(self)
        self.functionString =  ''
        self.parameterNames = [ 'A', 'n', 'rabiFreq' ]
        self.parameters = [0]*3
        self.startParameters = [1,7,0.28]
        # constants
        self.constantNames = ['mass','angle','trapFrequency','wavelength']
        self.mass = 40
        self.angle = 0
        self.trapFrequency = mg(1.578,'MHz')
        self.wavelength = mg(729,'nm' )
        self.resultNames = ['nstart','taufinal','scTimeInit','scIncrement']
        self.nstart=None
        self.taufinal=None
        self.scTimeInit=None
        self.scIncrement=None
        self.number_of_loops=None
        self.update()
        
    def setConstant(self, name, value):
        setattr(self,name,value)
        self.update()
        
    def update(self):
        self.m = self.mass * constants.m_p
        self.secfreq = self.trapFrequency.toval('Hz')
        self.eta = ( (2*pi/self.wavelength.toval('m'))*cos(self.angle*pi/180)
                     * sqrt(constants.hbar/(2*self.m*2*pi*self.secfreq)) )
        self.eta2 = pow(self.eta,2)

        
    def residuals(self,p, y, x):
        A,n,omega = p
        #return y-(A*s2/(s2+numpy.square(x-x0))+O)
        return y-( A/2*(1-1/(n+1)*(cos(2*omega*x)*(1-n/(n+1)*cos(2*omega*x*self.eta2))+(n/(n+1))*sin(2*omega*x)*sin(2*omega*x*self.eta2))/(1+(n/(n+1))**2
                -2*(n/(n+1))*cos(2*omega*x*self.eta2))) )
        
    def value(self,x,p=None):
        A,n,omega  = self.parameters if p is None else p
        value = ( A/2.*(1.-1./(n+1.)*(cos(2*omega*x)*(1-n/(n+1.)*cos(2*omega*x*self.eta2))+(n/(n+1.))*sin(2*omega*x)*sin(2*omega*x*self.eta2))/(1+(n/(n+1.))**2
                -2*(n/(n+1.))*cos(2*omega*x*self.eta2))) )
        return value
                
    def finalize(self,parameters):
        A,n,omega = parameters
        self.nstart=2*n
        self.taufinal= mg( (1/omega)/(self.eta), 'us')
        self.scTimeInit = mg( (1/omega)/(self.eta*sqrt(n)), 'us')
        self.scIncrement = (self.taufinal-self.scTimeInit)/self.nstart

        
        
