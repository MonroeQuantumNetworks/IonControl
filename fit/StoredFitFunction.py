'''
Created on Dec 21, 2014

@author: pmaunz
'''
from modules.HashableDict import HashableDict
from fit.FitFunctionBase import ResultRecord
from fit.FitFunctionBase import fitFunctionMap

class StoredFitFunction(object):
    def __init__(self, name=None, fitfunctionName=None ):
        self.name = name
        self.fitfunctionName = fitfunctionName
        self.startParameters = tuple()
        self.parameters = tuple()
        self.parametersConfidence = tuple()
        self.parameterEnabled = tuple()
        self.results = HashableDict()
        self.startParameterExpressions = None
        self.useSmartStartValues = False
        self.parameterBounds = tuple()
        self.parameterBoundsExpressions = tuple()
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault( 'parameters',tuple() )
        self.__dict__.setdefault( 'parametersConfidence', tuple() )
        self.__dict__.setdefault( 'startParameterExpressions', None )
        self.__dict__.setdefault( 'useSmartStartValues', False )
        self.__dict__.setdefault( 'parameterBounds', tuple(((None,None) for _ in range(len(self.parameters)))))
        self.__dict__.setdefault( 'parameterBoundsExpressions', tuple(((None,None) for _ in range(len(self.parameters)))))

    def fitfunction(self):
        fitfunction = fitFunctionMap[self.fitfunctionName]()
        fitfunction.startParameters = list(self.startParameters)
        fitfunction.parameterEnabled = list(self.parameterEnabled)
        fitfunction.useSmartStartValues = self.useSmartStartValues
        fitfunction.startParameterExpressions = list(self.startParameterExpressions) if self.startParameterExpressions is not None else [None]*len(self.startParameters)
        fitfunction.parameters = list(self.parameters)
        fitfunction.parametersConfidence = list(self.parametersConfidence)
        for result in self.results.values():
            fitfunction.results[result.name] = ResultRecord(name=result.name, definition=result.definition, value=result.value)
        fitfunction.parameterBounds = [ list(bound) for bound in self.parameterBounds ] if self.parameterBounds else [[None,None] for _ in range(len(fitfunction.parameterNames))]
        fitfunction.parameterBoundsExpressions =  [ list(bound) for bound in self.parameterBoundsExpressions ] if self.parameterBoundsExpressions else [[None,None] for _ in range(len(fitfunction.parameterNames))]
        return fitfunction
    
    @classmethod
    def fromFitfunction(cls, fitfunction):
        fitfunctionName = fitfunction.name if fitfunction else None
        instance = cls( name=None, fitfunctionName=fitfunctionName )
        instance.startParameters = tuple(fitfunction.startParameters)
        instance.parameterEnabled = tuple(fitfunction.parameterEnabled)
        instance.startParameterExpressions = tuple(fitfunction.startParameterExpressions) if fitfunction.startParameterExpressions is not None else tuple([None]*len(fitfunction.startParameters))
        instance.parameters = tuple(fitfunction.parameters)
        instance.parametersConfidence = tuple(fitfunction.parametersConfidence)
        instance.useSmartStartValues = fitfunction.useSmartStartValues
        for result in fitfunction.results.values():
            instance.results[result.name] = ResultRecord(name=result.name, definition=result.definition, value=result.value)
        instance.parameterBounds = tuple( (tuple(bound) for bound in fitfunction.parameterBounds) )
        instance.parameterBoundsExpressions = tuple( (tuple(bound) for bound in fitfunction.parameterBoundsExpressions) )
        return instance
     
    stateFields = ['name', 'fitfunctionName', 'startParameters', 'parameterEnabled', 'results', 'useSmartStartValues', 'startParameterExpressions', 'parameters', 'parametersConfidence',
                   'parameterBounds', 'parameterBoundsExpressions'] 
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))
        
