# -*- coding: utf-8 -*-
"""
Algorithms to evaluate the observed counts from a sequence of experiments:
This is used for simple averaging but also for different state detection algorithms

algorithms are expected to defined the fileds as stated in MeanEvaluation

"""
import copy
import math

from PyQt4 import QtCore
import numpy
from pyqtgraph.parametertree import Parameter

from modules.Observable import Observable
from modules.enum import enum 

class EvaluationException(Exception):
    pass

class EvaluationBase(Observable):
    def __init__(self,settings =  None):
        Observable.__init__(self)
        self.settings = settings if settings else dict()
        self.setDefault()
        self._parameter = Parameter.create(name='params', type='group',children=self.children())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        self.settingsName = None
               
    def update(self, param, changes):
        for param, _, data in changes:
            self.settings[param.name()] = data
        self.firebare()
            
    def children(self):
        return []    
    
    def setSettings(self, settings, settingsName):
        for name, value in self.settings.iteritems():
            settings.setdefault(name, value)
        self.settings = settings
        for name, value in settings.iteritems():
            self._parameter[name] = value
        self.settingsName = settingsName if settingsName else "unnamed"
        
    def setSettingsName(self, settingsName):
        self.settingsName = settingsName

    @property
    def parameter(self):
        # re-create to prevent exception for signal not connected
        self._parameter = Parameter.create(name=self.settingsName, type='group',children=self.children())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        return self._parameter
    
    def __deepcopy__(self, memo=None):
        return type(self)( copy.deepcopy(self.settings,memo) )
  

class MeanEvaluation(EvaluationBase):
    """
    returns mean and shot noise error
    """
    name = 'Mean'
    tooltip = "Mean of observed counts" 
    errorBarType = enum('shotnoise','statistical')
    def __init__(self,settings=None):
        EvaluationBase.__init__(self,settings)
        self.errorBarTypeLookup = [ self.evaluateShotnoise, self.evaluateStatistical ]
        
    def setDefault(self):
        self.settings.setdefault('errorBarType',0)
         
    def evaluateShotnoise(self, countarray ):
        summe = numpy.sum( countarray )
        l = float(len(countarray))
        mean = summe/l
        stderror = math.sqrt( max(summe,1) )/l
        return mean, (stderror/2. if summe>0 else 0, stderror/2. ), summe

    def evaluateStatistical(self, countarray):
        mean = numpy.mean( countarray )
        stderr = numpy.std( countarray, ddof=1 ) / math.sqrt( max( len(countarray)-1, 1) )
        return mean, (stderr/2.,stderr/2.), numpy.sum( countarray )
    
    def evaluate(self, data, counter=0, name=None, timestamps=None, expected=None ):
        countarray = data.count[counter]
        if not countarray:
            return 0, (0,0), 0
        return self.errorBarTypeLookup[self.settings['errorBarType']](countarray)

    def children(self):
        return [{'name':'errorBarType', 'type': 'list', 'values':self.errorBarType.mapping, 'value': self.settings['errorBarType'] } ]     

class NumberEvaluation(EvaluationBase):
    """
    returns mean and shot noise error
    """
    name = 'Number'
    tooltip = "Number of results" 
    def __init__(self,settings=None):
        EvaluationBase.__init__(self,settings)
        
    def setDefault(self):
        pass
    
    def evaluate(self, data, counter=0, name=None, timestamps=None, expected=None ):
        countarray = data.count[counter]
        if not countarray:
            return 0, None, 0
        return len(countarray), None, len(countarray)

    def children(self):
        return []     


