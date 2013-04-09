###########################################################################
#
#   PMTtest.pp -- Jan 17 2008
#  tests if talking to PMT.



#define DDS729	   0
#define DDSDoppler 1

var dataend 4000
var addr 0
var sample 0
var SP_counter 0
var IB 6
var SC_counter 0
var us_sctime 0
	
	DDSFRQ		DDSDoppler, F_Red_Doppler
	DDSAMP	 	DDSDoppler, A_Red_Doppler
	LDWR     	datastart
	STWR     	addr
	DDSFRQ	 	DDS729, F_729_off
	DDSAMP		DDS729, A_729_on

init: NOP
	SHUTRVAR	SHUTR_854_on
	DDSFRQ		DDSDoppler, F_Detect
	DDSAMP	 	DDSDoppler, A_Detect  
	COUNT    	us_Detect
    SHUTRVAR   	SHUTR_854_off 	
	CMP      	IB 	# if counts greater than threshold w=w else W=0
	JMPZ     	init  		# if w=0 back to init
	
cool: NOP
	DDSAMP	 	DDSDoppler, A_Blue_Doppler
	DDSFRQ   	DDSDoppler, F_Blue_Doppler
	DELAY	 	us_Doppler
	DDSFRQ		DDSDoppler, F_Doppler_off
	
	LDWR     	SP_loops      # Number of spin polarization Loops
	JMPZ	 	exp           # if SP_loops=0 it skips to exp
	STWR     	SP_counter    # put SP_loops into counter  
	
SP: NOP                       
	DDSFRQ	 	DDS729, F_729_SP
	DELAY    	us_729_SP
	DDSFRQ	 	DDS729, F_729_off
	SHUTRVAR 	SHUTR_repump
	DELAY	 	us_repump
	SHUTRVAR 	SHUTR_854_off
	DEC      	SP_counter
	STWR     	SP_counter
	JMPNZ    	SP

	LDWR	 SC_loops
    JMPZ     exp	# if SC_loops=0 it skips to exp
	STWR	 SC_counter # put SC_loops into counter
	LDWR     us_729_SC
	STWR     us_sctime
	
SC: NOP	
	DDSFRQ	 	DDS729, F_729_SC
	DELAY    	us_729_SC
	DDSFRQ	 	DDS729, F_729_off
	SHUTRVAR 	SHUTR_repump
	DELAY	 	us_repump
	SHUTRVAR 	SHUTR_854_off
	
	LDWR     us_sctime
	ADDW     us_SCINC
	STWR     us_sctime
	DEC      SC_counter
	STWR     SC_counter
	JMPZ     exp
	JMPNZ    SC
	

	
exp: NOP
	DDSFRQ	 	DDS729, F_729   #SHUTRVAR   	SHUTR_driveD5half
	DELAY	 	us_729
	DDSFRQ		DDS729, F_729_off  #SHUTRVAR    SHUTR_detect
	SHUTRVAR	SHUTR_854_on
	DELAY		us_854
	SHUTRVAR	SHUTR_854_off
	DDSFRQ		DDSDoppler, F_Detect
	DDSAMP	 	DDSDoppler, A_Detect
	COUNT    	us_Detect #SHUTR    0
	DDSFRQ		DDSDoppler, F_Red_Doppler
	DDSAMP	 	DDSDoppler, A_Red_Doppler
	SHUTRVAR	SHUTR_repump
	DELAY		us_repump
	SHUTRVAR	SHUTR_854_off
	LDINDF   	addr
	STWI                     #stores data to wherever addr is pointing
	INC      	addr            #increments address DELAY    ns_delay
	STWR     	addr
	CMP      	dataend
	JMPZ     	init

	DDSFRQ	 	DDS729, F_729_off
	DDSAMP		DDS729, A_729_off
	END 
