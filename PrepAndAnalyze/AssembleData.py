# -*- coding: utf-8 -*-
"""
Created on Wed Sep 11 12:09:09 2013

@author: plmaunz
"""

import datetime
import os.path

import numpy

from modules.DataDirectory import DataDirectory
from trace.Trace import Trace


resultsTable = None
headerList = list()

goodGateSequences = [ (datetime.date(2013,10,9), [3, 5, 6, 7, 8, 9, 10, 11, 12] ),
                 (datetime.date(2013,10,10), [2, 4, 5, 6, 7, 8, 10, 11, 12, 13] ),
                 (datetime.date(2013,10,11), [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20] ) ]

goodTestGateSequences = [  (datetime.date(2013,10,9),[1, 4, 5, 6, 7]),
                  (datetime.date(2013,10,10), [2, 3, 4, 5, 6]),
                  (datetime.date(2013,10,11), [2, 3, 5, 7, 9, 10, 11, 12, 14] ) ]


datadirectory = DataDirectory('QGA')
outputpath = datadirectory.path( datetime.date(2013,10,11))

filenamebody = "GateSequence"
expectedLength = 1066
for date, filenolist in goodGateSequences:
    path = datadirectory.path( date )
    for fileno in filenolist:
        filename = filenamebody+"_{0:03d}.txt".format(fileno)
        fullfilename =  os.path.join(path,filename)
        t = Trace()
        t.loadTrace(fullfilename)
        #print t.vars.experiments, t.x, t.raw
        if len(t.x)==expectedLength:
            #print filename, " has expected length."
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

a = numpy.array( resultsTable )
numpy.savetxt(os.path.join(outputpath,filenamebody+"_good.txt"),numpy.transpose(a),delimiter='\t',fmt='%.0f') #,header="\t".join(headerList)

resultsTable = list()
filenamebody = "GateTestSet"
expectedLength = 2020
for date, filenolist in goodTestGateSequences:
    path = datadirectory.path( date )
    for fileno in filenolist:
        filename = filenamebody+"_{0:03d}.txt".format(fileno)
        fullfilename =  os.path.join(path,filename)
        t = Trace()
        t.loadTrace(fullfilename)
        #print t.vars.experiments, t.x, t.raw
        if len(t.x)==expectedLength:
            #print filename, " has expected length."
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

a = numpy.array( resultsTable )
numpy.savetxt(os.path.join(outputpath,filenamebody+"_good.txt"),numpy.transpose(a),delimiter='\t',fmt='%.0f') #,header="\t".join(headerList)

