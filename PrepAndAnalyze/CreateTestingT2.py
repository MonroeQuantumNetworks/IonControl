# -*- coding: utf-8 -*-
"""
Created on Mon Sep 09 14:53:25 2013

@author: plmaunz
"""

import random
from xml.dom import minidom
from itertools import chain
 
import xml.etree.ElementTree as ElementTree


sequencelength = 1000
randomizations = 6

fiducials = [ ['I'], ['x'], ['y'], ['x','x'], ['x','x','x'], ['y','y','y'] ]
basis = [ ['I'], ['x'], ['y'] ]
training2 = [ ['x','y'], ['y','x']]
training3 = [ ['x','x','y'],['y','y','x'] ]

spamTime = 0.002
gateTime = 0.000045

#Maximum GST sequence length = 2^7 = 128
nmax = 10
filename = "TestingSequenceT2.xml"

class BlochState:
    positions = ['d','u','i','-i','1','-1']  # the 6 points on the Bloch sphere
    Transitions = { 'Ip':{'d':'d','u':'u','i':'i','-i':'-i','1':'1','-1':'-1'}, # Transitions between state as lookup tables
                    'xp':{'d':'u','u':'d','i':'i','-i':'-i','1':'-1','-1':'1'},
                    'yp':{'d':'u','u':'d','i':'-i','-i':'i','1':'1','-1':'-1'}, 
                    '-xp':{'d':'u','u':'d','i':'i','-i':'-i','1':'-1','-1':'1'},
                    '-yp':{'d':'u','u':'d','i':'-i','-i':'i','1':'1','-1':'-1'},
                    'I':{'d':'d','u':'u','i':'i','-i':'-i','1':'1','-1':'-1'},
                    'x':{'d':'1','u':'-1','i':'i','-i':'-i','1':'u','-1':'d'},
                    'y':{'d':'i','u':'-i','i':'u','-i':'d','1':'1','-1':'-1'},
                    '-x':{'d':'-1','u':'1','i':'i','-i':'-i','1':'d','-1':'u'},
                    '-y':{'d':'-i','u':'i','i':'d','-i':'u','1':'1','-1':'-1'}}
    TransitionToZLookup = { 'd':['Ic'], 'u':['Ic'], 'i':['yc','-yc'], '-i':['yc','-yc'], '1':['xc','-xc'], '-1':['xc','-xc']} # Lookup clifford gate that stransitions a state into the z-basis
                    
    def __init__(self):
        self.state = 'd'
        self.sequence = list()
                           
    def transition(self, gate):
        """transition the state with the gate and keep track of the sequence of applied gates
        """
        self.state = self.Transitions[gate][self.state]
        self.sequence.append(gate)
        
    def transitionToZ(self):
        """ Add Clifford gate to transition into the z-Basis
        """
        gateList = self.TransitionToZLookup[self.state]
        self.transition( gateList[random.randrange(0,len(gateList))] )

    def __len__(self):
        return len(self.sequence)

def flatten(listOfLists):
    "Flatten one level of nesting"
    return chain.from_iterable(listOfLists)
   
def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def gateSequence(parent, name, sequence, i):
    """Create XML element for gateSequence
    """
    state = BlochState()
    for op in flatten(sequence):
        state.transition(op)
    e  = ElementTree.SubElement(parent, 'GateSequence', {'name': name, 'index': str(i), 'expected': state.state, 'length':str(len(state))})
    e.text = ", ".join(flatten(sequence))

def allstrings(alphabet, length):
    """Find the list of all strings of 'alphabet' of length 'length'"""
    
    if length == 0: return []
    
    c = [[a] for a in alphabet[:]]
    if length == 1: return c
    
    c = [[x,y] for x in alphabet for y in alphabet]
    if length == 2: return c
    
    for _ in range(2, length):
        c = [[x]+y for x in alphabet for y in c]
    
    return c


testsequences = [ ['I'] * sequencelength,
                  ['x'] * sequencelength,
                  ['y'] * sequencelength,
                  ['x','y'] * int(sequencelength/2)]
                  
for i in range(randomizations):               
    testsequences.append([basis[random.randrange(0,len(basis))] for i in range(sequencelength)])
   
root = ElementTree.Element('GateSequenceDefinition')

i = 0
totalTime = 0
for truncation in range(0,101):
    root.append( ElementTree.Comment("Strings of length {0}".format(truncation)))
    for sequence in testsequences:
        gateSequence(root,str(i),sequence[0:truncation],i)
        i+=1
        totalTime += spamTime + gateTime*len(list(flatten(sequence[0:truncation])))

for truncation in range(110,1001,10):
    root.append( ElementTree.Comment("Strings of length {0}".format(truncation)))
    for sequence in testsequences:
        gateSequence(root,str(i),sequence[0:truncation],i)
        i+=1
        totalTime += spamTime + gateTime*len(list(flatten(sequence[0:truncation])))

    
with open(filename,'w') as f:
    f.write(prettify(root))



print "Number of sequences:", i
print "Total time for 1 experiment per sequence [s]:", totalTime
print "Total time for 1000 experiments per sequence [h]:", totalTime/3.6
