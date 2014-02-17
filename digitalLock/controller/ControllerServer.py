# -*- coding: utf-8 -*-
"""
Encapsulation of the Pulse Programmer Hardware 
"""
import logging
import math
from multiprocessing import Process
import struct

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
        self.stopMarker = None
        self.countOffset = 0

class FinishException(Exception):
    pass

class PulserHardwareServer(Process):
    timestep = magnitude.mg(20,'ns')
    def __init__(self, dataQueue, commandPipe, loggingQueue):
        super(PulserHardwareServer,self).__init__()
        self.dataQueue = dataQueue
        self.commandPipe = commandPipe
        self.running = True
        self.openModule = None
        self.xem = None
        self.loggingQueue = loggingQueue
        
        # PipeReader stuff
        self.state = self.analyzingState.normal
        self.data = Data()
        self.dedicatedData = DedicatedData()
        self.timestampOffset = 0

        self._shutter = 0
        self._trigger = 0
        self._adcCounterMask = 0
        self._integrationTime = magnitude.mg(100,'ms')
        
        self.logicAnalyzerEnabled = False
        self.logicAnalyzerStopAtEnd = False
        self.logicAnalyzerData = LogicAnalyzerData()
        
    def run(self):
        configureServerLogging(self.loggingQueue)
        logger = logging.getLogger(__name__)
        while (self.running):
            if self.commandPipe.poll(0.05):
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

    analyzingState = enum.enum('normal','scanparameter')
    def readDataFifo(self):
        """ run is responsible for reading the data back from the FPGA
            0xffffffff end of experiment marker
            0xfffexxxx exitcode marker
            0xff000000 timestamping overflow marker
            0xffffxxxx scan parameter, followed by scanparameter value
            0x1nxxxxxx count result from channel n
            0x2nxxxxxx timestamp result channel n
            0x3nxxxxxx timestamp gate start channel n
            0x4xxxxxxx other return
        """
        logger = logging.getLogger(__name__)
        if (self.logicAnalyzerEnabled):
            logicAnalyzerData, _ = self.ppReadLogicAnalyzerData(8)
            if logicAnalyzerData is not None:
                for s in sliceview(logicAnalyzerData,8):
                    (code, ) = struct.unpack('Q',s)
                    time = (code&0xffffff) + self.logicAnalyzerData.countOffset
                    pattern = (code >> 24) & 0x3fffffffff
                    header = (code >> 62 )
                    if code==0x8000000000000000:  # overrun marker
                        self.logicAnalyzerData.countOffset += 0x1000000   # overrun of 24 bit counter
                    elif code&0xffffffffff000000==0x800000000f000000:  # end marker
                        self.logicAnalyzerData.stopMarker = time
                        self.dataQueue.put( self.logicAnalyzerData )
                        self.logicAnalyzerData = LogicAnalyzerData()
                    elif header==0: # trigger
                        self.logicAnalyzerData.trigger.append( (time,pattern) )
                    elif header==1: # standard
                        self.logicAnalyzerData.data.append( (time,pattern) )  
                    elif header==3: # aux data
                        self.logicAnalyzerData.auxData.append( (time,pattern))                                          
                    #logger.debug("Time {0:x} header {1} pattern {2:x} {3:x} {4:x}".format(time, header, pattern, code, self.logicAnalyzerData.countOffset))
                   
        data, self.data.overrun = self.ppReadData(4)
        if data:
            for s in sliceview(data,4):
                (token,) = struct.unpack('I',s)
                if self.state == self.analyzingState.scanparameter:
                    if self.data.scanvalue is None:
                        self.data.scanvalue = token
                    else:
                        self.dataQueue.put( self.data )
                        self.data = Data()
                        self.data.scanvalue = token
                    self.state = self.analyzingState.normal
                elif token & 0xf0000000 == 0xe0000000: # dedicated results
                    channel = (token >>24) & 0xf
                    if self.dedicatedData.data[channel] is not None:
                        self.dataQueue.put( self.dedicatedData )
                        self.dedicatedData = DedicatedData()
                    self.dedicatedData.data[channel] = token & 0xffffff
                elif token & 0xff000000 == 0xff000000:
                    if token == 0xffffffff:    # end of run
                        self.data.final = True
                        self.data.exitcode = 0x0000
                        self.dataQueue.put( self.data )
                        logger.info( "End of Run marker received" )
                        self.data = Data()
                    elif token & 0xffff0000 == 0xfffe0000:  # exitparameter
                        self.data.final = True
                        self.data.exitcode = token & 0x0000ffff
                        logger.info( "Exitcode {0} received".format(self.data.exitcode) )
                        self.dataQueue.put( self.data )
                        self.data = Data()
                    elif token == 0xff000000:
                        self.timestampOffset += 1<<28
                    elif token & 0xffff0000 == 0xffff0000:  # new scan parameter
                        self.state = self.analyzingState.scanparameter
                else:
                    key = token >> 28
                    channel = (token >>24) & 0xf
                    value = token & 0xffffff
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
                        pass
            if self.data.overrun:
                logger.info( "Overrun detected, triggered data queue" )
                self.dataQueue.put( self.data )
                self.data = Data()
                
            
     
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

    def ppReadData(self,minbytes=4):
        if self.xem:
            self.xem.UpdateWireOuts()
            wirevalue = self.xem.GetWireOutValue(0x25)   # pipe_out_available
            byteswaiting = (wirevalue & 0xffe)*2
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
            byteswaiting = (wirevalue & 0xffe)*2
            if byteswaiting:
                data = bytearray('\x00'*byteswaiting)
                self.xem.ReadFromPipeOut(0xa1, data)
                overrun = (wirevalue & 0x4000)!=0
                return data, overrun
        return None, False
                        
    def ppWriteData(self,data):
        if self.xem:
            if isinstance(data,bytearray):
                return self.xem.WriteToPipeIn(0x81,data)
            else:
                code = bytearray()
                for item in data:
                    code.extend(struct.pack('I',item))
                #print "ppWriteData length",len(code)
                return self.xem.WriteToPipeIn(0x81,code)
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
            return None
                
    def wordListToBytearray(self, wordlist):
        """ convert list of words to binary bytearray
        """
        self.binarycode = bytearray()
        for word in wordlist:
            self.binarycode += struct.pack('I', word)
        return self.binarycode        

    def bytearrayToWordList(self, barray):
        wordlist = list()
        for offset in range(0,len(barray),4):
            (w,) = struct.unpack_from('I',buffer(barray),offset)
            wordlist.append(w)
        return wordlist
                           
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
            logger.info("upload bitfile '{0}'".format(bitfile))
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


       
        
def sliceview(view,length):
    return tuple(buffer(view, i, length) for i in range(0, len(view), length))    

