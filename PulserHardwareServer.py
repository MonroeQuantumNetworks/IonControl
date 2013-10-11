# -*- coding: utf-8 -*-
"""
Encapsulation of the Pulse Programmer Hardware 
"""
from fpgaUtilit import check
from PyQt4 import QtCore 
import struct
from Queue import Queue, Empty
import modules.magnitude as magnitude
from modules import enum
import math
import traceback
import time
from multiprocessing import Process, Queue, Pipe
import time

class PulserHardwareException(Exception):
    pass

class Data:
    def __init__(self):
        self.count = [list() for i in range(16)]
        self.timestamp = [list() for i in range(8)]
        self.timestampZero = [0]*8
        self.scanvalue = None
        self.final = False
        self.other = list()
        self.overrun = False
        
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


class PulserHardwareServer(Process):
    timestep = magnitude.mg(20,'ns')
    def __init__(self, dataQueue, commandPipe):
        super(P,self).__init__()
        self.dataQueue = dataQueue
        self.commandPipe = commandPipe
        self.running = True
        
        # PipeReader stuff
        self.state = self.analyzingState.normal
        self.data = Data()
        self.dedicatedData = DedicatedData()
        self.timestampOffset = 0

        self._shutter = 0
        self._trigger = 0
        self._adcCounterMask = 0
        self._integrationTime = magnitude.mg(100,'ms')

        
    def run(self):
        i = 0
        while (self.running):
            if self.commandPipe.poll(0.2):
                commandstring, argument = self.pipe.recv()
                command = getattr(self, commandstring)
                self.commandPipe.send(command(*argument))
            self.readDataFifo()
            
    def finish(self):
        self.running = False
        return 'Will finish'

    analyzingState = enum.enum('normal','scanparameter')
    def readDataFifo(self):
        """ run is responsible for reading the data back from the FPGA
            0xffffffff end of experiment marker
            0xff000000 timestamping overflow marker
            0xffffxxxx scan parameter, followed by scanparameter value
            0x1nxxxxxx count result from channel n
            0x2nxxxxxx timestamp result channel n
            0x3nxxxxxx timestamp gate start channel n
            0x4xxxxxxx other return
        """
        data, overrun = self.pulserHardware.ppReadData(4,1.0)
        self.data.overrun = self.data.overrun or overrun
        for s in sliceview(data,4):
            (token,) = struct.unpack('I',s)
            if self.state == self.analyzingState.scanparameter:
                if self.data.scanvalue is None:
                    self.data.scanvalue = token
                else:
                    self.dataQueue.put( self.data )
                    self.data = Data()
                    self.data.scanvalue = token
                state = self.analyzingState.normal
            elif token & 0xf0000000 == 0xe0000000: # dedicated results
                channel = (token >>24) & 0xf
                if self.dedicatedData.data[channel] is not None:
                    self.dataQueue.put( self.dedicatedData )
                    self.dedicatedData = DedicatedData()
                self.dedicatedData.data[channel] = token & 0xffffff
            elif token & 0xff000000 == 0xff000000:
                if token == 0xffffffff:    # end of run
                    self.data.final = True
                    self.dataQueue.put( self.data )
                    print "End of Run marker received"
                    self.data = Data()
                elif token == 0xff000000:
                    self.timestampOffset += 1<<28
                elif token & 0xffff0000 == 0xffff0000:  # new scan parameter
                    state = self.analyzingState.scanparameter
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


    def updateSettings(self,fpgaUtilit):
        self.stopPipeReader()
        self.fpga = fpgaUtilit
        self.xem = self.fpga.xem
        self.Mutex = self.fpga.Mutex
        self.pipeReader = PipeReader(self)
        self.pipeReader.start()        

    def stopPipeReader(self):
        self.pipeReader.finish()
        self.interruptRead()
        self.pipeReader.wait()
        
    def setHardware(self,xem):
        self.xem = xem
        if self.xem and not self.pipeReader.isRunning():
            self.pipeReader.start()            
        
    def getShutter(self):
        return self._shutter  #
         
    def setShutter(self, value):
        if self.xem:
            with QtCore.QMutexLocker(self.Mutex):
                check( self.xem.SetWireInValue(0x06, value, 0xFFFF) , 'SetWireInValue' )	
                check( self.xem.SetWireInValue(0x07, value>>16, 0xFFFF)	, 'SetWireInValue' )
                check( self.xem.UpdateWireIns(), 'UpdateWireIns' )
                self._shutter = value
                self.shutterChanged.emit( self._shutter )
        else:
            print "Pulser Hardware not available"
            
    def setShutterBit(self, bit, value):
        mask = 1 << bit
        newval = (self._shutter & (~mask)) | (mask if value else 0)
        self.shutter = newval
        
    def getTrigger(self):
        return self._trigger
            
    def setTrigger(self,value):
        if self.xem:
            with QtCore.QMutexLocker(self.Mutex):
                check( self.xem.SetWireInValue(0x08, value, 0xFFFF) , 'SetWireInValue' )	
                check( self.xem.SetWireInValue(0x09, value>>16, 0xFFFF)	, 'SetWireInValue' )
                check( self.xem.UpdateWireIns(), 'UpdateWireIns' )
                check( self.xem.ActivateTriggerIn( 0x41, 2), 'ActivateTrigger' )
                self._trigger = value
        else:
            print "Pulser Hardware not available"
            
    def getCounterMask(self):
        return self._adcCounterMask & 0xff
        
    def setCounterMask(self, value):
        if self.xem:
            with QtCore.QMutexLocker(self.Mutex):
                self._adcCounterMask = (self._adcCounterMask & 0xf00) | (value & 0xff)
                check( self.xem.SetWireInValue(0x0a, self._adcCounterMask, 0xFFFF) , 'SetWireInValue' )	
                check( self.xem.UpdateWireIns(), 'UpdateWireIns' )            
                print "set counterMask", hex(self._adcCounterMask)
        else:
            print "Pulser Hardware not available"

    def getAdcMask(self):
        return (self._adcCounterMask >> 8) & 0xff
        
    def setAdcMask(self, value):
        if self.xem:
            with QtCore.QMutexLocker(self.Mutex):
                self._adcCounterMask = ((value<<8) & 0xf00) | (self._adcCounterMask & 0xff)
                check( self.xem.SetWireInValue(0x0a, self._adcCounterMask, 0xFFFF) , 'SetWireInValue' )	
                check( self.xem.UpdateWireIns(), 'UpdateWireIns' )  
                print "set adc mask", hex(self._adcCounterMask)
        else:
            print "Pulser Hardware not available"
        
    def getIntegrationTime(self):
        return self._integrationTime
        
    def setIntegrationTime(self, value):
        self.integrationTimeBinary = int( (value/self.timestep).toval() )
        if self.xem:
            with QtCore.QMutexLocker(self.Mutex):
                print "set dedicated integration time" , value, self.integrationTimeBinary
                check( self.xem.SetWireInValue(0x0b, self.integrationTimeBinary >> 16, 0xFFFF) , 'SetWireInValue' )	
                check( self.xem.SetWireInValue(0x0c, self.integrationTimeBinary, 0xFFFF) , 'SetWireInValue' )	
                check( self.xem.UpdateWireIns(), 'UpdateWireIns' )            
                self._integrationTime = value
        else:
            print "Pulser Hardware not available"
            
    def getIntegrationTimeBinary(self, value):
        return int( (value/self.timestep).toval() ) & 0xffffffff
            
    def ppUpload(self,binarycode,startaddress=0):
        if self.xem:
            with QtCore.QMutexLocker(self.Mutex):
                print "starting PP upload",
                check( self.xem.SetWireInValue(0x00, startaddress, 0x0FFF), "ppUpload write start address" )	# start addr at zero
                self.xem.UpdateWireIns()
                check( self.xem.ActivateTriggerIn(0x41, 1), "ppUpload trigger" )
                print len(binarycode), "bytes,",
                num = self.xem.WriteToPipeIn(0x80, bytearray(binarycode) )
                check(num, 'Write to program pipe' )
                print "uploaded pp file {0} bytes".format(num),
                num, data = self.ppDownload(0,num)
                print "Verified {0} bytes. ".format(num),data==binarycode
                return True
        else:
            print "Pulser Hardware not available"
            return False
            
    def ppDownload(self,startaddress,length):
        if self.xem:
            with QtCore.QMutexLocker(self.Mutex):
                self.xem.SetWireInValue(0x00, startaddress, 0x0FFF)	# start addr at 3900
                self.xem.UpdateWireIns()
                self.xem.ActivateTriggerIn(0x41, 0)
                self.xem.ActivateTriggerIn(0x41, 1)
                data = bytearray('\000'*length)
                num = self.xem.ReadFromPipeOut(0xA0, data)
                return num, data
        else:
            print "Pulser Hardware not available"
            return 0,None
        
    def ppIsRunning(self):
        if self.xem:
            with QtCore.QMutexLocker(self.Mutex):
    		#Commented CWC 04032012
                data = '\x00'*32
                self.xem.ReadFromPipeOut(0xA1, data)
                if ((data[:2] != '\xED\xFE') or (data[-2:] != '\xED\x0F')):
                    print "Bad data string: ", map(ord, data)
                    return True
                data = map(ord, data[2:-2])
                #Decode
                active =  bool(data[1] & 0x80)
                return active
        else:
            print "Pulser Hardware not available"
            return False
            

    def ppReset(self):#, widget = None, data = None):
        if self.xem:
            with QtCore.QMutexLocker(self.Mutex):
                self.xem.ActivateTriggerIn(0x40,0)
                self.xem.ActivateTriggerIn(0x41,0)
                print "pp_reset is not working right now... CWC 08302012"
        else:
            print "Pulser Hardware not available"

    def ppStart(self):#, widget = None, data = None):
        if self.xem:
            with QtCore.QMutexLocker(self.Mutex):
                self.xem.ActivateTriggerIn(0x40, 3)  # pp_stop_trig
                self.xem.ActivateTriggerIn(0x40, 2)  # pp_start_trig
                self.xem.ActivateTriggerIn(0x41, 9)  # reset overrun
                return True
        else:
            print "Pulser Hardware not available"
            return False

    def ppStop(self):#, widget, data= None):
        if self.xem:
            with QtCore.QMutexLocker(self.Mutex):
                self.xem.ActivateTriggerIn(0x40, 3)  # pp_stop_trig
                return True
        else:
            print "Pulser Hardware not available"
            return False

    def interruptRead(self):
        self.sleepQueue.put(False)

    def ppReadData(self,minbytes=4):
        if self.xem:
            self.xem.UpdateWireOuts()
            wirevalue = self.xem.GetWireOutValue(0x25)   # pipe_out_available
            byteswaiting = max( (wirevalue & 0xffe)*2, 4 * bool( wirevalue & 0x000 ) )
            #if byteswaiting>0: print "byteswaiting", byteswaiting
            totaltime = 0
            while byteswaiting<minbytes and totaltime<timeout:
                try: 
                    self.sleepQueue.get(True, retryevery)
                    totaltime = timeout     # we were interrupted
                except Empty:         
                    pass                    # expiration is the normal case
                totaltime += retryevery
                with QtCore.QMutexLocker(self.Mutex):
                    self.xem.UpdateWireOuts()
                    wirevalue = self.xem.GetWireOutValue(0x25)   # pipe_out_available
                byteswaiting = max( (wirevalue & 0xffe)*2, 4 * bool( wirevalue & 0x000 ) )
                #if byteswaiting>0: print "byteswaiting", byteswaiting
            data = bytearray('\x00'*byteswaiting)
            #if byteswaiting>0: print "Reading", byteswaiting
            with QtCore.QMutexLocker(self.Mutex):
                self.xem.ReadFromPipeOut(0xa2, data)
            overrun = (wirevalue & 0x4000)!=0
            return data, overrun
        else:
            print "Pulser Hardware not available"
            return None
                        
    def ppWriteData(self,data):
        if self.xem:
            if isinstance(data,bytearray):
                with QtCore.QMutexLocker(self.Mutex):
                    return self.xem.WriteToPipeIn(0x81,data)
            else:
                code = bytearray()
                for item in data:
                    code.extend(struct.pack('I',item))
                print "ppWriteData length",len(code)
                with QtCore.QMutexLocker(self.Mutex):
                    return self.xem.WriteToPipeIn(0x81,code)
        else:
            print "Pulser Hardware not available"
            return None
                
    def ppWriteRam(self,data,address):
        if self.xem:
            appendlength = int(math.ceil(len(data)/128.))*128 - len(data)
            data += bytearray([0]*appendlength)
            with QtCore.QMutexLocker(self.Mutex):
                print "set write address"
                self.xem.SetWireInValue( 0x01, address & 0xffff )
                self.xem.SetWireInValue( 0x02, (address >> 16) & 0xffff )
                self.xem.UpdateWireIns()
                self.xem.ActivateTriggerIn( 0x41, 6 ) # ram set wwrite address
                return self.xem.WriteToPipeIn( 0x82, data )
        else:
            print "Pulser Hardware not available"
            return None
            
    def wordListToBytearray(self, wordlist):
        """ convert list of words to binary bytearray
        """
        self.binarycode = bytearray()
        for index, word in enumerate(wordlist):
