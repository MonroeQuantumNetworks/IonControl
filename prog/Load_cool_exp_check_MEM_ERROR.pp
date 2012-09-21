## Generic pulse sequence for AQC

#define SHUTR_LOAD 7
#define SHUTR_WAIT 0
#define SHUTR_COOL 7
#define SHUTR_OP 2
#define SHUTR_DEPUMP 6
#define	SHUTR_REPUMP 2
#define SHUTR_DETECT 7
#define	SHUTR_EXP	0
#define SHUTR_CHECK 15
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



var dataend 	   4000
var LOADIND        0
#var LOADREP        8000
#var LOADTHOLD      6
#var ms_WAIT        1
var us_DEPUMP      2
#var us_REPUMP      1
#var us_OP		   240
#var us_CheckTime   500
#var us_LoadDetectTime 500
var addr		   0
#var CHECKTHOLD     3
#var CHECKREP       4
var CHECKIND       0
var CHECKCOUNT     0
var DETECTCOUNT    0
var LOADCOUNT      0
#var V_MOTcoil_load 1.2
#var V_REPUMP_load  1.5
#var F_MOT_load	   68.14
#var V_Dipole_load  3.2
#var V_MOT_load	   1.6
#var V_Bx_load	   0.0
#var V_By_load	   0.0
#var V_Bz_load	   0.38

#var V_MOTcoil_cool 0.0
#var V_REPUMP_cool  1.5
#var F_MOT_cool	   68.14
#var V_Dipole_cool  3.2
#var V_MOT_cool	   0.0
#var V_Bx_cool	   0.625
#var V_By_cool	   0.55
#var V_Bz_cool	   0.5

#var V_MOTcoil_op   0.0
#var V_REPUMP_op	   1.5
#var F_MOT_op	   68.14
#var V_Dipole_op    3.2
#var V_MOT_op	   0.0
#var V_Bx_op	   	   0.625
#var V_By_op	       0.55
#var V_Bz_op	       0.5
#var V_OP_op		   1.0

#var V_MOTcoil_Exp  0.0
#var V_REPUMP_Exp   1.5
#var F_MOT_Exp	   68.14
#var V_Dipole_Exp   3.2
#var V_MOT_Exp	   0.0
#var V_Bx_Exp	   0.625
#var V_By_Exp	   0.55
#var V_Bz_Exp	   0.5

#var V_MOTcoil_Detect  0.0
#var V_REPUMP_Detect   1.5
#var F_MOT_Detect	   68.14
#var V_Dipole_Detect   3.2
#var V_MOT_Detect	   0.0
#var V_Bx_Detect	   0.625
#var V_By_Detect	   0.55
#var V_Bz_Detect	   0.5

#var V_MOTcoil_Check  0.0
#var V_REPUMP_Check   1.5
#var F_MOT_Check	   68.14
#var V_Dipole_Check   3.2
#var V_MOT_Check	   0.0
#var V_Bx_Check	   0.625
#var V_By_Check	   0.55
#var V_Bz_Check	   0.5

var RAMPIND 	   0
#var RAMPTOT        10
#var us_RAMP_T      20
var V_MOT          1.3
var F_MOT          68.14
#var F_INC         -0.15
#var V_INC         -0.1

	LDWR     datastart
	STWR     addr
	SHUTR	 SHUTR_LOAD
	DDSFRQ	 DDS_ch_MOT, F_MOT_load
	DDSFRQ	 DDS_ch_REPUMP, F_REPUMP_load
	DAC      DAC_ch_MOT_coil, V_MOTcoil_load
	DAC		 DAC_ch_Repump, V_Repump_load
	DAC	 	 DAC_ch_MOT, V_MOT_load
	DAC		 DAC_ch_Dipole, V_Dipole_load
	DAC		 DAC_ch_Bx, V_Bx_load
	DAC		 DAC_ch_By, V_By_load
	DAC		 DAC_ch_Bz, V_Bz_load
	DACUP

ini_load: NOP
	CLRW
	STWR     LOADIND
	SHUTR	 SHUTR_LOAD
	DDSFRQ	 DDS_ch_MOT, F_MOT_load
	DDSFRQ	 DDS_ch_REPUMP, F_REPUMP_load
	DAC      DAC_ch_MOT_coil, V_MOTcoil_load
	DAC		 DAC_ch_Repump, V_Repump_load
	DAC	 	 DAC_ch_MOT, V_MOT_load
	DAC		 DAC_ch_Dipole, V_Dipole_load
	DAC		 DAC_ch_Bx, V_Bx_load
	DAC		 DAC_ch_By, V_By_load
	DAC		 DAC_ch_Bz, V_Bz_load
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
	JMPNZ    wait

