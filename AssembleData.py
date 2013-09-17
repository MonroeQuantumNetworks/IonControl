# -*- coding: utf-8 -*-
"""
Created on Wed Sep 11 12:09:09 2013

@author: plmaunz
"""

from Trace import Trace
import os.path
import numpy

resultsTable = None
headerList = list()

path = r'\\snl\mesa\Projects\Quantum_Graph_Analysis\experiments\QGA\2013\2013_09\2013_09_10'
headerList.append("GateSequenceNo")


for num in range(10):
    filename = "GateSet_{0:03d}.txt".format(num+1)
    headerList.append(filename)
    fullfilename =  os.path.join(path,filename)
    t = Trace()
    t.loadTrace(fullfilename)
    #print t.vars.experiments, t.x, t.raw
    t.x, t.raw = zip(*sorted(zip(t.x,t.raw)))
    #print t.vars.experiments, t.x, t.raw
    if resultsTable:
        resultsTable.append(t.raw)        
    else:
        resultsTable = list()
        resultsTable.append(t.x)
        resultsTable.append(t.raw)
print resultsTable
print len(resultsTable)
a = numpy.array( resultsTable )

numpy.savetxt(os.path.join(path,"GateSet_001_010.txt"),numpy.transpose(a),delimiter='\t',fmt='%.0f',header="\t".join(headerList))

