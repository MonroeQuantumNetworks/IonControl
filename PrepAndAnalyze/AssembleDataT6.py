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
from modules.magnitude import mg

resultsTable = None
headerList = list()

gateDefinitionFile = r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\GateDefinition-Microwave-B2-3-allemptyI.xml"
compositeGateDefinitionFile = r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\GateDefinition-Microwave-B2-3-DriftControl.xml"

trainingSequenceFile = r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\GSTSequenceT6.xml"
RBSequenceFile = r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\Randomized-Clifford-2015-02-26.xml"

#allemptyI
goodGateSetTraining = [ (datetime.date(2015,3,1), [1,2,3] ),
                        (datetime.date(2015,3,2), [1] ) ]

goodCompositeGateSetTraining = [ (datetime.date(2015,2,27), [0,1] ),
                        (datetime.date(2015,2,28), [1,2,3]),
                        (datetime.date(2015,3,1), [1,2] ),
                        (datetime.date(2015,3,2), [1] )    ]

goodRB =[  (datetime.date(2015,2,28), [1] ), 
           (datetime.date(2015,3,1), [1,2] ), 
           (datetime.date(2015,3,2), [1] ) ]

goodCompositeRB = [ (datetime.date(2015,2,28), [1,2,3] ),
                        (datetime.date(2015,3,1), [1,2]),
                        (datetime.date(2015,3,2), [1] )       ]

datadirectory = DataDirectory('QGA')
outputpath = datadirectory.path( datetime.date(2015,3,2))

gatedef = GateDefinition()
gatedef.loadGateDefinition(gateDefinitionFile)    

trainingSequence = GateSequenceContainer(gatedef)
trainingSequence.loadXml(trainingSequenceFile)

compositeGatedef = GateDefinition()
compositeGatedef.loadGateDefinition(compositeGateDefinitionFile)    

compositeTrainingSequence = GateSequenceContainer(compositeGatedef)
compositeTrainingSequence.loadXml(trainingSequenceFile)

RBSequence = GateSequenceContainer(gatedef)
RBSequence.loadXml(RBSequenceFile)

compositeRBSequence = GateSequenceContainer(compositeGatedef)
compositeRBSequence.loadXml(RBSequenceFile)

from itertools import groupby

def runLengthEncode (plainText):
    res = []

    for k,i in groupby(plainText):
        run = list(i)
        if(len(run) > 4):
            res.append("(G{1})^{0}".format(len(run), k.lower()))
        else:
            res.append('G')
            res.append('G'.join(map(lambda s: s.lower(),run)))

    return "".join(res)

def addGs(raw):
    result = list()
    for char in raw:
        if char not in '()^0123456789':
            result.append('G'+char.lower())
        else:
            result.append(char.lower())
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
        total[x] += 20
        
    with open(filename, 'w') as f:
        f.write("## Columns = plus count, count total\n")
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
            print >> f, k, sequence.GateSequenceAttributes[str(k)]['expected'], "".join(v) if v else "{}"
   
def expectedDuration( trace, numPi, index, sequence ):
    return mg(0,'s')
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
        
def assembleData( filenameTemplate, filenameKeys, sequence, expectedLength, accumPulseLength, qualifier="" ):
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
                totalexperiments += 20
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
    
    saveResultsWithLookup(RawResultsTable, sequence, os.path.join(outputpath,"{0}_{1}assemble.txt".format(filenameBody,qualifier) ) )
    saveResultsRaw(RawResultsTable, os.path.join(outputpath,"{0}_{1}assemble_raw.txt".format(filenameBody,qualifier) ) )
    saveCondensedResults(RawResultsTable, sequence, os.path.join(outputpath,"{0}_{1}condensed.txt".format(filenameBody,qualifier) ) )
    print "Total experiments {0}".format(totalexperiments)
    
def createSeparateLists( filenameTemplate, filenameKeys ):
    filenameBody, filenameExt = os.path.splitext(filenameTemplate)
    linearList = list()
    randomizedList = list()
    for date, filenolist in filenameKeys:
        path = datadirectory.path( date )
        linearList.append((date,list()))
        randomizedList.append((date,list()))
        for fileno in filenolist:
            filename = filenameBody+"_{0:03d}".format(fileno)+filenameExt
            fullfilename =  os.path.join(path,filename)
            t = Trace()
            t.loadTrace(fullfilename)
            #print t.description["experiments"], t.x, t.raw
            if all(t.x[i] <= t.x[i+1] for i in xrange(len(t.x)-1)):
                linearList[-1][1].append( fileno )
            else:
                randomizedList[-1][1].append( fileno )
    return linearList, randomizedList
                
   
linearGST, randomizedGST = createSeparateLists( "GSTEmptyI", goodGateSetTraining )
linearCompensatedGST, randomizedCompensatedGST = createSeparateLists( "GST", goodCompositeGateSetTraining )
linearRb, randomizedRb = createSeparateLists( "RBEmptyI", goodRB)
linearCompensatedRb, randomizedCompensatedRb = createSeparateLists( "RB", goodCompositeRB)

print "GST Empty I"
print  linearGST
print  randomizedGST
print "GSTCompensated"   
print linearCompensatedGST
print randomizedCompensatedGST
print "RB Empty I"
print linearRb
print randomizedRb
print "RBCompensated"
print linearCompensatedRb
print randomizedCompensatedRb

assembleData( "GSTEmptyI", goodGateSetTraining, trainingSequence, 3889, 0.5)
saveLookupTable(trainingSequence, os.path.join(outputpath,"GateSequenceTraining_lookup.txt"))
assembleData( "GST", goodCompositeGateSetTraining, trainingSequence, 3889, 4.5)
  
assembleData( "RBEmptyI", goodRB, RBSequence, 1383, 0.5)
saveLookupTable(RBSequence, os.path.join(outputpath,"RB_lookup.txt"))
assembleData( "RB", goodCompositeRB, RBSequence, 1383, 4.5)

# linear

#assembleData( "GSTDrift", linearGST, trainingSequence, 2922, 0.5, "linear_")
#assembleData( "GSTCompensatedDrift", linearCompensatedGST, trainingSequence, 2922, 4.5, "linear_")
  
#assembleData( "RBDrift", linearRb, RBSequence, 834, 0.5, "linear_")
#assembleData( "RBCompensatedDrift", linearCompensatedRb, RBSequence, 834, 4.5, "linear_")

# randomized

#assembleData( "GSTDrift", randomizedGST, trainingSequence, 2922, 0.5, "randomized_")
#assembleData( "GSTCompensatedDrift", randomizedCompensatedGST, trainingSequence, 2922, 4.5, "randomized_")
  
#assembleData( "RBDrift", randomizedRb, RBSequence, 834, 0.5, "randomized_")
#assembleData( "RBCompensatedDrift", randomizedCompensatedRb, RBSequence, 834, 4.5, "randomized_")
