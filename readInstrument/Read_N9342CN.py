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
        self.t.description["Instrument"] = self.GPIB.ask("*IDN?")
        self.t.description["Center"] = float(self.GPIB.ask(":FREQuency:CENTer?"))
        self.t.description["Start"] = float(self.GPIB.ask(":FREQuency:STARt?") )
        self.t.description["Stop"] = float(self.GPIB.ask(":FREQuency:STOP?"))
        self.t.description["Attenuation"] = self.GPIB.ask(":POWer:ATTenuation?")
        self.t.description["PreAmp"] = self.GPIB.ask(":POWer:GAIN:STATe?")
        #self.t.description["IntegrationBandwidth"] = self.GPIB.ask("BANDwidth:INTegration?")
        self.t.description["ResolutionBandwidth"] = float(self.GPIB.ask(":BANDwidth:RESolution?"))
        self.t.description["VideoBandwidth"] = float(self.GPIB.ask(":BANDwidth:VIDeo?"))
        #self.t.description["ReferenceLevel"] = self.GPIB.ask(":DISPlay:WINDow:TRACe:Y:NRLevel?")
        self.t.rawTrace = numpy.array(self.GPIB.ask(":TRACe:DATA? TRACe1").split(","),dtype=float)
        self.t.Trace = self.t.rawTrace
        self.t.description["Step"] = (self.t.description["Stop"]-self.t.description["Start"])/(self.t.Trace.size-1)
        self.t.x = numpy.arange(self.t.description["Start"],self.t.description["Stop"]+0.5*self.t.description["Step"],self.t.description["Step"])
        self.t.y = self.t.Trace
        return self.t
        

if __name__== "__main__":
    Inst = N9342CN("USB0::0x0957::0xFFEF::SG05300073")
    t = Inst.readTrace()
    print t.description
    print t.Trace
    print t.Trace.size
    print t.TraceX.size
    Inst.save("Resonator_4.txt")
