###########################################################################
#
#   PMTtest.pp -- Jan 17 2008
#  tests if talking to PMT.



#define REDDDS	   0
#define BLUEDDS	   1  #Changed Craig Nov 15 2010 for new AOM
#define IRDDS	   4

#var datastart 3900
var dataend 4000
var addr 0
var sample 0
	
	SHUTR	 0
	LDWR     datastart
	STWR     addr

init_f: NOP
	SHUTRVAR   SHUTR_TEST
	COUNT    us_MeasTime #SHUTR    0
	DELAY	 ms_WAIT
	LDINDF   addr
	STWI                     #stores data to wherever addr is pointing
	INC      addr            #increments address DELAY    ns_delay
	STWR     addr
	CMP      dataend
	JMPZ     init_f


	END 
