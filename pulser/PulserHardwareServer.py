# -*- coding: utf-8 -*-
"""
Encapsulation of the Pulse Programmer Hardware 
"""
import logging
import math
from multiprocessing import Process
import struct
import numpy

import ok

from mylogging.ServerLogging import configureServerLogging
from modules import enum
import modules.magnitude as magnitude
from bitfileHeader import BitfileInfo

ModelStrings = {
        0: 'Unknown',
        1: 'XEM3001v1',
        2: 'XEM3001v2',
        3: 'XEM3010',
        4: 'XEM3005',
        5: 'XEM3001CL',
        6: 'XEM3020',
        7: 'XEM3050',
        8: 'XEM9002',
        9: 'XEM3001RB',
        10: 'XEM5010',
        11: 'XEM6110LX45',
        15: 'XEM6110LX150',
        12: 'XEM6001',
        13: 'XEM6010LX45',
        14: 'XEM6010LX150',
        16: 'XEM6006LX9',
        17: 'XEM6006LX16',
        18: 'XEM6006LX25',
        19: 'XEM5010LX110',
        20: 'ZEM4310',
        21: 'XEM6310LX45',
        22: 'XEM6310LX150',
        23: 'XEM6110v2LX45',
        24: 'XEM6110v2LX150'
}

ErrorMessages = {
     0: 'NoError',
    -1: 'Failed',
    -2: 'Timeout',
    -3: 'DoneNotHigh',
    -4: 'TransferError',
    -5: 'CommunicationError',
    -6: 'InvalidBitstream',
    -7: 'FileError',
    -8: 'DeviceNotOpen',
    -9: 'InvalidEndpoint',
    -10: 'InvalidBlockSize',
    -11: 'I2CRestrictedAddress',
    -12: 'I2CBitError',
    -13: 'I2CNack',
    -14: 'I2CUnknownStatus',
    -15: 'UnsupportedFeature',
    -16: 'FIFOUnderflow',
    -17: 'FIFOOverflow',
    -18: 'DataAlignmentError',
    -19: 'InvalidResetProfile',
    -20: 'InvalidParameter'
}


class DeviceDescription:
    pass

class FPGAException(Exception):
    pass
        
def check(number, command):
    if number is not None and number<0:
        raise FPGAException("OpalKelly exception '{0}' in command {1}".format(ErrorMessages.get(number,number),command))


class PulserHardwareException(Exception):
    pass

class Data:
    def __init__(self):
        self.count = [list() for _ in range(16)]
        self.timestamp = [list() for _ in range(8)]
        self.timestampZero = [0]*8
        self.scanvalue = None
        self.final = False
        self.other = list()
        self.overrun = False
        self.exitcode = 0
        self.dependentValues = list()
        self.evaluated = dict()
        
    def __str__(self):
        return str(len(self.count))+" "+" ".join( [str(self.count[i]) for i in range(16) ])

class DedicatedData:
    def __init__(self):
        self.data = [None]*13
        
    def count(self):
        return self.data[0:8]
        
    def analog(self):
        return self.data[8:12]
        
    def integration(self):
        return self.data[12]

class LogicAnalyzerData:
    def __init__(self):
        self.data = list()
        self.auxData = list()
        self.trigger = list()
        self.gateData = list()
        self.stopMarker = None
        self.countOffset = 0
        self.overrun = False
        self.wordcount = 0
        
    def dataToStr(self, l):
        strlist = list()
        for time, pattern in l:
            strlist.append("({0}, {1:x})".format(time, pattern))
        return "["+", ".join(strlist)+"]"
                  
    def __str__(self):
        return "data: {0} auxdata: {1} trigger: {2} gate: {3} stopMarker: {4} countOffset: {5}".format(self.dataToStr(self.data), self.dataToStr(self.auxData), self.dataToStr(self.trigger), 
                                                                                                       self.dataToStr(self.gateData), self.stopMarker, self.countOffset)

class FinishException(Exception):
    pass

