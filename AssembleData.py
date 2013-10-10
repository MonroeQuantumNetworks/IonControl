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

path = r'C:\Users\Public\Documents\experiments\QGA\2013\2013_10\2013_10_09'
headerList.append("GateSequenceNo")
filenamebody = "GateTestSet"
expectedLength = 2020
minfileno = 1
beyondmaxfileno = 8

for num in range(minfileno,beyondmaxfileno):
    filename = filenamebody+"_{0:03d}.txt".format(num)
    fullfilename =  os.path.join(path,filename)
    t = Trace()
    t.loadTrace(fullfilename)
    #print t.vars.experiments, t.x, t.raw
    if len(t.x)==expectedLength:
        print filename, " has expected length."
        headerList.append(filename)
        t.x, t.raw = zip(*sorted(zip(t.x,t.raw)))
        #print t.vars.experiments, t.x, t.raw
        if resultsTable:
            resultsTable.append(t.raw)        
        else:
            resultsTable = list()
            resultsTable.append(t.x)
            resultsTable.append(t.raw)
    else:
        print filename, "unexpected length {0} instead of expected {1}".format(len(t.x),expectedLength)
print resultsTable
print len(resultsTable)
a = numpy.array( resultsTable )

numpy.savetxt(os.path.join(path,filenamebody+"_{0:03d}_{1:03d}.txt".format(minfileno,beyondmaxfileno-1)),numpy.transpose(a),delimiter='\t',fmt='%.0f') #,header="\t".join(headerList)

