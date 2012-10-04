#define TESTDDS 1
var datastart 3900    #defines where to store counts
var A_DDS2  1000
var F_DDS2 1.7 
var F_INC -0.15
var dataend 4000
var addr 0
var sample 0
var RAMPIND 0
var RAMPINC 35
var RAMPTOT 10
var us_RAMPT 20

	LDWR     datastart
	STWR     addr

init_f: NOP
	SHUTR	 1
	DDSAMP	 TESTDDS, A_DDS2
	JMP		 ramp

ramp: NOP
	LDWR	 F_DDS2
	ADDW	 F_INC
	STWR	 F_DDS2
	DELAY  	 us_RAMPT
	INC		 RAMPIND
	STWR	 RAMPIND
	CMP	 	 RAMPTOT
	JMPNZ    detect
	DDSFRQ	 TESTDDS, F_DDS2
	JMP	 ramp
	
	

detect: NOP
	SHUTR	 0
	DELAY	 us_MeasTime
	SHUTR	 1
	DDSAMP	 TESTDDS, A_DDS1
	COUNT    us_MeasTime
    STWR     sample         #stores data from readout into W register

	LDINDF   addr
	LDWR     sample
	STWI                     #stores data to wherever addr is pointing
	INC      addr            #increments address 
 	STWR     addr
	CMP      dataend
	JMPZ     detect
	SHUTR    0
 END 