'''
Created on Dec 22, 2014

@author: pmaunz
'''


from modules.Expression import Expression
from modules.magnitude import mg
from modules import WeakMethod
from PyQt4 import QtCore


class ExpressionValueException(Exception):
    pass


class ExpressionValue(QtCore.QObject):
    expression = Expression()
    valueChanged = QtCore.pyqtSignal(object, object, object, object)

    def __init__(self, name=None, globalDict=None, value=mg(0)):
        super(ExpressionValue, self).__init__()
        self._globalDict = globalDict
        self.name = name
        self._string = None
        self._value = value
        self.registrations = list()        # subscriptions to global variable values
        
    def __getstate__(self):
        return self.name, self._string, self._value
    
    def __setstate__(self, state):
        self.__init__( state[0] )
        self._string = state[1]
        self._value = state[2]
        
    @property
    def globalDict(self):
        return self._globalDict
    
    @globalDict.setter
    def globalDict(self, d):
        self._globalDict = d
        self.string = self._string 
        
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, v):
        self._value = v
        self.valueChanged.emit(self.name, self._value, self._string, 'value')
        
    @property 
    def string(self):
        return self._string if self._string is not None else str(self._value)
    
    @string.setter
    def string(self, s):
        if self._globalDict is None:
            raise ExpressionValueException("Global dictionary is not set in {0}".format(self.name))
        self._string = s
        for name, reference in self.registrations:
            self._globalDict.valueChanged(name).disconnect(reference)
        self.registrations[:] = []
        if self._string:
            self._value, dependencies = self.expression.evaluateAsMagnitude(self._string, self._globalDict, listDependencies=True)
            for dep in dependencies:
                reference = WeakMethod.ref(self.recalculate)
                self._globalDict.valueChanged(dep).connect(reference)
                self.registrations.append((dep, reference))
                       
    @property
    def hasDependency(self):
        #return self._string is not None
        return len(self.registrations)>0
    
    @property
    def data(self):
        return (self.name, self._value, self._string )
    
    @data.setter
    def data(self, val):
        self.name, self.value, self.string = val
    
    def recalculate(self, name, value, origin):
        if self._globalDict is None:
            raise ExpressionValueException("Global dictionary is not set in {0}".format(self.name))
        if self._string:
            newValue = self.expression.evaluateAsMagnitude(self._string, self._globalDict)
        if newValue != self._value:
            self._value = newValue
            self.valueChanged.emit(self.name, self._value, self._string, 'recalculate')

    def __hash__(self):
        return hash(self._value)