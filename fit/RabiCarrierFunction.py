# -*- coding: utf-8 -*-
"""
Created on Thu May 16 20:56:17 2013

@author: pmaunz
"""

from FitFunctionBase import ResultRecord
from fit.FitFunctionBase import FitFunctionBase
from scipy import constants
from numpy import pi, cos, sqrt, sin, exp, dot, array, log
from modules.magnitude import mg
from scipy.special import laguerre
import logging
from modules.MagnitudeUtilit import value

class RabiCarrierFunction(FitFunctionBase):
    name = "RabiCarrier"
    def __init__(self):
        FitFunctionBase.__init__(self)
        self.functionString =  'Explicit Carrier Rabi Trnasition with Lamb-Dicke approx'
        self.parameterNames = [ 'A', 'n', 'rabiFreq', 'mass','angle','trapFrequency','wavelength']
        self.parameters = [1,7,0.28,40,0,1.578,729]
        self.startParameters = [1,7,0.28,40,0,mg(1.578,'MHz'),mg(729,'nm')]
        self.units = [None, None, None, None, 'MHz', 'nm' ]
        # constants
        self.results['nstart'] = ResultRecord( name='nstart')
        self.results['taufinal'] = ResultRecord( name='taufinal')
        self.results['scTimeInit'] = ResultRecord( name='scTimeInit' )
        self.results['scIncrement'] = ResultRecord( name='scIncrement' )
        self.results['numberLoops'] = ResultRecord( name='numberLoops' )
        self.update()
        
    def update(self,parameters=None):
        A,n,omega,mass,angle,trapFrequency,wavelength = self.parameters if parameters is None else parameters
        m = mass * constants.m_p
        secfreq = trapFrequency.toval('Hz')
        eta = ( (2*pi/wavelength.toval('m'))*cos(angle*pi/180)
                     * sqrt(constants.hbar/(2*m*2*pi*secfreq)) )
        scTimeInit =  mg( (1/omega)/(eta*sqrt(n)), 'us')
        taufinal = mg( (1/omega)/(eta), 'us')
        nstart = 2*n
        self.results['nstart'].value = nstart
        self.results['scTimeInit'].value = scTimeInit
        self.results['scIncrement'].value = (taufinal-scTimeInit)/nstart
        self.results['taufinal'].value = taufinal
        self.results['eta'] = self.eta

        
    def residuals(self,p, y, x, sigma):
        A,n,omega,mass,angle,trapFrequency,wavelength = self.allFitParameters(p)
        secfreq = value(trapFrequency,'Hz')
        m = mass * constants.m_p
        eta = ( (2*pi/value(wavelength,'m'))*cos(angle*pi/180)
                     * sqrt(constants.hbar/(2*m*2*pi*secfreq)) )
        eta2 = pow(eta,2)
        if sigma is not None:
            return (y-( A/2*(1-1/(n+1)*(cos(2*omega*x)*(1-n/(n+1)*cos(2*omega*x*eta2))+(n/(n+1))*sin(2*omega*x)*sin(2*omega*x*eta2))/(1+(n/(n+1))**2
                -2*(n/(n+1))*cos(2*omega*x*eta2))) ))/sigma
        else:
            return y-( A/2*(1-1/(n+1)*(cos(2*omega*x)*(1-n/(n+1)*cos(2*omega*x*eta2))+(n/(n+1))*sin(2*omega*x)*sin(2*omega*x*eta2))/(1+(n/(n+1))**2
                -2*(n/(n+1))*cos(2*omega*x*eta2))) )
        
    def value(self,x,p=None):
        A,n,omega,mass,angle,trapFrequency,wavelength  = self.parameters if p is None else p
        secfreq = value(trapFrequency,'Hz')
        m = mass * constants.m_p
        eta = ( (2*pi/value(wavelength,'m'))*cos(angle*pi/180)
                     * sqrt(constants.hbar/(2*m*2*pi*secfreq)) )
        eta2 = pow(eta,2)
        value = ( A/2.*(1.-1./(n+1.)*(cos(2*omega*x)*(1-n/(n+1.)*cos(2*omega*x*eta2))+(n/(n+1.))*sin(2*omega*x)*sin(2*omega*x*eta2))/(1+(n/(n+1.))**2
                -2*(n/(n+1.))*cos(2*omega*x*eta2))) )
        return value
                

        
class FullRabiCarrierFunction(RabiCarrierFunction):
    name = "FullRabiCarrier"
    def __init__(self):
        super(FullRabiCarrierFunction,self).__init__()
        self.functionString =  'Numerical Carrier Rabi Transition without Lamb-Dicke approx'
        self.laguerreCacheEta = -1
        self.laguerreTable = None
        self.pnCacheBeta = -1
        self.pnTable = None
               
    def updateTables(self,beta):
        logger = logging.getLogger(__name__)
        A,n,omega,mass,angle,trapFrequency,wavelength = self.parameters
        secfreq = value(trapFrequency,'Hz')
        m = mass * constants.m_p
        eta = ( (2*pi/value(wavelength,'m'))*cos(angle*pi/180)
                     * sqrt(constants.hbar/(2*m*2*pi*secfreq)) )
        eta2 = pow(eta,2)
        if eta != self.laguerreCacheEta:
            logger.info( "Calculating Laguerre Table for eta^2={0}".format(eta2) )
            self.laguerreTable = array([ laguerre(n)(eta2) for n in range(200) ])
            self.laguerreCacheEta2 = eta
        if self.pnCacheBeta != beta:
            logger.info( "Calculating Probability Table for beta {0}".format(beta) )
            self.pnTable = array([ exp(-(n+1)*beta)*(exp(beta)-1) for n in range(200)])
            self.pnCacheBeta = beta
            logger.info( 1-sum(self.pnTable) )
            
        
    def residuals(self,p, y, x, sigma):
        A,n,omega,mass,angle,trapFrequency,wavelength = self.allFitParameters(p)
        secfreq = value(trapFrequency,'Hz')
        m = mass * constants.m_p
        eta = ( (2*pi/value(wavelength,'m'))*cos(angle*pi/180)
                     * sqrt(constants.hbar/(2*m*2*pi*secfreq)) )
        beta = log(1+1./n)
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
        A,n,omega,mass,angle,trapFrequency,wavelength = self.allFitParameters(p)
        secfreq = value(trapFrequency,'Hz')
        m = mass * constants.m_p
        eta = ( (2*pi/value(wavelength,'m'))*cos(angle*pi/180)
                     * sqrt(constants.hbar/(2*m*2*pi*secfreq)) )
        beta = log(1+1./n)
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
                
        