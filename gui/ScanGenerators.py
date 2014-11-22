'''
Created on Nov 6, 2014

@author: pmaunz
'''
from modules.Expression import Expression
import numpy
import logging
import random
from modules import DataDirectory
from modules import enum

ExpectedLookup = { 'd': 0, 'u' : 1, '1':0.5, '-1':0.5, 'i':0.5, '-i':0.5 }
OpStates = enum.enum('idle','running','paused','starting','stopping', 'interrupted')


class ParameterScanGenerator:
    expression = Expression()
    def __init__(self, scan):
        self.scan = scan
        self.nextIndexToWrite = 0
        self.numUpdatedVariables = 1
        
    def prepare(self, pulseProgramUi, maxUpdatesToWrite=None ):
        if self.scan.gateSequenceUi.settings.enabled:
            _, data, self.gateSequenceSettings = self.scan.gateSequenceUi.gateSequenceScanData()    
        else:
            data = []
        if self.scan.scanTarget == 'Internal':
            self.scan.code, self.numVariablesPerUpdate = pulseProgramUi.variableScanCode(self.scan.scanParameter, self.scan.list, extendedReturn=True)
            self.numUpdatedVariables = len(self.scan.code)/2/len(self.scan.list)
            maxWordsToWrite = 2040 if maxUpdatesToWrite is None else 2*self.numUpdatedVariables*maxUpdatesToWrite
            self.maxUpdatesToWrite = maxUpdatesToWrite
            if len(self.scan.code)>maxWordsToWrite:
                self.nextIndexToWrite = maxWordsToWrite
                return ( self.scan.code[:maxWordsToWrite], data)
            self.nextIndexToWrite = len(self.scan.code)
        else:
            self.stepInPlaceValue = 0
            self.scan.code = list([4095, 0]) # writing the last memory location
        return ( self.scan.code, data)
        
    def restartCode(self,currentIndex ):
        maxWordsToWrite = 2040 if self.maxUpdatesToWrite is None else 2*self.numUpdatedVariables*self.maxUpdatesToWrite
        currentWordCount = 2*self.numUpdatedVariables*currentIndex
        if len(self.scan.code)-currentWordCount>maxWordsToWrite:
            self.nextIndexToWrite = maxWordsToWrite+currentWordCount
            return ( self.scan.code[currentWordCount:self.nextIndexToWrite])
        self.nextIndexToWrite = len(self.scan.code)
        return self.scan.code[currentWordCount:]
        
    def xValue(self, index):
        value = self.scan.list[index]
        if self.scan.xExpression:
            value = self.expression.evaluate( self.scan.xExpression, {"x": value} )
        if (not self.scan.xUnit and not value.dimensionless()) or not value.has_dimension(self.scan.xUnit):
            self.scan.xUnit = value.suggestedUnit() 
        return value.ounit(self.scan.xUnit).toval()
        
    def dataNextCode(self, experiment ):
        if self.scan.scanTarget == 'Internal':
            if self.nextIndexToWrite<len(self.scan.code):
                start = self.nextIndexToWrite
                self.nextIndexToWrite = min( len(self.scan.code)+1, self.nextIndexToWrite + 2*self.numUpdatedVariables )
                return self.scan.code[start:self.nextIndexToWrite]
        else:
            return list(self.scan.code)
        return []
        
    def dataOnFinal(self, experiment, currentState):
        if self.scan.scanRepeat == 1 and currentState == OpStates.running:
            experiment.startScan()
        else:
            experiment.onStop()                   
    
    def xRange(self):
        return self.scan.start.ounit(self.scan.xUnit).toval(), self.scan.stop.ounit(self.scan.xUnit).toval()
                                     
    def appendData(self,traceList,x,evaluated):
        if evaluated and traceList:
            traceList[0].x = numpy.append(traceList[0].x, x)
        for trace, (y, error, raw) in zip(traceList, evaluated):                                  
            trace.y = numpy.append(trace.y, y)
            trace.raw = numpy.append(trace.raw, raw)
            if error is not None:
                trace.bottom = numpy.append(trace.bottom, error[0])
                trace.top = numpy.append(trace.top, error[1])
                
    def expected(self, index):
        return None
                
class StepInPlaceGenerator:
    def __init__(self, scan):
        self.scan = scan
        
    def prepare(self, pulseProgramUi, maxUpdatesToWrite=None ):
        if self.scan.gateSequenceUi.settings.enabled:
            _, data, self.gateSequenceSettings = self.scan.gateSequenceUi.gateSequenceScanData()    
        else:
            data = []
        #self.stepInPlaceValue = pulseProgramUi.getVariableValue(self.scan.scanParameter)
        self.stepInPlaceValue = 0
        self.scan.code = [4095, 0] # writing the last memory location
        #self.scan.code = pulseProgramUi.pulseProgram.variableScanCode(self.scan.scanParameter, [self.stepInPlaceValue])
        return (self.scan.code*5, data) # write 5 points to the fifo queue at start,
                        # this prevents the Step in Place from stopping in case the computer lags behind evaluating by up to 5 points

    def restartCode(self,currentIndex):
        return self.scan.code * 5
        
    def dataNextCode(self, experiment):
        return self.scan.code
        
    def xValue(self,index):
        return index

    def xRange(self):
        return []

    def appendData(self,traceList,x,evaluated):
        if evaluated and traceList:
            if len(traceList[0].x)<self.scan.steps or self.scan.steps==0:
                traceList[0].x = numpy.append(traceList[0].x, x)
                for trace, (y, error, raw) in zip(traceList, evaluated):                                  
                    trace.y = numpy.append(trace.y, y)
                    trace.raw = numpy.append(trace.raw, raw)
                    if error is not None:
                        trace.bottom = numpy.append(trace.bottom, error[0])
                        trace.top = numpy.append(trace.top, error[1])
            else:
                steps = int(self.scan.steps)
                traceList[0].x = numpy.append(traceList[0].x[-steps+1:], x)
                for trace, (y, error, raw) in zip(traceList, evaluated):                                  
                    trace.y = numpy.append(trace.y[-steps+1:], y)
                    trace.raw = numpy.append(trace.raw[-steps+1:], raw)
                    if error is not None:
                        trace.bottom = numpy.append(trace.bottom[-steps+1:], error[0])
                        trace.top = numpy.append(trace.top[-steps+1:], error[1])

    def dataOnFinal(self, experiment, currentState):
        experiment.onStop()                   

    def expected(self, index):
        return None

