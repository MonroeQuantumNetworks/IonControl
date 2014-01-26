# -*- coding: utf-8 -*-
"""
Encapsulation of the Pulse Programmer Hardware 
"""
import struct
from modules import enum
import math
from multiprocessing import Process
import modules.magnitude as magnitude
import ok
from ServerLogging import configureServerLogging
import logging

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
            logicAnalyzerData, logicAnalyzerOverrun = self.ppReadLogicAnalyzerData(8)
            if logicAnalyzerData is not None:
                for s in sliceview(logicAnalyzerData,8):
                    (code, ) = struct.unpack('Q',s)
                    time = code&0xffffff + self.logicAnalyzerData.countOffset
                    pattern = (code >> 24) & 0x3fffffffff
                    header = (code >> 62 )
                    if code==0x8000000000000000:  # overrun marker
                        self.logicAnalyzerData.countOffset += 0x1000000   # overrun of 24 bit counter
                    elif code&0xffffffffff000000==0x800000000f000000:  # end marker
                        self.logicAnalyzerData.stopMarker = time
                        self.dataQueue.put( self.logicAnalyzerData )
                        logger.debug("Sending data back {0}, {1} {2}".format(self.logicAnalyzerData.data,self.logicAnalyzerData.trigger,time))
                        self.logicAnalyzerData = LogicAnalyzerData()
                    elif header==0: # trigger
                        self.logicAnalyzerData.trigger.append( (time,pattern) )
                    elif header==1: # standard
                        self.logicAnalyzerData.data.append( (time,pattern) )                                            
                    
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
            
    def ppUpload(self,binarycode,startaddress=0):
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
            num, data = self.ppDownload(0,num)
            logger.info(   "Verified {0} bytes. {1}".format(num,data==binarycode) )
            return True
        else:
            logging.getLogger(__name__).warning("Pulser Hardware not available")
            return False
            
    def ppDownload(self,startaddress,length):
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
            
    def ppWriteRamWordlist(self,wordlist,address):
        logger = logging.getLogger(__name__)
        data = self.wordListToBytearray(wordlist)
        self.ppWriteRam( data, address)
        testdata = bytearray([0]*len(data))
        self.ppReadRam( testdata, address)
        logger.info( "ppWriteRamWordlist {0} {1} {2}".format( len(data), len(testdata), data==testdata ) )
        if data!=testdata:
            logger.error( "Write unsuccessfull data does not match write length {0} read length {1}".format(len(data),len(testdata)))
            raise PulserHardwareException("RAM write unsuccessful")

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
            
    def ppReadRamWordList(self, wordlist, address):
        data = bytearray([0]*len(wordlist)*4)
        self.ppReadRam(data,address)
        wordlist = self.bytearrayToWordList(data)
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
        if self.xem is not None and self.xem.IsOpen():
            check( self.xem.ConfigureFPGA(bitfile), "Configure bitfile {0}".format(bitfile))
            self.xem.ActivateTriggerIn(0x41, 9)  # reset overrun

    def openByName(self,name):
        self.xem = ok.FrontPanel()
        check( self.xem.OpenBySerial( self.modules[name].serial ), "OpenByName {0}".format(name) )
        return self.xem

    def openBySerial(self,serial):
        logger = logging.getLogger(__name__)
        logger.debug("Open Serial {0}".format(serial) )
        if self.xem is None or not self.xem.IsOpen() or self.xem.GetSerialNumber()!=serial:
            self.xem = ok.FrontPanel()
            check( self.xem.OpenBySerial( serial ), "OpenBySerial {0}".format(serial) )
            self.openModule = self.getDeviceDescription(self.xem)
        return None

    def enableLogicAnalyzer(self, enable):
        if enable != self.logicAnalyzerEnabled:
            self.logicAnalyzerEnabled = enable
            if enable:
                self.logicAnalyzerFile = open('logic.bin','wb')
                if self.xem:
                    self.xem.SetWireInValue(0x0d, 1, 0x01)    # set logic analyzer enabled
                    self.xem.UpdateWireIns()
            else:
                self.logicAnalyzerFile.close()
                self.logicAnalyzerFile = None
                if self.xem:
                    self.xem.SetWireInValue(0x0d, 0, 0x01)    # set logic analyzer disabled
                    self.xem.UpdateWireIns()
                    
    def logicAnalyzerTrigger(self):
        self.logicAnalyzerEnabled = True
        self.logicAnalyzerStopAtEnd = True
        if self.xem:
            self.xem.ActivateTriggerIn( 0x40, 12 ) # Ram set read address

       
        
def sliceview(view,length):
    return tuple(buffer(view, i, length) for i in range(0, len(view), length))    

if __name__ == "__main__":
    import fpgaUtilit
    import PulseProgram
    
    printdata = True
    
    pp = PulseProgram.PulseProgram()
    pp.loadSource(r'prog\Ions\ram_test.pp')
    #pp.loadSource(r'prog\Ions\ScanParameter.pp')
    fpga = fpgaUtilit.FPGAUtilit()
    xem = fpga.openBySerial('12320003V5')
    fpga.uploadBitfile(r'FPGA_ions\fpgafirmware.bit')
    hw = PulserHardwareServer(fpga,startReader=False)
    data = bytearray( struct.pack('IIIIIIII',0x12345678,0xabcdef,0x1,0x10,0x100,0x1000,0x567,0x67) )
    length = len(data)
    hw.ppWriteRam( data, 8 )
    print length
    backdata = bytearray([0]*length )
    hw.ppReadRam( backdata, 8 )
    print "data readback comparison, matches", data[0:len(backdata)] == backdata
    hw.ppUpload( pp.toBinary() )
    xem.UpdateWireOuts()
    print "DataOutPipe", hex(xem.GetWireOutValue(0x25))
    hw.ppWriteData( bytearray('\x12\x34\x00\x00\x21\x22\x23\x24'))
    xem.UpdateWireOuts()
    print "DataOutPipe",hex(xem.GetWireOutValue(0x25))
    hw.ppStart()
    Finished = False
    while not Finished:#for j in range(60):
        data, overrun = hw.ppReadData(4,1.0)
        if printdata:
            for i in sliceview(data,4):
                (num,) = struct.unpack('I',i)
                Finished |= (num==0xffffffff)
                print "data", hex(num)
        else:
            for i in sliceview(data,4):
                (num,) = struct.unpack('I',i)
                Finished |= (num==0xffffffff)
            if len(data)>0:
                print "read {0} bytes".format(len(data))
            else:
                print ".",
            
    xem.UpdateWireOuts()
    print "DataOutPipe",hex(xem.GetWireOutValue(0x25))
    print "byteswaiting" , xem.GetWireOutValue(0x25) & 0xfff  # pipe_out_available
