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
from modules import MyException, MagnitudeUtilit
from modules.SequenceDict import SequenceDict
from AdjustValue import AdjustValue
from pulser.DACController import DACControllerException   
from numpy import linspace
from modules.doProfile import doprofile

try:
    from Chassis.WaveformChassis import WaveformChassis
    from Chassis.DAQmxUtility import Mode
    import PyDAQmx.DAQmxFunctions

    HardwareDriverLoaded = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning( "Import of waveform hardware drivers failed '{0}' proceeding without.".format(e) )
    HardwareDriverLoaded = False

class HardwareException(Exception):
    pass

class NoneHardware(object):
    name = "No DAC Hardware"
    nativeShuttling = False
    def __init__(self):
        pass
    
    def applyLine(self, line):
        logging.getLogger(__name__).warning( "Hardware Driver not loaded, cannot write voltages" )

    def shuttle(self, outputmatrix, lineno):
        logging.getLogger(__name__).warning( "Hardware Driver not loaded, cannot write voltages" )

    def close(self):
        pass
    
    @property
    def channelCount(self):
        return 0


class NIHardware(object):
    name = "NI DAC"
    def __init__(self):
        try:
            self.chassis = WaveformChassis()
            self.chassis.mode = Mode.Static
            self.hostname = socket.gethostname()
            ConfigFilename = os.path.join( ProjectSelection.configDir(), "VoltageControl", self.hostname+'.cfg' )
            if not os.path.exists( ConfigFilename):
                raise MyException.MissingFile( "Chassis configuration file '{0}' not found.".format(ConfigFilename))
            self.chassis.initFromFile( ConfigFilename )
            self.DoLine = self.chassis.createFalseDoBuffer()
            self.DoLine[0] = 1
            logging.getLogger(__name__).debug( str(self.DoLine) )
        except PyDAQmx.DAQmxFunctions.DAQError as e:
            raise HardwareException(str(e))

    def applyLine(self, line):
        try:
            self.chassis.writeAoBuffer(line)
            logging.getLogger(__name__).debug( "Wrote voltages {0}".format(line))
            self.chassis.writeDoBuffer(self.DoLine)
        except PyDAQmx.DAQmxFunctions.DAQError as e:
            raise HardwareException(str(e))

    def shuttle(self, outputmatrix):
        try:
            self.chassis.mode = DAQmxUtility.Mode.Finite
            self.chassis.writeAoBuffer( (numpy.array(outputmatrix)).flatten('F') )
            self.chassis.setOnDoneCallback( self.onChassisDone )
            self.chassis.start()
        except PyDAQmx.DAQmxFunctions.DAQError as e:
            raise HardwareException(str(e))
        
    def close(self):
        self.chassis.close()

    def onChassisDone( self, generator, value ):
        logger = logging.getLogger(__name__)
        logger.info( "onChassisDone {0} {1}".format(generator, value) )
        self.chassis.mode = DAQmxUtility.Mode.Static
        self.chassis.setOnDoneCallback( None )
#         self.outputVoltage = self.shuttleTo
#         self.dataChanged.emit(0,1,len(self.electrodes)-1,1)

    @property
    def channelCount(self):
        return self.chassis.getNumAoChannels()


class FPGAHardware(object):
    name = "FPGA Hardware"
    nativeShuttling = True
    def __init__(self, dacController):
        self.dacController = dacController
        
    def applyLine(self, line):
        self.dacController.writeVoltage( 0, line )
        self.dacController.readVoltage(0, line)
        self.dacController.shuttleDirect( 0, 1, idleCount=0, immediateTrigger=True )
        self.dacController.triggerShuttling()
        
    def shuttle(self, lookupIndex, reverseEdge=False, immediateTrigger=False ):
        self.dacController.shuttle( lookupIndex, reverseEdge, immediateTrigger  )  
        
    def shuttlePath(self, path):
        self.dacController.shuttlePath(path)
        
    def close(self):
        pass
    
    def writeData(self, address, lineList):
        self.dacController.writeVoltages(address,lineList)
        
    def writeShuttleLookup(self, shuttleEdges, startAddress=0 ):
        self.dacController.writeShuttleLookup(shuttleEdges, startAddress)
        
    def triggerShuttling(self):
        self.dacController.triggerShuttling()
        
    @property
    def channelCount(self):
        return self.dacController.channelCount
 

