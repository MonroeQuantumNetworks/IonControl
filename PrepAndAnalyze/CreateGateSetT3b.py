# -*- coding: utf-8 -*-
"""
Created on Mon Sep 09 14:53:25 2013

@author: plmaunz

This script is used to create lists of gate sequences for use in gate set
tomography (GST). The output is an XML file, containing a list of gates, formed
from the elements of 'basis'.
"""

from xml.dom import minidom
from itertools import chain
import xml.etree.ElementTree as ElementTree
import random
import collections

#fiducials = [ ['I'], ['x'], ['y'], ['x','x'], ['x','x','x'], ['y','y','y'] ]
fiducials = [ ['I'], ['x'], ['y'], ['-x'], ['-y'], ['x','x'] ]
germs1 = [ ['x'], ['y'] ,['-x'], ['-y'], ['I']]
germs2 = [ ['x','y'] ,['x','-x'],['x','-y'],['y','-x'],['y','-y'], ['-x','-y']]
germs3 = [ ['x','x','y'],['x','-x','y'],['x','y','-y'], ['y','-y','-y'],['y','-y','-x'] ]


spamTime = 0.002
gateTime = 0.000045

#Maximum GST sequence length = 2^7 = 128
nmax = 10
filename = "TrainingSequenceT3b.xml"

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

def flattenAll(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el
    
def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def gateSequence(parent, name, sequence, i, **kwargs):
    """Add a new GateSequence element to the XML element tree. 
    'sequence' is the gate sequence string itself.
    'parent' is the top level XML header.
    'name' and 'i' are used to label each gate sequence.
    """
    state = BlochState()
    for op in flatten(sequence):
        state.transition(op)
    kwargs.update({'name': name, 'index': str(i), 'expected':state.state, 'length':str(len(state))})
    e  = ElementTree.SubElement(parent, 'GateSequence', kwargs)
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

def all_fiducial_strings(fiducials, alphabet, length):
    """Find the list of all strings of 'alphabet' of length 'length'"""
    
    if length == 0: return []
    
    c = [[a] for a in fiducials]
    if length == 1: return c
    
    c = [[x,y] for x in fiducials for y in fiducials]
    if length == 2: return c
    
    for _ in range(2, length):
        c = [y[0:-1]+[x]+y[-1:] for x in alphabet for y in c]
    
    return c



def gst_strings(fiducials, alphabet, length):
    """return the list of all gate set tomography strings with gates taken from 'alphabet'.
    
    A single gate from 'alphabet' is repeated 'length' times. Each element of alphabet is used to prepare
    and analyze. The total length of the returned string is length + 2.    
    """
    #Triply nested loop, as each element of alphabet can be the first, middle, or last gate
    return [[x] + [alphabet[i]]*length + [y] for i in range(0,len(alphabet)) for x in fiducials for y in fiducials]

def gst_strings_condensed(fiducials, alphabet, length):
    """return the list of all gate set tomography strings with gates taken from 'alphabet'.
    
    A single gate from 'alphabet' is repeated 'length' times. Each element of alphabet is used to prepare
    and analyze. The total length of the returned string is length + 2.    
    """
    #Triply nested loop, as each element of alphabet can be the first, middle, or last gate
    return [flattenAll([x, '(' , alphabet[i],  ')^', str(length) ,y]) for i in range(0,len(alphabet)) for x in fiducials for y in fiducials]
       
root = ElementTree.Element('GateSequenceDefinition')

#'i' counts each element. Every time a gate sequence is added, i is incremented.
i = 0
totalTime = 0

root.append( ElementTree.Comment('Strings of length 0'))
gateSequence(root,str(i),[],i)
i += 1
totalTime += spamTime

for length in range(1,4):
    root.append( ElementTree.Comment('Strings of length {0}'.format(length)))
    for sequence in all_fiducial_strings(fiducials,germs1,length):
        gateSequence(root,str(i),sequence,i)
        i += 1
        totalTime += spamTime + gateTime*len(list(flatten(sequence)))

#GST sequences, of the form prep-G^n-analyze 
seqlengths = [2**n for n in range(1, nmax+1)]
for length in seqlengths:    
    root.append( ElementTree.Comment('GST sequences G^n, n = {0}'.format(length)))
    for sequence, condensed in zip( gst_strings(fiducials, germs1, length), gst_strings_condensed(fiducials, germs1, length)):
        gateSequence(root, str(i), sequence, i, condensed=''.join(list(condensed)))
        i += 1
        totalTime += spamTime + gateTime*len(list(flatten(sequence)))

seqlengths = [2**n for n in range(0, nmax)]
for length in seqlengths:    
    root.append( ElementTree.Comment('GST sequences G^n, n = {0} for products of gates'.format(length)))
    for sequence, condensed in zip( gst_strings(fiducials, germs2+germs3, length), gst_strings_condensed(fiducials, germs2+germs3, length)):
        gateSequence(root, str(i), sequence, i, condensed=''.join(list(condensed)))
        i += 1
        totalTime += spamTime + gateTime*len(list(flatten(sequence)))
"""
seqlengths = [2**n for n in range(0, nmax-1)]
for length in seqlengths:    
    root.append( ElementTree.Comment('GST sequences G^n, n = {0} for products of three gates'.format(length)))
    for sequence, condensed in zip( gst_strings(fiducials, germs6, length), gst_strings_condensed(fiducials, germs6, length)):
        gateSequence(root, str(i), sequence, i, condensed=''.join(list(condensed)))
        i += 1
        totalTime += spamTime + gateTime*len(list(flatten(sequence)))
        
"""
with open(filename,'w') as f:
    f.write(prettify(root))

print "Number of sequences:", i
print "Total time for 1 experiment per sequence [s]:", totalTime
print "Total time for 1000 experiments per sequence [h]:", totalTime/3.6