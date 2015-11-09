"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
from PyQt4 import QtCore
from externalParameter.persistence import DBPersist
from externalParameter.decimation import StaticDecimation
from modules import magnitude
from modules.magnitude import is_magnitude
from collections import deque, MutableMapping
import time

class GlobalVariablesException(Exception):
    pass


class GlobalVariable(QtCore.QObject):
    valueChanged = QtCore.pyqtSignal(object, object, object)
    persistSpace = 'globalVar'
    persistence = DBPersist()

    def __init__(self, name, value=magnitude.mg(0)):
        super(GlobalVariable, self).__init__()
        self.decimation = StaticDecimation(magnitude.mg(10, 's'))
        self.history = deque(maxlen=10)
        self._value = value
        self._name = name
        self.categories = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newvalue):
        print "GlobalVariable setter {0}: {1}".format(self._name, newvalue)
        if isinstance(newvalue, tuple):
            v, o = newvalue
        else:
            v, o = newvalue, None
        if self._value != v:
            self._value = v
            self.valueChanged.emit(self.name, v, o)
            self.history.appendleft((v, time.time(), o))
            if o is not None:
                self.persistCallback((time.time(), v, None, None))
            else:
                self.decimation.decimate(time.time(), v, self.persistCallback)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, newname):
        self._name, oldname = newname, self._name
        self.persistence.rename(self.persistSpace, oldname, newname)

    def __getstate__(self):
        return self._name, self._value, self.categories, self.history

    def __setstate__(self, state):
        super(GlobalVariable, self).__init__()
        self.decimation = StaticDecimation(magnitude.mg(10, 's'))
        self._name, self._value, self.categories, self.history = state

    def persistCallback(self, data):
        time, value, minval, maxval = data
        unit = None
        if is_magnitude(value):
            value, unit = value.toval(returnUnit=True)
        self.persistence.persist(self.persistSpace, self.name, time, value, minval, maxval, unit)


class GlobalVariablesLookup(MutableMapping):
    def __init__(self, globalDict):
        self.globalDict = globalDict

    def __getitem__(self, key):
        return self.globalDict[key].value

    def __setitem__(self, key, value):
        self.globalDict[key].value = value

    def __delitem__(self, key):
        raise GlobalVariablesException("Cannot delete globals via the GlobalVariablesLookup class")

    def __len__(self):
        return len(self.globalDict)

    def __contains__(self, x):
        return x in self.globalDict

    def __iter__(self):
        return self.globalDict.__iter__()

    def valueChanged(self, key):
        return self.globalDict[key].valueChanged