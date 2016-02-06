"""
Created on 01 Feb 2016 at 10:12 AM

author: jmizrahi
"""

import numpy
from collections import OrderedDict

cacheDepth = 2
waveformCache = OrderedDict()

def computeFunction(start, stop):
    numSamples = stop-start+1
    if numSamples <= 0:
        res = numpy.array([])
    else:
        res = numpy.array([n*n for n in range(start, stop+1)])
    return res

def evaluateWaveform(key, startStep, stopStep):
    if cacheDepth > 0: #meaning, use the cache
        if key in waveformCache:
            waveformCache[key] = waveformCache.pop(key) #move key to the most recent position in cache
            for (sampleStartStep, sampleStopStep), samples in waveformCache[key].iteritems():
                if startStep >= sampleStartStep and stopStep <= sampleStopStep: #this means the required waveform is contained within the cached waveform
                    sliceStart = startStep - sampleStartStep
                    sliceStop  = stopStep  - sampleStartStep + 1
                    sampleList = samples[sliceStart:sliceStop]
                    break
                elif max(startStep, sampleStartStep) > min(stopStep, sampleStopStep): #this means there is no overlap
                    continue
                else: #This means there is some overlap, but not an exact match
                    if startStep < sampleStartStep: #compute the first part of the sampleList
                        sampleListStart = computeFunction(startStep, sampleStartStep-1)
                        if stopStep <= sampleStopStep: #use the cached part for the rest
                            sliceStop = stopStep - sampleStartStep + 1
                            sampleList = numpy.append(sampleListStart, samples[:sliceStop])
                            waveformCache[key].pop((sampleStartStep, sampleStopStep)) #update cache entry with new samples
                            waveformCache[key][(startStep, sampleStopStep)] = numpy.append(sampleListStart, samples)
                        else: #compute the end of the sampleList, then use the cached part for the middle
                            sampleListEnd = computeFunction(sampleStopStep+1, stopStep)
                            sampleList = numpy.append(numpy.append(sampleListStart, samples), sampleListEnd)
                            waveformCache[key].pop((sampleStartStep, sampleStopStep))
                            waveformCache[key][(startStep, stopStep)] = sampleList
                    else: #compute the end of the sampleList, and use the cached part for the beginning
                        sampleListEnd = computeFunction(sampleStopStep+1, stopStep)
                        sliceStart = startStep - sampleStartStep
                        sampleList = numpy.append(samples[sliceStart:], sampleListEnd)
                        waveformCache[key].pop((sampleStartStep, sampleStopStep))
                        waveformCache[key][(sampleStartStep, stopStep)] = numpy.append(samples, sampleListEnd)
                    break
            else: #This is an else on the for loop, it executes if there is no break (i.e. if there are no computed samples with overlap)
                sampleList = computeFunction(startStep, stopStep)
                waveformCache[key][(startStep, stopStep)] = sampleList
        else: #if the waveform is not in the cache
            sampleList = computeFunction(startStep, stopStep)
            waveformCache[key] = {(startStep, stopStep): sampleList}
            if len(waveformCache) > cacheDepth:
                waveformCache.popitem(last=False) #remove the least recently used cache item
    else: #if we're not using the cache at all
        sampleList = computeFunction(startStep, stopStep)
    return sampleList

print evaluateWaveform('abc', 0, 5)
print evaluateWaveform('abc', 3, 7)
print evaluateWaveform('abc', 8, 12)
print evaluateWaveform('bqb', 0, 4)
print evaluateWaveform('bqb', 0, 2)
print evaluateWaveform('bqb', 3, 6)
print evaluateWaveform('abc', 8, 12)
print evaluateWaveform('ccc', 10, 15)
print evaluateWaveform('ccc', 12, 14)
print evaluateWaveform('ccc', 6, 12)
print evaluateWaveform('ccc', 4, 20)
print waveformCache