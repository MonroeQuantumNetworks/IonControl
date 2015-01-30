'''
Created on Sep 23, 2014

@author: pmaunz
'''

from CountEvaluation import EvaluationBase
import numpy
import logging
from scipy.optimize import leastsq
from modules import magnitude
from math import sqrt
from trace.Trace import Trace
import xml.etree.ElementTree as ElementTree
from itertools import izip_longest
from copy import deepcopy
from os import path

class HistogramFitFunction:
    name = "HistogramApproximation"
    functionString = "p0*H(0)+p1*H(1)+p2*H(2)"
    def __init__(self):
        self.param = (0,0,0)
        self.totalCounts = 1
    
    def value(self, x):
        return self.functionEval(x, self.param) * self.totalCounts
    
    def functionEval(self, x, p ):
        return numpy.array( [ p[0] * self.ZeroBright[el] + p[1] * self.OneBright[el] + (1-p[0]-p[1]) * self.TwoBright[el] for el in x ] )

    def residuals(self, p, y, x):
        penalty = 0
        if p[0]<0:
            penalty += abs(p[0])*1
        if p[0]>1:
            penalty += (p[0]-1)*1
        if p[1]<0:
            penalty += abs(p[1])*1
        if p[1]>1:
            penalty += (p[1]-1)*1
        if p[0]+p[1]>1:
            penalty += (p[0]+p[1]-1)*1  
        return y-self.functionEval(x, p)+penalty

    def toXmlElement(self, parent):
        myroot  = ElementTree.SubElement(parent, 'FitFunction', {'name': self.name, 'functionString': self.functionString})
        for name, value in izip_longest(["p0","p1","p2", "totalCounts"],self.param+[self.totalCounts]):
            e = ElementTree.SubElement( myroot, 'Parameter', {'name':name, 'enabled': str(True)})
            e.text = str(value)
        return myroot
 
