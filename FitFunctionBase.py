# -*- coding: utf-8 -*-
"""
Created on Thu May 16 20:53:03 2013

@author: pmaunz
"""

from scipy.optimize import leastsq
import numpy
from math import sqrt
from modules import magnitude
import xml.etree.ElementTree as ElementTree
from itertools import izip_longest
import logging

class FitFunctionBase(object):
    name = 'None'
    def __init__(self):
        self.epsfcn=0.0
        self.parameterNames = []
        self.parameters = []
        self.parametersConfidence = []
        self.constantNames = []
        self.resultNames = ["RMSres"]
        self.RMSres = 0

    def leastsq(self, x, y, parameters=None, sigma=None):
        logger = logging.getLogger(__name__)
        if parameters is None:
            parameters = self.parameters
        #self.parameters, self.n = leastsq(self.residuals, parameters, args=(y,x), epsfcn=self.epsfcn)
        
        self.parameters, self.cov_x, self.infodict, self.mesg, self.ier = leastsq(self.residuals, parameters, args=(y,x,sigma), epsfcn=self.epsfcn, full_output=True)
        self.finalize(self.parameters)
        logger.info( "chisq {0}".format( sum(self.infodict["fvec"]*self.infodict["fvec"]) ) )        
        
        # calculate final chi square
        self.chisq=sum(self.infodict["fvec"]*self.infodict["fvec"])
        
        self.dof=len(x)-len(parameters)
        self.RMSres = magnitude.mg(sqrt(self.chisq/self.dof),'')
        self.RMSres.significantDigits = 3
        # chisq, sqrt(chisq/dof) agrees with gnuplot
        logger.info(  "success {0} {1}".format( self.ier, self.mesg ) )
        logger.info(  "Converged with chi squared {0}".format(self.chisq) )
        logger.info(  "degrees of freedom, dof {0}".format( self.dof ) )
        logger.info(  "RMS of residuals (i.e. sqrt(chisq/dof)) {0}".format( self.RMSres ) )
        logger.info(  "Reduced chisq (i.e. variance of residuals) {0}".format( self.chisq/self.dof ) )
        
        # uncertainties are calculated as per gnuplot, "fixing" the result
        # for non unit values of the reduced chisq.
        # values at min match gnuplot
        if self.cov_x is not None:
            self.parametersConfidence = numpy.sqrt(numpy.diagonal(self.cov_x))*sqrt(self.chisq/self.dof)
            self.parametersRelConfidence = self.parametersConfidence/numpy.abs(self.parameters)*100
            logger.info(  "Fitted parameters at minimum, with 68% C.I.:" )
            for i,pmin in enumerate(self.parameters):
                logger.info(  "%2i %-10s %12f +/- %10f"%(i,self.parameterNames[i],pmin,sqrt(self.cov_x[i,i])*sqrt(self.chisq/self.dof)) )
        
            logger.info(  "Correlation matrix" )
            # correlation matrix close to gnuplot
            messagelist = ["               "]
            for i in range(len(self.parameters)): messagelist.append( "%-10s"%(self.parameterNames[i],) )
            logger.info( " ".join(messagelist))
            messagelist = []
            for i in range(len(self.parameters)):
                messagelist.append( "%10s"%self.parameterNames[i] )
                for j in range(i+1):
                    messagelist.append(  "%10f"%(self.cov_x[i,j]/sqrt(self.cov_x[i,i]*self.cov_x[j,j]),) )
                logger.info( " ".join(messagelist))
    
                #-----------------------------------------------
        else:
            self.parametersConfidence = None
            self.parametersRelConfidence = None

        return self.parameters
                
    def __str__(self):
        return "; ".join([", ".join([self.name, self.functionString] + [ "{0}={1}".format(name, value) for name, value in zip(self.parameterNames,self.parameters)]),
                          ", ".join([ "{0}={1}".format(name,getattr(self,name)) for name in self.constantNames ])])

    def setConstant(self, name, value):
        setattr(self,name,value)
        
    def finalize(self,parameters):
        pass
    
    def toXmlElement(self, parent):
        myroot  = ElementTree.SubElement(parent, 'FitFunction', {'name': self.name, 'functionString': self.functionString})
        for name, value, confidence in izip_longest(self.parameterNames,self.parameters,self.parametersConfidence):
            e = ElementTree.SubElement( myroot, 'Parameter', {'name':name, 'confidence':repr(confidence)})
            e.text = str(value)
        for name in self.constantNames:
            e = ElementTree.SubElement( myroot, 'Constant', {'name':name})
            e.text = str(getattr(self,name))
           
        return myroot
