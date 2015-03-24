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

fiducials = [ tuple(), ('x',), ('y',), ('x','x','x'), ('y','y','y'), ('x','x') ]
germs = [ ('x',), ('y',) , ('I',), ('x','y'), ('x' ,'y','I'), ('x','I','y'), ('x','I','I'),('y','I','I'), ('x','x','I','y'), ('x','y','y','I'), ('x','x','y','x','y','y') ]


spamTime = 0.002
gateTime = 0.000040  
gateTimeBB1 = 9*gateTime

nmax = 8
filename = "GSTSequenceT7-256.xml"

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
    for op in flattenAll(sequence):
        state.transition(op)
    kwargs.update({'name': name, 'index': str(i), 'expected':state.state, 'length':str(len(state))})
    e  = ElementTree.SubElement(parent, 'GateSequence', kwargs)
    e.text = ", ".join(flattenAll(sequence))

def allstrings(alphabet, length):
    """Find the list of all strings of 'alphabet' of length 'length'"""
    
    if length == 0: return []
    
    c = [(a,) for a in alphabet[:]]
    if length == 1: return c
    
    c = [(x,y) for x in alphabet for y in alphabet]
    if length == 2: return c
    
    for _ in range(2, length):
        c = [(x,)+y for x in alphabet for y in c]
    
    return c

def all_fiducial_strings(fiducials, alphabet, length):
    """Find the list of all strings of 'alphabet' of length 'length'"""
    
    if length == 0: return []
    
    c = [(a,) for a in fiducials]
    if length == 1: return c
    
    c = [(x,y) for x in fiducials for y in fiducials]
    if length == 2: return c
    
    for _ in range(2, length):
        c = [y[0:-1]+(x,)+y[-1:] for x in alphabet for y in c]
    
    return c



def gst_strings(fiducials, alphabet, length):
    """return the list of all gate set tomography strings with gates taken from 'alphabet'.
    
    A single gate from 'alphabet' is repeated 'length' times. Each element of alphabet is used to prepare
    and analyze. The total length of the returned string is length + 2.    
    """
    #Triply nested loop, as each element of alphabet can be the first, middle, or last gate
    gstStrings = list()
    condensedGstStrings = list()
    for a in alphabet:
        germString = list()
        repetition = 0
        while len(germString)+len(a)<=length:
            germString.extend(a)
            repetition += 1
#         if len(germString)>length:
#             repetition -= 1
#             condensedGermString = [ "(", a, ")^", str(repetition),germString[len(a)*repetition:length]] if repetition>0 else [germString[len(a)*repetition:length]]
#         else:
        condensedGermString = [ "(", a, ")^", str(repetition),germString[len(a)*repetition:length]]            
        germString = germString[0:length]
        gstStrings.extend( [[x] + germString + [y] for x in fiducials for y in fiducials] )
        condensedGstStrings.extend( [[x] + condensedGermString + [y] for x in fiducials for y in fiducials] )
    return gstStrings, condensedGstStrings
       
root = ElementTree.Element('GateSequenceDefinition')

#'i' counts each element. Every time a gate sequence is added, i is incremented.
i = 0
totalTime = 0
totalTimeBB1 = 0

gstSet = set()   # used to check for redundant sequences

root.append( ElementTree.Comment('Strings of length 0'))
gstSet.add( tuple() )
gateSequence(root,str(i),[],i)
i += 1

germlist = [g for g in germs if len(g)==1]
for length in range(1,4):
    root.append( ElementTree.Comment('Strings of length {0}'.format(length)))
    for sequence in all_fiducial_strings(fiducials,germlist,length):
        flatTuple = tuple(flattenAll(sequence))
        if flatTuple not in gstSet:
            gstSet.add(flatTuple)
            gateSequence(root,str(i),sequence,i)
            i += 1
            gatecount = len(list(flatten(sequence)))
            totalTime += spamTime + gateTime*gatecount
            totalTimeBB1 += spamTime + gateTimeBB1*gatecount

#GST sequences, of the form prep-G^n-analyze 
seqlengths = [2**n for n in range(1, nmax+1)]
for length in seqlengths:    
    root.append( ElementTree.Comment('GST sequences G^n, n = {0}'.format(length)))
    for sequence, condensed in zip( *gst_strings(fiducials, germs, length) ):
        flatTuple = tuple(flattenAll(sequence))
        if flatTuple not in gstSet:
            gstSet.add(flatTuple)
            gateSequence(root, str(i), sequence, i, condensed=''.join(flattenAll(condensed)))
            i += 1
            gatecount = len(list(flatten(sequence)))
            totalTime += spamTime + gateTime*gatecount
            totalTimeBB1 += spamTime + gateTimeBB1*gatecount
        else:
            print "Skipping {0} ".format(''.join(flattenAll(condensed)), sequence)



with open(filename,'w') as f:
    f.write(prettify(root))

print "Number of sequences:", i
print "Total time for 1 experiment per sequence [s]:", totalTime
print "Total time for 1 experiment BB1 per sequence [s]:", totalTimeBB1
print "Total time for 100 experiments per sequence [h]:", totalTime/36
print "Total time for 100 experiments BB1 per sequence [h]:", totalTimeBB1/36