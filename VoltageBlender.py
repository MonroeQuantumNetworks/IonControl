# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 23:14:52 2013

@author: pmaunz
"""
from Chassis.itfParser import itfParser
from Chassis.WaveformChassis import WaveformChassis
from Chassis.DAQmxUtility import Mode
import math
import numpy
from PyQt4 import QtCore

class VoltageBlender(QtCore.QObject):
    dataChanged = QtCore.pyqtSignal(int,int,int,int)
    
    def __init__(self):
        super(VoltageBlender,self).__init__()
        self.chassis = WaveformChassis()
        self.itf = itfParser()
        self.chassis.mode = Mode.Static
        self.chassis.initFromFile(r'Chassis\config\old_chassis.cfg')
        self.lines = list()  # a list of lines with numpy arrays
        self.adjustDict = dict()  # names of the lines presented as possible adjusts
        self.adjustLines = []
        self.lineGain = 1.0
        self.globalGain = 1.0
        self.lineno = 0
        self.mappingpath = None
        self.adjust = dict()
        self.outputVoltage = None
        self.electrodes = None
        self.aoNums = None
        self.dsubNums = None
        self.tableHeader = list()
        
    def currentData(self):
        return self.electrodes, self.aoNums, self.dsubNums, self.outputVoltage
    
    def loadMapping(self,path):
        self.itf.eMapFilePath = path
        self.mappingpath = path
        self.electrodes, self.aoNums, self.dsubNums = self.itf._getEmapData()
        self.dataChanged.emit(0,0,len(self.electrodes)-1,3)
        print "VoltageBlender emit"
        print "electrodes", self.electrodes
        print "aoNums", self.aoNums
        print "dsubNums", self.dsubNums
    
    def loadVoltage(self,path):
        self.itf.open(path)
        print "Number of lines in file", self.itf.getNumLines()
        self.lines = list()
        for i in range(self.itf.getNumLines()):
            line = self.itf.eMapReadLine() 
            print "line",i,line
            for index, value in enumerate(line):
                if math.isnan(value): line[index]=0
            self.lines.append( line )
        self.tableHeader = self.itf.tableHeader

    def loadGlobalAdjust(self,path):
        self.adjustLines = list()
        itf = itfParser()
        itf.eMapFilePath = self.mappingpath
        itf.open(path)
        for i in range(itf.getNumLines()):
            line = itf.eMapReadLine() 
            for index, value in enumerate(line):
                if math.isnan(value): line[index]=0
            self.adjustLines.append( line )
        for name, value in itf.meta.iteritems():
            try:
                if int(value)<len(self.adjustLines):
                    self.adjustDict[name] = int(value)
            except ValueError:
                pass   # if it's not an int we will ignore it here
    
    def setAdjust(self, adjust):
        self.adjust = adjust
        self.applyLine(self.lineno,self.lineGain,self.globalGain)
    
    def applyLine(self, lineno, lineGain, globalGain):
        floor = int(math.floor(lineno))
        ceil = int(math.ceil(lineno))
        line = self.blendLines(floor,ceil,lineno-floor,lineGain)
        self.lineGain = lineGain
        self.globalGain = globalGain
        self.lineno = lineno
        line = self.adjustLine( line )
        print "writeAoBuffer", line
        self.chassis.writeAoBuffer(line)
        self.outputVoltage = line
        self.dataChanged.emit(0,1,len(self.electrodes)-1,1)
        print "VoltageBlender emit"
            
    def adjustLine(self, line):
        offset = numpy.array([0.0]*len(line))
        for name, value in self.adjust.iteritems():
            if name in self.adjustDict:
                offset = offset + self.adjustLines[self.adjustDict[name]] * value
        if "__GAIN__" in self.adjust:
            offset *= self.adjust["__GAIN__"]
        print "adjustLine", self.globalGain, self.adjust
        return (line+offset)*self.globalGain
            
    def blendLines(self,left,right,convexc,lineGain):
        print "blendlines", left, right, convexc, lineGain
        return (self.lines[left]*(1-convexc) + self.lines[right]*convexc)*lineGain
            
    def close(self):
        self.chassis.close()

    