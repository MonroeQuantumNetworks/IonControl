#define	SHUTR_REPUMP 2
#define SHUTR_OP_WAIT 138
#define	SHUTR_EXP   2
#define SHUTR_EXP_WAIT 10
#define SHUTR_EXP_WAIT_AFTER 10
#define DAC_ch_MOT_coil 0
#define DAC_ch_Bz 1
#define DAC_ch_MOT 3
#define DAC_ch_Dipole 9
#define DAC_ch_Bx 6
#define DAC_ch_By 7
#define DAC_ch_Repump 5
#define DAC_ch_OP 13
#define DDS_ch_MOT 3
#define DDS_ch_uWave 1
#define DDS_ch_OP 2
#define DDS_ch_Repump 0

var dataend 	   4000
var LOADIND        0
var us_DEPUMP      2
var addr		   0
var CHECKIND       0
var CHECKCOUNT     0
var DETECTCOUNT    0
var LOADCOUNT      0
var RAMPIND 	   0
var V_MOT          0
var F_MOT          0
var	SWITCH			0

# Atom reuse variables
var atomReuse 		0 		# keeps track of number of times atom is reused
var reuseAddr 		0 		# keeps track of current atomReuse address
var reuseBinNum		0		# keep track of number of atom reuse bins

# TODO: initialize memory used for storing counts during detection
	LDWR     	datastart
	STWR     	addr
	LDWR 		reuseDataStart 	# v
	STWR 		reuseAddr  		# set reuseAddr to the start address
	SHUTRVAR 	SHUTR_load
	DDSFRQ	 	DDS_ch_MOT, F_MOT_load
	DDSFRQ	 	DDS_ch_uWave, F_uWave_load
	DAC      	DAC_ch_MOT_coil, V_MOTcoil_load
	DAC		 	DAC_ch_Repump, V_Repump_load
	DAC	 	 	DAC_ch_MOT, V_MOT_load
	DAC		 	DAC_ch_Dipole, V_Dipole_load
	DAC		 	DAC_ch_Bx, V_Bx_load
	DAC		 	DAC_ch_By, V_By_load
	DAC		 	DAC_ch_Bz, V_Bz_load
	DACUP


# Initialize memory used for counts to 0
ini_countsMemory: NOP
	CLRW
	LDINDF 		addr					# v
	STWI    	       					# stores 0 to wherever reuseAddr is pointing
	INC    		addr 		      		# v
	STWR   		addr 					# increments addr
	CMP			dataend					# v
	JMPZ		ini_countsMemory		# loop if addr <= dataend
	LDWR 	 	datastart 	 			# v
	STWR 	    addr 	 				# addr = datastart

# Set atom reuse memory section to 0
ini_atomReuseMemory: NOP
	CLRW
	LDINDF 		reuseAddr				# v
	STWI    	       					# stores 0 to wherever reuseAddr is pointing
	INC    		reuseAddr       		# v
	STWR   		reuseAddr 				# increments reuseAddr
	CMP			reuseDataEnd			# v
	JMPZ		ini_atomReuseMemory		# loop if reuseAddr <= reuseDataEnd
	LDWR 	 	reuseDataStart 			# v
	STWR 	    reuseAddr  				# reuseAddr = reuseDataStart
	CLRW
	STWR		reuseBinNum

ini_load: NOP
	CLRW
	STWR    	LOADIND
	CLRW								#
	STWR		atomReuse				# reset atomReuse for new atom
	SHUTRVAR	SHUTR_load
	DDSFRQ		DDS_ch_MOT, F_MOT_load
	DDSFRQ		DDS_ch_uWave, F_uWave_load
	DAC     	DAC_ch_MOT_coil, V_MOTcoil_load
	DAC			DAC_ch_Repump, V_Repump_load
	DAC	 		DAC_ch_MOT, V_MOT_load
	DAC			DAC_ch_Dipole, V_Dipole_load
	DAC			DAC_ch_Bx, V_Bx_load
	DAC			DAC_ch_By, V_By_load
	DAC			DAC_ch_Bz, V_Bz_load
	DACUP
	JMP		 load

load: NOP
    COUNT    us_LoadDetectTime
	STWR	 LOADCOUNT
	INC		 LOADIND
	STWR	 LOADIND
	CMP		 LOADREP
	JMPNZ    done
	LDWR     LOADCOUNT
	CMP		 LOADTHOLD
	JMPZ     load
	JMPNZ    set_shutter_save

set_shutter_save: NOP
	SHUTRVAR	SHUTR_wait5
	DAC	 		DAC_ch_MOT, V_MOT_wait5 # changed from V_MOT_exp_end CWC 09262012
	DACUP
	DELAY 	us_Time_wait5
	INC 	atomReuse		# v
	STWR 	atomReuse		# increment and store atom reuse
	LDWR	DETECTCOUNT
	LDINDF  addr
	STWI                    #stores data to wherever addr is pointing
	INC     addr            #increments address
	STWR    addr
	CMP     dataend
	JMPZ    ini_load		 # ini_load, ini_sub_D_cooling
	JMPNZ	done
	
done: NOP
	LDWR 		reuseBinNum		# v
	LDINDF		reuseBinAddr	# v
	STWI						# store reuseBinNum in memory location 'reuseBinAddr'
	SHUTRVAR SHUTR_load
	DDSFRQ	 DDS_ch_MOT, F_MOT_load
	DAC      DAC_ch_MOT_coil, V_MOTcoil_load
	DAC		 DAC_ch_Repump, V_Repump_load
	DAC	 	 DAC_ch_MOT, V_MOT_load
	DAC		 DAC_ch_Dipole, V_Dipole_load
	DAC		 DAC_ch_Bx, V_Bx_load
	DAC		 DAC_ch_By, V_By_load
	DAC		 DAC_ch_Bz, V_Bz_load
	DACUP
	END

	