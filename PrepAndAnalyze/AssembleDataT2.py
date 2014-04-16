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

resultsTable = None
headerList = list()

gateDefinitionFile = r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\GateDefinition-Microwave.xml"
compositeGateDefinitionFile = r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\GateDefinition-Microwave-B2.xml"

trainingSequenceFile = r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\TrainingSequenceT2.xml"
testingSequenceFile = r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\TestingSequenceT2.xml"

goodGateSetTraining = [ (datetime.date(2014,4,3), [3, 4, 5] ),
                        (datetime.date(2014,4,4), [1] ),
                        (datetime.date(2014,4,8), [1, 3, 5] ),
                        (datetime.date(2014,4,9), [1, 2] ),
                        (datetime.date(2014,4,10), [1] ),
                        (datetime.date(2014,4,11), [1] ),
                        (datetime.date(2014,4,14), [1,2,3,4,5,6,7] ),
                        (datetime.date(2014,4,15), [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16] ),
                        (datetime.date(2014,4,16), [1,2,3,4,5] )     ]

goodGateSetTesting = [  (datetime.date(2014,4,3),[3, 4]),
                        (datetime.date(2014,4,9), [1, 2, 3, 4] ),
                        (datetime.date(2014,4,10), [1] ),
                        (datetime.date(2014,4,11), [1] ),
                        (datetime.date(2014,4,14), [1,2,3,4,5,6,7] ),
                        (datetime.date(2014,4,15), [1,2,3,4,5,6,7,8,9,10,11,12,13,14] ),
                        (datetime.date(2014,4,16), [1,2,3,4,5] )      ]

goodCompositeGateSetTraining = [  (datetime.date(2014,4,8),[5]),
                                  (datetime.date(2014,4,9), [1,2, 3, 4] ),
                        (datetime.date(2014,4,14), [1,2,3,4,5,6] ),
                        (datetime.date(2014,4,15), [1,2,3,4,5,6,7,8,9,10,11,12,13,14] ),
                        (datetime.date(2014,4,16), [1,2,3,4] )    ]

goodCompositeGateSetTesting = [  (datetime.date(2014,4,9),[1, 2]),
                        (datetime.date(2014,4,10), [1] ),
                        (datetime.date(2014,4,14), [1,2,3,4,5,6] ),
                        (datetime.date(2014,4,15), [1,2,3,4,5,6,7,8,9,10,11,12,13] ) ,
                        (datetime.date(2014,4,16), [1,2,3,4,5] )   ]

datadirectory = DataDirectory('QGA')
outputpath = datadirectory.path( datetime.date(2014,4,16))



gatedef = GateDefinition()
gatedef.loadGateDefinition(gateDefinitionFile)    

trainingSequence = GateSequenceContainer(gatedef)
trainingSequence.loadXml(trainingSequenceFile)

testingSequence = GateSequenceContainer(gatedef)
testingSequence.loadXml(trainingSequenceFile)

compositeGatedef = GateDefinition()
compositeGatedef.loadGateDefinition(compositeGateDefinitionFile)    

compositeTrainingSequence = GateSequenceContainer(compositeGatedef)
compositeTrainingSequence.loadXml(trainingSequenceFile)

compositeTestingSequence = GateSequenceContainer(compositeGatedef)
compositeTestingSequence.loadXml(trainingSequenceFile)

def saveResultsWithLookup(resultsTable, sequence, filename):
    with open(filename, 'w') as f:
        for r in resultsTable:
            gateseq = sequence.GateSequenceDict[ str(int(r[0]))]
            gateseq = "".join(gateseq) if gateseq else "0"
            print >> f, gateseq, " ".join( map(str, r[1:]))

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
    SingleExperiment = ( Pulses*numPi*parse(trace.headerDict['piTime'])+parse(trace.headerDict['PreWaitTime']) )
    return SingleExperiment * parse(trace.headerDict['experiments'])
    
    
def add_expected_time( results, trace, sequence, accumPulseLength ):
    resultslist = list()
    for record in results:
        x, _, _, start = record
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
            #print t.vars.experiments, t.x, t.raw
            if len(t.x)==expectedLength:
                #print filename, " has expected length."
                headerList.append(filename)
                totalexperiments += t.raw3[0]
                RawResultsTable.extend( add_expected_time( zip(t.x, t.raw0, t.raw3, t.timestamp), t, sequence, accumPulseLength ) )
                t.x, t.raw0 = zip(*sorted(zip(t.x,t.raw0)))
                #print t.vars.experiments, t.x, t.raw
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
    print "Total experiments {0}".format(totalexperiments)

assembleData( "GateSequenceTraining", goodGateSetTraining, trainingSequence, 2599, 0.5)
saveLookupTable(trainingSequence, os.path.join(outputpath,"GateSequenceTraining_lookup.txt"))
assembleData( "GateSequenceTesting", goodGateSetTesting, testingSequence, 1910, 0.5)
saveLookupTable(testingSequence, os.path.join(outputpath,"GateSequenceTesting_lookup.txt"))
assembleData( "CompositeGateSequenceTraining", goodCompositeGateSetTraining, trainingSequence, 2599, 4.5)
assembleData( "CompositeGateSequenceTesting", goodCompositeGateSetTesting, testingSequence, 1910, 4.5)

