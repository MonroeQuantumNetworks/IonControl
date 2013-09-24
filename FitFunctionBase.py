# -*- coding: utf-8 -*-
"""
Created on Thu May 16 20:53:03 2013

@author: pmaunz
"""

from scipy.optimize import leastsq
from scipy.optimize import curve_fit
from math import sqrt

class FitFunctionBase(object):
    name = 'None'
    def __init__(self):
        self.epsfcn=0.0
        self.parameterNames = []
        self.parameters = []
        self.constantNames = []
        self.resultNames = []

    def leastsq(self, x, y, parameters=None, sigma=None):
        if parameters is None:
            parameters = self.parameters
        #self.parameters, self.n = leastsq(self.residuals, parameters, args=(y,x), epsfcn=self.epsfcn)
        
        self.parameters, self.cov_x, self.infodict, self.mesg, self.ier = leastsq(self.residuals, parameters, args=(y,x,sigma), epsfcn=self.epsfcn, full_output=True)
        self.finalize(self.parameters)
        print "chisq", sum(self.infodict["fvec"]*self.infodict["fvec"])        
        
        # calculate final chi square
        self.chisq=sum(self.infodict["fvec"]*self.infodict["fvec"])
        
        self.dof=len(x)-len(parameters)
        # chisq, sqrt(chisq/dof) agrees with gnuplot
        print "success", self.ier
        print "Converged with chi squared ",self.chisq
        print "degrees of freedom, dof ", self.dof
        print "RMS of residuals (i.e. sqrt(chisq/dof)) ", sqrt(self.chisq/self.dof)
        print "Reduced chisq (i.e. variance of residuals) ", self.chisq/self.dof
        print
        
        # uncertainties are calculated as per gnuplot, "fixing" the result
        # for non unit values of the reduced chisq.
        # values at min match gnuplot
        print "Fitted parameters at minimum, with 68% C.I.:"
        for i,pmin in enumerate(self.parameters):
            print "%2i %-10s %12f +/- %10f"%(i,self.parameterNames[i],pmin,sqrt(self.cov_x[i,i])*sqrt(self.chisq/self.dof))
        print
        
        print "Correlation matrix"
        # correlation matrix close to gnuplot
        print "               ",
        for i in range(len(self.parameters)): print "%-10s"%(self.parameterNames[i],),
        print
        for i in range(len(self.parameters)):
            print "%10s"%self.parameterNames[i],
            for j in range(i+1):
                print "%10f"%(self.cov_x[i,j]/sqrt(self.cov_x[i,i]*self.cov_x[j,j]),),
            print
            #-----------------------------------------------
        return self.parameters
                
    def __str__(self):
         return "; ".join([", ".join([self.name, self.functionString] + [ "{0}={1}".format(name, value) for name, value in zip(self.parameterNames,self.parameters)]),
                          ", ".join([ "{0}={1}".format(name,getattr(self,name)) for name in self.constantNames ])])

    def setConstant(self, name, value):
        setattr(self,name,value)
        
    def finalize(self,parameters):
        pass
