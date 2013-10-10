# -*- coding: utf-8 -*-
"""
Created on Mon Sep 09 14:53:25 2013

@author: plmaunz

This script is used to create lists of gate sequences for use in gate set
tomography (GST). The output is an XML file, containing a list of gates, formed
from the elements of 'basis'.
"""

import xml.etree.ElementTree as ElementTree
from xml.dom import minidom

basis = ['I', 'x', 'y', 'x2' ]
#Maximum GST sequence length = 2^7 = 128
nmax = 7
filename = "GateSetV2.xml"
    
def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def gateSequence(parent, name, sequence, i):
    """Add a new GateSequence element to the XML element tree. 
    'sequence' is the gate sequence string itself.
    'parent' is the top level XML header.
    'name' and 'i' are used to label each gate sequence.
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

def gst_strings(alphabet, length):
    """return the list of all gate set tomography strings with gates taken from 'alphabet'.
    
    A single gate from 'alphabet' is repeated 'length' times. Each element of alphabet is used to prepare
    and analyze. The total length of the returned string is length + 2.    
    """
    #Triply nested loop, as each element of alphabet can be the first, middle, or last gate
    return [[x] + [alphabet[i]]*length + [y] for i in range(0,len(alphabet)) for x in alphabet for y in alphabet]
       
root = ElementTree.Element('GateSetDefinition')

#'i' counts each element. Every time a gate sequence is added, i is incremented.
i = 0
root.append( ElementTree.Comment('Strings of length 0'))
gateSequence(root,str(i),[],i)
i += 1
for length in range(1,4):
    root.append( ElementTree.Comment('Strings of length {0}'.format(length)))
    for sequence in allstrings(basis,length):
        gateSequence(root,str(i),sequence,i)
        i += 1
#
##GST sequences, of the form prep-G^n-analyze 
#seqlengths = [2**n for n in range(1, nmax+1)]
#for length in seqlengths:    
#    root.append( ElementTree.Comment('GST sequences G^n, n = {0}'.format(length)))
#    for sequence in gst_strings(basis, length):
#        gateSequence(root, str(i), sequence, i)
#        i += 1
#
#        
##This creates the same sequences as above, with x2 appended to each
#root.append( ElementTree.Comment('Inverted Strings of length {0}'.format(0)))
#gateSequence(root,str(i),['x2'],i)
#i += 1
#for length in range(1,4):
#    root.append( ElementTree.Comment('Inverted Strings of length {0}'.format(length)))
#    for sequence in allstrings(basis,length):
#        gateSequence(root,str(i),sequence+['x2'],i)
#        i += 1
#
#for length in seqlengths:    
#    root.append( ElementTree.Comment('Inverted GST sequences G^n, n = {0}'.format(length)))
#    for sequence in gst_strings(basis, length):
#        gateSequence(root, str(i), sequence +['x2'], i)
#        i += 1

with open(filename,'w') as f:
    f.write(prettify(root))

print i