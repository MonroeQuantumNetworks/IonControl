###########################################################################
#
# simple sequence with one cooling interval during which countrates can be measured
# repeated in infinite loop
#
# A Pulse Programmer file for the ScanParameter experiment has to fulfill the following conditions
# 
#define COOLDDS 4
#define TickleDDS 5

# var syntax:
# var name value, type, unit, encoding
var datastart 3900, address   # serves as tooltip
var dataend 4000, address
var coolingFreq     118, parameter, MHz, AD9912_FRQ
var tickleFreq          15, parameter, MHz, AD9912_FRQ
var startupMask      0x4000001, mask
var startup           0x4000001, shutter startupMask
var startupTime       1, parameter, ms
var coolingOnMask     1, mask
var coolingOn         1, shutter coolingOnMask
var coolingCounter    2, counter
var coolingOffMask    1, mask
var coolingOff        0, shutter coolingOffMask
var coolingOffCounter 0, counter
var coolingTime       10, parameter, ms
var experiments   10, parameter
var experimentsleft 10
var epsilon         2, parameter, us
var ddsApplyTrigger   0x3f,trigger
var endLabel 0xffffffff
var dummy3 42, parameter, MHz, AD9912_FRQ

# Preparation
	SHUTTERMASK startupMask
	ASYNCSHUTTER startup
	DDSFRQ COOLDDS, coolingFreq
	DDSFRQFINE COOLDDS, coolingFreq
	DDSFRQ TickleDDS, tickleFreq
	TRIGGER ddsApplyTrigger
	UPDATE startupTime

scanloop: NOP
	# Read the scan parameter from the input data if there is nothing else jump to stop
	# the parameters are echoed to the output stream as separators
	JMPPIPEEMPTY endlabel
	READPIPEINDF
	NOP
	WRITEPIPEINDF 
	NOP
	READPIPE
	NOP
	WRITEPIPE
	NOP
	STWI
	# reload the number of experiments
	LDWR experiments
	STWR experimentsleft

	DDSFRQ COOLDDS, coolingFreq 
	DDSFRQ TickleDDS, tickleFreq
	TRIGGER ddsApplyTrigger
	
cooling: NOP
	SHUTTERMASK coolingOnMask
	ASYNCSHUTTER coolingOn
	COUNTERMASK coolingCounter
	WAIT                             # for end of startup or last
	UPDATE coolingTime

	SHUTTERMASK coolingOffMask
	ASYNCSHUTTER coolingOff
	COUNTERMASK coolingOffCounter
	WAIT
	UPDATE epsilon
	DEC experimentsleft
	STWR experimentsleft
	JMPNZ cooling
	JMP scanloop
	
endlabel: LDWR endLabel
	WRITEPIPE
	END