class PulserHardwareServer(Process):
    timestep = magnitude.mg(20,'ns')
    dedicatedDataClass = DedicatedData
    def __init__(self, dataQueue=None, commandPipe=None, loggingQueue=None, sharedMemoryArray=None):
        super(PulserHardwareServer,self).__init__()
        self.dataQueue = dataQueue
        self.commandPipe = commandPipe
        self.running = True
        self.openModule = None
        self.xem = None
        self.loggingQueue = loggingQueue
        self.sharedMemoryArray = sharedMemoryArray
        
        # PipeReader stuff
        self.state = self.analyzingState.normal
        self.data = Data()
        self.dedicatedData = self.dedicatedDataClass()
        self.timestampOffset = 0

        self._shutter = 0
        self._trigger = 0
        self._adcCounterMask = 0
        self._integrationTime = magnitude.mg(100,'ms')
        
        self.logicAnalyzerEnabled = False
        self.logicAnalyzerStopAtEnd = False
        self.logicAnalyzerData = LogicAnalyzerData()
        
        self.logicAnalyzerBuffer = bytearray()
        
    def run(self):
        configureServerLogging(self.loggingQueue)
        logger = logging.getLogger(__name__)
        while (self.running):
            if self.commandPipe.poll(0.01):
                try:
                    commandstring, argument = self.commandPipe.recv()
                    command = getattr(self, commandstring)
                    logger.debug( "PulserHardwareServer {0}".format(commandstring) )
                    self.commandPipe.send(command(*argument))
                except Exception as e:
                    self.commandPipe.send(e)
            self.readDataFifo()
        self.dataQueue.put(FinishException())
        logger.info( "Pulser Hardware Server Process finished." )
        self.dataQueue.close()
        self.loggingQueue.put(None)
        self.loggingQueue.close()
