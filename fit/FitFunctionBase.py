# -*- coding: utf-8 -*-
"""
Created on Thu May 16 20:53:03 2013

@author: pmaunz
"""

from itertools import izip_longest
import logging
from math import sqrt

import numpy
from scipy.optimize import leastsq

from modules import magnitude
from modules.MagnitudeUtilit import value
from modules.SequenceDict import SequenceDict
import xml.etree.ElementTree as ElementTree
from modules.Expression import Expression
from modules.Observable import Observable
from packages.leastsqbound.leastsqbound import leastsqbound


class FitFunctionException(Exception):
    pass

class ResultRecord(object):
    def __init__(self, name=None, definition=None, value=None):
        self.name = name
        self.definition = definition
        self.value = value

    stateFields = ['name', 'definition', 'value'] 
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))
    
fitFunctionMap = dict()    
   
class FitFunctionMeta(type):
    def __new__(self, name, bases, dct):
        if 'name' not in dct:
            raise FitFunctionException("Fitfunction class needs to have class attribute 'name'")
        instrclass = super(FitFunctionMeta, self).__new__(self, name, bases, dct)
        fitFunctionMap[dct['name']] = instrclass
        return instrclass
    
def native(method):
    """Tag a method native to detect function overwrites in derived classes.
    Used to detect whether smartStartValues are implemented"""
    method.isNative = True
    return method    

