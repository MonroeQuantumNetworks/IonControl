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

class FitHistogramEvaluation(EvaluationBase):
    """
    simple threshold state detection: if more than threshold counts are observed 
    the ion is considered bright. For threshold photons or less it is considered
    dark.
    In addition it receives the expected state and calculates the fidelity
    """
    name = "FitHistogram"
    tooltip = "Fit measured histograms to data"
    def __init__(self,settings=None):
        EvaluationBase.__init__(self,settings)
        self.epsfcn=0.0
        self.loadReferenceData()
        
    def loadReferenceData(self):
        for name in ['ZeroBright','OneBright', 'TwoBright']:
            filename = self.settings[name]
            if filename:
                t = Trace()
                t.loadTrace(filename)
                yColumnName = t.tracePlottingList[0].yColumn
                setattr(self, name, self.normalizeHistogram( getattr(t, yColumnName )) )
        
    def setDefault(self):
        self.settings.setdefault('ZeroBright','')
        self.settings.setdefault('OneBright','')
        self.settings.setdefault('TwoBright','')
        self.settings.setdefault('HistogramBins',50)
        self.settings.setdefault('NumberBright',0)
        self.settings.setdefault('OnlyOneIon',True)

        
    def update(self, param, changes):
        super( FitHistogramEvaluation, self ).update(param, changes)
        if any([ p.name() in ['ZeroBright','OneBright', 'TwoBright'] for p, _, _ in changes]):
            self.loadReferenceData()

    def normalizeHistogram(self, hist):
        hist = numpy.array(hist, dtype=float)
        return hist / numpy.sum( hist )
        
    def evaluate(self, data, counter=0, name=None, timestamps=None, expected=None ):
        params, confidence = data.evaluated.get('FitHistogramsResult',(None,None))
        if params is not None:
            return params[self.settings['NumberBright']], (confidence[self.settings['NumberBright']],  confidence[self.settings['NumberBright']]) , params[self.settings['NumberBright']]
        y, x = numpy.histogram( data.count[counter] , range=(0,self.settings['HistogramBins']), bins=self.settings['HistogramBins']) 
        y = self.normalizeHistogram(y)
        params, confidence = self.leastsq(x[0:-1], y, [0.3,0.3])
        params = list(params) + [ 1-params[0]-params[1] ]     # fill in the constrained parameter
        confidence = list(confidence)
        confidence.append( 0 )  # don't know what to do :(
        data.evaluated['FitHistogramsResult'] = (params, confidence)
        return params[self.settings['NumberBright']], (confidence[self.settings['NumberBright']],  confidence[self.settings['NumberBright']]) , params[self.settings['NumberBright']]

        
    def children(self):
        return [{'name':'ZeroBright','type':'str','value':self.settings['ZeroBright'], 'tip': 'filename for ZeroBright data' },
                {'name':'OneBright','type':'str','value':self.settings['OneBright'], 'tip': 'filename for OneBright data' },
                {'name':'TwoBright','type':'str','value':self.settings['TwoBright'], 'tip': 'filename for TwoBright data' },
                {'name':'NumberBright','type':'int','value':self.settings['NumberBright'], 'range': (0,2),  'tip': 'Number of bright ions' },
                {'name':'HistogramBins','type':'int','value':self.settings['HistogramBins'], 'tip': 'Number of histogram bins in data' },
                {'name':'OnlyOneIon','type':'bool','value':self.settings['OnlyOneIon'], 'tip': 'One ion vs Two ions' }]     

    def functionEval(self, x, p ):
        return numpy.array( [ p[0] * self.ZeroBright[el] + p[1] * self.OneBright[el] + (1-p[0]-p[1]) * self.TwoBright[el] for el in x ] )

    def residuals(self, p, y, x):
        penalty = 0
        if p[0]<0:
            penalty += abs(p[0])*100
        if p[0]>1:
            penalty += (p[0]-1)*100
        if p[1]<0:
            penalty += abs(p[1])*100
        if p[1]>1:
            penalty += (p[1]-1)*100
        if p[0]+p[1]>1:
            penalty += (p[0]+p[1]-1)*100  
        return y-self.functionEval(x, p)+penalty

    def leastsq(self, x, y, parameters=None, sigma=None):
        logger = logging.getLogger(__name__)
        if parameters is None:
            parameters = [0.3,0.3]
        
        params, self.cov_x, self.infodict, self.mesg, self.ier = leastsq(self.residuals, parameters, args=(y,x), epsfcn=self.epsfcn, full_output=True)
        logger.info( "chisq {0}".format( sum(self.infodict["fvec"]*self.infodict["fvec"]) ) )        
        
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
            self.parametersConfidence = numpy.sqrt(numpy.diagonal(self.cov_x))*sqrt(self.chisq/self.dof)
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
            self.parametersConfidence = [None]*len(self.parametersConfidence)
 
        return params, self.parametersConfidence

   

