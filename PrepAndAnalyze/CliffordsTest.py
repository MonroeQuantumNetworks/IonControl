'''
Created on Nov 27, 2014

@author: pmaunz
'''

from qecc import Clifford as CliffordBase
from qecc import Pauli
from _collections import defaultdict
import copy

class MyClifford(CliffordBase):
    def __init__(self, *args, **kwargs):
        super(MyClifford, self ).__init__(*args, **kwargs)
        
    def __hash__(self):
        return hash(str(self))
    
    def __mul__(self, other):
        base = super(MyClifford, self).__mul__(other)
        my = copy.deepcopy(other)
        my.__dict__ = base.__dict__
        return my


x = MyClifford([Pauli('X',0)], [Pauli('Y',2)]) 
y = MyClifford([Pauli('Z',2)], [Pauli('X',0)]) 
i = MyClifford([Pauli('X',0)], [Pauli('Z',0)]) 


CliffordMap = { 'x': x, 'y': y, 'I': i}

StringList = [('I'), ('x', 'x', 'x', 'y'), ('x', 'x', 'x'), ('x', 'x', 'y', 'x'), ('x', 'x', 'y', 'y'), ('x', 'x', 'y'), ('x', 'x'), ('x', 'y', 'x', 'x'), ('x', 'y', 'x'), 
               ('y', 'y'), ('x', 'y', 'y', 'y'), ('x', 'y', 'y'), ('x', 'y'), ('x'), ('y', 'x', 'x', 'x'), ('y', 'x', 'x'), ('y', 'x'), ('y', 'y', 'x'), ('y', 'y', 'y', 'x'), 
               ('y', 'y', 'y'), ('y'), ('x', 'y', 'y', 'y', 'x'), ('x', 'x', 'x', 'y', 'x'), ('x', 'y', 'x', 'x', 'x'),
               ('I'), ('x', 'x', 'x', 'y'), ('x', 'x', 'x'), ('y', 'x', 'y', 'y'), ('y', 'y', 'x', 'x'), ('x', 'x', 'y'), ('x', 'x'), ('y', 'y', 'x', 'y'), ('y', 'x', 'y'), 
               ('y', 'y'), ('x', 'y', 'y', 'y'), ('x', 'y', 'y'), ('x', 'y'), ('x'), ('y', 'x', 'x', 'x'), ('y', 'x', 'x'), ('y', 'x'), ('y', 'y', 'x'), ('y', 'y', 'y', 'x'), 
               ('y', 'y', 'y'), ('y'), ('y', 'x', 'x', 'x', 'y'), ('y', 'x', 'y', 'y', 'y'), ('y', 'y', 'y', 'x', 'y')]

CliffordToString = defaultdict(list)
StringToClifford = dict()

for string in StringList:
    C = i
    for char in string:
        C *= CliffordMap[char]
    CliffordToString[C].append(string)
    StringToClifford[string] = C
    
print len(CliffordToString)
print len(StringToClifford)