class FitFunctionBase(object):
    __metaclass__ = FitFunctionMeta
    expression = Expression()
    name = 'None'
    parameterNames = list()
    def __init__(self, numParameters):
        self.epsfcn=0.0
        self.parameters = [0] * numParameters
        self.startParameters = [1] * numParameters 
        self.startParameterExpressions = None   # will be initialized by FitUiTableModel if values are available
        self.parameterEnabled = [True] * numParameters
        self.parametersConfidence = [None] * numParameters
        self.units = None
        self.results = SequenceDict({'RMSres': ResultRecord(name='RMSres')})
        self.useSmartStartValues = False
        self.hasSmartStart = not hasattr(self.smartStartValues, 'isNative' )
        self.parametersUpdated = Observable()
        self.parameterBounds = [[None,None] for _ in range(numParameters) ]
        self.parameterBoundsExpressions = None
        
    def __setstate__(self, state):
        state.pop( 'parameterNames', None )
        self.__dict__ = state
        self.__dict__.setdefault( 'useSmartStartValues', False )
        self.__dict__.setdefault( 'startParameterExpressions', None )
        self.__dict__.setdefault( 'parameterBounds' , [[None,None] for _ in range(len(self.parameterNames)) ]  )
        self.__dict__.setdefault( 'parameterBoundsExpressions' , None)
        self.hasSmartStart = not hasattr(self.smartStartValues, 'isNative' ) 
        self.parameterBounds = [[None,None] for _ in range(len(self.parameterNames)) ]
        self.parameterBoundsExpressions =  [[None,None] for _ in range(len(self.parameterNames)) ]
 
    def allFitParameters(self, p):
        """return a list where the disabled parameters are added to the enabled parameters given in p"""
        pindex = 0
        params = list()
        for index, enabled in enumerate(self.parameterEnabled):
            if enabled:
                params.append(p[pindex])
                pindex += 1
            else:
                params.append(value(self.startParameters[index]))
        return params
    
    def enabledStartParameters(self, parameters=None):
        """return a list of only the enabled start parameters"""
        if parameters is None:
            parameters = self.startParameters
        params = list()
        for enabled, param in zip(self.parameterEnabled, parameters):
            if enabled:
                params.append(value(param))
        return params

    def enabledFitParameters(self, parameters=None):
        """return a list of only the enabled fit parameters"""
        if parameters is None:
            parameters = self.parameters
        params = list()
        for enabled, param in zip(self.parameterEnabled, parameters):
            if enabled:
                params.append(value(param))
        return params

    def enabledParameterNames(self):
        """return a list of only the enabled fit parameters"""
        params = list()
        for enabled, param in zip(self.parameterEnabled, self.parameterNames):
            if enabled:
                params.append(param)
        return params
    
    def setEnabledFitParameters(self, parameters):
        """set the fitted parameters if enabled"""
        pindex = 0
        for index, enabled in enumerate(self.parameterEnabled):
            if enabled:
                self.parameters[index] = parameters[pindex]
                pindex += 1
            else:
                self.parameters[index] = value(self.startParameters[index])
    
    def setEnabledConfidenceParameters(self, confidence):
        """set the parameter confidence values for the enabled parameters"""
        pindex = 0
        for index, enabled in enumerate(self.parameterEnabled):
            if enabled:
                self.parametersConfidence[index] = confidence[pindex]
                pindex += 1
            else:
                self.parametersConfidence[index] = None        

    @native
    def smartStartValues(self, x, y, parameters, enabled):
        return None

    def evaluate(self, globalDict ):
        myReplacementDict = self.replacementDict()
        if globalDict is not None:
            myReplacementDict.update( globalDict )
        if self.startParameterExpressions is not None:
            self.startParameters = [param if expr is None else self.expression.evaluateAsMagnitude(expr, myReplacementDict ) for param, expr in zip(self.startParameters, self.startParameterExpressions)]
        if self.parameterBoundsExpressions is not None:
            self.parameterBounds = [[bound[0] if expr[0] is None else self.expression.evaluateAsMagnitude(expr[0], myReplacementDict),
                                     bound[1] if expr[1] is None else self.expression.evaluateAsMagnitude(expr[0], myReplacementDict)]
                                     for bound, expr in zip(self.parameterBounds, self.parameterBoundsExpressions)]

    def enabledBounds(self):
        result = [[value(bounds[0]), value(bounds[1])] for enabled, bounds in zip(self.parameterEnabled, self.parameterBounds) if enabled]
        enabled = any( (any(bounds) for bounds in result) )
        return result if enabled else None

    def leastsq(self, x, y, parameters=None, sigma=None):
        logger = logging.getLogger(__name__)
        # Ensure all values of sigma or non zero by replacing with the minimum nonzero value
        if sigma is not None:
            nonzerosigma = sigma[sigma>0]
            sigma[sigma==0] = numpy.min(nonzerosigma) if len(nonzerosigma)>0 else 1.0 
        if parameters is None:
            parameters = [value(param) for param in self.startParameters]
        if self.useSmartStartValues:
            smartParameters = self.smartStartValues(x,y,parameters,self.parameterEnabled)
            if smartParameters is not None:
                parameters = [ smartparam if enabled else param for enabled, param, smartparam in zip(self.parameterEnabled, parameters, smartParameters)]
        
        myEnabledBounds = self.enabledBounds()
        if myEnabledBounds:
            enabledOnlyParameters, self.cov_x, self.infodict, self.mesg, self.ier = leastsqbound(self.residuals, self.enabledStartParameters(parameters), 
                                                                                                 args=(y,x,sigma), epsfcn=self.epsfcn, full_output=True, bounds=myEnabledBounds)
        else:
            enabledOnlyParameters, self.cov_x, self.infodict, self.mesg, self.ier = leastsq(self.residuals, self.enabledStartParameters(parameters), args=(y,x,sigma), epsfcn=self.epsfcn, full_output=True)
        self.setEnabledFitParameters(enabledOnlyParameters)
        self.update(self.parameters)
        logger.info( "chisq {0}".format( sum(self.infodict["fvec"]*self.infodict["fvec"]) ) )        
        
        # calculate final chi square
        self.chisq=sum(self.infodict["fvec"]*self.infodict["fvec"])
        
        self.dof=len(x)-len(parameters)
        RMSres = magnitude.mg(sqrt(self.chisq/self.dof),'')
        RMSres.significantDigits = 3
        self.results['RMSres'].value = RMSres
        # chisq, sqrt(chisq/dof) agrees with gnuplot
        logger.info(  "success {0} {1}".format( self.ier, self.mesg ) )
        logger.info(  "Converged with chi squared {0}".format(self.chisq) )
        logger.info(  "degrees of freedom, dof {0}".format( self.dof ) )
        logger.info(  "RMS of residuals (i.e. sqrt(chisq/dof)) {0}".format( RMSres ) )
        logger.info(  "Reduced chisq (i.e. variance of residuals) {0}".format( self.chisq/self.dof ) )
        
        # uncertainties are calculated as per gnuplot, "fixing" the result
        # for non unit values of the reduced chisq.
        # values at min match gnuplot
        enabledParameterNames = self.enabledParameterNames()
        if self.cov_x is not None:
            enabledOnlyParametersConfidence = numpy.sqrt(numpy.diagonal(self.cov_x))*sqrt(self.chisq/self.dof)
            self.setEnabledConfidenceParameters(enabledOnlyParametersConfidence)
            logger.info(  "Fitted parameters at minimum, with 68% C.I.:" )
            for i,pmin in enumerate(enabledOnlyParameters):
                logger.info(  "%2i %-10s %12f +/- %10f"%(i,enabledParameterNames[i],pmin,sqrt(max(self.cov_x[i,i],0))*sqrt(self.chisq/self.dof)) )
        
            logger.info(  "Correlation matrix" )
            # correlation matrix close to gnuplot
            messagelist = ["               "]
            for i in range(len(enabledOnlyParameters)): messagelist.append( "%-10s"%(enabledParameterNames[i],) )
            logger.info( " ".join(messagelist))
            messagelist = []
            for i in range(len(enabledOnlyParameters)):
                messagelist.append( "%10s"%enabledParameterNames[i] )
                for j in range(i+1):
                    messagelist.append(  "%10f"%(self.cov_x[i,j]/sqrt(abs(self.cov_x[i,i]*self.cov_x[j,j])),) )
                logger.info( " ".join(messagelist))
    
                #-----------------------------------------------
        else:
            self.parametersConfidence = [None]*len(self.parametersConfidence)
 
        return self.parameters
                
    def __str__(self):
        return "; ".join([", ".join([self.name, self.functionString] + [ "{0}={1}".format(name, value) for name, value in zip(self.parameterNames,self.parameters)])])

    def setConstant(self, name, value):
        setattr(self,name,value)
        
    def update(self,parameters=None):
        self.parametersUpdated.fire( values=self.replacementDict() )
    
    def toXmlElement(self, parent):
        myroot  = ElementTree.SubElement(parent, 'FitFunction', {'name': self.name, 'functionString': self.functionString})
        for name, value, confidence, enabled in izip_longest(self.parameterNames,self.parameters,self.parametersConfidence,self.parameterEnabled):
            e = ElementTree.SubElement( myroot, 'Parameter', {'name':name, 'confidence':repr(confidence), 'enabled': str(enabled)})
            e.text = str(value)
        for result in self.results.values():
            e = ElementTree.SubElement( myroot, 'Result', {'name':result.name, 'definition':str(result.definition)})
            e.text = str(result.value)
        return myroot
   
    def residuals(self,p, y, x, sigma):
        p = self.allFitParameters(p)
        if sigma is not None:
            return (y-self.functionEval(x, *p))/sigma
        else:
            return y-self.functionEval(x, *p)
        
    def value(self,x,p=None):
        p = self.parameters if p is None else p
        return self.functionEval(x, *p )

    def replacementDict(self):
        replacement = dict(zip(self.parameterNames,self.parameters))
        replacement.update( dict( ( (v.name, v.value) for v in self.results.values() ) ) )
        return replacement
    
        
        