class ThresholdEvaluation(EvaluationBase):
    """
    simple threshold state detection: if more than threshold counts are observed 
    the ion is considered bright. For threshold photons or less it is considered
    dark.
    """
    name = "Threshold"
    tooltip = "Obove threshold is bright"
    def __init__(self,settings=None):
        EvaluationBase.__init__(self,settings)
        
    def setDefault(self):
        self.settings.setdefault('threshold',1)
        self.settings.setdefault('invert',False)
        
    def evaluate(self, data, counter=0, name=None, timestamps=None, expected=None ):
        countarray = data.count[counter]
        if not countarray:
            return 0, None, 0
        N = float(len(countarray))
        if self.settings['invert']:
            descriminated = [ 0 if count > self.settings['threshold'] else 1 for count in countarray ]
        else:
            descriminated = [ 1 if count > self.settings['threshold'] else 0 for count in countarray ]
        if name:
            data.evaluated[name] = descriminated
        x = numpy.sum( descriminated )
        p = x/N
        # Wilson score interval with continuity correction
        # see http://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
        rootp = 3-1/N -4*p+4*N*(1-p)*p
        top = min( 1, (2 + 2*N*p + math.sqrt(rootp))/(2*(N+1)) ) if rootp>=0 else 1
        rootb = -1-1/N +4*p+4*N*(1-p)*p
        bottom = max( 0, (2*N*p - math.sqrt(rootb))/(2*(N+1)) ) if rootb>=0 else 0            
        return p, (p-bottom, top-p), x

    def children(self):
        return [{'name':'threshold','type':'int','value':self.settings['threshold']},
                {'name':'invert', 'type': 'bool', 'value':self.settings['invert'] }]     

class RangeEvaluation(EvaluationBase):
    """
    simple threshold state detection: if more than threshold counts are observed 
    the ion is considered bright. For threshold photons or less it is considered
    dark.
    """
    name = "Count Range"
    tooltip = ""
    def __init__(self,settings=None):
        EvaluationBase.__init__(self,settings)
        
    def setDefault(self):
        self.settings.setdefault('min',0)
        self.settings.setdefault('max',1)
        self.settings.setdefault('invert',False)
        
    def evaluate(self, data, counter=0, name=None, timestamps=None, expected=None ):
        countarray = data.count[counter]
        if not countarray:
            return 0, None, 0
        N = float(len(countarray))
        if self.settings['invert']:
            descriminated = [ 0 if self.settings['min'] <= count <= self.settings['max'] else 1 for count in countarray ]
        else:
            descriminated = [ 1 if self.settings['min'] <= count <= self.settings['max'] else 0 for count in countarray ]
        if name:
            data.evaluated[name] = descriminated
        x = numpy.sum( descriminated )
        p = float(x)/N
        # Wilson score interval with continuity correction
        # see http://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
        # caution: not applicable to this situation, needs to be fixed
        rootp = 3-1/N -4*p+4*N*(1-p)*p
        top = min( 1, (2 + 2*N*p + math.sqrt(rootp))/(2*(N+1)) ) if rootp>=0 else 1
        rootb = -1-1/N +4*p+4*N*(1-p)*p
        bottom = max( 0, (2*N*p - math.sqrt(rootb))/(2*(N+1)) ) if rootb>=0 else 0            
        return p, (p-bottom, top-p), x

    def children(self):
        return [{'name':'min','type':'int','value':self.settings['min']},
                {'name':'max','type':'int','value':self.settings['max']},
                {'name':'invert', 'type': 'bool', 'value':self.settings['invert'] }]     

class DoubleRangeEvaluation(EvaluationBase):
    """
    simple threshold state detection: if more than threshold counts are observed 
    the ion is considered bright. For threshold photons or less it is considered
    dark.
    """
    name = "Double Count Range"
    tooltip = ""
    def __init__(self,settings=None):
        EvaluationBase.__init__(self,settings)
        
    def setDefault(self):
        self.settings.setdefault('min_1',0)
        self.settings.setdefault('max_1',1)
        self.settings.setdefault('min_2',0)
        self.settings.setdefault('max_2',1)
        self.settings.setdefault('invert',False)
        
    def evaluate(self, data, counter=0, name=None, timestamps=None, expected=None ):
        countarray = data.count[counter]
        if not countarray:
            return 0, None, 0
        N = float(len(countarray))
        if self.settings['invert']:
            descriminated = [ 0 if ( self.settings['min_1'] <= count <= self.settings['max_1'] ) or 
                             ( self.settings['min_2'] <= count <= self.settings['max_2'] )  else 1 for count in countarray ]
        else:
            descriminated = [ 1 if ( self.settings['min_1'] <= count <= self.settings['max_1'] ) or 
                             ( self.settings['min_2'] <= count <= self.settings['max_2'] )  else 0 for count in countarray ]
        if name:
            data.evaluated[name] = descriminated
        x = numpy.sum( descriminated )
        p = float(x)/N
        # Wilson score interval with continuity correction
        # see http://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
        # caution: not applicable to this situation, needs to be fixed
        rootp = 3-1/N -4*p+4*N*(1-p)*p
        top = min( 1, (2 + 2*N*p + math.sqrt(rootp))/(2*(N+1)) ) if rootp>=0 else 1
        rootb = -1-1/N +4*p+4*N*(1-p)*p
        bottom = max( 0, (2*N*p - math.sqrt(rootb))/(2*(N+1)) ) if rootb>=0 else 0            
        return p, (p-bottom, top-p), x

    def children(self):
        return [{'name':'min_1','type':'int','value':self.settings['min_1']},
                {'name':'max_1','type':'int','value':self.settings['max_1']},
                {'name':'min_2','type':'int','value':self.settings['min_2']},
                {'name':'max_2','type':'int','value':self.settings['max_2']},
                {'name':'invert', 'type': 'bool', 'value':self.settings['invert'] }]     


