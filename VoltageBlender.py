# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 23:14:52 2013

@author: pmaunz
"""
from Chassis.itfParser import itfParser

try:
    from Chassis.WaveformChassis import WaveformChassis
    from Chassis.DAQmxUtility import Mode
    import PyDAQmx.DAQmxFunctions
    HardwareDriverLoaded = True
except ImportError as e:
    print "Import of waveform hardware drivers failed '{0}' proceeding without.".format(e)
    HardwareDriverLoaded = False
    
import math
import numpy
from PyQt4 import QtCore
import socket
import ProjectSelection
import os.path
from modules import MyException

class VoltageBlender(QtCore.QObject):
    dataChanged = QtCore.pyqtSignal(int,int,int,int)
    dataError = QtCore.pyqtSignal(object)
    shuttlingOnLine = QtCore.pyqtSignal(float)
    
    def __init__(self):
        super(VoltageBlender,self).__init__()
        if HardwareDriverLoaded:
            self.chassis = WaveformChassis()
            self.chassis.mode = Mode.Static
            self.hostname = socket.gethostname()
            ConfigFilename = os.path.join( ProjectSelection.configDir(), "VoltageControl", self.hostname+'.cfg' )
            if not os.path.exists( ConfigFilename):
                raise MyException.MissingFile( "Chassis configuration file '{0}' not found.".format(ConfigFilename))
            self.chassis.initFromFile( ConfigFilename )
        self.itf = itfParser()
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
        #print "VoltageBlender emit"
        #print "electrodes", self.electrodes
        #print "aoNums", self.aoNums
        #print "dsubNums", self.dsubNums
    
    def loadVoltage(self,path):
        self.itf.open(path)
        #print "Number of lines in file", self.itf.getNumLines()
        self.lines = list()
        for i in range(self.itf.getNumLines()):
            line = self.itf.eMapReadLine() 
            #print "line",i,line
            for index, value in enumerate(line):
                if math.isnan(value): line[index]=0
            self.lines.append( line )
        self.tableHeader = self.itf.tableHeader
        self.itf.close()
        self.dataChanged.emit(0,0,len(self.electrodes)-1,3)

    def loadGlobalAdjust(self,path):
        self.adjustLines = list()
        self.adjustDict = dict()
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
        itf.close()
        self.dataChanged.emit(0,0,len(self.electrodes)-1,3)
    
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
        #print "writeAoBuffer", line
        try:
            if HardwareDriverLoaded:
                self.chassis.writeAoBuffer(line)
            else:
                print "Hardware Driver not loaded, cannot write voltages"
            self.outputVoltage = line
            self.dataChanged.emit(0,1,len(self.electrodes)-1,1)
        except PyDAQmx.DAQmxFunctions.DAQError as e:
            print e
            outOfRange = line>10
            outOfRange |= line<-10
            self.dataError.emit(outOfRange.tolist())
            
    def shuttle(self, definition):
        for edge in definition:
            for line in numpy.linspace(edge.fromLine if not edge.reverse else edge.toLine,
                                       edge.toLine if not edge.reverse else edge.fromLine, edge.steps,True):
                self.applyLine(line,edge.lineGain,edge.globalGain)
                print "shuttling applied line", line
        self.shuttlingOnLine.emit(line)
            
    def adjustLine(self, line):
        offset = numpy.array([0.0]*len(line))
        for name, value in self.adjust.iteritems():
            if name in self.adjustDict:
                offset = offset + self.adjustLines[self.adjustDict[name]] * value
        if "__GAIN__" in self.adjust:
            offset *= self.adjust["__GAIN__"]
        #print "adjustLine", self.globalGain, self.adjust
        return (line+offset)*self.globalGain
            
    def blendLines(self,left,right,convexc,lineGain):
        #print "blendlines", left, right, convexc, lineGain
        return (self.lines[left]*(1-convexc) + self.lines[right]*convexc)*lineGain
            
    def close(self):
        if HardwareDriverLoaded:
            self.chassis.close()

    