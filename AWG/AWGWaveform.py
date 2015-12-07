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


class AWGWaveform(object):
    expression = Expression() #This has to be a class attribute rather than an instance attribute, so that deepcopy works on a waveform
    def __init__(self, equation, devicePropertiesDict):
        self.devicePropertiesDict = devicePropertiesDict
        self.varDict = SequenceDict()
        self.equation = equation #this sets _equation, stack and varDict

    def __setstate__(self, state):
        self.__dict__ = state

    stateFields = ['devicePropertiesDict', 'equation', 'varDict']

    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    @property
    def sampleRate(self):
        return self.devicePropertiesDict['sampleRate']

    @property
    def minSamples(self):
        return self.devicePropertiesDict['minSamples']

    @property
    def maxSamples(self):
        return self.devicePropertiesDict['maxSamples']

    @property
    def sampleChunkSize(self):
        return self.devicePropertiesDict['sampleChunkSize']

    @property
    def padValue(self):
        return self.devicePropertiesDict['padValue']

    @property
    def minAmplitude(self):
        return self.devicePropertiesDict['minAmplitude']

    @property
    def maxAmplitude(self):
        return self.devicePropertiesDict['maxAmplitude']

    @property
    def stepsize(self):
        return 1/self.sampleRate

    @property
    def equation(self):
        return self._equation

    @equation.setter
    def equation(self, equation):
        self._equation = equation
        oldvars = self.varDict
        self.stack = self.expression._parse_expression(self.equation)
        dependencies = self.expression.findDependencies(self.stack)
        self.varDict = SequenceDict( [(varname,
                                                {'value': oldvars[varname]['value'] if oldvars.has_key(varname) else mg(0),
                                                 'text': oldvars[varname]['text'] if oldvars.has_key(varname) else None})
                                               for varname in dependencies]
                                              )
        self.varDict.pop('t')
        self.varDict['Duration'] = {'value': oldvars['Duration']['value'] if oldvars.has_key('Duration') else mg(1, 'us'),
                                             'text': oldvars['Duration']['text'] if oldvars.has_key('Duration') else None}
        self.varDict.sort(key = lambda val: -1 if val[0]=='Duration' else ord( str(val[0])[0] ))

    @property
    def varMagnitudeDict(self):
        """dict of form var:magnitude"""
        return {varName:varValueTextDict['value'] for varName, varValueTextDict in self.varDict.iteritems()}

    @property
    def varValueDict(self):
        """dict of the form var:value"""
        return {varName:varValueTextDict['value'].to_base_units().val for varName, varValueTextDict in self.varDict.iteritems()}

    def evaluate(self):
        """Evaluate the waveform.

        Returns:
            sampleList: list of values to program to the AWG.
        """
        self.varDict.setdefault('Duration', {'value': mg(1, 'us'), 'text': None}) #varDict should always have a duration

        #calculate number of samples
        numSamples = self.varDict['Duration']['value']*self.sampleRate
        numSamples = int( numSamples.toval() ) #convert to float, then to integer
        numSamples = min(numSamples, self.maxSamples) #cap at maxSamples

        # first test expression with dummy variable to see if units match up, so user is warned otherwise
        self.expression.variabledict = self.varMagnitudeDict
        self.expression.variabledict.update({'t':mg(1, 'us')})
        self.expression.evaluateWithStack(self.stack[:])

        varValueDict = self.varValueDict
        varValueDict.pop('Duration')
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