# -*- coding: utf-8 -*-
"""
Created on Mon Sep 09 14:53:25 2013

@author: plmaunz
"""

import xml.etree.ElementTree as ElementTree
from xml.dom import minidom
import random

basis = ['I', 'x', 'y', 'x2' ]
filename = "TestSet.xml"
filenameinversion = "TestSetInversion.xml"
sequencelength = 100
randomizations = 5
    
def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def gateSequence(parent, name, sequence, i):
    """Create XML element for gateSequence
    """
    e  = ElementTree.SubElement(parent, 'GateSequence', {'name': name, 'index': str(i)})
    e.text = ", ".join(sequence)

def allstrings(alphabet, length):
	"""Find the list of all strings of 'alphabet' of length 'length'"""
	
	if length == 0: return []
	
	c = [[a] for a in alphabet[:]]
	if length == 1: return c
	
	c = [[x,y] for x in alphabet for y in alphabet]
	if length == 2: return c
	
	for l in range(2, length):
		c = [[x]+y for x in alphabet for y in c]
		
	return c


testsequences = [ ['I'] * sequencelength,
                  ['x'] * sequencelength,
                  ['y'] * sequencelength,
                  ['x2'] * sequencelength,
                  ['x','y'] * int(sequencelength/2)]
                  
for i in range(randomizations):               
    testsequences.append([basis[random.randrange(0,len(basis))] for i in range(sequencelength)])
   
root = ElementTree.Element('GateSetDefinition')

i = 0
for truncation in range(0,sequencelength+1):
    root.append( ElementTree.Comment("Strings of length {0}".format(truncation)))
    for sequence in testsequences:
        gateSequence(root,str(i),sequence[0:truncation],i)
        i+=1
    
with open(filename,'w') as f:
    f.write(prettify(root))

for truncation in range(0,sequencelength+1):
    root.append( ElementTree.Comment("Strings of length {0}".format(truncation)))
    for sequence in testsequences:
        gateSequence(root,str(i),sequence[0:truncation]+['x2'],i)
        i+=1

with open(filenameinversion,'w') as f:
    f.write(prettify(root))


print i