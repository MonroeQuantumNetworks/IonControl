# -*- coding: utf-8 -*-
"""
Created on Tue Oct 08 17:26:24 2013

@author: Jonathan Mizrahi
"""

basis = ['I', 'x', 'y', 'x2' ]
Tgate= 7500
Tpi = 2700
numexpts = 50

Iphase = 0
Iwait  = Tgate
Ipulse = 0

xphase = 0
xwait  = Tgate-Tpi/2
xpulse = Tpi/2

yphase = 4096
ywait  = Tgate-Tpi/2
ypulse = Tpi/2

x2phase = 0
x2wait  = Tgate-Tpi
x2pulse = Tpi

gate_dict = {'I' :[Iphase, Iwait, Ipulse],
             'x' :[xphase, xwait, xpulse],
             'y' :[yphase, ywait, ypulse],
             'x2':[x2phase, x2wait, x2pulse]}

#Maximum GST sequence length = 2^7 = 128
nmax = 7

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
       
expectedContent = []

def addToExpectedContent(sequence):
    """Add a gate sequence string to the expected unprocessed content"""
    for expt in range(numexpts):
        expectedContent.append(999999)
        expectedContent.append(len(sequence))
        for gate in sequence:
            expectedContent.extend(gate_dict.get(gate))
    
##'i' counts each element. Every time a gate sequence is added, i is incremented.
i = 0
expectedContent.extend([0]*(2*numexpts))
i += 1
#This creates the expected contents of the unprocessed file
for length in range(1,4):
    for sequence in allstrings(basis,length):
        addToExpectedContent(sequence)
        i += 1

#GST sequences, of the form prep-G^n-analyze 
seqlengths = [2**n for n in range(1, nmax+1)]
for length in seqlengths:    
    for sequence in gst_strings(basis, length):
        addToExpectedContent(sequence)
        i += 1
        
#This creates the same sequences as above, with x2 appended to each
addToExpectedContent(['x2'])
i += 1
for length in range(1,4):
    for sequence in allstrings(basis,length):
        addToExpectedContent(sequence + ['x2'])
        i += 1

for length in seqlengths:    
    for sequence in gst_strings(basis, length):
        addToExpectedContent(sequence + ['x2'])
        i += 1

with open('C:\\Users\\Public\\Documents\\aaAQC_FPGA\\unprocessed.dat', 'r') as unprocessed:
    content = map(int, unprocessed.readlines())

if len(expectedContent) != len(content):
    print 'unprocessed data does not match :-('
#check that all the file contents, except the memory address, match the expected contents
elif all([content[i] == expectedContent[i] for i in range(len(content)) if expectedContent[i] != 999999]):
    print 'unprocessed data checks out!'
else:
    print 'unprocessed data does not match :-('