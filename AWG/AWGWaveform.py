"""
Created on 01 Dec 2015 at 10:51 AM

author: jmizrahi
"""

from modules.Expression import Expression
from modules.magnitude import mg, Magnitude
from modules.SequenceDict import SequenceDict
import numpy
import sympy
from sympy.parsing.sympy_parser import parse_expr
import math
import logging

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
        return self.settings.deviceProperties['padValue']

    @property
    def minAmplitude(self):
        return self.settings.deviceProperties['minAmplitude']

    @property
    def maxAmplitude(self):
        return self.settings.deviceProperties['maxAmplitude']

    @property
    def stepsize(self):
        return 1/self.sampleRate

    @property
    def equation(self):
        return self.settings.channelSettingsList[self.channel]['equation']

    def updateDependencies(self):
        logger = logging.getLogger(__name__)
        self.stack = self.expression._parse_expression(self.equation)
        self.dependencies = self.expression.findDependencies(self.stack)
        self.dependencies.remove('t')
        for varname in self.dependencies:
            if varname.startswith('Duration'):
                logger.exception("Equation variables cannot start with 'Duration'")
        self.dependencies.add(self.durationName)

    def evaluate(self):
        """Evaluate the waveform.

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
        func = numpy.vectorize(func, otypes=[numpy.int]) #vectorize the function and set output to integers
        step = self.stepsize.toval(ounit='s')
        sampleList = func( numpy.arange(numSamples)*step ) #apply the function to each time step value

        #make sampleList match what the AWG device can program
        numpy.clip(sampleList, self.minAmplitude, self.maxAmplitude, out=sampleList) #clip between minAmplitude and maxAmplitude
        if numSamples < self.minSamples:
            extraNumSamples = self.minSamples - numSamples #make sure there are at least minSamples
            if self.minSamples % self.sampleChunkSize != 0: #This should always be False if minSamples and sampleChunkSize are internally consistent
                extraNumSamples += self.sampleChunkSize - (self.minSamples % self.sampleChunkSize)
        elif numSamples % self.sampleChunkSize != 0:
            extraNumSamples = self.sampleChunkSize - (numSamples % self.sampleChunkSize)
        else:
            extraNumSamples = 0
        sampleList = numpy.pad(sampleList, (0,extraNumSamples), 'constant', constant_values = self.padValue)
        sampleList = sampleList.tolist()
        return sampleList