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
        self.ZeroBright = None
        self.OneBright = None
        self.TwoBright = None
        
    def loadReferenceData(self):
        pass
        
    def setDefault(self):
        self.settings.setdefault('ZeroBright','')
        self.settings.setdefault('OneBright','')
        self.settings.setdefault('TwoBright','')
        self.settings.setdefault('HistogramBins',50)
        self.settings.setdefault('NumberBright',0)
        
    def update(self, param, changes):
        for param, _, data in changes:
            self.settings[param.name()] = data
            if param.name() in ['ZeroBright','OneBright', 'TwoBright']:
                t = Trace()
                t.loadTrace(data)
                setattr(self, param.name(), self.normalizeHistogram(t.y) )
        self.firebare()

    def normalizeHistogram(self, hist):
        return hist / numpy.sum( hist )
        
    def evaluate(self, data, counter=0, name=None, timestamps=None, expected=None ):
        params, confidence = data.evaluated.get('FitHistogramsResult')
        if params is not None:
            return params[self.settings['NumberBright']], (confidence[self.settings['NumberBright']],  confidence[self.settings['NumberBright']]) , params[self.settings['NumberBright']]
        y, x = numpy.histogram( data.count[counter] , range=(0,self.settings['HistogramBins']), bins=self.settings['HistogramBins']) 
        y = self.normalizeHistogram(y)
        params, confidence = self.leastsq(x, y, [0.3,0.3])
        data.evaluated['FitHistogramsResult'] = (params, confidence)
        return params[self.settings['NumberBright']], (confidence[self.settings['NumberBright']],  confidence[self.settings['NumberBright']]) , params[self.settings['NumberBright']]

        
    def children(self):
        return [{'name':'ZeroBright','type':'str','value':self.settings['ZeroBright'], 'tip': 'filename for ZeroBright data' },
                {'name':'OneBright','type':'str','value':self.settings['OneBright'], 'tip': 'filename for OneBright data' },
                {'name':'TwoBright','type':'str','value':self.settings['TwoBright'], 'tip': 'filename for TwoBright data' },
                {'name':'NumberBright','type':'int','value':self.settings['NumberBright'], 'range': (0,2),  'tip': 'Number of bright ions' }]     

    def functionEval(self, x, p ):
        return p[0] * self.ZeroBright[x] + p[1] * self.OneBright[x] + (1-p[0]-p[1]) * self.TwoBright

    def residuals(self, p, y, x, sigma):
        if sigma is not None:
            return (y-self.functionEval(x, p))/sigma
        else:
            return y-self.functionEval(x, p)

    def leastsq(self, x, y, parameters=None, sigma=None):
        logger = logging.getLogger(__name__)
        if parameters is None:
            parameters = [0.3,0.3]
        
        params, self.cov_x, self.infodict, self.mesg, self.ier = leastsq(self.residuals, self.enabledStartParameters(parameters), args=(y,x,sigma), epsfcn=self.epsfcn, full_output=True)
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
            self.parametersConfidence = numpy.sqrt(numpy.diagonal(self.cov_x))*sqrt(self.chisq/self.dof)
            logger.info(  "Fitted parameters at minimum, with 68% C.I.:" )
            for i,pmin in enumerate(params):
                logger.info(  "%2i %-10s %12f +/- %10f"%(i,enabledParameterNames[i],pmin,sqrt(max(self.cov_x[i,i],0))*sqrt(self.chisq/self.dof)) )
        
            logger.info(  "Correlation matrix" )
            # correlation matrix close to gnuplot
            messagelist = ["               "]
            for i in range(len(params)): messagelist.append( "%-10s"%(enabledParameterNames[i],) )
            logger.info( " ".join(messagelist))
            messagelist = []
            for i in range(len(params)):
                messagelist.append( "%10s"%enabledParameterNames[i] )
                for j in range(i+1):
                    messagelist.append(  "%10f"%(self.cov_x[i,j]/sqrt(self.cov_x[i,i]*self.cov_x[j,j]),) )
                logger.info( " ".join(messagelist))
    
                #-----------------------------------------------
        else:
            self.parametersConfidence = [None]*len(self.parametersConfidence)
 
        return self.parameters, self.parametersConfidence

   

