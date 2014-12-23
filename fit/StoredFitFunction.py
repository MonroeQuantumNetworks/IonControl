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
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault( 'parameters',tuple() )
        self.__dict__.setdefault( 'parametersConfidence', tuple() )
        self.__dict__.setdefault( 'startParameterExpressions', None )
        self.__dict__.setdefault( 'useSmartStartValues', False )

    def fitfunction(self):
        fitfunction = fitFunctionMap[self.fitfunctionName]()
        fitfunction.startParameters = list(self.startParameters)
        fitfunction.parameterEnabled = list(self.parameterEnabled)
        fitfunction.useSmartStartValues = self.useSmartStartValues
        fitfunction.startParameterExpressions = list(self.startParameterExpressions) if self.startParameterExpressions is not None else [None]*len(self.startParameters)
        fitfunction.parameters = list(self.parameters)
        fitfunction.parametersConfidence = list(self.parametersConfidence)
        return fitfunction
    
    @classmethod
    def fromFitfunction(cls, fitfunction):
        instance = cls( name=None, fitfunctionName=fitfunction.name )
        instance.startParameters = tuple(fitfunction.startParameters)
        instance.parameterEnabled = tuple(fitfunction.parameterEnabled)
        instance.startParameterExpressions = tuple(fitfunction.startParameterExpressions) if fitfunction.startParameterExpressions is not None else tuple([None]*len(fitfunction.startParameters))
        instance.parameters = tuple(fitfunction.parameters)
        instance.parametersConfidence = tuple(fitfunction.parametersConfidence)
        instance.useSmartStartValues = fitfunction.useSmartStartValues
        for result in fitfunction.results.values():
            instance.results[result.name] = ResultRecord(name=result.name, definition=result.definition)
        return instance
     
    stateFields = ['name', 'fitfunctionName', 'startParameters', 'parameterEnabled', 'results', 'useSmartStartValues', 'startParameterExpressions', 'parameters', 'parametersConfidence'] 
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))
        
