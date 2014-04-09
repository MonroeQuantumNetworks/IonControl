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


resultsTable = None
headerList = list()

gateDefinitionFile = r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\GateDefinition-Microwave.xml"
compositeGateDefinitionFile = r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\GateDefinition-Microwave-B2.xml"

trainingSequenceFile = r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\TrainingSequenceT2.xml"
testingSequenceFile = r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\TestingSequenceT2.xml"

goodGateSetTraining = [ (datetime.date(2014,4,3), [3, 4, 5] ),
                        (datetime.date(2014,4,4), [1] ),
                        (datetime.date(2014,4,8), [1, 3, 5] ) ]

goodGateSetTesting = [  (datetime.date(2014,4,3),[3, 4]),
                        (datetime.date(2014,4,9), [1] )  ]

goodCompositeGateSetTraining = [  (datetime.date(2014,4,8),[5]) ]

goodCompositeGateSetTesting = [  (datetime.date(2014,4,9),[1]) ]

datadirectory = DataDirectory('QGA')
outputpath = datadirectory.path( datetime.date(2014,4,9))



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
            print >> f, gateseq, r[1], r[2], r[3], r[3]

def saveResultsRaw(resultsTable, filename):
    with open(filename, 'w') as f:
        for r in resultsTable:
            print >> f, r[0], r[1], r[2], r[3], r[3]

def saveLookupTable(sequence, filename):
    with open(filename, 'w') as f:
        for k, v in sequence.GateSequenceDict.iteritems():
            print >> f, k, "".join(v) if v else "0"
   
def assembleData( filenameTemplate, filenameKeys, sequence, expectedLength ):
    filenameBody, filenameExt = os.path.splitext(filenameTemplate)
    RawResultsTable = list()
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
                RawResultsTable.extend( zip(t.x, t.raw0, t.raw3, t.timestamp) )
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
                print filename, "unexpected length {0} instead of expected {1}".format(len(t.x),expectedLength)
    
    a = numpy.array( resultsTable )
    numpy.savetxt(os.path.join(outputpath,filenameBody+"_table.txt"),numpy.transpose(a),delimiter='\t',fmt='%.0f') #,header="\t".join(headerList)
    
    saveResultsWithLookup(RawResultsTable, sequence, os.path.join(outputpath,filenameBody+"_assemble.txt") )
    saveResultsRaw(RawResultsTable, os.path.join(outputpath,filenameBody+"_assemble_raw.txt") )

assembleData( "GateSequenceTraining", goodGateSetTraining, trainingSequence, 2599)
saveLookupTable(trainingSequence, os.path.join(outputpath,"GateSequenceTraining_lookup.txt"))
assembleData( "GateSequenceTesting", goodGateSetTesting, testingSequence, 1910)
saveLookupTable(testingSequence, os.path.join(outputpath,"GateSequenceTesting_lookup.txt"))
assembleData( "CompositeGateSequenceTraining", goodCompositeGateSetTraining, trainingSequence, 2599)
assembleData( "CompositeGateSequenceTesting", goodCompositeGateSetTesting, testingSequence, 1910)

