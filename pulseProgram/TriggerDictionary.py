'''
Created on Apr 13, 2014

@author: pmaunz
'''

from modules.SequenceDict import SequenceDict
from copy import deepcopy

class TriggerDictionary(SequenceDict):
    def __init__(self, variabledict):
        super(TriggerDictionary,self).__init__()
        self.update( (x.name,x) for x in variabledict.values() if x.type=='trigger' )

    def merge(self, variabledict, overwrite=False):
        # pop all variables that are not in the variabledict
        for var in self:
            if var.name not in variabledict or variabledict[var.name].type != 'trigger':
                self.pop(var.name)
        # add missing ones
        for var in variabledict.values():
            if var.type == 'trigger':
                if var.name not in self or overwrite:
                    self[var.name] = deepcopy(var)
                        