#         self.loggingQueue.join_thread()
            
    def finish(self):
        self.running = False
        return True

    analyzingState = enum.enum('normal','scanparameter', 'dependentscanparameter')
    def readDataFifo(self):
        """ run is responsible for reading the data back from the FPGA
            0xffffffffffffffff end of experiment marker
            0xfffexxxxxxxxxxxx exitcode marker
            0xfffd000000000000 timestamping overflow marker
            0xfffcxxxxxxxxxxxx scan parameter, followed by scanparameter value
            0x01nnxxxxxxxxxxxx count result from channel n
            0x02nnxxxxxxxxxxxx timestamp result channel n
            0x03nnxxxxxxxxxxxx timestamp gate start channel n
            0x04nnxxxxxxxxxxxx other return
            0xeennxxxxxxxxxxxx dedicated result
        """
        logger = logging.getLogger(__name__)
        if (self.logicAnalyzerEnabled):
            logicAnalyzerData, _ = self.ppReadLogicAnalyzerData(8)
            if self.logicAnalyzerOverrun:
                logger.error("Logic Analyzer Pipe overrun")
                self.logicAnalyzerClearOverrun()
                self.logicAnalyzerData.overrun = True
            if logicAnalyzerData:
                self.logicAnalyzerBuffer.extend(logicAnalyzerData)
            for s in sliceview(self.logicAnalyzerBuffer,8):
                (code, ) = struct.unpack('Q',s)
                self.logicAnalyzerData.wordcount += 1
                time = (code & 0xffffff) + self.logicAnalyzerData.countOffset
                pattern = (code >> 24) & 0xffffffff
                header = (code >> 56 )
                if header==2:  # overrun marker
                    self.logicAnalyzerData.countOffset += 0x1000000   # overrun of 24 bit counter
                elif header==1:  # end marker
                    self.logicAnalyzerData.stopMarker = time
                    self.dataQueue.put( self.logicAnalyzerData )
                    self.logicAnalyzerData = LogicAnalyzerData()
                elif header==4: # trigger
                    self.logicAnalyzerData.trigger.append( (time,pattern) )
                elif header==3: # standard
                    self.logicAnalyzerData.data.append( (time,pattern) )  
                elif header==5: # aux data
                    self.logicAnalyzerData.auxData.append( (time,pattern))
                elif header==6:
                    self.logicAnalyzerData.gateData.append( (time,pattern) )                                          
                logger.debug("Time {0:x} header {1} pattern {2:x} {3:x} {4:x}".format(time, header, pattern, code, self.logicAnalyzerData.countOffset))
            self.logicAnalyzerBuffer = bytearray( sliceview_remainder(self.logicAnalyzerBuffer, 8) )           

                   
        data, self.data.overrun = self.ppReadData(8)
        if data:
            for s in sliceview(data,8):
                (token,) = struct.unpack('Q',s)
 #               print hex(token)
                if self.state == self.analyzingState.dependentscanparameter:
                    self.data.dependentValues.append(token)
                    logger.debug( "Dependent value {0} received".format(token) )
                    self.state = self.analyzingState.normal
                elif self.state == self.analyzingState.scanparameter:
                    logger.debug( "Scan value {0} received".format(token) )
                    if self.data.scanvalue is None:
                        self.data.scanvalue = token
                    else:
                        self.dataQueue.put( self.data )
                        self.data = Data()
                        self.data.scanvalue = token
                    self.state = self.analyzingState.normal
                elif token & 0xff00000000000000 == 0xee00000000000000: # dedicated results
                    channel = (token >>48) & 0xff
                    if self.dedicatedData.data[channel] is not None:
                        self.dataQueue.put( self.dedicatedData )
                        self.dedicatedData = self.dedicatedDataClass()
                    self.dedicatedData.data[channel] = token & 0xffffffffffff
                elif token & 0xff00000000000000 == 0xff00000000000000:
                    if token == 0xffffffffffffffff:    # end of run
                        self.data.final = True
                        self.data.exitcode = 0x0000
                        self.dataQueue.put( self.data )
                        logger.info( "End of Run marker received" )
                        self.data = Data()
                    elif token & 0xffff000000000000 == 0xfffe000000000000:  # exitparameter
                        self.data.final = True
                        self.data.exitcode = token & 0x0000ffffffffffff
                        logger.info( "Exitcode {0} received".format(self.data.exitcode) )
                        self.dataQueue.put( self.data )
                        self.data = Data()
                    elif token == 0xfffd000000000000:
                        self.timestampOffset += 1<<28
                    elif token & 0xffff000000000000 == 0xfffc000000000000:  # new scan parameter
                        self.state = self.analyzingState.dependentscanparameter if (token & 0x8000 == 0x8000) else self.analyzingState.scanparameter 
                else:
                    key = token >> 56 
                    channel = (token >>48) & 0xff 
                    value = token & 0x0000ffffffffffff
                    #print hex(token)
                    if key==1:   # count
                        (self.data.count[channel]).append(value)
                    elif key==2:  # timestamp
                        self.data.timestamp[channel].append(self.timestampOffset + value - self.data.timestampZero[channel])
                    elif key==3:  # timestamp gate start
                        self.data.timestampZero[channel] = self.timestampOffset + value
                    elif key==4: # other return value
                        self.data.other.append(value)
                    else:
                        self.data.other.append(token)
            if self.data.overrun:
                logger.info( "Overrun detected, triggered data queue" )
                self.dataQueue.put( self.data )
                self.data = Data()
                self.clearOverrun()
                
            
     
    def __getattr__(self, name):
        """delegate not available procedures to xem"""
        if name.startswith('__') and name.endswith('__'):
            return super(PulserHardwareServer, self).__getattr__(name)
        def wrapper(*args):
            if self.xem:
                return getattr( self.xem, name )(*args)
            return None
        setattr(self, name, wrapper)
        return wrapper      
     
    def SetWireInValue(self, address, data):
        if self.xem:
            self.xem.SetWireInValue(address, data)

    def getShutter(self):
        return self._shutter  #
         
    def setShutter(self, value):
        if self.xem:
            check( self.xem.SetWireInValue(0x06, value, 0xFFFF) , 'SetWireInValue' )	
            check( self.xem.SetWireInValue(0x07, value>>16, 0xFFFF)	, 'SetWireInValue' )
            check( self.xem.UpdateWireIns(), 'UpdateWireIns' )
            self._shutter = value
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
        return self._shutter
            
    def setShutterBit(self, bit, value):
        mask = 1 << bit
        newval = (self._shutter & (~mask)) | (mask if value else 0)
        return self.setShutter( newval )
        
    def getTrigger(self):
        return self._trigger
            
    def setTrigger(self,value):
        if self.xem:
            check( self.xem.SetWireInValue(0x08, value, 0xFFFF) , 'SetWireInValue' )	
            check( self.xem.SetWireInValue(0x09, value>>16, 0xFFFF)	, 'SetWireInValue' )
            check( self.xem.UpdateWireIns(), 'UpdateWireIns' )
            check( self.xem.ActivateTriggerIn( 0x41, 2), 'ActivateTrigger' )
            self._trigger = value
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
        return self._trigger
            
    def getCounterMask(self):
        return self._adcCounterMask & 0xff
        
    def setCounterMask(self, value):
        if self.xem:
            self._adcCounterMask = (self._adcCounterMask & 0xf00) | (value & 0xff)
            check( self.xem.SetWireInValue(0x0a, self._adcCounterMask, 0xFFFF) , 'SetWireInValue' )	
            check( self.xem.UpdateWireIns(), 'UpdateWireIns' )            
            logging.getLogger(__name__).info( "set counterMask {0}".format( hex(self._adcCounterMask) ) )
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
        return self._adcCounterMask & 0xff

    def getAdcMask(self):
        return (self._adcCounterMask >> 8) & 0xff
        
    def setAdcMask(self, value):
        if self.xem:
            self._adcCounterMask = ((value<<8) & 0xf00) | (self._adcCounterMask & 0xff)
            check( self.xem.SetWireInValue(0x0a, self._adcCounterMask, 0xFFFF) , 'SetWireInValue' )	
            check( self.xem.UpdateWireIns(), 'UpdateWireIns' )  
            logging.getLogger(__name__).info( "set adc mask {0}".format(hex(self._adcCounterMask)) )
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
        return (self._adcCounterMask >> 8) & 0xff
        
    def getIntegrationTime(self):
        return self._integrationTime
        
    def setIntegrationTime(self, value):
        self.integrationTimeBinary = int( (value/self.timestep).toval() )
        if self.xem:
            logging.getLogger(__name__).info(  "set dedicated integration time {0} {1}".format( value, self.integrationTimeBinary ) )
            check( self.xem.SetWireInValue(0x0b, self.integrationTimeBinary >> 16, 0xFFFF) , 'SetWireInValue' )	
            check( self.xem.SetWireInValue(0x0c, self.integrationTimeBinary, 0xFFFF) , 'SetWireInValue' )	
            check( self.xem.UpdateWireIns(), 'UpdateWireIns' )            
            self._integrationTime = value
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
        return self.integrationTimeBinary
            
    def getIntegrationTimeBinary(self, value):
        return int( (value/self.timestep).toval() ) & 0xffffffff
    
    def ppUpload(self, (code,data), codestartaddress=0, datastartaddress=0 ):
        self.ppUploadCode(code, codestartaddress)
        self.ppUploadData(data, datastartaddress)
        
    def ppUploadCode(self,binarycode,startaddress=0):
        if self.xem:
            logger = logging.getLogger(__name__)
            logger.info(  "starting PP upload" )
            check( self.xem.SetWireInValue(0x00, startaddress, 0x0FFF), "ppUpload write start address" )	# start addr at zero
            self.xem.UpdateWireIns()
            check( self.xem.ActivateTriggerIn(0x41, 1), "ppUpload trigger" )
            logger.info(  "{0} bytes".format(len(binarycode)) )
            num = self.xem.WriteToPipeIn(0x80, bytearray(binarycode) )
            check(num, 'Write to program pipe' )
            logger.info(   "uploaded pp file {0} bytes".format(num) )
            num, data = self.ppDownloadCode(0,num)
            logger.info(   "Verified {0} bytes. {1}".format(num,data==binarycode) )
            return True
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
            return False
            
    def ppDownloadCode(self,startaddress,length):
        if self.xem:
            self.xem.SetWireInValue(0x00, startaddress, 0x0FFF)	# start addr at 3900
            self.xem.UpdateWireIns()
            self.xem.ActivateTriggerIn(0x41, 0)
            self.xem.ActivateTriggerIn(0x41, 1)
            data = bytearray('\000'*length)
            num = self.xem.ReadFromPipeOut(0xA0, data)
            return num, data
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
            return 0,None
        
    def ppUploadData(self, binarydata,startaddress=0):
        if self.xem:
            logger = logging.getLogger(__name__)
            logger.info(  "starting PP upload" )
            check( self.xem.SetWireInValue(0x00, startaddress, 0x0FFF), "ppUpload write start address" )    # start addr at zero
            self.xem.UpdateWireIns()
            check( self.xem.ActivateTriggerIn(0x41, 10), "ppUpload trigger" )
            logger.info(  "{0} bytes".format(len(binarydata)) )
            num = self.xem.WriteToPipeIn(0x83, bytearray(binarydata) )
            check(num, 'Write to program pipe' )
            logger.info(   "uploaded pp file {0} bytes".format(num) )
            num, data = self.ppDownloadData(0,num)
            logger.info(   "Verified {0} bytes. {1}".format(num,data==binarydata) )
            return True
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
            return False
        
    def ppDownloadData(self,startaddress,length):
        if self.xem:
            self.xem.SetWireInValue(0x00, startaddress, 0x0FFF)    # start addr at 3900
            self.xem.UpdateWireIns()
            self.xem.ActivateTriggerIn(0x41, 0)
            self.xem.ActivateTriggerIn(0x41, 10)
            data = bytearray('\000'*length)
            num = self.xem.ReadFromPipeOut(0xA4, data)
            return num, data
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
            return 0,None
        
    def ppIsRunning(self):
        if self.xem:
            data = '\x00'*32
            self.xem.ReadFromPipeOut(0xA1, data)
            if ((data[:2] != '\xED\xFE') or (data[-2:] != '\xED\x0F')):
                logging.getLogger(__name__).warning( "Bad data string: {0}".format( map(ord, data) ) )
                return True
            data = map(ord, data[2:-2])
            #Decode
            active =  bool(data[1] & 0x80)
            return active
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
            return False
            

    def ppReset(self):#, widget = None, data = None):
        if self.xem:
            self.xem.ActivateTriggerIn(0x40,0)
            self.xem.ActivateTriggerIn(0x41,0)
            logging.getLogger(__name__).warning( "pp_reset is not working right now... CWC 08302012" )
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")

    def ppStart(self):#, widget = None, data = None):
        if self.xem:
            self.xem.ActivateTriggerIn(0x40, 3)  # pp_stop_trig
            self.xem.ActivateTriggerIn(0x41, 9)  # reset overrun
            self.readDataFifo()
            self.readDataFifo()   # after the first time the could still be data in the FIFO not reported by the fifo count
            self.data = Data()    # flush data that might have been accumulated
            logging.getLogger(__name__).debug("Sending start trigger")
            self.xem.ActivateTriggerIn(0x40, 2)  # pp_start_trig
            return True
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
            return False

    def ppStop(self):#, widget, data= None):
        if self.xem:
            self.xem.ActivateTriggerIn(0x40, 3)  # pp_stop_trig
            return True
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
            return False

    def interruptRead(self):
        self.sleepQueue.put(False)

    def ppWriteData(self,data):
        if self.xem:
            if isinstance(data,bytearray):
                return self.xem.WriteToPipeIn(0x81,data)
            else:
                code = bytearray()
                for item in data:
                    code.extend(struct.pack('L',item))
                #print "ppWriteData length",len(code)
                return self.xem.WriteToPipeIn(0x81,code)
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
            return None
                
    def ppReadData(self,minbytes=8):
        if self.xem:
            self.xem.UpdateWireOuts()
            wirevalue = self.xem.GetWireOutValue(0x25)   # pipe_out_available
            byteswaiting = (wirevalue & 0x1ffe)*2
            if byteswaiting:
                data = bytearray('\x00'*byteswaiting)
                self.xem.ReadFromPipeOut(0xa2, data)
                overrun = (wirevalue & 0x4000)!=0
                return data, overrun
        return None, False
                        
    def ppReadLogicAnalyzerData(self,minbytes=8):
        if self.xem:
            self.xem.UpdateWireOuts()
            wirevalue = self.xem.GetWireOutValue(0x27)   # pipe_out_available
            byteswaiting = (wirevalue & 0x1ffe)*2
            self.logicAnalyzerOverrun = (wirevalue & 0x4000) == 0x4000
            if byteswaiting:
                data = bytearray('\x00'*byteswaiting)
                self.xem.ReadFromPipeOut(0xa1, data)
                overrun = (wirevalue & 0x4000)!=0
                return data, overrun
        return None, False
                        
    def wordListToBytearray(self, wordlist):
        """ convert list of words to binary bytearray
        """
        return bytearray(numpy.array(wordlist, dtype=numpy.int32).view(dtype=numpy.int8))

    def bytearrayToWordList(self, barray):
        return list(numpy.array( barray, dtype=numpy.int8).view(dtype=numpy.int32 ))
            
    def ppWriteRam(self,data,address):
        if self.xem:
            appendlength = int(math.ceil(len(data)/128.))*128 - len(data)
            data += bytearray([0]*appendlength)
            logging.getLogger(__name__).info( "set write address {0}".format(address) )
            self.xem.SetWireInValue( 0x01, address & 0xffff )
            self.xem.SetWireInValue( 0x02, (address >> 16) & 0xffff )
            self.xem.UpdateWireIns()
            self.xem.ActivateTriggerIn( 0x41, 6 ) # ram set wwrite address
            return self.xem.WriteToPipeIn( 0x82, data )
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
            return None
            
    def ppReadRam(self,data,address):
        if self.xem:
