# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 23:14:52 2013

@author: pmaunz
"""
import logging
import math
import os.path
import socket

from PyQt4 import QtCore
import numpy

from Chassis import DAQmxUtility     
from Chassis.itfParser import itfParser
from gui import ProjectSelection
from modules import MyException


try:
    from Chassis.WaveformChassis import WaveformChassis
    from Chassis.DAQmxUtility import Mode
    import PyDAQmx.DAQmxFunctions

    HardwareDriverLoaded = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error( "Import of waveform hardware drivers failed '{0}' proceeding without.".format(e) )
    HardwareDriverLoaded = False


class VoltageBlender(QtCore.QObject):
    dataChanged = QtCore.pyqtSignal(int,int,int,int)
    dataError = QtCore.pyqtSignal(object)
    shuttlingOnLine = QtCore.pyqtSignal(float)
    
    def __init__(self):
        logger = logging.getLogger(__name__)
        super(VoltageBlender,self).__init__()
        if HardwareDriverLoaded:
            self.chassis = WaveformChassis()
            self.chassis.mode = Mode.Static
            self.hostname = socket.gethostname()
            ConfigFilename = os.path.join( ProjectSelection.configDir(), "VoltageControl", self.hostname+'.cfg' )
            if not os.path.exists( ConfigFilename):
                raise MyException.MissingFile( "Chassis configuration file '{0}' not found.".format(ConfigFilename))
            self.chassis.initFromFile( ConfigFilename )
            self.DoLine = self.chassis.createFalseDoBuffer()
            self.DoLine[0] = 1
            logger.debug( str(self.DoLine) )
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
    
    def loadVoltage(self,path):
        self.itf.open(path)
        self.lines = list()
        for _ in range(self.itf.getNumLines()):
            line = self.itf.eMapReadLine() 
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
        for _ in range(itf.getNumLines()):
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
        logger = logging.getLogger(__name__)
        line = self.blendLines(lineno,lineGain)
        self.lineGain = lineGain
        self.globalGain = globalGain
        self.lineno = lineno
        line = self.adjustLine( line )
        line *= self.globalGain
        try:
            if HardwareDriverLoaded:
                self.chassis.writeAoBuffer(line)
                logger.debug( "Wrote voltages {0}".format(line))
                self.chassis.writeDoBuffer(self.DoLine)
            else:
                logger.error( "Hardware Driver not loaded, cannot write voltages" )
            self.outputVoltage = line
            self.dataChanged.emit(0,1,len(self.electrodes)-1,1)
        except PyDAQmx.DAQmxFunctions.DAQError as e:
            logger.exception("Exception")
            outOfRange = line>10
            outOfRange |= line<-10
            self.dataError.emit(outOfRange.tolist())
            
    def shuttle(self, definition, cont):
        logger = logging.getLogger(__name__)
        if True:
            for edge in definition:
                for line in numpy.linspace(edge.fromLine if not edge.reverse else edge.toLine,
                                           edge.toLine if not edge.reverse else edge.fromLine, edge.steps,True):
                    self.applyLine(line,edge.lineGain,edge.globalGain)
                    logger.debug( "shuttling applied line {0}".format( line ) )
            self.shuttlingOnLine.emit(line)
        else:  # this stuff does not work yet
            logger.info( "Starting finite shuttling" )
            outputmatrix = list()
            globaladjust = [0]*len(self.lines[0])
            self.adjustLine(globaladjust)
            for edge in definition:
                for lineno in numpy.linspace(edge.fromLine if not edge.reverse else edge.toLine,
                                           edge.toLine if not edge.reverse else edge.fromLine, edge.steps,True):
                    outputmatrix.append( (self.blendLines(lineno,edge.lineGain)+globaladjust)*self.globalGain )
            try:
                if HardwareDriverLoaded:
                    self.chassis.mode = DAQmxUtility.Mode.Finite
                    self.chassis.writeAoBuffer( (numpy.array(outputmatrix)).flatten('F') )
                    self.chassis.setOnDoneCallback( self.onChassisDone )
                    self.chassis.start()
                    self.shuttleTo = lineno
                else:
                    logger.error( "Hardware Driver not loaded, cannot write voltages" )
            except PyDAQmx.DAQmxFunctions.DAQError as e:
                logger.exception("")
            
    def onChassisDone( self, generator, value ):
        logger = logging.getLogger(__name__)
        logger.info( "onChassisDone {0} {1}".format(generator, value) )
        self.chassis.mode = DAQmxUtility.Mode.Static
        self.chassis.setOnDoneCallback( None )
        self.outputVoltage = self.shuttleTo
        self.dataChanged.emit(0,1,len(self.electrodes)-1,1)
            
    def adjustLine(self, line):
        offset = numpy.array([0.0]*len(line))
        for name, value in self.adjust.iteritems():
            if name in self.adjustDict:
                offset = offset + self.adjustLines[self.adjustDict[name]] * float(value)
        if "__GAIN__" in self.adjust:
            offset *= float(self.adjust["__GAIN__"])
        return (line+offset)
            
    def blendLines(self,lineno,lineGain):
        if self.lines:
            left = int(math.floor(lineno))
            right = int(math.ceil(lineno))
            convexc = lineno-left
            return (self.lines[left]*(1-convexc) + self.lines[right]*convexc)*lineGain
        return None
            
    def close(self):
        if HardwareDriverLoaded:
            self.chassis.close()

    