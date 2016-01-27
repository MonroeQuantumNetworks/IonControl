"""
Created on 01 Dec 2015 at 10:51 AM

author: jmizrahi
"""

import logging

import numpy
import sympy
from sympy.parsing.sympy_parser import parse_expr

from modules.Expression import Expression
from modules.MagnitudeParser import isIdentifier, isValueExpression
from modules.magnitude import mg, MagnitudeError
from modules.enum import enum
from AWGSegmentModel import nodeTypes


class AWGWaveform(object):
    """waveform object for AWG channels. Responsible for parsing and evaluating waveforms.

    Attributes:
       settings (Settings): main settings
       channel (int): which channel this waveform belongs to
       dependencies (set): The variable names that this waveform depends on
       waveformCache (OrderedDict): cache of evaluated waveforms. The key in the waveform cache is a waveform, with all
       variables evaluated except 't' (e.g. 7*sin(3*t)+4). The value is a dict. The key to that dict is a range (min, max), and the
       value is a numpy array of samples, e.g. {(0, 2): numpay.array([1,2,31]), (12, 15): numpy.array([6,16,23,5])}
       """
    def __init__(self, channel, settings, waveformCache):
        self.settings = settings
        self.channel = channel
        self.waveformCache = waveformCache
        self.dependencies = set()
        self.updateDependencies()

    @property
    def sampleRate(self):
        return self.settings.deviceProperties['sampleRate']

    @property
    def minSamples(self):
        return self.settings.deviceProperties['minSamples']

    @property
    def maxSamples(self):
        return self.settings.deviceProperties['maxSamples']

    @property
    def sampleChunkSize(self):
        return self.settings.deviceProperties['sampleChunkSize']

    @property
    def padValue(self):
        return self.calibrateInvIfNecessary(self.settings.deviceProperties['padValue'])

    @property
    def minAmplitude(self):
        return self.calibrateInvIfNecessary(self.settings.deviceProperties['minAmplitude'])

    @property
    def maxAmplitude(self):
        return self.calibrateInvIfNecessary(self.settings.deviceProperties['maxAmplitude'])

    @property
    def stepsize(self):
        return 1/self.sampleRate

    @property
    def segmentDataRoot(self):
        return self.settings.channelSettingsList[self.channel]['segmentDataRoot']

    def calibrateInvIfNecessary(self, p):
        """Converts raw to volts if useCalibration is True"""
        if not self.settings.deviceSettings.get('useCalibration'):
            return p
        else:
            return self.settings.deviceProperties['calibrationInv'](p)

    def updateDependencies(self):
        """Determine the set of variables that the waveform depends on"""
        logger = logging.getLogger(__name__)
        self.dependencies = set()
        self.updateSegmentDependencies(self.segmentDataRoot.children)
        self.dependencies.discard('t')

    def updateSegmentDependencies(self, nodeList):
        for node in nodeList:
            if node.nodeType==nodeTypes.segment:
                node.stack = node.expression._parse_expression(node.equation)
                nodeDependencies = node.expression.findDependencies(node.stack)
                self.dependencies.update(nodeDependencies)
                if isIdentifier(node.duration):
                    self.dependencies.add(node.duration)
            elif node.nodeType==nodeTypes.segmentSet:
                if isIdentifier(node.repetitions):
                    self.dependencies.add(node.repetitions)
                self.updateSegmentDependencies(node.children) #recursive

    def evaluate(self):
        """evaluate the waveform"""
        _, sampleList = self.evaluateSegments(self.segmentDataRoot.children)
        return self.compliantSampleList(sampleList)

    def evaluateSegments(self, nodeList, startStep=0):
        """Evaluate the list of nodes in nodeList.
        Args:
            nodeList: list of nodes to evaluate
            startStep: the step number at which evaluation starts
        Returns:
            startStep, sampleList: The step at which the next waveform begins, together with a list of samples
        """
        sampleList = numpy.array([])
        for node in nodeList:
            if node.enabled:
                if node.nodeType==nodeTypes.segment:
                    duration = self.settings.varDict[node.duration]['value'] if isIdentifier(node.duration) else Expression().evaluateAsMagnitude(node.duration)
                    startStep, newSamples = self.evaluateEquation(node, duration, startStep)
                    sampleList = numpy.append(sampleList, newSamples)
                elif node.nodeType==nodeTypes.segmentSet:
                    repMag = self.settings.varDict[node.repetitions]['value'] if isIdentifier(node.repetitions) else Expression().evaluateAsMagnitude(node.repetitions)
                    repetitions = int(repMag.to_base_units().val) #convert to float, then to integer
                    for n in range(repetitions):
                        startStep, newSamples = self.evaluateSegments(node.children, startStep) #recursive
                        sampleList = numpy.append(sampleList, newSamples)
        return startStep, sampleList

    def evaluateEquation(self, node, duration, startStep):
        """Evaluate the waveform of the specified node's equation.

        Returns:
            sampleList: list of values to program to the AWG.
        """
        #calculate number of samples
        numSamples = duration*self.sampleRate
        numSamples = int( numSamples.toval() ) #convert to float, then to integer
        numSamples = max(0, min(numSamples, self.maxSamples-startStep)) #cap at maxSamples-startStep, so that the last sample does not exceed maxSamples
        stopStep = numSamples + startStep - 1
        nextSegmentStartStep = stopStep + 1
        # first test expression with dummy variable to see if units match up, so user is warned otherwise
        try:
            node.expression.variabledict = {varName:varValueTextDict['value'] for varName, varValueTextDict in self.settings.varDict.iteritems()}
            node.expression.variabledict.update({'t':mg(1, 'us')})
            node.expression.evaluateWithStack(node.stack[:])
            error = False
        except MagnitudeError:
            logging.getLogger(__name__).warning("Must be dimensionless!")
            error = True
            nextSegmentStartStep = startStep
            sampleList = numpy.array([])
        if not error:
            varValueDict = {varName:varValueTextDict['value'].to_base_units().val for varName, varValueTextDict in self.settings.varDict.iteritems()}
            varValueDict['t'] = sympy.Symbol('t')
            sympyExpr = parse_expr(node.equation, varValueDict) #parse the equation
            key = str(sympyExpr)
            if self.settings.cacheDepth > 0:
                if key in self.waveformCache:
                    self.waveformCache[key] = self.waveformCache.pop(key) #move key to the most recent position in cache
                    for (sampleStartStep, sampleStopStep), samples in self.waveformCache[key].iteritems():
                        if sampleStartStep==startStep and sampleStopStep==stopStep: #this means that there is an exact match
                            sampleList = samples
                            break
                        elif max(startStep, sampleStartStep) > min(stopStep, sampleStopStep): #this means there is no overlap
                            continue
                        else: #This means there is some overlap, but not an exact match
                            if startStep < sampleStartStep and stopStep < sampleStopStep:
                                sampleList = self.computeFunction(sympyExpr, varValueDict['t'], startStep, sampleStartStep-1)
                                sampleList = numpy.append(sampleList, samples[:stopStep]) #TODO: THIS IS PROBABLY OFF BY ONE
                                
                            break
                    else: #This is an else on the for loop, it executes if there is no break (i.e. if there are no computed samples with overlap)
                        sampleList = self.computeFunction(sympyExpr, varValueDict['t'], startStep, numSamples)
                        self.waveformCache[key][(startStep, stopStep)] = sampleList
                else:
                    sampleList = self.computeFunction(sympyExpr, varValueDict['t'], startStep, numSamples)
                    self.waveformCache[sympyExpr] = {(startStep, stopStep): sampleList}
                    if len(self.waveformCache) > self.settings.cacheDepth:
                        self.waveformCache.popitem(last=False) #remove the least recently used cache item
            else:
                sampleList = self.computeFunction(sympyExpr, varValueDict['t'], startStep, numSamples)
        return nextSegmentStartStep, sampleList

    def computeFunction(self, sympyExpr, tVar, startStep, numSamples):
        """Compute the value of a function over a specified range.
        Args:
            sympyExpr (str): A string containing a function of 't' (e.g. 7*sin(3*t))
            tVar (Symbol): sympy symbol for 't'
            startStep (int): where to start computation
            numSamples (int): how many samples to compute
        Returns:
            sampleList (numpy.array): list of function values
        """
        func = sympy.lambdify(tVar, sympyExpr, "numpy") #turn string into a python function
        clippedFunc = lambda t: max(self.minAmplitude, min(self.maxAmplitude, func(t))) #clip at min and max amplitude
        vectorFunc = numpy.vectorize(clippedFunc, otypes=[numpy.float64]) #vectorize the function
        step = self.stepsize.toval(ounit='s')
        sampleList = vectorFunc( (numpy.arange(numSamples)+startStep)*step ) #apply the function to each time step value
        return sampleList

    def compliantSampleList(self, sampleList):
        """Make the sample list compliant with the capabilities of the AWG
        Args:
            sampleList (numpy array): calculated list of samples, might be impossible for AWG to output
        Returns:
            sampleList (numpy array): output list of samples, within AWG capabilities
            """
        numSamples = len(sampleList)
        if numSamples > self.maxSamples:
            sampleList = sampleList[:self.maxSamples]
        if numSamples < self.minSamples:
            extraNumSamples = self.minSamples - numSamples #make sure there are at least minSamples
            if self.minSamples % self.sampleChunkSize != 0: #This should always be False if minSamples and sampleChunkSize are internally consistent
                extraNumSamples += self.sampleChunkSize - (self.minSamples % self.sampleChunkSize)
        elif numSamples % self.sampleChunkSize != 0:
            extraNumSamples = self.sampleChunkSize - (numSamples % self.sampleChunkSize)
        else:
            extraNumSamples = 0
        sampleList = numpy.append(sampleList, [self.padValue]*extraNumSamples)
        return sampleList