wait: NOP
	SHUTR 	 SHUTR_WAIT
	DDSFRQ	 DDS_ch_MOT, F_MOT_cool
	DDSFRQ	 DDS_ch_REPUMP, F_REPUMP_cool
	DAC      DAC_ch_MOT_coil, V_MOTcoil_cool
	DAC		 DAC_ch_Repump, V_Repump_cool
	DAC	 	 DAC_ch_MOT, V_MOT_cool
	DAC		 DAC_ch_Dipole, V_Dipole_cool
	DAC		 DAC_ch_Bx, V_Bx_cool
	DAC		 DAC_ch_By, V_By_cool
	DAC		 DAC_ch_Bz, V_Bz_cool
	DACUP
	DELAY	 ms_WAIT
	JMP		 ini_sub_D_cooling

ini_sub_D_cooling: NOP
	SHUTR 	 SHUTR_COOL
	DDSFRQ	 DDS_ch_MOT, F_MOT_cool
	DAC		 DAC_ch_Repump, V_Repump_cool
	DAC	 	 DAC_ch_MOT, V_MOT_cool
	DAC		 DAC_ch_Dipole, V_Dipole_cool
	DAC		 DAC_ch_Bx, V_Bx_cool
	DAC		 DAC_ch_By, V_By_cool
	DAC		 DAC_ch_Bz, V_Bz_cool
	DACUP
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
	JMPNZ    OPump
	DDSFRQ	 DDS_ch_MOT, F_MOT
	DAC	 	 DAC_ch_MOT, V_MOT
	DACUP
	JMP	 	 sub_D_cooling

OPump: NOP
	DDSFRQ	 DDS_ch_REPUMP, F_REPUMP_op
	DDSFRQ	 DDS_ch_OP, F_OP_op
	DAC		 DAC_ch_Repump, V_Repump_op
	DAC		 DAC_ch_Bx, V_Bx_op
	DAC		 DAC_ch_By, V_By_op
	DAC		 DAC_ch_Bz, V_Bz_op
	DAC		 DAC_ch_OP, V_OP_op
	DACUP
	SHUTR    SHUTR_OP
	DELAY	 us_OP
	SHUTR	 SHUTR_EXP
	JMP		 Exp

Exp: NOP
	DDSFRQ	 DDS_ch_MOT, F_MOT_exp
	DDSFRQ	 DDS_ch_REPUMP, F_REPUMP_exp
	DDSFRQ	 DDS_ch_uWave, F_uWave_exp
	DAC		 DAC_ch_Repump, V_Repump_exp
	DAC	 	 DAC_ch_MOT, V_MOT_exp
	DAC		 DAC_ch_Dipole, V_Dipole_exp
	DAC		 DAC_ch_Bx, V_Bx_exp
	DAC		 DAC_ch_By, V_By_exp
	DAC		 DAC_ch_Bz, V_Bz_exp
	DACUP
    SHUTR    SHUTR_EXP
	DELAY	 us_EXP
	SHUTR	 SHUTR_WAIT
	DDSFRQ	 DDS_ch_MOT, F_MOT_Detect
	DAC	 	 DAC_ch_MOT, V_MOT_Detect
	DAC		 DAC_ch_Dipole, V_Dipole_Detect
	DAC		 DAC_ch_Bx, V_Bx_Detect
	DAC		 DAC_ch_By, V_By_Detect
	DAC		 DAC_ch_Bz, V_Bz_Detect
	DACUP
	SHUTR	 SHUTR_DETECT
	COUNT    us_MeasTime
	STWR     DETECTCOUNT
	CMP		 CHECKTHOLD
	JMPZ	 ini_check
	JMPNZ	 save_data

save_data: NOP
	LDWR	 DETECTCOUNT
	LDINDF   addr
	STWI                     #stores data to wherever addr is pointing
	INC      addr            #increments address
	STWR     addr
	CMP      dataend
	JMPZ     ini_sub_D_cooling
	JMPNZ	 done


ini_check: NOP
	CLRW
	STWR     CHECKIND
	SHUTR	 SHUTR_REPUMP
	DELAY	 us_Repump
	JMP		 check

check: NOP
	SHUTR	 SHUTR_CHECK
    COUNT	 us_CheckTime
	SHUTR	 SHUTR_WAIT
	STWR	 CHECKCOUNT
    CMP      CHECKTHOLD
	JMPNZ	 save_data
	INC 	 CHECKIND
	STWR     CHECKIND
	CMP		 CHECKREP
	JMPZ     check
	JMPNZ    ini_load

done: NOP
	SHUTR	 SHUTR_LOAD
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
