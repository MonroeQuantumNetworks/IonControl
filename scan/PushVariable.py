'''
Created on Dec 20, 2014

@author: pmaunz
'''
from modules.Expression import Expression
import logging


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
        self.strMinimum = None
        self.strMaximum = None
        
    def __setstate__(self, s):
        self.__dict__ = s
        self.__dict__.setdefault( 'destinationName', None )
        self.__dict__.setdefault( 'variableName', None )
        self.__dict__.setdefault( 'strMinimum', None )
        self.__dict__.setdefault( 'strMaximum', None )
        
    def evaluate(self, variables=dict(), useFloat=False):
        if self.definition:
            self.value = self.expression.evaluate( self.definition, variables, useFloat=useFloat )
        if self.strMinimum:
            self.minimum = self.expression.evaluate( self.strMinimum, variables, useFloat=useFloat )
        if self.strMaximum:
            self.maximum = self.expression.evaluate( self.strMaximum, variables, useFloat=useFloat )
        
    def pushRecord(self, variables=None):
        if variables is not None:
            self.evaluate(variables)
        if (self.push and self.destinationName is not None and self.destinationName != 'None' and 
            self.variableName is not None and self.variableName != 'None' and self.value is not None and 
            (not self.minimum or self.value >= self.minimum) and 
            (not self.maximum or self.value <= self.maximum)):
            return [(self.destinationName, self.variableName, self.value)]
        else:
            logging.getLogger(__name__).info("Not pushing {0} to {1}: {2} <= {3} <= {4}".format(self.variableName, self.destinationName, self.minimum, self.value, self.maximum))
        return []
    
    @property
    def key(self):
        return (self.destinationName, self.variableName)


