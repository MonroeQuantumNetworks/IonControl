## Take the dark histogram

#define SHUTR_LOAD 6
#define SHUTR_WAIT 2
#define SHUTR_COOL 2
#define SHUTR_DEPUMP 2
#define	SHUTR_REPUMP 4
#define SHUTR_DETECT 2
#define SHUTR_CHECK 6
#define DAC_ch_MOTcoil 0
#define DAC_ch_Bx 1
#define DAC_ch_By 3
#define DAC_ch_Bz 5
#define DDS_ch_MOT 0


var dataend 	   4000
var LOADIND        0
var LOADREP        8000
var LOADTHOLD      6
var MS_WAIT        1
var MS_DEPUMP      2
var MS_REPUMP      1
var addr		   0
var CHECKTHOLD     3
var CHECKREP       4
var CHECKIND       0
var CHECKCOUNT     0
var DETECTCOUNT    0
var LOADCOUNT      0
var V_MOT_On	   4.99
var V_Bx_On		   1.0
var V_By_On		   0.5
var V_Bz_On		   0.2
var V_MOT_On	   0.0
var V_Bx_On		   0.3
var V_By_On		   0.3
var V_Bz_On		   0.1
var RAMPIND 	   0
var RAMPTOT        10
var us_RAMPT       20
var A_MOT_ini      1023
var F_MOT_ini      40.0
var A_MOT          1023
var F_MOT          40.0
var F_INC         -0.15
var A_INC         -10

	LDWR     datastart
	STWR     addr	
	SHUTR	 SHUTR_LOAD
	DDSFRQ	 DDS_ch_MOT, F_MOT_ini
	DDSAMP	 DDS_ch_MOT, A_MOT_ini
	DAC		 DAC_ch_MOTcoil, V_MOT_On
	DAC		 DAC_ch_Bx, V_Bx_On
	DAC		 DAC_ch_By, V_By_On
	DAC		 DAC_ch_Bz, V_Bz_On
	DACUP
	
ini_load: NOP
	CLRW
	STWR     LOADIND
	DDSFRQ	 DDS_ch_MOT, F_MOT_ini
	DDSAMP	 DDS_ch_MOT, A_MOT_ini
	DAC		 DAC_ch_MOTcoil, V_MOT_On
	DAC		 DAC_ch_Bx, V_Bx_On
	DAC		 DAC_ch_By, V_By_On
	DAC		 DAC_ch_Bz, V_Bz_On
	DACUP
	JMP		 load
	
	
load: NOP
    SHUTR    SHUTR_LOAD
    COUNT    us_MeasTime
	STWR	 LOADCOUNT
	INC		 LOADIND
	STWR	 LOADIND
	CMP		 LOADREP
	JMPNZ    done
	LDWR     LOADCOUNT
	CMP		 LOADTHOLD
	JMPZ     load
	JMPNZ    ini_detect
	
ini_detect: NOP
	SHUTR    SHUTR_WAIT
	DAC		 DAC_ch_MOTcoil, V_MOT_Off
	DAC		 DAC_ch_Bx, V_Bx_Off
	DAC		 DAC_ch_By, V_By_Off
	DAC		 DAC_ch_Bz, V_Bz_Off
	DACUP
	DELAY	 MS_WAIT
	JMP		 sub_D_cooling_ini

sub_D_cooling_ini: NOP
	CLRW
	STWR     RAMPIND
	SHUTR 	 SHUTR_COOL
	LDWR 	 F_MOTini
	STWR	 F_MOT
	LDWR	 A_MOTini
	STWR	 A_MOT
	JMP	 	 sub_D_cooling
	
sub_D_cooling: NOP
	LDWR	 F_MOT
	ADDW	 F_INC
	STWR	 F_MOT
	LDWR	 A_MOT
	ADDW	 A_INC
	STWR	 A_MOT
	DELAY  	 us_RAMPT
	INC		 RAMPIND
	STWR	 RAMPIND
	CMP	 	 RAMPTOT
	JMPNZ    detect
	DDSFRQ	 DDS_ch_MOT, F_MOT
	DDSAMP	 DDS_ch_MOT, A_MOT
	JMP	 	 sub_D_cooling
	
detect: NOP
    SHUTR    SHUTR_DEPUMP
	DELAY	 MS_DEPUMP
	SHUTR	 SHUTR_DETECT
	COUNT    us_MeasTime
	STWR     DETECTCOUNT
	SHUTR	 SHUTR_REPUMP
	DELAY	 MS_REPUMP
	SHUTR	 SHUTR_CHECK
	COUNT    us_MeasTime
	CMP		 CHECKTHOLD
	JMPZ     ini_check
	SHUTR	 7
	DELAY    us_MeasTime
	LDWR	 DETECTCOUNT
	LDINDF   addr
	STWI                     #stores data to wherever addr is pointing
	INC      addr            #increments address
	STWR     addr
	CMP      dataend
	JMPZ     detect
	JMPNZ	 done
	
ini_check: NOP
	CLRW
	STWR     CHECKIND
	SHUTR	 SHUTR_CHECK
	DELAY    MS_WAIT
	JMP		 check
	
check: NOP
	SHUTR	 SHUTR_CHECK
    COUNT	 us_MeasTime
	STWR	 CHECKCOUNT
    CMP      CHECKTHOLD
	JMPNZ	 detect
	INC 	 CHECKIND
	STWR     CHECKIND
	CMP		 CHECKREP
	JMPZ     check
	JMPNZ    ini_load

done: NOP
	SHUTR	 SHUTR_LOAD
	END
