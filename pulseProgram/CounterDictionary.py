'''
Created on Apr 13, 2014

@author: pmaunz
'''

from modules.SequenceDict import SequenceDict
from copy import deepcopy

class CounterDictionary(SequenceDict):
    def __init__(self, *args, **kwargs):
        super(CounterDictionary,self).__init__(*args, **kwargs)
 
    def merge(self, variabledict, overwrite=False):
        # pop all variables that are not in the variabledict
        for var in self.values():
            if var.name not in variabledict or variabledict[var.name].type != 'counter':
                self.pop(var.name)
        # add missing ones
        for var in variabledict.values():
            if var.type == 'counter':
                if var.name not in self or overwrite:
                    self[var.name] = deepcopy(var)
        self.sortToMatch( variabledict.keys() )
                        
        