#            if self.debug:
#                print hex(index), hex(word)
            self.binarycode += struct.pack('I', word)
        return self.binarycode        

    def bytearrayToWordList(self, barray):
        wordlist = list()
        for offset in range(0,len(barray),4):
            (w,) = struct.unpack_from('I',buffer(barray),offset)
            wordlist.append(w)
        return wordlist
            
    def ppWriteRamWordlist(self,wordlist,address):
        data = self.wordListToBytearray(wordlist)
        self.ppWriteRam( data, address)
        testdata = bytearray([0]*len(data))
        self.ppReadRam( testdata, address)
        print "ppWriteRamWordlist", len(data), len(testdata), data==testdata
        if data!=testdata:
            print "Write unsuccessfull data does not match"
            print len(data), self.bytearrayToWordList(data)
            print len(testdata), self.bytearrayToWordList(testdata)
            raise PulserHardwareException("RAM write unsuccessful")

    def ppReadRam(self,data,address):
        if self.xem:
            with QtCore.QMutexLocker(self.Mutex):
#                print "set read address"
                self.xem.SetWireInValue( 0x01, address & 0xffff )
                self.xem.SetWireInValue( 0x02, (address >> 16) & 0xffff )
                self.xem.UpdateWireIns()
                self.xem.ActivateTriggerIn( 0x41, 7 ) # Ram set read address
                self.xem.ReadFromPipeOut( 0xa3, data )
