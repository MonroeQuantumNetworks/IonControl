'''
Created on Sep 30, 2014

@author: wolverine
'''

from numpy import pi, cos, sqrt, sin, exp, dot, array, log
from scipy import constants
from scipy.special import genlaguerre

from FitFunctionBase import ResultRecord
from fit.FitFunctionBase import FitFunctionBase
from modules import MagnitudeUtilit
from modules.magnitude import mg
import logging

def factorialRatio(nl,ng):
    r = 1
    for i in range(nl+1, ng+1):
        r *= i
    return r

def transitionAmplitude(eta, n, m):
    eta2 = eta*eta
    nl = min(n,m)
    ng = max(n,m)
    d = abs(n-m)
    return exp(-eta2/2) * pow(eta, d) * genlaguerre(nl, d)(eta2) / sqrt( factorialRatio(nl, ng ) ) if n>=0 and m>=0 else 0

class MotionalRabiFlopping(FitFunctionBase):
    name = "MotionalRabiFlopping"
    def __init__(self):
        FitFunctionBase.__init__(self)
        self.functionString =  'Motional Rabi Flopping'
        self.parameterNames = [ 'A', 'n', 'rabiFreq', 'mass','angle','trapFrequency','wavelength', 'delta_n']
        self.parameters = [1,7,0.28,40,0,1.578,729,0]
        self.startParameters = [1,7,0.28,40,0,mg(1.578,'MHz'),mg(729,'nm'),0]
        self.units = [None, None, None, None, None, 'MHz', 'nm', None ]
        self.parameterEnabled = [True, True, True, False, False, False, False, False ]
        self.parametersConfidence = [None]*8
        # constants
        self.results['eta'] = ResultRecord( name='eta',value=0 )
        self.update()
        self.laguerreCacheEta = -1
        self.laguerreTable = None
        self.pnCache_nBar = -1
        self.pnTable = None

    def update(self,parameters=None):
        A,n,omega,mass,angle,trapFrequency,wavelength,delta_n = self.parameters if parameters is None else parameters #@UnusedVariable
        m = mass * constants.m_p
        secfreq = trapFrequency*10**6
        eta = ( (2*pi/(wavelength*10**-9))*cos(angle*pi/180)
                     * sqrt(constants.hbar/(2*m*2*pi*secfreq)) )
        self.results['eta'] = ResultRecord( name='eta',value=eta )
               
    def updateTables(self,nBar):
        logger = logging.getLogger(__name__)
        A,n,omega,mass,angle,trapFrequency,wavelength,delta_n = self.parameters #@UnusedVariable
        secfreq = MagnitudeUtilit.value(trapFrequency,'Hz') * 10**6
        m = mass * constants.m_p
        eta = ( (2*pi/(wavelength*10**-9))*cos(angle*pi/180)
                     * sqrt(constants.hbar/(2*m*2*pi*secfreq)) )
        eta2 = pow(eta,2)
        if eta != self.laguerreCacheEta:
            logger.info( "Calculating Laguerre Table for eta^2={0}".format(eta2) )
            self.laguerreTable = array([ transitionAmplitude(eta, n, n+delta_n) for n in range(200) ])
            self.laguerreCacheEta = eta
        if self.pnCache_nBar != nBar:
            logger.info( "Calculating Probability Table for nBar {0}".format(nBar) )
            current = 1/(nBar+1)
            a = [current]
            factor = nBar*current
            for _ in range(1,200):
                current *= factor
                a.append( current )
            self.pnTable = array(a)
            self.pnCache_nBar = nBar
            logger.info( 1-sum(self.pnTable) )
            
        
    def residuals(self,p, y, x, sigma):
        A,n,omega,mass,angle,trapFrequency,wavelength,delta_n = self.allFitParameters(self.parameters if p is None else p) #@UnusedVariable
        self.updateTables(n)
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
        A,n,omega,mass,angle,trapFrequency,wavelength,delta_n = self.parameters if p is None else p  #@UnusedVariable
        self.updateTables(n)
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
                
        
