# -*- coding: utf-8 -*-
"""
Created on Thu May 16 20:56:17 2013

@author: pmaunz
"""

from FitFunctionBase import FitFunctionBase
from scipy import constants
from numpy import pi, cos, sqrt, sin, exp, dot, array, log
from modules.magnitude import mg
from scipy.special import laguerre
import logging

class RabiCarrierFunction(FitFunctionBase):
    name = "RabiCarrier"
    def __init__(self):
        FitFunctionBase.__init__(self)
        self.functionString =  'Explicit Carrier Rabi Trnasition with Lamb-Dicke approx'
        self.parameterNames = [ 'A', 'n', 'rabiFreq' ]
        self.parameters = [0]*3
        self.startParameters = [1,7,0.28]
        # constants
        self.constantNames = ['mass','angle','trapFrequency','wavelength']
        self.mass = 40
        self.angle = 0
        self.trapFrequency = mg(1.578,'MHz')
        self.wavelength = mg(729,'nm' )
        self.resultNames = self.resultNames + ['nstart','taufinal','scTimeInit','scIncrement']
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

        
    def residuals(self,p, y, x, sigma):
        A,n,omega = p
        #return y-(A*s2/(s2+numpy.square(x-x0))+O)
        if sigma is not None:
            return (y-( A/2*(1-1/(n+1)*(cos(2*omega*x)*(1-n/(n+1)*cos(2*omega*x*self.eta2))+(n/(n+1))*sin(2*omega*x)*sin(2*omega*x*self.eta2))/(1+(n/(n+1))**2
                -2*(n/(n+1))*cos(2*omega*x*self.eta2))) ))/sigma
        else:
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

        
class FullRabiCarrierFunction(FitFunctionBase):
    name = "FullRabiCarrier"
    def __init__(self):
        FitFunctionBase.__init__(self)
        self.functionString =  'Numerical Carrier Rabi Transition without Lamb-Dicke approx'
        self.parameterNames = [ 'A', 'nbar', 'rabiFreq' ]
        self.parameters = [0]*3
        self.startParameters = [1,7,0.28]
        # constants
        self.constantNames = ['mass','angle','trapFrequency','wavelength']
        self.mass = 40
        self.angle = 0
        self.trapFrequency = mg(1.578,'MHz')
        self.wavelength = mg(729,'nm' )
        self.resultNames = self.resultNames + ['eta','taufinal','scTimeInit','scIncrement']
        self.nstart=None
        self.taufinal=None
        self.scTimeInit=None
        self.scIncrement=None
        self.number_of_loops=None
        self.update()
        self.laguerreCacheEta2 = -1
        self.laguerreTable = None
        self.pnCacheBeta = -1
        self.pnTable = None
        
    def setConstant(self, name, value):
        setattr(self,name,value)
        self.update()
        
    def update(self):
        self.m = self.mass * constants.m_p
        self.secfreq = self.trapFrequency.toval('Hz')
        self.eta = ( (2*pi/self.wavelength.toval('m'))*cos(self.angle*pi/180)
                     * sqrt(constants.hbar/(2*self.m*2*pi*self.secfreq)) )
        self.eta2 = pow(self.eta,2)
        
    def updateTables(self,beta):
        logger = logging.getLogger(__name__)
        if self.eta2 != self.laguerreCacheEta2:
            logger.info( "Calculating Laguerre Table for eta^2={0}".format(self.eta2) )
            self.laguerreTable = array([ laguerre(n)(self.eta2) for n in range(200) ])
            self.laguerreCacheEta2 = self.eta2
        if self.pnCacheBeta != beta:
            logger.info( "Calculating Probability Table for beta {0}".format(beta) )
            self.pnTable = array([ exp(-(n+1)*beta)*(exp(beta)-1) for n in range(200)])
            self.pnCacheBeta = beta
            logger.info( 1-sum(self.pnTable) )
            
        
    def residuals(self,p, y, x, sigma):
        A,nbar,omega = p
        beta = log(1+1./nbar)
        self.updateTables(beta)
        if hasattr(x,'__iter__'):
            result = list()
            for xn in x:
                valueList = sin((omega * xn )* self.laguerreTable )**2
                value = A*dot( self.pnTable, valueList )
                result.append(value)
        else:
            valueList = sin(omega * self.laguerreTable * x)**2
            result = A*dot( self.pnTable, valueList )
        if sigma is not None:
            return (y-result)/sigma
        else:
            return y-result
        
    def value(self,x,p=None):
        A,nbar,omega  = self.parameters if p is None else p
        beta = log(1+1./nbar)
        self.updateTables(beta)
        if hasattr(x,'__iter__'):
            result = list()
            for xn in x:
                valueList = sin((omega * xn )* self.laguerreTable )**2
                value = A*dot( self.pnTable, valueList )
                result.append(value)
        else:
            valueList = sin(omega * self.laguerreTable * x)**2
            result = A*dot( self.pnTable, valueList )
        return result
                
    def finalize(self,parameters):
        A,beta,omega = parameters
        self.nbar = exp(beta)/(exp(beta)-1)**2
        self.nstart=2*self.nbar
        self.taufinal= mg( (1/omega)/(self.eta), 'us')
        self.scTimeInit = mg( (1/omega)/(self.eta*sqrt(self.nbar)), 'us')
        self.scIncrement = (self.taufinal-self.scTimeInit)/self.nstart
        #self.scIncrement.out_unit()
        
