#define SHUTR_LOAD 6
#define SHUTR_WAIT 2
#define SHUTR_COOL 2
#define SHUTR_OP 3
#define SHUTR_DEPUMP 2
#define	SHUTR_REPUMP 4
#define SHUTR_DETECT 2
#define	SHUTR_EXP	3
#define SHUTR_CHECK 6
#define DAC_ch_MOT_coil 0
#define DAC_ch_Repump 1
#define DAC_ch_MOT 3
#define DAC_ch_Dipole 5
#define DAC_ch_Bx 6
#define DAC_ch_By 7
#define DAC_ch_Bz 9
#define DAC_ch_OP 13

#define DDS_ch_MOT 0
#define DDS_ch_REPUMP 1
#define DDS_ch_OP 2
#define DDS_ch_uWave 3

var F_MOT 68.14
var V_MOT 3.5
var RAMPIND 0

	SHUTR 	 SHUTR_COOL
	DAC	 	 DAC_ch_MOT, V_MOT_cool
	DACUP
	CLRW
	STWR     RAMPIND
	LDWR	 V_MOT_cool
	STWR	 V_MOT
	JMP	 	 sub_D_cooling
	
sub_D_cooling: NOP
	DELAY  	 us_RAMP_T
	LDWR	 V_MOT
	ADDW	 V_INC
	STWR	 V_MOT
	INC	     RAMPIND
	STWR	 RAMPIND
	CMP	     RAMPTOT
	JMPNZ    done
	DAC	 	 DAC_ch_MOT, V_MOT
	DACUP
	JMP	 	 sub_D_cooling
	
done: NOP 
	SHUTR 	 SHUTR_COOL
	DAC	 	 DAC_ch_MOT, V_MOT_load
	DACUP
	END 