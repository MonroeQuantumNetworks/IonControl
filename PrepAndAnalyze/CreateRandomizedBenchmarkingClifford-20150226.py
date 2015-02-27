# -*- coding: utf-8 -*-
"""
Created on Mon Sep 09 14:53:25 2013

@author: plmaunz

Generate the sequences necessary for randomized benchmarking
"""

from collections import Counter
import os.path
import random
from xml.dom import minidom
import collections
from modules.flatten import flattenAll

import xml.etree.ElementTree as ElementTree
from qecc import Clifford as CliffordBase
from qecc import Pauli
from _collections import defaultdict
import copy
from modules.doProfile import doprofile

random.seed(6276514257268929411L)

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
    
    def inv(self):
        base = super(MyClifford, self).inv()
        my = copy.deepcopy(self)
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

SequenceLengths = range(2,502,50)
Randomizations = 50   # at length 100
filename = "Randomized-Clifford-2015-02-26.xml"
path = ""

        
def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def gateSequence(parent, sequence, name, index, expected, indices):
    """Create the XML Element representing one gate sequence from that sequence.
        The element is given the supplied name, index and expected attributes
    """
    e  = ElementTree.SubElement(parent, 'GateSequence', {'name': name, 'index': str(index), 'expected':expected, 'length': str(len(indices)), 'indices': '-'.join(map(str,indices))})
    e.text = ", ".join(flattenAll(sequence))
    return e


def createRandomization(length):
    """create one randomization given length
       returns the BlochState object representing the sequence
    """
    state = i
    randomization = list()
    indexlist = list()
    for _ in range(length):
        randomindex = random.randrange(0,len(StringList))
        randomization.append( StringList[randomindex]  )
        indexlist.append(randomindex)
    for g in randomization:
        state = state * StringToClifford[g]
    inversionstrings = CliffordToString[state.inv()]
    inversionindex = random.randrange(0,len(inversionstrings))
    indexlist.append( inversionindex )
    randomization.append( inversionstrings[inversionindex] )
    state = state * state.inv()
    if state != i:
        raise( Exception("overall string is not the identity" ))
    return randomization, indexlist

def randomizations(length):
    return 25 + int(Randomizations * (length/100.))
    
def getRandomizations(root, length, outcomes, index, totallength):
    print "Sequencelength {0} randomizations {1} ".format(length,randomizations(length))
    for randindex in range(randomizations(length)): 
        sequence, indices = createRandomization(length)
        gateSequence( root, sequence, "{0}".format(index), index, 'd', indices)
        outcomes.append('d')
        totallength += len(sequence)
        index += 1
    return index, totallength
    
    
if __name__=="__main__":    
    root = ElementTree.Element('GateSequenceDefinition')
    index = 0     # keep track of the current index
    outcomes = list() # list of all expected outcomes  
    totallength = 0   # total number of gates
    for length in SequenceLengths:
        index, totallength = getRandomizations(root, length, outcomes, index, totallength)

    with open(os.path.join(path,filename),'w') as f:
        f.write(prettify(root))
    
    print index
    print Counter(outcomes)
    print totallength