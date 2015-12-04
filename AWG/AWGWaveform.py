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
    def __init__(self, equation, sampleRate, maxSamples, maxAmplitude):
        self.sampleRate = sampleRate
        self.maxSamples = maxSamples
        self.maxAmplitude = maxAmplitude
        self.varDict = SequenceDict()
        self.equation = equation #this sets _equation, stack and varDict

    def __setstate__(self, state):
        self.__dict__ = state

    stateFields = ['sampleRate', 'maxSamples', 'maxAmplitude', 'equation', 'varDict']

    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

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
        if not self.varDict.has_key('Duration'):
            self.varDict['Duration'] = {'value': mg(1, 'us'), 'text': None}
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

        sympyExpr = parse_expr(self.equation, varValueDict)
        func = sympy.lambdify(varValueDict['t'], sympyExpr, "numpy")
        func = numpy.vectorize(func, otypes=[numpy.int])
        step = self.stepsize.toval(ounit='s')
        res = func( numpy.arange(numSamples)*step )
        numpy.clip(res, 0, self.maxAmplitude, out=res)
        res = res.tolist() + [2047]*(64+64*int(math.ceil(numSamples/64.0)) - numSamples)
        return res