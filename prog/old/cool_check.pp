ini_cool_check: NOP 
	DDSFRQ	 DDS_ch_MOT, F_MOT_cool
	DAC      DAC_ch_MOT_coil, V_MOTcoil_cool
	DAC		 DAC_ch_Repump, V_Repump_cool
	DAC	 	 DAC_ch_MOT, V_MOT_cool
	DAC		 DAC_ch_Dipole, V_Dipole_cool
	DAC		 DAC_ch_Bx, V_Bx_cool
	DAC		 DAC_ch_By, V_By_cool
	DAC		 DAC_ch_Bz, V_Bz_cool
	DACUP
	SHUTR 	 SHUTR_COOL
	CLRW
	STWR     RAMPIND
	LDWR 	 F_MOT_cool
	STWR	 F_MOT
	LDWR	 V_MOT_cool
	STWR	 V_MOT
	JMP	 	 cool_check
	
cool_check: NOP	#Ramp MOT beam freq. and power.
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
	JMPNZ    check
	DDSFRQ	 DDS_ch_MOT, F_MOT
	DAC	 	 DAC_ch_MOT, V_MOT
	DACUP
	JMP	 	 cool_check	