#                print "read", len(data)
        else:
            print "Pulser Hardware not available"
            
    def ppReadRamWordList(self, wordlist, address):
        data = bytearray([0]*len(wordlist)*4)
        self.ppReadRam(data,address)
        wordlist = self.bytearrayToWordList(data)
        return wordlist
                
    def ppClearWriteFifo(self):
        if self.xem:
            with QtCore.QMutexLocker(self.Mutex):
                self.xem.ActivateTriggerIn(0x41, 3)
        else:
            print "Pulser Hardware not available"
            
    def ppFlushData(self):
        if self.xem:
            self.pipeReader.flushData()
        else:
            print "Pulser Hardware not available"

    def ppClearReadFifo(self):
        if self.xem:
            with QtCore.QMutexLocker(self.Mutex):
                self.xem.ActivateTriggerIn(0x41, 4)
        else:
            print "Pulser Hardware not available"
            
    def ppReadLog(self):
        if self.xem:
            with QtCore.QMutexLocker(self.Mutex):
     		#Commented CWC 04032012
                data = bytearray('\x00'*32)
                self.xem.ReadFromPipeOut(0xA1, data)
                with open(r'debug\log','wb') as f:
                    f.write(data)
            return data
        else:
            print "Pulser Hardware not available"
            return None
        
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
    hw = PulserHardware(fpga,startReader=False)
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
