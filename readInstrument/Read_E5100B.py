# -*- coding: utf-8 -*-
"""
Created on Fri Dec 14 15:37:21 2012

@author: plmaunz
"""

from trace import Trace

import numpy
import visa #@UnresolvedImport

import ReadGeneric


class E5100B(ReadGeneric.ReadGeneric):
    def __init__(self,address):
        self.GPIB = visa.instrument(address)
        
    def readTrace(self):
        self.t = Trace.Trace()
        self.t.addColumn('real')
        self.t.addColumn('imaginary')
        self.t.addColumn('amplitude')       
        self.t.vars.Instrument = self.GPIB.ask("*IDN?")
        self.t.vars.Center = float(self.GPIB.ask("CENT?"))
        self.t.vars.Start = float(self.GPIB.ask("STAR?") )
        self.t.vars.Stop = float(self.GPIB.ask("STOP?"))
        self.t.rawTrace = numpy.array(self.GPIB.ask("OUTPDATA?").split(","),dtype=float)
        self.t.Trace = self.t.rawTrace.view(complex)
        self.t.vars.Step = (self.t.vars.Stop-self.t.vars.Start)/(self.t.Trace.size-1)
        self.t.x = numpy.arange(self.t.vars.Start,self.t.vars.Stop+self.t.vars.Step,self.t.vars.Step)
        self.t.y = 10*numpy.log(numpy.abs(self.t.Trace))
        self.t.real = numpy.real(self.Trace)
        self.t.imaginary = numpy.imag(self.Trace)
        self.t.amplitude = numpy.imag(self.Trace)
        return self.t
        
if __name__== "__main__":
    Inst = E5100B("GPIB::17")
    t = Inst.readTrace()
    print t.vars.__dict__
    print numpy.abs(t.Trace)
    print t.Trace.size
    print t.TraceX.size
    Inst.save("Resonator_4.txt") 