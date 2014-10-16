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


class ResultRecord(object):
    def __init__(self, name=None, definition=None, value=None):
        self.name = name
        self.definition = definition
        self.value = value

class PushVariable(object):
    expression = Expression()
    def __init__(self):
        self.push = False
        self.destinationName = None
        self.variableName = None
        self.definition = ""
        self.value = None
        self.minimum = ""
        self.maximum = ""
        
        
    def __setstate__(self, s):
        self.__dict__ = s
        self.__dict__.setdefault( 'destinationName', None )
        self.__dict__.setdefault( 'variableName', None )
        
    def evaluate(self, variables=dict(), useFloat=False):
        if self.definition:
            self.value = self.expression.evaluate( self.definition, variables, useFloat=useFloat )
        
    def pushRecord(self, variables=None):
        if variables is not None:
            self.evaluate(variables)
        if (self.push and self.destinationName is not None and self.destinationName != 'None' and 
            self.variableName is not None and self.variableName != 'None' and self.value is not None and 
            (not self.minimum or self.value >= self.minimum) and 
            (not self.maximum or self.value <= self.maximum)):
            return [(self.destinationName, self.variableName, self.value)]
        return []
    
    @property
    def key(self):
        return (self.destinationName, self.variableName)


class FitFunctionBase(object):
    name = 'None'
    def __init__(self):
        self.epsfcn=0.0
        self.parameterNames = []
        self.parameters = []
        self.startParameters = []
        self.parameterEnabled = []
        self.parametersConfidence = []
        self.pushVariables = SequenceDict()
        self.units = None
        self.results = SequenceDict({'RMSres': ResultRecord(name='RMSres')})
        self.useSmartStartValues = False
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault( 'pushVariables', SequenceDict() )
        self.__dict__.setdefault( 'useSmartStartValues', False )

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

    def smartStartValues(self, x, y, parameters, enabled):
        return None

    def leastsq(self, x, y, parameters=None, sigma=None):
        logger = logging.getLogger(__name__)
        if parameters is None:
            parameters = [value(param) for param in self.startParameters]
        if self.useSmartStartValues:
            smartParameters = self.smartStartValues(x,y,parameters,self.parameterEnabled)
            if smartParameters is not None:
                parameters = [ smartparam if enabled else param for enabled, param, smartparam in zip(self.parameterEnabled, parameters, smartParameters)]
        
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
                    messagelist.append(  "%10f"%(self.cov_x[i,j]/sqrt(self.cov_x[i,i]*self.cov_x[j,j]),) )
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
        pass
    
    def toXmlElement(self, parent):
        myroot  = ElementTree.SubElement(parent, 'FitFunction', {'name': self.name, 'functionString': self.functionString})
        for name, value, confidence, enabled in izip_longest(self.parameterNames,self.parameters,self.parametersConfidence,self.parameterEnabled):
            e = ElementTree.SubElement( myroot, 'Parameter', {'name':name, 'confidence':repr(confidence), 'enabled': str(enabled)})
            e.text = str(value)
        for result in self.results.values():
            e = ElementTree.SubElement( myroot, 'Result', {'name':result.name, 'definition':str(result.definition)})
            e.text = str(result.value)
        for push in self.pushVariables.values():
            e = ElementTree.SubElement( myroot, 'PushVariable', {'destination':push.destinationName, 'variable':push.variableName, 'definition': push.definition, 'value': str(push.value), 'minimum': str(push.minimum), 'maximum': str(push.maximum)})
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

    def pushVariableValues(self):
        pushVarValues = list()
        for pushvar in self.pushVariables.values():
            pushVarValues.extend( pushvar.pushRecord(self.replacementDict()) )
        return pushVarValues
            
    def replacementDict(self):
        replacement = dict(zip(self.parameterNames,self.parameters))
        replacement.update( dict( ( (v.name, v.value) for v in self.results.values() ) ) )
        return replacement
    
    def updatePushVariables(self):
        for pushvar in self.pushVariables.values():
            pushvar.evaluate(self.replacementDict())

        
        
fitFunctionMap = dict()    
