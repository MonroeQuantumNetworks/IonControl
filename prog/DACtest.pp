#define DAC_ch_0 0
#define DAC_ch_1 1
var V_DAC_0 1.9
var V_DAC_1 2.5
var V_dv_0 0.2
var V_dv_1 0.4
var RAMPIND 0
 

loop: NOP
 LDWR	 V_DAC_0
 ADDW	 V_dv_0
 STWR	 V_DAC_0
 LDWR	 V_DAC_1
 ADDW	 V_dv_1
 STWR	 V_DAC_1
 DAC DAC_ch_0, V_DAC_0
 DAC DAC_ch_1, V_DAC_1
 DACUP
 DELAY   us_RAMP_T
 INC     RAMPIND
 STWR	 RAMPIND
 CMP 	 RAMPTOT
 JMPNZ   done
 JMPZ    loop

 DAC DAC_ch_0, V_DAC_0
 DAC DAC_ch_1, V_DAC_1
 DACUP
 DELAY   us_RAMP_T
 LDWR	 V_DAC_0
 ADDW	 V_dv_0
 STWR	 V_DAC_0
 LDWR	 V_DAC_1
 ADDW	 V_dv_1
 STWR	 V_DAC_1
 DAC DAC_ch_0, V_DAC_0
 DAC DAC_ch_1, V_DAC_1
 DACUP 
 DAC DAC_ch_0, V_MOT_load
 DAC DAC_ch_1, V_MOT_cool
 DACUP 
done: NOP
 END 