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
from modules.SequenceDict import SequenceDict
from AdjustValue import AdjustValue
from pulser.DACController import DACControllerException   

try:
    from Chassis.WaveformChassis import WaveformChassis
    from Chassis.DAQmxUtility import Mode
    import PyDAQmx.DAQmxFunctions

    HardwareDriverLoaded = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error( "Import of waveform hardware drivers failed '{0}' proceeding without.".format(e) )
    HardwareDriverLoaded = False

class HardwareException(Exception):
    pass

class NoneHardware(object):
    name = "No DAC Hardware"
    def __init__(self):
        pass
    
    def applyLine(self, line):
        logging.getLogger(__name__).error( "Hardware Driver not loaded, cannot write voltages" )

    def shuttle(self, outputmatrix, lineno):
        logging.getLogger(__name__).error( "Hardware Driver not loaded, cannot write voltages" )

    def close(self):
        pass

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


class FPGAHardware(object):
    name = "FPGA Hardware"
    def __init__(self, dacController):
        self.dacController = dacController
        
    def applyLine(self, line):
        self.dacController.writeVoltage( 0, line )
        self.dacController.shuttle( 0, 1, 0, 0 )
        self.dacController.triggerShuttling()
        
    def shuttle(self, outputmatrix):
        logging.getLogger(__name__).error( "FPGAHardware: Shuttling not implemented" )
        self.dacController.writeVoltage( 0, (numpy.array(outputmatrix)).flatten('F') )
        self.dacController.shuttle( 0, 0, 0, 0 )  # needs startline beyondendline gapcount direction
        self.dacController.triggerShuttling()
        
    def close(self):
        pass

class VoltageBlender(QtCore.QObject):
    dataChanged = QtCore.pyqtSignal(int,int,int,int)
    dataError = QtCore.pyqtSignal(object)
    shuttlingOnLine = QtCore.pyqtSignal(float)
    
    def __init__(self, globalDict, dacController):
        logger = logging.getLogger(__name__)
        super(VoltageBlender,self).__init__()
        self.dacController = dacController
        self.hardware = FPGAHardware(self.dacController) if dacController.isOpen else ( NIHardware() if HardwareDriverLoaded else NoneHardware() )
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
        self.adjustDict = SequenceDict()
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
                    self.adjustDict[name] = AdjustValue(name=name, line=int(value), globalDict=self.globalDict)
            except ValueError:
                pass   # if it's not an int we will ignore it here
        itf.close()
        self.dataChanged.emit(0,0,len(self.electrodes)-1,3)
    
    def setAdjust(self, adjust, gain):
        self.adjustDict = adjust
        self.adjustGain = gain
        self.applyLine(self.lineno,self.lineGain,self.globalGain)
    
    def applyLine(self, lineno, lineGain, globalGain):
        line = self.blendLines(lineno,lineGain)
        self.lineGain = lineGain
        self.globalGain = globalGain
        self.lineno = lineno
        line = self.adjustLine( line )
        line *= self.globalGain
        try:
            self.hardware.applyLine(line)
            self.outputVoltage = line
            self.dataChanged.emit(0,1,len(self.electrodes)-1,1)
        except (HardwareException, DACControllerException) as e:
            logging.getLogger(__name__).exception("Exception")
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
                self.hardware.shuttle( outputmatrix )
                self.shuttleTo = lineno
            except (HardwareException, DACControllerException) as e:
                logger.exception("")
                        
    def adjustLine(self, line):
        offset = numpy.array([0.0]*len(line))
        for _, adjust in self.adjustDict.iteritems():
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
            
    def close(self):
        self.hardware.close()

    