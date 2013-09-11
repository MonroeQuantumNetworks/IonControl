# -*- coding: utf-8 -*-
"""
Created on Mon Sep 09 14:53:25 2013

@author: plmaunz
"""

import xml.etree.ElementTree as ElementTree
from xml.dom import minidom
import random

Paulis = ['I', 'xp', 'yp', '-xp', '-yp' ]
Cliffords = ['I', 'xc', 'yc', '-xc', '-yc' ]
SequenceLength = range(0,101,10)
Randomizations = 100

filename = "Randomized-1.xml"
    
def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def gateSequence(parent, name, sequence, index):
    e  = ElementTree.SubElement(parent, 'GateSequence', {'name': name, 'index': str(index)})
    e.text = ", ".join(sequence)

root = ElementTree.Element('GateSetDefinition')




def createRandomization(length):
    randomization = list()
    for i in range(length):
        randomization.append( Paulis[random.randrange(0,len(Paulis))])
        




i = 0
root.append( ElementTree.Comment('Strings of length 0'))
gateSequence(root,str(i),[],i)
i += 1
for length in range(1,4):
    root.append( ElementTree.Comment('Strings of length {0}'.format(length)))
    for sequence in allstrings(basis,length):
        gateSequence(root,str(i),sequence,i)
        i += 1


root.append( ElementTree.Comment('Inverted Strings of length {0}'.format(0)))
gateSequence(root,str(i),['x2'],i)
i += 1
for length in range(1,4):
    root.append( ElementTree.Comment('Inverted Strings of length {0}'.format(length)))
    for sequence in allstrings(basis,length):
        gateSequence(root,str(i),sequence+['x2'],i)
        i += 1


with open(filename,'w') as f:
    f.write(prettify(root))

print i