class VoltageBlender(QtCore.QObject):
    dataChanged = QtCore.pyqtSignal(int,int,int,int)
    dataError = QtCore.pyqtSignal(object)
    shuttlingOnLine = QtCore.pyqtSignal(float)
    
    def __init__(self, globalDict, dacController):
        logger = logging.getLogger(__name__)
        super(VoltageBlender,self).__init__()
        self.dacController = dacController
        try:
            self.hardware = FPGAHardware(self.dacController) if dacController.isOpen else ( NIHardware() if HardwareDriverLoaded else NoneHardware() )
        except HardwareException as e:
            self.hardware = NoneHardware()
            logger.error(str(e))
            logger.error("Loading Voltage driver failed. Running without available voltage output.")
        self.itf = itfParser()
        self.lines = list()  # a list of lines with numpy arrays
        self.adjustDict = SequenceDict()  # names of the lines presented as possible adjusts
        self.adjustLines = []
        self.lineGain = 1.0
        self.globalGain = 1.0
        self.lineno = 0
        self.mappingpath = None
        self.outputVoltage = None
        self.electrodes = None
        self.aoNums = None
        self.dsubNums = None
        self.tableHeader = list()
        self.globalDict = globalDict
        self.adjustGain = 1.0
        self.localAdjustVoltages = list()
        self.uploadedDataHash = None
        
    def currentData(self):
        return self.electrodes, self.aoNums, self.dsubNums, self.outputVoltage
    
    def loadMapping(self,path):
        self.itf.eMapFilePath = path
        self.mappingpath = path
        self.electrodes, self.aoNums, self.dsubNums = self.itf._getEmapData()
        self.dataChanged.emit(0,0,len(self.electrodes)-1,3)
    
    def loadVoltage(self,path):
        channelCount = self.hardware.channelCount if self.hardware else 0
        self.itf.open(path)
        self.lines = list()
        for _ in range(self.itf.getNumLines()):
            line = self.itf.eMapReadLine() 
            for index, value in enumerate(line):
                if math.isnan(value): line[index]=0
            line = numpy.append( line, [0.0]*max(0,channelCount-len(line)))
            self.lines.append( line )
        self.tableHeader = self.itf.tableHeader
        self.itf.close()
        self.dataChanged.emit(0,0,len(self.electrodes)-1,3)

    def loadGlobalAdjust(self,path):
        channelCount = self.hardware.channelCount if self.hardware else 0
        self.adjustLines = list()
        self.adjustDict = SequenceDict()
        itf = itfParser()
        itf.eMapFilePath = self.mappingpath
        itf.open(path)
        for _ in range(itf.getNumLines()):
            line = itf.eMapReadLine() 
            for index, value in enumerate(line):
                if math.isnan(value): line[index]=0
            line = numpy.append( line, [0.0]*max(0,channelCount-len(line)))
            self.adjustLines.append( line )
        for name, value in itf.meta.iteritems():
            try:
                if int(value)<len(self.adjustLines):
                    self.adjustDict[name] = AdjustValue(name=name, line=int(value), globalDict=self.globalDict)
            except ValueError:
                pass   # if it's not an int we will ignore it here
        itf.close()
        self.dataChanged.emit(0,0,len(self.electrodes)-1,3)
        
    def loadLocalAdjust(self, localAdjustList, forceupdate=list() ):
        channelCount = self.hardware.channelCount if self.hardware else 0        
        for index, record in enumerate(localAdjustList):
            path = record.path
            if index in forceupdate or record.solutionPath != record.path:
                if os.path.exists(path):
                    linelist = list()
                    itf = itfParser()
                    itf.eMapFilePath = self.mappingpath
                    itf.open(path)
                    for _ in range(itf.getNumLines()):
                        line = itf.eMapReadLine() 
                        for index, value in enumerate(line):
                            if math.isnan(value): line[index]=0
                        line = numpy.append( line, [0.0]*max(0,channelCount-len(line)))
                        linelist.append( line )
                    itf.close()
                    record.solution = linelist
                    record.solutionPath = path
                else:
                    logging.getLogger(__name__).warning("Local Adjust file '{0}' not found".format(path))
        self.dataChanged.emit(0,0,len(self.electrodes)-1,3)
        self.localAdjustVoltages = localAdjustList
    
    def setAdjust(self, adjust, gain):
        self.adjustDict = adjust
        self.adjustGain = MagnitudeUtilit.value( gain )
        self.applyLine(self.lineno,self.lineGain,self.globalGain)
        
    def setLocalAdjust(self, localAdjustDict ):
        self.localAdjustVoltages = localAdjustDict
        self.applyLine(self.lineno,self.lineGain,self.globalGain)
    
    def applyLine(self, lineno, lineGain, globalGain):
        line = self.calculateLine( MagnitudeUtilit.value(lineno), MagnitudeUtilit.value(lineGain), MagnitudeUtilit.value(globalGain) )
        try:
            self.hardware.applyLine(line)
            self.outputVoltage = line
            self.lineno = lineno
            self.dataChanged.emit(0,1,len(self.electrodes)-1,1)
        except (HardwareException, DACControllerException) as e:
            logging.getLogger(__name__).exception("Exception")
            outOfRange = line>10
            outOfRange |= line<-10
            self.dataError.emit(outOfRange.tolist())
            
    def calculateLine(self, lineno, lineGain, globalGain):
        line = self.blendLines(lineno,lineGain)
        localadjustline = self.blendLocalAdjustLines(lineno)
        self.lineGain = lineGain
        self.globalGain = globalGain
        #self.lineno = lineno
        line = self.adjustLine( line )
        line = numpy.add( line, localadjustline )
        line *= self.globalGain
        return line
            
    def shuttle(self, definition, cont):
        logger = logging.getLogger(__name__)
        if not self.hardware.nativeShuttling:
            for start, _, edge, _ in definition:
                fromLine, toLine = (edge.startLine, edge.stopLine) if start==edge.startName else (edge.stopLine, edge.startLine)
                for line in numpy.linspace(fromLine, toLine, edge.steps+2, True):
                    self.applyLine(line,self.lineGain,self.globalGain)
                    logger.debug( "shuttling applied line {0}".format( line ) )
            self.shuttlingOnLine.emit(line)
        else:  # this stuff does not work yet
            if definition:
                logger.info( "Starting finite shuttling" )
                globaladjust = [0]*len(self.lines[0])
                self.adjustLine(globaladjust)
                self.hardware.shuttlePath( [(index, start!=edge.startName, True) for start, _, edge, index in definition] )
                start, _, edge, _ = definition[-1]
                self.shuttleTo = edge.startLine if start!=edge.startName else edge.stopLine
                self.shuttlingOnLine.emit(self.shuttleTo)
                        
    def adjustLine(self, line):
        offset = numpy.zeros(len(line))
        for adjust in self.adjustDict.itervalues():
            offset = offset + self.adjustLines[adjust.line] * float(adjust.value)
        offset *= self.adjustGain
        return (line+offset)
            
    def blendLines(self,lineno,lineGain):
        if self.lines:
            left = int(math.floor(lineno))
            right = int(math.ceil(lineno))
            convexc = lineno-left
            return (self.lines[left]*(1-convexc) + self.lines[right]*convexc)*lineGain
        return None
    
    def blendLocalAdjustLines(self, lineno):
        channelCount = self.hardware.channelCount if self.hardware else 0
        left = int(math.floor(lineno))
        right = int(math.ceil(lineno))
        convexc = lineno-left
        result = numpy.zeros(channelCount)
        for record in self.localAdjustVoltages:
            if record.solution:
                result = numpy.add(result, (record.solution[left]*(1-convexc) + record.solution[right]*convexc)*record.gain.value)
        return result
            
    def close(self):
        self.hardware.close()

    def writeShuttleLookup(self, edgeList, address=0):
        self.dacController.writeShuttleLookup(edgeList,address)
    
    @doprofile
    def writeData(self, shuttlingGraph):
        towrite = list()
        startline = 1
        currentline = startline
        lineGain = MagnitudeUtilit.value(self.lineGain)
        globalGain = MagnitudeUtilit.value(self.globalGain)
        for edge in shuttlingGraph:         
            towrite.extend( [self.calculateLine(lineno, lineGain, globalGain ) for lineno in edge.iLines() ] )
            edge.interpolStartLine = currentline
            currentline = startline+len(towrite)
            edge.interpolStopLine = currentline 
        data = self.dacController.writeVoltages(1, towrite )
        self.dacController.verifyVoltages(1, data )
        self.uploadedDataHash = self.shuttlingDataHash()
        
    def shuttlingDataHash(self):
        h =  hash( (self.lineGain, self.globalGain, self.adjustGain, tuple(self.adjustDict.values()), tuple(self.localAdjustVoltages) ))
        logging.getLogger(__name__).info("Shuttling Hash: {0:x}".format(h))
        return h
    
    def shuttlingDataValid(self):
        return self.shuttlingDataHash()==self.uploadedDataHash
        
    def trigger(self):
        self.dacController.triggerShuttling()
