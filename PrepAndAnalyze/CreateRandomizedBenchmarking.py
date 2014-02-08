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

import xml.etree.ElementTree as ElementTree


Paulis = ['Ip', 'xp', 'Ip', 'yp', 'Ip', '-xp', 'Ip', '-yp' ]
Cliffords = ['Ic', 'xc', 'yc', '-xc', '-yc' ]

SequenceLengths = range(10,101,10)
Randomizations = 100
filename = "Randomized-1.xml"
path = ""

class BlochState:
    positions = ['d','u','i','-i','1','-1']  # the 6 points on the Bloch sphere
    Transitions = { 'Ip':{'d':'d','u':'u','i':'i','-i':'-i','1':'1','-1':'-1'}, # Transitions between state as lookup tables
                    'xp':{'d':'u','u':'d','i':'i','-i':'-i','1':'-1','-1':'1'},
                    'yp':{'d':'u','u':'d','i':'-i','-i':'i','1':'1','-1':'-1'}, 
                    '-xp':{'d':'u','u':'d','i':'i','-i':'-i','1':'-1','-1':'1'},
                    '-yp':{'d':'u','u':'d','i':'-i','-i':'i','1':'1','-1':'-1'},
                    'Ic':{'d':'d','u':'u','i':'i','-i':'-i','1':'1','-1':'-1'},
                    'xc':{'d':'1','u':'-1','i':'i','-i':'-i','1':'u','-1':'d'},
                    'yc':{'d':'i','u':'-i','i':'u','-i':'d','1':'1','-1':'-1'},
                    '-xc':{'d':'-1','u':'1','i':'i','-i':'-i','1':'d','-1':'u'},
                    '-yc':{'d':'-i','u':'i','i':'d','-i':'u','1':'1','-1':'-1'}}
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
        
def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def gateSequence(parent, sequence, name, index, expected):
    """Create the XML Element representing one gate sequence from that sequence.
        The element is given the supplied name, index and expected attributes
    """
    e  = ElementTree.SubElement(parent, 'GateSequence', {'name': name, 'index': str(index), 'expected':expected})
    e.text = ", ".join(sequence)
    return e


def createRandomization(length):
    """create one randomization given length
       returns the BlochState object representing the sequence
    """
    state = BlochState()
    for _ in range(length):
        state.transition( Paulis[random.randrange(0,len(Paulis))] )
        state.transition( Cliffords[random.randrange(0,len(Cliffords))] )       
    state.transition( Paulis[random.randrange(0,len(Paulis))] )
    state.transitionToZ()
    state.transition( Paulis[random.randrange(0,len(Paulis))] )
    return state
    
if __name__=="__main__":    

    root = ElementTree.Element('GateSequenceDefinition')
    index = 0     # keep track of the current index
    outcomes = list() # list of all expected outcomes  
    totallength = 0   # total number of gates
    for length in SequenceLengths:
        for randindex in range(Randomizations): 
            state = createRandomization(length)
            gateSequence( root, state.sequence, "{0},{1}".format(length,randindex), index, state.state)
            outcomes.append(state.state)
            totallength += len(state.sequence)
            index += 1

    with open(os.path.join(path,filename),'w') as f:
        f.write(prettify(root))
    
    print index
    print Counter(outcomes)
    print totallength