# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 23:14:52 2013

@author: pmaunz
"""
from Chassis.itfParser import itfParser
from Chassis.WaveformChassis import WaveformChassis
from DAQmxUtility import Mode
import math
class VoltageBlender(object):
    def __init__(self):
        self.chassis = WaveformChassis()
        self.itf = itfParser()
        self.chassis.mode = Mode.Static
        self.chassis.initFromFile(r'Chassis\\config\\chassis.cfg')
        self.lines = list()
    
    def loadMapping(self,path):
        self.itf.eMapFilePath = path
    
    def loadVoltage(self,path):
        self.itf.open(path)
        for i in range(self.itf.getNumLines()):
            self.lines.append( self.itf.eMapReadLine() )

    def loadGlobalAdjust(self,path):
        pass
    
    def setAdjust(self, adjust):
        self.adjust = adjust
    
    def applyLine(self, line, lineGain, globalGain):
        floor = int(math.floor(line))
        ceil = int(math.ceil(line))
        line = self.blendLines(floor,ceil,line-floor,lineGain)
        self.adjustLine( line, globalGain )
        self.chassis.writeAoBuffer(line)
            
    def adjustLine(self, line, globalGain):
        for ident in line.keys():
            line[ident] = line[ident]*globalGain
            
    def blendLines(self,floor,ceil,convexc,lineGain):
        blended = dict()
        ceildict = self.lines[ceil]
        for ident, value in self.lines[floor].iteritems():
            blended[ident] = (value*(1-convexc) + ceildict[ident]*convexc)*lineGain
        return blended
            
    def close(self):
        self.chassis.close()

    