#C. Spencer Nichols
#3-31-2012
#This code sends commands from the user interface to the DDS boards when not running a
#  pulse-profile program

#IMPORTANT NOTES: - the initialize function also resets the board, so there is no
#                       need for a reset method
#                 - if adding a new board type, be sure to update the private
#                       variables

import sys, time, ok

class adBoard:
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

    _adTypes = ('ad9958', 'ad9959', 'ad9910', 'ad9858')
    #maximum frequency, phasem and amplitude tuning words allowed by each board
    _freqMax = {'ad9958' : 250, #each board has 32 bits of frequency precision
                'ad9959' : 250, #but different output maxima
                'ad9910' : 400,
                'ad9858' : 400}
    _halfClockMax = {'ad9958' : 250,
                     'ad9959' : 250,
                     'ad9910' : 500,
                     'ad9858' : 500}
    _phaseMax = {'ad9958' : 16383, #14 bits
                 'ad9959' : 16383, #14 bits
                 'ad9910' : 65535, #16 bits
                 'ad9858' : 16383} #14 bits
    _ampMax = {'ad9958' : 1023,  #10 bits
               'ad9959' : 1023,  #10 bits
               'ad9910' : 16383, #14 bits
               'ad9858' : 63}    #the max ad9858 amplitude is determined by any
                                #attenuators attached to that particular board
    _boardChannels = {'ad9958' : 2,
                      'ad9959' : 4,
                      'ad9910' : 1,
                      'ad9858' : 1}
    _boardIDs = {'ad9958' : 0,
                 'ad9959' : 1,
                 'ad9910' : 2,
                 'ad9858' : 3}
    _xem = ok.FrontPanel()

    #################################################################
    #private functions
    #################################################################

    def _checkOutputs(self):
        time.sleep(0.2)
        print 'shifting out:'
        self._xem.UpdateWireOuts()
        print hex(self._xem.GetWireOutValue(0x20))
        print hex(self._xem.GetWireOutValue(0x21))
        print hex(self._xem.GetWireOutValue(0x22))
        print hex(self._xem.GetWireOutValue(0x23))
        return

    def _send(self, data, addr, special, cmd, check):
#        print 'send in:'
#        print hex(addr)
#        print hex(data)
#        print hex(special)
        self._xem.SetWireInValue(0x00, (self.boardIndex<<2) + cmd, 0x0FFF)
        self._xem.SetWireInValue(0x01, (data & 0x0000FFFF))
        self._xem.SetWireInValue(0x02, (data & 0xFFFF0000) >> 16)
        self._xem.SetWireInValue(0x03, ((special & 0x000000FF) << 8) + (addr & 0x000000FF))
        self._xem.UpdateWireIns()
        self._xem.ActivateTriggerIn(0x40, 1)

        if(special): #special signals should only be sent once
            self._xem.SetWireInValue(0x03, (addr & 0x000000FF))
            self._xem.UpdateWireIns()

        if(check):
            self._checkOutputs()
        return

    def _reset(self):
        self._xem.SetWireInValue(0x00, (self.boardIndex<<2))
        self._xem.UpdateWireIns()
        self._xem.ActivateTriggerIn(0x42, 0)
        time.sleep(0.2)

    def _checkID(self):
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

    def _ad9958Init(self, check):
        #reset board and set to 4-wire serial
        #self._xem.SetWireInValue(0x03, 0x0001)
        initData = 0x00000000
        self._reset()
        self._send(initData, 0, 1, 2, check)

        #send pll data
        pllData = 0x01940000 #M = 5; 0x01a80000 M = 10 #0x01a00000 M = 8
        self._send(pllData, 0, 0, 2, check)
        return

    def _ad9959Init(self, check):
        #reset board and set to 4-wire serial
        initData = 0x00000000
        self._reset()
        self._send(initData, 0, 1, 2, check)

        #send pll data
        pllData = 0x01940000#M = 5; 0x01a80000 M = 10 #0x01a00000 M = 8
        self._send(pllData, 0, 0, 2, check)
        return

    def _ad9910Init(self, check):
        #reset board and set pll data
        addr = 0x02
        pllData = 0x1d1f41c8
        self._reset()
        self._send(pllData, addr, 0, 3, check)

        #allow profile amplitude modulation
        addr = 0x01
        ampData = 0x01400820
        self._send(ampData, addr, 0, 3, check)

        #enable multi-board sync output
        addr = 0x0a
        ampData = 0x04000000
        self._send(ampData, addr, 0, 3, check)
        return

    def _ad9858Init(self, check):
        #this board is not yet supported
        print 'the AD9858 board is not supported yet . . . :('
        sys.exit(1)
        return

    #################################################################
    #more private variables
    #################################################################

    _initialize = {'ad9958' : _ad9958Init,
                   'ad9959' : _ad9959Init,
                   'ad9910' : _ad9910Init,
                   'ad9858' : _ad9858Init}
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
    def __init__(self, xemObject, adType, index):
        #check if board is valid
        if (adType not in self._adTypes):
            print 'ERROR: ' + adType + ' is not a valid board'
            sys.exit(1)
        #make public variables
        self._xem = xemObject
        self.board = adType
        self.boardIndex = index
        self.freqLimit = self._freqMax[adType]
        self.halfClockLimit = self._halfClockMax[adType]
        self.phaseLimit = self._phaseMax[adType]
        self.ampLimit = self._ampMax[adType]
        self.channelLimit = self._boardChannels[adType]
        self.boardID = self._boardIDs[adType]
        return

    #################################################################
    #public DDS initialize
    #################################################################

    def initialize(self, check):
        #the initialize function also resets the board, so there is no need for
        #a reset method
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

