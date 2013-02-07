###########################################################################
#
#   PMTtest.pp -- Jan 17 2008
#  tests if talking to PMT.



#define REDDDS	   0
#define BLUEDDS	   1  #Changed Craig Nov 15 2010 for new AOM
#define IRDDS	   4
#define COOLDDS    3

var datastart 3900, , address   # serves as tooltip
var dataend 4000, ,  address
var addr 0,     ,  address
var sample 0 , ,   address
var delay 0
var coolingFreq     210, MHz, parameter
var coolingOnMask     1,    , mask 
var coolingOn         1,    , shutter coolingMask
var coolingOffMask    1,    , mask
var coolingOff        0,    , shutter 
var coolingTime       1,  ms, parameter
var experiments     350,    , parameter
var epsilon         100,  ns, parameter

	LDWR     datastart
	STWR     addr	
	LDWR	 experiments
	STWR	 sample
cooling: NOP
	DDSFRQ COOLDDS, coolingFreq
	DDSFRQFINE COOLDDS, coolingFreq
	SHUTTERMASK coolingMask
	ASYNCSHUTTER coolingOn
	WAIT
	UPDATE coolingTime
	ASYNCSHUTTER coolingOff
	WAIT
	UPDATE epsilon
	DEC
	JMPNZ cooling
	
	END
