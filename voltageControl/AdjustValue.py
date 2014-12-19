'''
Created on Dec 10, 2014

@author: pmaunz
'''
from modules.Expression import Expression
from modules.magnitude import mg
from modules.Observable import Observable


class AdjustValue(object):
    expression = Expression()
    def __init__(self, name=None, line=0, globalDict=None):
        self.globalDict = globalDict
        self.name = name
        self.line = line
        self._string = None
        self._value = mg(0)
        self.observable = Observable()
        self.registrations = list()
        
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, v):
        self._value = v
        self.observable.fire( name=self.name, value=self._value, string=self._string, origin='value' )
        
    @property 
    def string(self):
        return self._string if self._string is not None else str(self._value)
    
    @string.setter
    def string(self, s):
        self._string = s
        for name in self.registrations:
            self.globalDict.observables[name].unsubscribe(self.recalculate)
        if self._string:
            self._value, dependencies = self.expression.evaluateAsMagnitude(self._string, self.globalDict, listDependencies=True)
            for dep in dependencies:
                self.globalDict.observables[dep].subscribe(self.recalculate)
                self.registrations.append(dep)
                       
    @property
    def hasDependency(self):
        return self._string is not None
    
    @property
    def data(self):
        return (self.name, self._value, self._string )
    
    @data.setter
    def data(self, val):
        self.name, self.value, self.string = val
    
    def recalculate(self, event=None):
        if self._string:
            newValue = self.expression.evaluateAsMagnitude(self._string, self.globalDict)
        if newValue!=self._value:
            self._value = newValue
            self.observable.fire( name=self.name, value=self._value, string=self._string, origin='recalculate' )
        