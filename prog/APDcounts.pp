###########################################################################
#
#   PMTtest.pp -- Jan 17 2008
#  tests if talking to PMT.



#define REDDDS	   0
#define BLUEDDS	   1  #Changed Craig Nov 15 2010 for new AOM
#define IRDDS	   4
#define SHUTR1     13
#define SHUTR2      3

#var datastart 3900
var dataend 4000
var addr 0
var sample 0

	LDWR     datastart
	STWR     addr

init_f: NOP
    SHUTR   SHUTR1
	COUNT   us_MeasTime
	LDINDF   addr
	STWI                     #stores data to wherever addr is pointing
	INC      addr            #increments address DELAY    ns_delay
	STWR     addr
	CMP      dataend
	JMPZ     init_f


	END
