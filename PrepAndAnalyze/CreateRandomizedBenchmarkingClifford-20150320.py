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
import math
from math import ceil

random.seed(6276514257268921149L)

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

spamTime = 0.002
gateTime = 0.000040 * 9

CliffordMap = { 'x': x, 'y': y, 'I': i}


StringList = [('I'), ('x', 'x', 'x', 'y'), ('x', 'x', 'x'), ('x', 'x', 'y', 'x'), ('x', 'x', 'y', 'y'), ('x', 'x', 'y'), ('x', 'x'), ('x', 'y', 'x', 'x'), ('x', 'y', 'x'), 
               ('y', 'y'), ('x', 'y', 'y', 'y'), ('x', 'y', 'y'), ('x', 'y'), ('x'), ('y', 'x', 'x', 'x'), ('y', 'x', 'x'), ('y', 'x'), ('y', 'y', 'x'), ('y', 'y', 'y', 'x'), 
               ('y', 'y', 'y'), ('y'), ('x', 'y', 'y', 'y', 'x'), ('x', 'x', 'x', 'y', 'x'), ('x', 'y', 'x', 'x', 'x'),
               ('I'), ('x', 'x', 'x', 'y'), ('x', 'x', 'x'), ('y', 'x', 'y', 'y'), ('y', 'y', 'x', 'x'), ('x', 'x', 'y'), ('x', 'x'), ('y', 'y', 'x', 'y'), ('y', 'x', 'y'), 
               ('y', 'y'), ('x', 'y', 'y', 'y'), ('x', 'y', 'y'), ('x', 'y'), ('x'), ('y', 'x', 'x', 'x'), ('y', 'x', 'x'), ('y', 'x'), ('y', 'y', 'x'), ('y', 'y', 'y', 'x'), 
               ('y', 'y', 'y'), ('y'), ('y', 'x', 'x', 'x', 'y'), ('y', 'x', 'y', 'y', 'y'), ('y', 'y', 'y', 'x', 'y')]

CliffordToString = defaultdict(list)
StringToClifford = dict()

for index, string in enumerate(StringList):
    C = i
    for char in string:
        C *= CliffordMap[char]
    CliffordToString[C].append((string, index))
    StringToClifford[string] = C
    
print len(CliffordToString)
print len(StringToClifford)

SequenceLengths = [1,10,50,100,150,200,250,300,350,400,450,500,550,600]
filename = "Randomized-Clifford-2015-03-20.xml"
descriptorfilename = "Randomized-Clifford-2015-03-20.txt"
path = ""

infidelity = 15e-5
epsilon = 0.02
delta = 0.02

def H(e,n):
    return (1.0/(1.0-e))**((1-e)/(n+1)) * (n/(n+e))**((n+e)/(n+1))
                                           
def sigmansq(m,r):
    return m**2 * r**2 + 7./4. * m * r**2

def randomizations(length):
    return -math.log(2/delta)/math.log(H(epsilon,sigmansq(length,infidelity)))
        
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
        state = state * StringToClifford[StringList[randomindex]]
    inversionstrings = CliffordToString[state.inv()]
    inversion = inversionstrings[ random.randrange(0,len(inversionstrings)) ]
    indexlist.append( inversion[1] )
    randomization.append( inversion[0] )
    state = state * state.inv()
    if state != i:
        raise( Exception("overall string is not the identity" ))
    return randomization, indexlist

    
def getRandomizations(root, length, outcomes, index, totallength):
    global totaltime
    numrandomizations = int(ceil(randomizations(length)))
    print "Sequencelength {0} randomizations {1} ".format(length,numrandomizations)
    indexlist = list()
    for randindex in range(numrandomizations): 
        sequence, indices = createRandomization(length)
        gateSequence( root, sequence, "{0}".format(index), index, 'd', indices)
        outcomes.append('d')
        totallength += len(sequence)
        totaltime += spamTime + gateTime * sum(1 for _ in flattenAll(sequence))
        index += 1
        indexlist.append( indices )
    return index, totallength, indexlist

def gatestr(n): 
    return 'G{0}'.format(n)
    
if __name__=="__main__":
    totaltime = 0
    root = ElementTree.Element('GateSequenceDefinition')
    index = 0     # keep track of the current index
    outcomes = list() # list of all expected outcomes  
    totallength = 0   # total number of gates
    indexlist = list()
    for length in SequenceLengths:
        index, totallength, randindexlist = getRandomizations(root, length, outcomes, index, totallength)
        indexlist.extend( randindexlist )

    with open(os.path.join(path,filename),'w') as f:
        f.write(prettify(root))
    
    with open(os.path.join(path,descriptorfilename),'w') as f:
        for index, string in enumerate(StringList):
            f.write( "G{0} {1}\n".format( index, ''.join(string) ) )
        f.write("\n\n")
        for i, l in enumerate(indexlist):
            s = ''.join( map(gatestr,l) )
            f.write( "{0} {1}\n".format(i,s))
        
        
    
    print index
    print Counter(outcomes)
    print totallength
    print "Total time for 1 experiment:", totaltime