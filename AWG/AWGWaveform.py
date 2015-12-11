"""
Created on 01 Dec 2015 at 10:51 AM

author: jmizrahi
"""

import logging

import numpy
import sympy
from sympy.parsing.sympy_parser import parse_expr

from modules.Expression import Expression
from modules.magnitude import mg
from modules.enum import enum
from uiModules.CategoryTree import CategoryTreeModel


class AWGWaveform(object):
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
    def segmentList(self):
        return self.settings.channelSettingsList[self.channel]['segmentList']

    def calibrateInvIfNecessary(self, p):
        if not self.settings.deviceSettings.get('useCalibration'):
            return p
        else:
            return self.settings.deviceProperties['calibrationInv'](p)

    def updateDependencies(self):
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
            for segment in self.segmentList:
                self.dependencies.add(segment['amplitude'])
                self.dependencies.add(segment['duration'])

    def evaluate(self):
        """evaluate the waveform based on either the equation or the segment list"""
        equationMode = self.settings.waveformMode==self.settings.waveformModes.equation
        return self.evaluateEquation() if equationMode else self.evaluateSegments()

    def evaluateSegments(self):
        sampleList = numpy.array([])
        for segment in self.segmentList:
            if segment['enabled']:
                amplitude = self.settings.varDict[segment['amplitude']]['value'].to_base_units().val
                numSamples = self.settings.varDict[segment['duration']]['value']*self.sampleRate
                numSamples = int( numSamples.toval() ) #convert to float, then to integer
                sampleList = numpy.append(sampleList, [amplitude]*numSamples)
        return self.compliantSampleList(sampleList)

    def evaluateEquation(self):
        """Evaluate the waveform based on the equation.

        Returns:
            sampleList: list of values to program to the AWG.
        """
        #calculate number of samples
        numSamples = self.settings.varDict[self.durationName]['value']*self.sampleRate
        numSamples = int( numSamples.toval() ) #convert to float, then to integer
        numSamples = min(numSamples, self.maxSamples) #cap at maxSamples

        # first test expression with dummy variable to see if units match up, so user is warned otherwise
        self.expression.variabledict = {varName:varValueTextDict['value'] for varName, varValueTextDict in self.settings.varDict.iteritems()}
        self.expression.variabledict.update({'t':mg(1, 'us')})
        self.expression.evaluateWithStack(self.stack[:])

        varValueDict = {varName:varValueTextDict['value'].to_base_units().val for varName, varValueTextDict in self.settings.varDict.iteritems()}
        varValueDict.pop(self.durationName)
        varValueDict['t'] = sympy.Symbol('t')

        sympyExpr = parse_expr(self.equation, varValueDict) #parse the equation
        func = sympy.lambdify(varValueDict['t'], sympyExpr, "numpy") #make into a python function
        func = numpy.vectorize(func, otypes=[numpy.float64]) #vectorize the function
        step = self.stepsize.toval(ounit='s')
        sampleList = func( numpy.arange(numSamples)*step ) #apply the function to each time step value
        return self.compliantSampleList(sampleList)

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