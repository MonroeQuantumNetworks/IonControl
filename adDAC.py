#C. Spencer Nichols
#3-31-2012
#This code sends commands from the user interface to the DDS boards when not running a
#  pulse-profile program

#IMPORTANT NOTES: - the initialize function also resets the board, so there is no
#                       need for a reset method
#                 - if adding a new board type, be sure to update the private
#                       variables

import sys, time, ok

class adDAC:
    """public data
            - amplitude  - integer
            - frequency  - float
            - phase      - integer
            - profiles   - list of profile data
       public methods:
            - __init__(xemObject, adType, index) - adBoard constructor
                - xemObject = OK FrontPanel object
                - ad type 'ad9958', 'ad9959', 'ad9910', 'ad9858'
                - index = board number
            - initialize(check) - initializes communication with AD board
                - check = print data sent to board
            - setAmplitude(amp, chan, check)
                - amp = amplitude integer
                - chan = channel integer
                - check = print data sent to board
            - setFrequency(freq, chan, check)
                - freq = frequency float
                - chan = channel integer
                - check = print data sent to board
            - setPhase(phs, chan, check)
                - phs = phase integer
                - chan = channel integer
                - check = print data sent to board
            - setProfile(prof, idx, chan, check) - not implemented yet :(
                -
                -
                - chan = channel integer
                - check = print data sent to board"""

    #################################################################
    #private variables
    #
    #if adding a new board type, be sure to include it here
    #################################################################

    _dacTypes = ('ad5390', 'ad5380')
    #maximum Vout tuning words allowed by each board

    _VoutLimit = {'ad5390' : 16383,  #14 bits
                'ad5380' : 16383}  #14 bits

    _dacChannels = {'ad5390' : 16,
                    'ad5380' : 40}

    _boardIDs = {'ad5390' : 4,
                 'ad5380' : 5}

    _xem = ok.FrontPanel()

    #################################################################
    #private functions
    #################################################################

    def _checkOutputs(self):
        time.sleep(0.2)
        print '_checkOutputs to be implemented...'
##        print 'shifting out:'
##        self._xem.UpdateWireOuts()
##        print hex(self._xem.GetWireOutValue(0x20))
##        print hex(self._xem.GetWireOutValue(0x21))
##        print hex(self._xem.GetWireOutValue(0x22))
##        print hex(self._xem.GetWireOutValue(0x23))
        return

    def _send(self, data, addr, special, cmd, check):
#        print 'send in:'
#        print hex(addr)
        print bin(data)
#        print hex(special)
        self._xem.SetWireInValue(0x04, (data & 0x0000FF) << 8, 0xFF00)
        self._xem.SetWireInValue(0x05, (data & 0xFFFF00) >> 8)
        self._xem.UpdateWireIns()
        self._xem.ActivateTriggerIn(0x40, 4)
        self._xem.ActivateTriggerIn(0x40, 5)

##        if(special): #special signals should only be sent once
##            self._xem.SetWireInValue(0x03, (addr & 0x000000FF))
##            self._xem.UpdateWireIns()

        if(check):
            self._checkOutputs()
        return

    def _reset(self): # To be implemented CWC 08242012
