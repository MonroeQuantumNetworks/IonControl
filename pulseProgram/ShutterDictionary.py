'''
Created on Apr 13, 2014

@author: pmaunz
'''

from modules.SequenceDict import SequenceDict
from copy import deepcopy
import re

class ShutterDictionary(SequenceDict):
    def __init__(self, variabledict):
        super(ShutterDictionary,self).__init__()
        for name, var in variabledict.iteritems():
            if var.type is not None:
                m = re.match("\s*shutter(?:\s+(\w+)){0,1}",var.type)
                if m:
                    mask = deepcopy(self.variabledict[m.group(1)]) if m.group(1) is not None and m.group(1) in self.variabledict else None
                    self.append( (name,(deepcopy(var),mask) ) )
                    
    def merge(self, variabledict, overwrite=False):
        # pop all variables that are not in the variabledict
        for var in self:
            if var.name not in variabledict:
                self.pop(var.name)
        # add missing ones
        for name, var in variabledict.iteritems():
            if var.type is not None:
                m = re.match("\s*shutter(?:\s+(\w+)){0,1}",var.type)
                if m and ( name not in self or overwrite):
                    mask = deepcopy(self.variabledict[m.group(1)]) if m.group(1) is not None and m.group(1) in self.variabledict else None
                    self[name] = (deepcopy(var),mask)
                        
                    