class FitHistogramEvaluation(EvaluationBase):
    name = "FitHistogram"
    tooltip = "Fit measured histograms to data"
    def __init__(self,settings=None):
        EvaluationBase.__init__(self,settings)
        self.epsfcn=0.0
        self.fitFunction = HistogramFitFunction()
        self.loadReferenceData()
        
    def __setstate__(self, d):
        self.__dict__ = d
        self.__dict__.setdefault('fitFunction', HistogramFitFunction())
        self.loadReferenceData()
        
    def loadReferenceData(self):
        for name in ['ZeroBright','OneBright', 'TwoBright']:
            filename = path.join(self.settings['Path'],self.settings[name])
            if filename:
                t = Trace()
                t.loadTrace(filename)
                yColumnName = t.tracePlottingList[0].yColumn
                setattr(self.fitFunction, name, self.normalizeHistogram( getattr(t, yColumnName )) )
        
    def setDefault(self):
        self.settings.setdefault('Path',r'C:\Users\Public\Documents\experiments\QGA\2014\2014_10\2014_10_21')
        self.settings.setdefault('ZeroBright','ZeroIonHistogram')
        self.settings.setdefault('OneBright','OneIonHistogram')
        self.settings.setdefault('TwoBright','TwoIonHistogram')
        self.settings.setdefault('HistogramBins',50)
        self.settings.setdefault('Mode','Zero')
        
    def update(self, param, changes):
        super( FitHistogramEvaluation, self ).update(param, changes)
        if any([ p.name() in ['ZeroBright','OneBright', 'TwoBright'] for p, _, _ in changes]):
            self.loadReferenceData()

    def normalizeHistogram(self, hist, longOutput=False):
        hist = numpy.array(hist, dtype=float)
        histsum = numpy.sum( hist )
        return (hist / histsum, histsum) if longOutput else hist/histsum
        
    def evaluate(self, data, counter=0, name=None, timestamps=None, expected=None ):
        params, confidence, reducedchisq = data.evaluated.get('FitHistogramsResult',(None,None,None))
        if params is None:
            y, x = numpy.histogram( data.count[counter] , range=(0,self.settings['HistogramBins']), bins=self.settings['HistogramBins']) 
            y, self.fitFunction.totalCounts = self.normalizeHistogram(y, longOutput=True)
            params, confidence = self.leastsq(x[0:-1], y, [0.3,0.3])
            params = list(params) + [ 1-params[0]-params[1] ]     # fill in the constrained parameter
            confidence = list(confidence)
            confidence.append( 0 )  # don't know what to do :(
            data.evaluated['FitHistogramsResult'] = (params, confidence, self.chisq/self.dof)
        if self.settings['Mode']=='Parity':
            return params[0]+params[2]-params[1], None, params[0]+params[2]-params[1]
        elif self.settings['Mode']=='Zero':
            return params[0], (confidence[0],  confidence[0]) , params[0]
        elif self.settings['Mode']=='One':
            return params[1], (confidence[1],  confidence[1]) , params[1]
        elif self.settings['Mode']=='Two':
            return params[2], (confidence[2],  confidence[2]) , params[2]
        elif self.settings['Mode']=='Residuals':
            return reducedchisq, None, reducedchisq

        
    def children(self):
        return [{'name':'Path','type':'str','value':str(self.settings['Path']), 'tip': 'Path for histogram files' },
                {'name':'ZeroBright','type':'str','value':str(self.settings['ZeroBright']), 'tip': 'filename for ZeroBright data' },
                {'name':'OneBright','type':'str','value':str(self.settings['OneBright']), 'tip': 'filename for OneBright data' },
                {'name':'TwoBright','type':'str','value':str(self.settings['TwoBright']), 'tip': 'filename for TwoBright data' },
                {'name':'HistogramBins','type':'int','value':int(self.settings['HistogramBins']), 'tip': 'Number of histogram bins in data' },
                {'name':'Mode','type':'list', 'values': ['Zero','One','Two','Parity','Residuals'], 'value': str(self.settings['Mode']), 'tip': 'Evaluation mode' }]     


    def leastsq(self, x, y, parameters=None, sigma=None):
        logger = logging.getLogger(__name__)
        if parameters is None:
            parameters = [0.3,0.3]
        
        params, self.cov_x, self.infodict, self.mesg, self.ier = leastsq(self.fitFunction.residuals, parameters, args=(y,x), epsfcn=self.epsfcn, full_output=True)
        logger.info( "chisq {0}".format( sum(self.infodict["fvec"]*self.infodict["fvec"]) ) )        
        self.fitFunction.param = params
        
        # calculate final chi square
        self.chisq=sum(self.infodict["fvec"]*self.infodict["fvec"])
        
        self.dof=len(x)-len(parameters)
        RMSres = magnitude.mg(sqrt(self.chisq/self.dof),'')
        RMSres.significantDigits = 3
        self.RMSres = RMSres
        # chisq, sqrt(chisq/dof) agrees with gnuplot
        logger.info(  "success {0} {1}".format( self.ier, self.mesg ) )
        logger.info(  "Converged with chi squared {0}".format(self.chisq) )
        logger.info(  "degrees of freedom, dof {0}".format( self.dof ) )
        logger.info(  "RMS of residuals (i.e. sqrt(chisq/dof)) {0}".format( RMSres ) )
        logger.info(  "Reduced chisq (i.e. variance of residuals) {0}".format( self.chisq/self.dof ) )
        
        # uncertainties are calculated as per gnuplot, "fixing" the result
        # for non unit values of the reduced chisq.
        # values at min match gnuplot
        if self.cov_x is not None:
            self.fitFunction.parametersConfidence = numpy.sqrt(numpy.diagonal(self.cov_x))*sqrt(self.chisq/self.dof)
            logger.info(  "Fitted parameters at minimum, with 68% C.I.:" )
            for i,pmin in enumerate(params):
                logger.info(  "%2i %-10s %12f +/- %10f"%(i,params[i],pmin,sqrt(max(self.cov_x[i,i],0))*sqrt(self.chisq/self.dof)) )
        
            logger.info(  "Correlation matrix" )
            # correlation matrix close to gnuplot
            messagelist = ["               "]
            for i in range(len(params)): messagelist.append( "%-10s"%(params[i],) )
            logger.info( " ".join(messagelist))
            messagelist = []
            for i in range(len(params)):
                messagelist.append( "%10s"%params[i] )
                for j in range(i+1):
                    messagelist.append(  "%10f"%(self.cov_x[i,j]/sqrt(self.cov_x[i,i]*self.cov_x[j,j]),) )
                logger.info( " ".join(messagelist))
    
                #-----------------------------------------------
        else:
            self.fitFunction.parametersConfidence = [None]*len(self.parametersConfidence)
 
        return params, self.fitFunction.parametersConfidence

    def histogram(self, data, counter=0, histogramBins=50 ):
        y, x, _ = super(FitHistogramEvaluation, self).histogram( data, counter, histogramBins)
        return y, x, deepcopy(self.fitFunction)   # third parameter is optional function 

  