#           print "set read address"
            self.xem.SetWireInValue( 0x01, address & 0xffff )
            self.xem.SetWireInValue( 0x02, (address >> 16) & 0xffff )
            self.xem.UpdateWireIns()
            self.xem.ActivateTriggerIn( 0x41, 7 ) # Ram set read address
            self.xem.ReadFromPipeOut( 0xa3, data )
#           print "read", len(data)
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
            
    quantum = 1024*1024
    def ppWriteRamWordList(self,wordlist,address):
        logger = logging.getLogger(__name__)
        data = self.wordListToBytearray(wordlist)
        for start in range(0, len(data), self.quantum ):
            self.ppWriteRam( data[start:start+self.quantum], address+start)
        matches = True
        myslice = bytearray(self.quantum)
        for start in range(0, len(data), self.quantum ):
            self.ppReadRam(myslice, address+start)
            length = min(self.quantum,len(data)-start)
            matches = matches and data[start:start+self.quantum] == myslice[:length]
        logger.info( "ppWriteRamWordList {0}".format( len(data)) )
        if not matches:
            logger.error( "Write unsuccessful data does not match write length {0} read length {1}".format(len(data),len(data)))
            raise PulserHardwareException("RAM write unsuccessful")

    def ppReadRamWordList(self, wordlist, address):
        data = bytearray([0]*len(wordlist)*4)
        myslice = bytearray(self.quantum)
        for start in range(0, len(data), self.quantum ):
            length = min(self.quantum, len(data)-start )
            self.ppReadRam(myslice, address+start)
            data[start:start+length] = myslice[:length]
        wordlist = self.bytearrayToWordList(data)
        return wordlist

    def ppWriteRamWordListShared(self, length, address, check=True):
        #self.ppWriteRamWordList(self.sharedMemoryArray[:length], address)
        logger = logging.getLogger(__name__)
        data = self.wordListToBytearray(self.sharedMemoryArray[:length])
        self.ppWriteRam( data, address)
        if check:
            myslice = bytearray(len(data))
            self.ppReadRam(myslice, address)
            matches = data == myslice
            logger.info( "ppWriteRamWordList {0}".format( len(data)) )
            if not matches:
                logger.error( "Write unsuccessful data does not match write length {0} read length {1}".format(len(data),len(data)))
                raise PulserHardwareException("RAM write unsuccessful")
                
    def ppReadRamWordListShared(self, length, address):
        data = bytearray([0]*length*4)
        self.ppReadRam(data, address)
        self.sharedMemoryArray[:length] = self.bytearrayToWordList(data)
        return True

    def ppClearWriteFifo(self):
        if self.xem:
            self.xem.ActivateTriggerIn(0x41, 3)
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
            
    def ppFlushData(self):
        if self.xem:
            self.data = Data()
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
        return None

    def ppClearReadFifo(self):
        if self.xem:
            self.xem.ActivateTriggerIn(0x41, 4)
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
            
    def ppReadLog(self):
        if self.xem:
            #Commented CWC 04032012
            data = bytearray('\x00'*32)
            self.xem.ReadFromPipeOut(0xA1, data)
            with open(r'debug\log','wb') as f:
                f.write(data)
            return data
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
            return None
        
        
    def listBoards(self):
        xem = ok.FrontPanel()
        self.moduleCount = xem.GetDeviceCount()
        self.modules = dict()
        for i in range(self.moduleCount):
            serial = xem.GetDeviceListSerial(i)
            tmp = ok.FrontPanel()
            check( tmp.OpenBySerial( serial ), "OpenBySerial" )
            desc = self.getDeviceDescription(tmp)
            tmp = None
            self.modules[desc.identifier] = desc
        del(xem)
        if self.openModule is not None:
            self.modules[self.openModule.identifier] = self.openModule
        return self.modules
        
    def getDeviceDescription(self,xem):
        """Get informaion from an open device
        """
        desc = DeviceDescription()
        desc.serial = xem.GetSerialNumber()
        desc.identifier = xem.GetDeviceID()
        desc.major = xem.GetDeviceMajorVersion()
        desc.minor = xem.GetDeviceMinorVersion()
        desc.model = xem.GetBoardModel()
        desc.modelName = ModelStrings.get(desc.model,'Unknown')
        return desc
        
    def renameBoard(self,serial,newname):
        tmp = ok.FrontPanel()
        tmp.OpenBySerial(serial)
        oldname = tmp.GetDeviceID()
        tmp.SetDeviceId( newname )
        tmp.OpenBySerial(serial)
        newname = tmp.GetDeviceID()
        if newname!=oldname:
            self.modules[newname] = self.modules.pop(oldname)
            
    def uploadBitfile(self,bitfile):
        logger = logging.getLogger(__name__)
        if self.xem is not None and self.xem.IsOpen():
            check( self.xem.ConfigureFPGA(bitfile), "Configure bitfile {0}".format(bitfile))
            self.xem.ActivateTriggerIn(0x41, 9)  # reset overrun
            logger.info("upload bitfile '{0}' to {1}".format(bitfile,self.xem.GetSerialNumber()))
            logger.info(str(BitfileInfo(bitfile)))

    def openByName(self,name):
        self.xem = ok.FrontPanel()
        check( self.xem.OpenBySerial( self.modules[name].serial ), "OpenByName {0}".format(name) )
        return self.xem

    def openBySerial(self,serial):
        logger = logging.getLogger(__name__)
        if self.xem is None or not self.xem.IsOpen() or self.xem.GetSerialNumber()!=serial:
            logger.debug("Open Serial {0}".format(serial) )
            self.xem = ok.FrontPanel()
            check( self.xem.OpenBySerial( serial ), "OpenBySerial '{0}'".format(serial) )
            self.openModule = self.getDeviceDescription(self.xem)
        else:
            logger.debug("Serial {0} is already open".format(serial) )         
        return None

    def enableLogicAnalyzer(self, enable):
        if enable != self.logicAnalyzerEnabled:
            self.logicAnalyzerEnabled = enable
            if enable:
                if self.xem:
                    self.xem.SetWireInValue(0x0d, 1, 0x01)    # set logic analyzer enabled
                    self.xem.UpdateWireIns()
            else:
                if self.xem:
                    self.xem.SetWireInValue(0x0d, 0, 0x01)    # set logic analyzer disabled
                    self.xem.UpdateWireIns()
                    
    def logicAnalyzerTrigger(self):
        self.logicAnalyzerEnabled = True
        self.logicAnalyzerStopAtEnd = True
        if self.xem:
            self.xem.ActivateTriggerIn( 0x40, 12 ) # Ram set read address

    def logicAnalyzerClearOverrun(self):
        if self.xem:
            self.xem.ActivateTriggerIn( 0x40, 10 ) # Ram set read address
            
    def clearOverrun(self):
        if self.xem:
            self.xem.ActivateTriggerIn(0x41, 9)  # reset overrun
       
        
def sliceview(view,length):
    return tuple(buffer(view, i, length) for i in range(0, len(view)-length+1, length))

def sliceview_remainder(view,length):
    l = len(view)
    full_items = l//length
    appendix = l-length*full_items
    return buffer(view, l-appendix, appendix )