if __name__ == '__main__':
    from AWG.AWGSegmentModel import AWGSegmentNode, AWGSegment, AWGSegmentSet
    import timeit
    class Settings:
        deviceProperties = dict(
        sampleRate = mg(1, 'GHz'), #rate at which the samples programmed are output by the AWG
        minSamples = 1, #minimum number of samples to program
        maxSamples = 4000000, #maximum number of samples to program
        sampleChunkSize = 1, #number of samples must be a multiple of sampleCnunkSize
        padValue = 2047, #the waveform will be padded with this number ot make it a multiple of sampleChunkSize, or to make it the length of minSamples
        minAmplitude = 0, #minimum amplitude value (raw)
        maxAmplitude = 4095, #maximum amplitude value (raw)
        numChannels = 2,  #Number of channels
        calibration = lambda voltage: 2047. + 3413.33*voltage, #function that returns raw amplitude number, given voltage
        calibrationInv = lambda raw: -0.599707 + 0.000292969*raw #function that returns voltage, given raw amplitude number
        )
        deviceSettings = {}
        root = AWGSegmentSet(None)
        channelSettingsList = [{'segmentDataRoot':root}]
        varDict = {'a':{'value':mg(1, 'MHz'), 'text':None},
                   'b':{'value':mg(3, ''), 'text':None},
                   'w1':{'value':mg(.6, 'Hz'), 'text':None},
                   'w2':{'value':mg(17, 'kHz'), 'text':None},
                   'q':{'value':mg(12, ''), 'text':None},
                   'd':{'value':mg(1, ''), 'text':None},
                   'w':{'value':mg(200, 'GHz'), 'text':None},
                   'w3':{'value':mg(1, 'GHz'), 'text':None}}

    def setup():
        s = Settings()
        w = AWGWaveform(0, s)
        node1 = AWGSegment(equation='sin(a*b*t)', duration='1 ms', parent=s.root)
        node2 = AWGSegment(equation='sin(w1*t+q)+sin(w2*t+d)', duration='1 ms', parent=s.root)
        node3 = AWGSegment(equation='cos(w*t)', duration='1 ms', parent=s.root)
        node4 = AWGSegment(equation='sin(w1*t)*sin(w2*t)', duration='1 ms', parent=s.root)
        node5 = AWGSegment(equation='sin(w3*t)', duration='1 ms', parent=s.root)
        s.root.children.append(node1)
        s.root.children.append(node2)
        s.root.children.append(node3)
        s.root.children.append(node4)
        s.root.children.append(node5)
        w.updateDependencies()
        return w, s

    def test(w, s):
        w.evaluateSegments(s.root.children)

    n=1
    t=timeit.timeit("test(w,s)", setup="from __main__ import test, setup; w,s = setup()", number=n)
    print t/n


