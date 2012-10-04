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
#define DDS_ch_MOT 0
#define DDS_ch_uWave 1
#define DDS_ch_OP 2
#define DDS_ch_Repump 3

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
#var reuseDataStart 	3000 	# first memory location for stored value
#var reuseDataEnd 	3099 	# largest allowed memory location
var reuseAddr 		0 		# keeps track of current atomReuse address
var reuseBinNum		0		# keep track of number of atom reuse bins
#var reuseBinAddr    2999	# store reuseBinNum at this memory location

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
	LDWR		LOAD_SWITCH
	CMP			SWITCH
	JMPZ		ini_sub_D_cooling
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
	JMPNZ    wait1

wait1: NOP 
	DAC	 	 DAC_ch_MOT, V_MOT_comp 
	DACUP 
	DELAY	 us_MotServo_wait
	SHUTRVAR SHUTR_wait1
	DDSFRQ	 DDS_ch_MOT, F_MOT_cool
	DDSFRQ	 DDS_ch_uWave, F_uWave_cool
	DAC		 DAC_ch_Repump, V_Repump_cool
	DAC      DAC_ch_MOT_coil, V_MOTcoil_cool
	DAC	 	 DAC_ch_MOT, V_MOT_cool
	DAC		 DAC_ch_Dipole, V_Dipole_cool
	DAC		 DAC_ch_Bx, V_Bx_cool
	DAC		 DAC_ch_By, V_By_cool
	DAC		 DAC_ch_Bz, V_Bz_cool
	DACUP
	DELAY	 us_Time_wait1
	JMP		 ini_sub_D_cooling

ini_sub_D_cooling: NOP
	LDWR	 COOL_SWITCH
	CMP		 SWITCH
	JMPZ	 OPump
	DAC      DAC_ch_MOT_coil, V_MOTcoil_cool
	DAC	 	 DAC_ch_MOT, V_MOT_cool
	DAC		 DAC_ch_Repump, V_Repump_cool
	DAC		 DAC_ch_Dipole, V_Dipole_cool
	DAC		 DAC_ch_Bx, V_Bx_cool
	DAC		 DAC_ch_By, V_By_cool
	DAC		 DAC_ch_Bz, V_Bz_cool
	DACUP
	DDSFRQ	 DDS_ch_MOT, F_MOT_cool
	DELAY	 us_cool_delay
	SHUTRVAR SHUTR_cool
	CLRW
	STWR     RAMPIND
	LDWR 	 F_MOT_cool
	STWR	 F_MOT
	LDWR	 V_MOT_cool
	STWR	 V_MOT
	JMP	 	 sub_D_cooling

sub_D_cooling: NOP	#Ramp MOT beam freq. and power.
	LDWR	 F_MOT
	ADDW	 F_INC
	STWR	 F_MOT
	LDWR	 V_MOT
	ADDW	 V_INC
	STWR	 V_MOT
	DELAY  	 us_RAMP_T
	INC		 RAMPIND
	STWR	 RAMPIND
	CMP	 	 RAMPTOT
	JMPNZ    wait2
	DDSFRQ	 DDS_ch_MOT, F_MOT
	DAC	 	 DAC_ch_MOT, V_MOT
	DACUP
	JMP	 	 sub_D_cooling

wait2: NOP
	LDWR	 WAIT2_SWITCH
	CMP		 SWITCH
	JMPZ	 OPump
	DAC      DAC_ch_MOT_coil, V_MOTcoil_wait2
	DAC	 	 DAC_ch_MOT, V_MOT_wait2
	DAC		 DAC_ch_Repump, V_Repump_wait2
	DAC		 DAC_ch_Dipole, V_Dipole_wait2
	DAC		 DAC_ch_Bx, V_Bx_wait2
	DAC		 DAC_ch_By, V_By_wait2
	DAC		 DAC_ch_Bz, V_Bz_wait2
	DACUP
	DDSFRQ	 DDS_ch_MOT, F_MOT_wait2
	DELAY	 us_Time_wait2
	SHUTRVAR SHUTR_wait2	
	
OPump: NOP
	LDWR	 OP_SWITCH
	CMP		 SWITCH
	JMPZ	 wait3
	DDSFRQ	 DDS_ch_uWave, F_uWave_op
	DDSFRQ	 DDS_ch_OP, F_OP_op
	DDSAMP	 DDS_ch_OP, A_OP_op
	DAC		 DAC_ch_MOT, V_MOT_op
	DAC		 DAC_ch_Repump, V_Repump_op
	DAC		 DAC_ch_Bx, V_Bx_op
	DAC		 DAC_ch_By, V_By_op
	DAC		 DAC_ch_Bz, V_Bz_op
	DAC		 DAC_ch_OP, V_OP_op
	DACUP
	SHUTRVAR SHUTR_op
	DELAY	 us_Time_op 	#SHUTR	 SHUTR_OP_WAIT
	SHUTRVAR SHUTR_wait3
	
