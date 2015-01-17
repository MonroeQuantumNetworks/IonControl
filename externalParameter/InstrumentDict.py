'''
Created on Jan 16, 2015

@author: pmaunz
'''

InstrumentDict = dict()

class InstrumentException(Exception):
    pass

class InstrumentMeta(type):
    def __new__(self, name, bases, dct):
        if 'className' not in dct:
            raise InstrumentException("Instrument class needs to have class attribute 'className'")
        instrclass = super(InstrumentMeta, self).__new__(self, name, bases, dct)
        InstrumentDict[dct['className']] = instrclass
        return instrclass
    
