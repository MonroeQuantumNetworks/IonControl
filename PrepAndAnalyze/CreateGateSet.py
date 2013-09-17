# -*- coding: utf-8 -*-
"""
Created on Mon Sep 09 14:53:25 2013

@author: plmaunz
"""

import xml.etree.ElementTree as ElementTree
from xml.dom import minidom

basis = ['I', 'x', 'y', 'x2' ]
filename = "GateSetV2.xml"
    
def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def gateSequence(parent, name, sequence, i):
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

   
root = ElementTree.Element('GateSetDefinition')

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