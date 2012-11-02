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

	LDWR     datastart
	STWR     addr	
		
init_f: NOP
	SHUTR    1
	SHUTR    0
	DELAY    ns_delay
	SHUTR    1
		
	END