class FidelityEvaluation(EvaluationBase):
    """
    simple threshold state detection: if more than threshold counts are observed 
    the ion is considered bright. For threshold photons or less it is considered
    dark.
    In addition it receives the expected state and calculates the fidelity
    """
    name = "Fidelity"
    tooltip = "Obove threshold is bright"
    def __init__(self,settings=None):
        EvaluationBase.__init__(self,settings)
        
    def setDefault(self):
        self.settings.setdefault('threshold',1)
        self.settings.setdefault('invert',False)
        
    def evaluate(self, data, counter=0, name=None, timestamps=None, expected=None ):
        countarray = data.count[counter]
        if not countarray:
            return 0, None, 0
        N = float(len(countarray))
        if self.settings['invert']:
            descriminated = [ 0 if count > self.settings['threshold'] else 1 for count in countarray ]
        else:
            descriminated = [ 1 if count > self.settings['threshold'] else 0 for count in countarray ]
        if name:
            data.evaluated[name] = descriminated
        x = numpy.sum( descriminated )
        p = x/N
        # Wilson score interval with continuity correction
        # see http://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
        rootp = 3-1/N -4*p+4*N*(1-p)*p
        top = min( 1, (2 + 2*N*p + math.sqrt(rootp))/(2*(N+1)) ) if rootp>=0 else 1
        rootb = -1-1/N +4*p+4*N*(1-p)*p
        bottom = max( 0, (2*N*p - math.sqrt(rootb))/(2*(N+1)) ) if rootb>=0 else 0  
        if expected is not None:
            p = abs(expected-p)
            bottom = abs(expected-bottom)
            top = abs(expected-top)
        return p, (p-bottom, top-p), x
        
    def children(self):
        return [{'name':'threshold','type':'int','value':self.settings['threshold']},
                {'name':'invert', 'type': 'bool', 'value':self.settings['invert'] }]     
        

class ParityEvaluation(EvaluationBase):
    """
    simple threshold state detection: if more than threshold counts are observed 
    the ion is considered bright. For threshold photons or less it is considered
    dark.
    In addition it receives the expected state and calculates the fidelity
    """
    name = "Parity"
    tooltip = "Two ion parity evaluation"
    def __init__(self,settings=None):
        EvaluationBase.__init__(self,settings)
        
    def setDefault(self):
        self.settings.setdefault('Ion_1','')
        self.settings.setdefault('Ion_2','')
        
    def evaluate(self, data, counter=0, name=None, timestamps=None, expected=None ):
        name1, name2 = self.settings['Ion_1'], self.settings['Ion_2']
        eval1, eval2 = data.evaluated.get(name1), data.evaluated.get(name2) 
        if eval1 is None:
            raise EvaluationException("Cannot find data '{0}'".format(name1))
        if eval2 is None:
            raise EvaluationException("Cannot find data '{0}'".format(name2))
        if len(eval1)!=len(eval2):
            raise EvaluationException("Evaluated arrays have different length {0}, {1}".format(len(eval1),len(eval2)))
        N = float(len(eval1))
        descriminated = [ 1 if e1==e2 else -1 for e1, e2 in zip(eval1, eval2) ]
        if name:
            data.evaluated[name] = descriminated
        x = numpy.sum( descriminated )
        p = x/N
        # Wilson score interval with continuity correction
        # see http://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
        rootp = 3-1/N -4*p+4*N*(1-p)*p
        top = min( 1, (2 + 2*N*p + math.sqrt(rootp))/(2*(N+1)) ) if rootp>=0 else 1
        rootb = -1-1/N +4*p+4*N*(1-p)*p
        bottom = max( 0, (2*N*p - math.sqrt(rootb))/(2*(N+1)) ) if rootb>=0 else 0  
        if expected is not None:
            p = abs(expected-p)
            bottom = abs(expected-bottom)
            top = abs(expected-top)
        return p, (p-bottom, top-p), x
        
    def children(self):
        return [{'name':'Ion_1','type':'str','value':self.settings['Ion_1']},
                {'name':'Ion_2','type':'str','value':self.settings['Ion_2'] }]     

