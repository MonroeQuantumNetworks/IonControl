###########################################################################
#  Take the bright histogram

#define SHUTR_LOAD 7
#define SHUTR_WAIT 7
#define SHUTR_DETECT 7
#define SHUTR_CHECK 7

var dataend 	   4000
var LOADIND        0
#var LOADREP        8000
#var LOADTHOLD      15
#var MS_WAIT        1
var addr		   0
#var CHECKTHOLD     3
#var CHECKREP       4
var CHECKIND       0
var CHECKCOUNT     0
var DETECTCOUNT 0
var LOADCOUNT 0

	LDWR     datastart
	STWR     addr
	SHUTR	 SHUTR_LOAD

ini_load: NOP
	CLRW
	STWR     LOADIND
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
	DELAY	 ms_WAIT
	JMP		 detect

detect: NOP
	SHUTR	 SHUTR_DETECT
	COUNT    us_MeasTime
	STWR     DETECTCOUNT
	LDINDF   addr
	STWI                     #stores data to wherever addr is pointing
	INC      addr            #increments address
	STWR     addr
	LDWR     DETECTCOUNT
	CMP		 CHECKTHOLD
	JMPZ     ini_check
	LDWR	 addr
	CMP      dataend
	JMPZ     detect
	JMPNZ	 done

ini_check: NOP
	CLRW
	STWR     CHECKIND
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
