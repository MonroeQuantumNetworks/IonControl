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

goodGateSetTraining = [ (datetime.date(2014,4,3), [3, 4, 5] ),
                        (datetime.date(2014,4,4), [1] ),
                        (datetime.date(2014,4,8), [1, 3] ) ]

goodGateSetTesting = [  (datetime.date(2014,4,3),[3, 4]) ]


datadirectory = DataDirectory('QGA')
outputpath = datadirectory.path( datetime.date(2014,4,8))

filenamebody = "GateSequenceTraining"
expectedLength = 2599
for date, filenolist in goodGateSetTraining:
    path = datadirectory.path( date )
    for fileno in filenolist:
        filename = filenamebody+"_{0:03d}".format(fileno)
        fullfilename =  os.path.join(path,filename)
        t = Trace()
        t.loadTrace(fullfilename)
        #print t.vars.experiments, t.x, t.raw
        if len(t.x)==expectedLength:
            #print filename, " has expected length."
            headerList.append(filename)
            t.x, t.raw0 = zip(*sorted(zip(t.x,t.raw0)))
            #print t.vars.experiments, t.x, t.raw
            if resultsTable:
                resultsTable.append(t.raw0)        
            else:
                resultsTable = list()
                resultsTable.append(t.x)
                resultsTable.append(t.raw0)
        else:
            print filename, "unexpected length {0} instead of expected {1}".format(len(t.x),expectedLength)

a = numpy.array( resultsTable )
numpy.savetxt(os.path.join(outputpath,filenamebody+"_good.txt"),numpy.transpose(a),delimiter='\t',fmt='%.0f') #,header="\t".join(headerList)

resultsTable = list()
filenamebody = "GateSequenceTesting"
expectedLength = 1910
for date, filenolist in goodGateSetTesting:
    path = datadirectory.path( date )
    for fileno in filenolist:
        filename = filenamebody+"_{0:03d}".format(fileno)
        fullfilename =  os.path.join(path,filename)
        t = Trace()
        t.loadTrace(fullfilename)
        #print t.vars.experiments, t.x, t.raw
        if len(t.x)==expectedLength:
            #print filename, " has expected length."
            headerList.append(filename)
            t.x, t.raw0 = zip(*sorted(zip(t.x,t.raw0)))
            #print t.vars.experiments, t.x, t.raw0
            if resultsTable:
                resultsTable.append(t.raw0)        
            else:
                resultsTable = list()
                resultsTable.append(t.x)
                resultsTable.append(t.raw0)
        else:
            print filename, "unexpected length {0} instead of expected {1}".format(len(t.x),expectedLength)

a = numpy.array( resultsTable )
numpy.savetxt(os.path.join(outputpath,filenamebody+"_good.txt"),numpy.transpose(a),delimiter='\t',fmt='%.0f') #,header="\t".join(headerList)