class TwoIonEvaluation(EvaluationBase):
    """
    simple threshold state detection: if more than threshold counts are observed 
    the ion is considered bright. For threshold photons or less it is considered
    dark.
    In addition it receives the expected state and calculates the fidelity
    """
    name = "TwoIon"
    tooltip = "Two ion parity evaluation"
    def __init__(self,settings=None):
        EvaluationBase.__init__(self,settings)
        
    def setDefault(self):
        self.settings.setdefault('Ion_1','')
        self.settings.setdefault('Ion_2','')
        self.settings.setdefault('dd',1)
        self.settings.setdefault('db',-1)
        self.settings.setdefault('bd',-1)
        self.settings.setdefault('bb',1)
        
    def evaluate(self, data, counter=0, name=None, timestamps=None, expected=None ):
        name1, name2 = self.settings['Ion_1'], self.settings['Ion_2']
        eval1, eval2 = data.evaluated.get(name1), data.evaluated.get(name2) 
        if eval1 is None:
            raise EvaluationException("Cannot find data '{0}'".format(name1))
        if eval2 is None:
            raise EvaluationException("Cannot find data '{0}'".format(name2))
        if len(eval1)!=len(eval2):
            raise EvaluationException("Evaluated arrays have different length {0}, {1}".format(len(eval1),len(eval2)))
        N = float(len(eval1))
        lookup = {(0,0): self.settings['dd'], (0,1): self.settings['db'], (1,0): self.settings['bd'], (1,1):self.settings['bb'] }
        descriminated = [ lookup[pair] for pair in zip(eval1, eval2) ]
        if name:
            data.evaluated[name] = descriminated
        x = numpy.sum( descriminated )
        p = x/N
        # Wilson score interval with continuity correction
        # see http://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
        rootp = 3-1/N -4*p+4*N*(1-p)*p
        top = min( 1, (2 + 2*N*p + math.sqrt(rootp))/(2*(N+1)) ) if rootp>=0 else 1
        rootb = -1-1/N +4*p+4*N*(1-p)*p
        bottom = max( 0, (2*N*p - math.sqrt(rootb))/(2*(N+1)) ) if rootb>=0 else 0  
        if expected is not None:
            p = abs(expected-p)
            bottom = abs(expected-bottom)
            top = abs(expected-top)
        return p, (p-bottom, top-p), x
        
    def children(self):
        return [{'name':'Ion_1','type':'str','value':self.settings['Ion_1']},
                {'name':'Ion_2','type':'str','value':self.settings['Ion_2'] },
                {'name':'dd','type':'float','value':self.settings['dd'], 'tip': 'multiplicator for dd' },
                {'name':'db','type':'float','value':self.settings['db'], 'tip': 'multiplicator for db' },
                {'name':'bd','type':'float','value':self.settings['bd'], 'tip': 'multiplicator for bd' },
                {'name':'bb','type':'float','value':self.settings['bb'], 'tip': 'multiplicator for bb' }]     



   
EvaluationAlgorithms = { MeanEvaluation.name: MeanEvaluation, 
                         ThresholdEvaluation.name: ThresholdEvaluation,
                         RangeEvaluation.name: RangeEvaluation,
                         DoubleRangeEvaluation.name: DoubleRangeEvaluation,
                         NumberEvaluation.name: NumberEvaluation,
                         FidelityEvaluation.name: FidelityEvaluation,
                         ParityEvaluation.name: ParityEvaluation,
                         TwoIonEvaluation.name: TwoIonEvaluation }

