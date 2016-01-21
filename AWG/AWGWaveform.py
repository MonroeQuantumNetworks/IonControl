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
       expression (Expression): used for parsing equation
       durationName (str): the name to use for the duration of this waveform
       dependencies (set): The variable names that this waveform depends on
       """
    def __init__(self, channel, settings):
        self.settings = settings
        self.channel = channel
        self.expression = Expression()
        self.durationName = 'Duration (Channel {0})'.format(self.channel)
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
    def equation(self):
        return self.settings.channelSettingsList[self.channel]['equation']

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
        if self.settings.waveformMode==self.settings.waveformModes.equation:
            self.stack = self.expression._parse_expression(self.equation)
            self.dependencies = self.expression.findDependencies(self.stack)
            self.dependencies.remove('t')
            for varname in self.dependencies:
                if varname.startswith('Duration'):
                    logger.exception("Equation variables cannot start with 'Duration'")
            self.dependencies.add(self.durationName)
        else:
            self.dependencies = set()
            self.updateSegmentDependencies(self.segmentDataRoot.children)
        self.dependencies.discard('t')

    def updateSegmentDependencies(self, nodeList):
        for node in nodeList:
            if node.nodeType==nodeTypes.segment:
                node.stack = node.expression._parse_expression(node.equation)
                self.dependencies.update(node.expression.findDependencies(node.stack))
                if isIdentifier(node.duration):
                    self.dependencies.add(node.duration)
            elif node.nodeType==nodeTypes.segmentSet:
                if isIdentifier(node.repetitions):
                    self.dependencies.add(node.repetitions)
                self.updateSegmentDependencies(node.children) #recursive

    def evaluate(self):
        """evaluate the waveform based on either the equation or the segment list"""
        equationMode = self.settings.waveformMode==self.settings.waveformModes.equation
        _, sampleList = self.evaluateEquation() if equationMode else self.evaluateSegments(self.segmentDataRoot.children)
        return self.compliantSampleList(sampleList)

    def evaluateSegments(self, nodeList, startStep=0):
        """Evaluate the waveform based on the segment table.
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
        numSamples = min(numSamples, self.maxSamples) #cap at maxSamples

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
            func = sympy.lambdify(varValueDict['t'], sympyExpr, "numpy") #make into a python function
            func = numpy.vectorize(func, otypes=[numpy.float64]) #vectorize the function
            step = self.stepsize.toval(ounit='s')
            sampleList = func( (numpy.arange(numSamples)+startStep)*step ) #apply the function to each time step value
            nextSegmentStartStep = numSamples + startStep
        return nextSegmentStartStep, sampleList

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
        numpy.clip(sampleList, self.minAmplitude, self.maxAmplitude, out=sampleList) #clip between minAmplitude and maxAmplitude
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
        waveformModes = enum('equation', 'segment')
        waveformMode = 1
        root = AWGSegmentSet(None)
        channelSettingsList = [{'segmentDataRoot':root}]
        varDict = {'a':{'value':mg(1, 'MHz'), 'text':None},
                   'b':{'value':mg(1, ''), 'text':None}}
    s = Settings()
    w = AWGWaveform(0, s)
    node1 = AWGSegment(equation='a*b*t', duration='5 ns', parent=s.root)
    s.root.children.append(node1)
    w.updateDependencies()
    newtime, j = w.evaluateSegments(s.root.children)
    print j
    print len(j)