class GateSequenceScanGenerator:
    def __init__(self, scan):
        self.scan = scan
        self.nextIndexToWrite = 0
        self.numUpdatedVariables = 1
        self.maxWordsToWrite = 2040
        
    def prepare(self, pulseProgramUi, maxUpdatesToWrite=None):
        logger = logging.getLogger(__name__)
        self.maxUpdatesToWrite = maxUpdatesToWrite
        address, data, self.gateSequenceSettings = self.scan.gateSequenceUi.gateSequenceScanData()
        self.gateSequenceAttributes = self.scan.gateSequenceUi.gateSequenceAttributes()
        parameter = self.gateSequenceSettings.startAddressParam
        logger.debug( "GateSequenceScan {0} {1}".format( address, parameter ) )
        self.scan.list = address
        self.scan.index = range(len(self.scan.list))
        if self.scan.scantype == 1:
            self.scan.list.reverse()
            self.scan.index.reverse()
        elif self.scan.scantype == 2:
            zipped = zip(self.scan.index,self.scan.list)
            random.shuffle(zipped)
            self.scan.index, self.scan.list = zip( *zipped )
        self.scan.code = pulseProgramUi.pulseProgram.variableScanCode(parameter, self.scan.list)
        self.numVariablesPerUpdate = 1
        logger.debug( "GateSequenceScanCode {0} {1}".format(self.scan.list, self.scan.code) )
        if self.scan.gateSequenceSettings.debug:
            dumpFilename, _ = DataDirectory.DataDirectory().sequencefile("fpga_sdram.bin")
            with open( dumpFilename, 'wb') as f:
                f.write( bytearray(numpy.array(data, dtype=numpy.int32).view(dtype=numpy.int8)) )
            codeFilename, _ = DataDirectory.DataDirectory().sequencefile("start_address.txt")
            with open( codeFilename, 'w') as f:
                for a in self.scan.code[1::2]:
                    f.write( "{0}\n".format(a) )
            codeFilename, _ = DataDirectory.DataDirectory().sequencefile("start_address_sorted.txt")
            with open( codeFilename, 'w') as f:
                for index, a in enumerate(sorted(self.scan.code[1::2])):
                    f.write( "{0} {1}\n".format(index, a) )
        if len(self.scan.code)>self.maxWordsToWrite:
            self.nextIndexToWrite = self.maxWordsToWrite
            return ( self.scan.code[:self.maxWordsToWrite], data)
        self.nextIndexToWrite = len(self.scan.code)
        return ( self.scan.code, data)

    def restartCode(self,currentIndex):
        currentWordCount = 2*self.numUpdatedVariables*currentIndex
        if len(self.scan.code)-currentWordCount>self.maxWordsToWrite:
            self.nextIndexToWrite = self.maxWordsToWrite+currentWordCount
            return ( self.scan.code[currentWordCount:self.nextIndexToWrite])
        self.nextIndexToWrite = len(self.scan.code)
        return self.scan.code[currentWordCount:]

    def xValue(self,index):
        return self.scan.index[index]

    def dataNextCode(self, experiment):
        if self.nextIndexToWrite<len(self.scan.code):
            start = self.nextIndexToWrite
            self.nextIndexToWrite = min( len(self.scan.code)+1, self.nextIndexToWrite + 2*self.numUpdatedVariables )
            return self.scan.code[start:self.nextIndexToWrite]
        return []
        
    def xRange(self):
        return [0, len(self.scan.list)]

    def appendData(self,traceList,x,evaluated):
        if evaluated and traceList:
            traceList[0].x = numpy.append(traceList[0].x, x)
        for trace, (y, error, raw) in zip(traceList, evaluated):                                  
            trace.y = numpy.append(trace.y, y)
            trace.raw = numpy.append(trace.raw, raw)
            if error is not None:
                trace.bottom = numpy.append(trace.bottom, error[0])
                trace.top = numpy.append(trace.top, error[1])

    def dataOnFinal(self, experiment, currentState):
        if self.scan.scanRepeat == 1 and currentState==OpStates.running:
            experiment.startScan()
        else:
            experiment.onStop()                   

    def expected(self, index):
        if self.gateSequenceAttributes is not None:
            try:
                expected = ExpectedLookup[ self.gateSequenceAttributes[self.scan.index[index]]['expected'] ]
            except (IndexError, KeyError):
                expected = None
            return expected
        return None 
        
GeneratorList = [ParameterScanGenerator, StepInPlaceGenerator, GateSequenceScanGenerator]   
