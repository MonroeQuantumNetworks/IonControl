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
from gateSequence.GateDefinition import GateDefinition
from gateSequence.GateSequenceContainer import GateSequenceContainer
from modules.MagnitudeParser import parse
from collections import defaultdict

resultsTable = None
headerList = list()

gateDefinitionFile = r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\GateDefinition-Microwave.xml"
compositeGateDefinitionFile = r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\GateDefinition-Microwave-B2-2.xml"

trainingSequenceFile = r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\TrainingSequenceT3-2014-10-16.xml"

goodGateSetTraining = [ (datetime.date(2014,11,21), [3, 4] ),
                        (datetime.date(2014,11,22), [1,2] ),
                        (datetime.date(2014,11,23), [1,2] ),
                        (datetime.date(2014,11,24), [1,2] )     ]

goodCompositeGateSetTraining = [  (datetime.date(2014,11,21), [1,2,3] ),
                        (datetime.date(2014,11,22), [1,2] ),
                        (datetime.date(2014,11,23), [1] ),
                        (datetime.date(2014,11,24), [1] )      ]


datadirectory = DataDirectory('QGA')
outputpath = datadirectory.path( datetime.date(2014,11,24))

gatedef = GateDefinition()
gatedef.loadGateDefinition(gateDefinitionFile)    

trainingSequence = GateSequenceContainer(gatedef)
trainingSequence.loadXml(trainingSequenceFile)

compositeGatedef = GateDefinition()
compositeGatedef.loadGateDefinition(compositeGateDefinitionFile)    

compositeTrainingSequence = GateSequenceContainer(compositeGatedef)
compositeTrainingSequence.loadXml(trainingSequenceFile)

from itertools import groupby

def runLengthEncode (plainText):
    res = []

    for k,i in groupby(plainText):
        run = list(i)
        if(len(run) > 4):
            res.append("(G{1})^{0}".format(len(run), k))
        else:
            res.append('G')
            res.append('G'.join(run))

    return "".join(res)

def addGs(raw):
    result = list()
    for char in raw:
        if char not in '()^0123456789':
            result.append('G'+char)
        else:
            result.append(char)
    return ''.join(result)

def saveResultsWithLookup(resultsTable, sequence, filename):
    with open(filename, 'w') as f:
        for r in resultsTable:
            gateseq = sequence.GateSequenceDict[ str(int(r[0]))]
            gateseq = "".join(gateseq) if gateseq else "0"
            print >> f, gateseq, " ".join( map(str, r[1:]))

def saveCondensedResults(resultsTable, sequence, filename):
    bright =  defaultdict( lambda: 0 )
    total = defaultdict( lambda:0 )
    for x, b, _, _ in resultsTable:
        bright[x] += b
        total[x] += 10
        
    with open(filename, 'w') as f:
        for (x1, b), (x2, t) in zip( sorted(bright.iteritems()), sorted(total.iteritems()) ): #@UnusedVariable
            gateseq = sequence.GateSequenceAttributes[str(int(x1))].get('condensed', None)
            if gateseq is None:
                gateseq = sequence.GateSequenceDict[ str(int(x1))]
                if gateseq:
                    gateseq = runLengthEncode(gateseq)
                else:
                    gateseq = '{}'
            else:
                gateseq = addGs(gateseq)
            print >> f, gateseq, b, t, 0, 0


def saveResultsRaw(resultsTable, filename):
    with open(filename, 'w') as f:
        for r in resultsTable:
            print >> f, " ".join( map(str, r))

def saveLookupTable(sequence, filename):
    with open(filename, 'w') as f:
        for k, v in sequence.GateSequenceDict.iteritems():
            print >> f, k, "".join(v) if v else "0"
   
def expectedDuration( trace, numPi, index, sequence ):
    Attributes = sequence.GateSequenceAttributes[str(int(index))]
    Pulses = parse(Attributes['length'])
    SingleExperiment = ( Pulses*numPi*parse(trace.description['PulseProgram']['piTime'])+parse(trace.description['PulseProgram']['PreWaitTime']) )
    experiments = trace.description['PulseProgram']['experiments']
    experiments = parse(experiments) if isinstance(experiments,str) else experiments
    return SingleExperiment * experiments
    
    
def add_expected_time( results, trace, sequence, accumPulseLength ):
    resultslist = list()
    for record in results:
        x, _, start = record
        newrecord = record +  (expectedDuration(trace, accumPulseLength, x, sequence ).toval('s')+start, )
        resultslist.append( newrecord )
    return resultslist
        
def assembleData( filenameTemplate, filenameKeys, sequence, expectedLength, accumPulseLength ):
    filenameBody, filenameExt = os.path.splitext(filenameTemplate)
    RawResultsTable = list()
    totalexperiments = 0
    resultsTable = None
    for date, filenolist in filenameKeys:
        path = datadirectory.path( date )
        for fileno in filenolist:
            filename = filenameBody+"_{0:03d}".format(fileno)+filenameExt
            fullfilename =  os.path.join(path,filename)
            t = Trace()
            t.loadTrace(fullfilename)
            #print t.description["experiments"], t.x, t.raw
            if len(t.x)==expectedLength:
                #print filename, " has expected length."
                headerList.append(filename)
                totalexperiments += 10
                RawResultsTable.extend( add_expected_time( zip(t.x, t.raw0, t.timestamp), t, sequence, accumPulseLength ) )
                t.x, t.raw0 = zip(*sorted(zip(t.x,t.raw0)))
                #print t.description["experiments"], t.x, t.raw
                if resultsTable:
                    resultsTable.append(t.raw0)        
                else:
                    resultsTable = list()
                    resultsTable.append(t.x)
                    resultsTable.append(t.raw0)
                # Accumulate data
            else:
                print filename, "unexpected length {0} instead of expected {1} file {2} is ignored".format(len(t.x),expectedLength,fullfilename)
    
    a = numpy.array( resultsTable )
    numpy.savetxt(os.path.join(outputpath,filenameBody+"_table.txt"),numpy.transpose(a),delimiter='\t',fmt='%.0f') #,header="\t".join(headerList)
    
    saveResultsWithLookup(RawResultsTable, sequence, os.path.join(outputpath,filenameBody+"_assemble.txt") )
    saveResultsRaw(RawResultsTable, os.path.join(outputpath,filenameBody+"_assemble_raw.txt") )
    saveCondensedResults(RawResultsTable, sequence, os.path.join(outputpath,filenameBody+"_condensed.txt"))
    print "Total experiments {0}".format(totalexperiments)
    

assembleData( "GST", goodGateSetTraining, trainingSequence, 3679, 0.5)
saveLookupTable(trainingSequence, os.path.join(outputpath,"GateSequenceTraining_lookup.txt"))
assembleData( "GSTCompensated", goodCompositeGateSetTraining, trainingSequence, 3679, 4.5)