wait3: NOP
	LDWR	 WAIT3_SWITCH
	CMP		 SWITCH
	JMPZ	 Exp
	DAC      DAC_ch_MOT_coil, V_MOTcoil_wait3
	DAC	 	 DAC_ch_MOT, V_MOT_wait3
	DAC		 DAC_ch_Repump, V_Repump_wait3
	DAC		 DAC_ch_Dipole, V_Dipole_wait3
	DAC		 DAC_ch_Bx, V_Bx_wait3
	DAC		 DAC_ch_By, V_By_wait3
	DAC		 DAC_ch_Bz, V_Bz_wait3
	DACUP
	DDSFRQ	 DDS_ch_MOT, F_MOT_wait3
	DELAY	 us_Time_wait3
	SHUTRVAR SHUTR_wait3
	
#TODO: Figure out what do to do with SHUT_exp_after (place control in GUI?) 
Exp: NOP
	LDWR	 EXP_SWITCH
	CMP		 SWITCH
	JMPZ	 wait4
	DDSFRQ	 DDS_ch_MOT, F_MOT_exp
	DDSFRQ	 DDS_ch_uWave, F_uWave_exp
	DAC	 	 DAC_ch_MOT, V_MOT_exp
	DAC		 DAC_ch_Repump, V_Repump_exp	# DAC		 DAC_ch_Dipole, V_Dipole_exp
	DAC		 DAC_ch_Bx, V_Bx_exp
	DAC		 DAC_ch_By, V_By_exp
	DAC		 DAC_ch_Bz, V_Bz_exp
	DACUP
    SHUTRVAR SHUTR_exp
	DELAY	 us_Time_exp 			#DDSFRQ	 DDS_ch_MOT, F_MOT_exp
	SHUTRVAR SHUTR_exp_after
	
wait4: NOP
	LDWR	 WAIT4_SWITCH
	CMP		 SWITCH
	JMPZ	 Detect
	DAC      DAC_ch_MOT_coil, V_MOTcoil_wait4
	DAC	 	 DAC_ch_MOT, V_MOT_wait4
	DAC		 DAC_ch_Repump, V_Repump_wait4 # DAC	 DAC_ch_Dipole, V_Dipole_wait4
	DAC		 DAC_ch_Bx, V_Bx_wait4
	DAC		 DAC_ch_By, V_By_wait4
	DAC		 DAC_ch_Bz, V_Bz_wait4
	DACUP
	DDSFRQ	 DDS_ch_MOT, F_MOT_wait4
	DELAY	 us_Time_wait4
	SHUTRVAR SHUTR_wait4
	
Detect: NOP
	DAC	 	 DAC_ch_MOT, V_MOT_detect
	DAC		 DAC_ch_Repump, V_Repump_detect	# DAC	 DAC_ch_Dipole, V_Dipole_detect
	DAC		 DAC_ch_Bx, V_Bx_detect
	DAC		 DAC_ch_By, V_By_detect
	DAC		 DAC_ch_Bz, V_Bz_detect
	DACUP
	DDSFRQ	 DDS_ch_MOT, F_MOT_detect
	SHUTRVAR SHUTR_detect

	COUNT    us_Time_detect

	STWR     DETECTCOUNT

	CMP		 CHECKTHOLD
	JMPZ	 ini_check
	JMPNZ	 save_data

save_data: NOP
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
	JMPZ    load_decision		 # ini_load, ini_sub_D_cooling
	JMPNZ	save_atomReuse
	
load_decision: NOP
	LDWR	 CHECK_SWITCH
	CMP		 SWITCH
	JMPZ	 ini_load
	JMPNZ    ini_sub_D_cooling

ini_check: NOP

	LDWR	 CHECK_SWITCH # blah 	
	CMP		 SWITCH
	JMPZ	 save_data
	CLRW
	STWR     CHECKIND
	SHUTRVAR SHUTR_wait5
	DAC	 	 DAC_ch_MOT, V_MOT_check
	DAC		 DAC_ch_Repump, V_Repump_check
	DAC		 DAC_ch_Dipole, V_Dipole_check
	DAC		 DAC_ch_Bx, V_Bx_check
	DAC		 DAC_ch_By, V_By_check
	DAC		 DAC_ch_Bz, V_Bz_check
	DACUP
	DDSFRQ	 DDS_ch_MOT, F_MOT_check
	JMP		 check

check: NOP
	SHUTRVAR	SHUTR_check
    COUNT		us_Time_check
	SHUTRVAR	SHUTR_wait6
	STWR		CHECKCOUNT
    CMP     	CHECKTHOLD
	JMPNZ		save_data
	INC 		CHECKIND
	STWR    	CHECKIND
	CMP			CHECKREP
	JMPZ    	check
	JMPNZ		save_atomReuse # JMPNZ    ini_load

save_atomReuse: NOP
	INC 		reuseBinNum		# v
	STWR		reuseBinNum		# increment number of bins where atomReuse is store
	LDWR 		atomReuse 	 	# v
	LDINDF 		reuseAddr		# v
	STWI    	       			# stores atomReuse to wherever reuseAddr is pointing
	INC    		reuseAddr       # v
	STWR   		reuseAddr 		# increments reuseAddr
	CLRW 						# v
	STWR 		atomReuse 		# atomReuse = 0
	LDWR 		addr
	CMP 		dataend
	JMPZ   		ini_load 		# addr <= dataend (load a new atom)
	JMPNZ  		done 			# addr > dataend (you have reached end or memory, finish sequence)

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