##        self._xem.SetWireInValue(0x00, (self.boardIndex<<2))
##        self._xem.UpdateWireIns()
##        self._xem.ActivateTriggerIn(0x42, 0)
        time.sleep(0.2)

    def _checkID(self): # To be implemented CWC 08242012
        self._xem.SetWireInValue(0x00, (self.boardIndex<<2))
        self._xem.UpdateWireIns()
        self._xem.UpdateWireOuts()
        print 'board ID: ' + str(self.boardIndex)
        id = self._xem.GetWireOutValue(0x24)
        if ((id > 3) | (id < 0)):
            print 'ERROR: found DDS ID greater than 3: ' + str(id)
            print 'This probably means there is an error in the bitfile - try reloading or restarting'
            sys.exit(1)
        if (id != self.boardID):
            print 'ERROR: DDS board ' + str(self.boardIndex) + ' is not a ' + self.board + '.  It is a ' + self._boardIDs.keys()[id]
            sys.exit(1)
        else:
            print 'successfully found ' + self.board + ' at index ' + str(self.boardIndex)

    def _ad5380Init(self, check):
        #reset board and set to 4-wire serial
        #self._xem.SetWireInValue(0x03, 0x0001)
        initData = 0x00000000
        self._reset()
        self._send(initData, 0, 1, 2, check)

        #send pll data
        pllData = 0x01a80000 #0x01d00000
        self._send(pllData, 0, 0, 2, check)
        return

    def _ad5390Init(self, check):
        initData = 0x606000
        #self._reset()
        self._xem.SetWireInValue(0x03, 0x0200, 0x0200)
        self._xem.UpdateWireIns()
        self._send(initData, 0, 0, 2, check)
        self._xem.SetWireInValue(0x03, 0x0000, 0x0200)
        self._xem.UpdateWireIns()
        return


    #################################################################
    #more private variables
    #################################################################

    _initialize = {'ad5390' : _ad5390Init,
                   'ad5380' : _ad5380Init}
    #################################################################
    #public variables
    #################################################################

    amplitude = 0
    frequency = 0
    phase = 0
    profiles = ()

    #################################################################
    #__init__
    #################################################################
    def __init__(self, xemObject, dacType, index):
        #check if board is valid
        if (dacType not in self._dacTypes):
            print 'ERROR: ' + dacType + ' is not a valid board'
            sys.exit(1)
        #make public variables
        self._xem = xemObject
        self.board = dacType
        self.boardIndex = index
        self.VoutLimit = self._VoutLimit[dacType]
        self.channelLimit = self._dacChannels[dacType]
        self.boardID = self._boardIDs[dacType]
        return

    #################################################################
    #public DDS initialize
    #################################################################

    def initialize(self, check):
        #the initialize function also resets the board, so there is no need for
        #a reset method
        if(check): #Bypassed checkID by setting check to false CWC 08142012
            self._checkID()
        self._initialize[self.board](self, check)
        #self._ad9959Init(check)
        return

    #################################################################
    #public DDS commands
    #################################################################

    def setAmplitude(self, amp, chan, check):
        if (amp > self.ampLimit):
            print 'ERROR: amplitude sent to board ' + self.boardIndex + ' is greater than amp limit'
        else:
            if(self.board == 'ad9958'):
                #send channel command
                chanData = int(0x00000006 + (0x01 << (6 + chan)))
                self._send(chanData, 0, 0, 3, check)
                #send amplitude data
                ampData = int(0x06001000 + amp)
            elif (self.board == 'ad9959'):
                #send command
                chanData = int(0x00000006 + (0x01 << (4 + chan)))
                self._send(chanData, 0, 0, 3, check)
                #send amplitude data
                ampData = int(0x06001000 + amp)
            elif (self.board == 'ad9910'):
                ampData = int(amp & 0x00003FFF)
            elif (self.board == 'ad9858'):
                #write to OK Wire Ins that control external attenuators
                print 'uncompleted'
            self._send(ampData, 0, 0, 2, check)
        return

    def setVout(self, Vout, chan, check):
        VoutData = int(Vout/2.5*2**13)
        if (VoutData > self.VoutLimit):
            print 'ERROR: Vout sent to board ' + str(self.boardIndex) + ' is greater than Vout limit'
        else:
            if(self.board == 'ad5390'):
##                #send channel command
                #self._xem.SetWireInValue(0x03, 0x0000, 0x0200)
                #self._xem.UpdateWireIns()
                data =int( (0x0<<20)+(chan<<16)+(0b11<<14)+(VoutData&0x3FFF))
                print 'data: %i'%(data)
                self._send(data, 0, 0, 2, check)
                #self._xem.SetWireInValue(0x03, 0x0000, 0x0200)
                #self._xem.UpdateWireIns()
##            elif (self.board == 'ad5380'):
##                #send channel command
##                chanData = int(0x00000006 + (0x01 << (4 + chan)))
##                self._send(chanData, 0, 0, 3, check)

            return
        return

    def setFrequency(self, freq, chan, check):
        if (freq > self.freqLimit):
            print 'ERROR: frequency sent to board ' + self.boardIndex + ' is greater than amp limit'
        else:
            if(self.board == 'ad9958'):
                #send channel command
                chanData = int(0x00000006 + (0x01 << (6 + chan)))
                self._send(chanData, 0, 0, 3, check)
            elif (self.board == 'ad9959'):
                #send channel command
                chanData = int(0x00000006 + (0x01 << (4 + chan)))
                self._send(chanData, 0, 0, 3, check)
            freqData = int((float(freq)/self.halfClockLimit) * 0x80000000)
            self._send(freqData, 0, 0, 0, check)
        return

    def setPhase(self, phs, chan, check):
        if (phs > self.phaseLimit):
            print 'ERROR: phase sent to board ' + self.boardIndex + ' is greater than amp limit'
        else:
            if(self.board == 'ad9958'):
                #send channel command
                chanData = int(0x00000006 + (0x01 << (6 + chan)))
                self._send(chanData, 0, 0, 3, check)
                #send phase data
                phaseData = int((phs & 0x00003FFF) + 0x00050000)
            elif (self.board == 'ad9959'):
                #send channel command
                chanData = int(0x00000006 + (0x01 << (4 + chan)))
                self._send(chanData, 0, 0, 3, check)
                #send phase data
                phaseData = int((phs & 0x00003FFF) + 0x00050000)
            elif(self.board == 'ad9910'):
                phaseData = int(phs & 0x0000FFFF)
            elif(self.board == 'ad9858'):
                phaseData = int(phs & 0x00003FFF)
            self._send(phaseData, 0, 0, 1, check)
            return

    def setProfile(self, prof, idx, chan, check):
        if((self.board == 'ad9958') | (self.board == 'ad9959')):
            #send channel command
            chanData = int(0x00000006 + (0x01 << (6 + chan)))
            self._send(chanData, 0, 0, 3, check)
            #send profile data
            print 'uncompleted'
        elif (self.board == 'ad9910'):
            print 'uncompleted'
        elif (self.board == 'ad9858'):
            print 'uncompleted'
        return

    def addCMD(self, chan):
        data = [];
        if(self.board == 'ad9958'):
            data = int(0x00000006 + (0x01 << (6 + chan)))
        elif(self.board == 'ad9959'):
            data = int(0x00000006 + (0x01 << (4 + chan)))
        return data

