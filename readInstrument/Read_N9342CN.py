# -*- coding: utf-8 -*-
"""
Created on Fri Dec 14 15:37:21 2012

@author: plmaunz
"""

from trace import Trace

import numpy
import visa #@UnresolvedImport

import ReadGeneric 


class N9342CN(ReadGeneric.ReadGeneric):
    def __init__(self,address):
        self.GPIB = visa.instrument(address)
        
    def readTrace(self):
        self.t = Trace.Trace()
        self.t.vars.Instrument = self.GPIB.ask("*IDN?")
        self.t.vars.Center = float(self.GPIB.ask(":FREQuency:CENTer?"))
        self.t.vars.Start = float(self.GPIB.ask(":FREQuency:STARt?") )
        self.t.vars.Stop = float(self.GPIB.ask(":FREQuency:STOP?"))
        self.t.vars.Attenuation = self.GPIB.ask(":POWer:ATTenuation?")
        self.t.vars.PreAmp = self.GPIB.ask(":POWer:GAIN:STATe?")
        #self.t.vars.IntegrationBandwidth = self.GPIB.ask("BANDwidth:INTegration?")
        self.t.vars.ResolutionBandwidth = float(self.GPIB.ask(":BANDwidth:RESolution?"))
        self.t.vars.VideoBandwidth = float(self.GPIB.ask(":BANDwidth:VIDeo?"))
        #self.t.vars.ReferenceLevel = self.GPIB.ask(":DISPlay:WINDow:TRACe:Y:NRLevel?")
        self.t.rawTrace = numpy.array(self.GPIB.ask(":TRACe:DATA? TRACe1").split(","),dtype=float)
        self.t.Trace = self.t.rawTrace
        self.t.vars.Step = (self.t.vars.Stop-self.t.vars.Start)/(self.t.Trace.size-1)
        self.t.x = numpy.arange(self.t.vars.Start,self.t.vars.Stop+0.5*self.t.vars.Step,self.t.vars.Step)
        self.t.y = self.t.Trace
        return self.t
        

if __name__== "__main__":
    Inst = N9342CN("USB0::0x0957::0xFFEF::SG05300073")
    t = Inst.readTrace()
    print t.vars.__dict__
    print t.Trace
    print t.Trace.size
    print t.TraceX.size
    Inst.save("Resonator_4.txt")
