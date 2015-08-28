//
// 120731	Correct Clock Select Decoding
// 121218	Change 

#ifndef	__MW2DEFS_H
#define __MW2DEFS_H


//#include <iostream>
//#include <cstdio>
//#include <ctime>
#include <Wtypes.h>
#include <sys/types.h>
#include "mw2Lib.h"

// [120724a]	Changed powerDac to attanuatorDac in the channel structure.

/*
	MW2 SPI Device Mapping

	----------------------------------------------------
	Channel		HMC833	    AD5621 DAC	   AD5621 DAC    
			  Synthesizer    (for VVA)      (for LPF)
	----------------------------------------------------
		0          0            2              4
	----------------------------------------------------
		1          1            3              5
	----------------------------------------------------
	EEPROM SPI view: 253
	       Register view: 254

	MW4062 clock selection
	----------------------------------------------------
	CLKSEL2	CLKSEL1 CLKSEL0
	----------------------------------------------------
	  0        0       0		internal osc for both ch.
	  0        0       1		PXI10 for both ch.
	  0        1       1		external for both ch.
	----------------------------------------------------
	  1        0       0		ch0=ext, ch1=int.
	  1        0       1		ch0=ext, ch1=PXI10
	----------------------------------------------------

	MW4062 filter bank selection
	----------------------------------------------
	FB0a FB0B FB1A FB1B FB1C
	FB2a FB2B FB3A FB3B FB3C		Freq (MHz)
	----------------------------------------------
	  0    0    x    x    x       f > 4000
	  1    0    x    x    x       3000 < f <= 4000 
	  0    1    x    x    x       (no filter)
	  1    1    1    0    0         145< f <= 195
	  1    1    0    1    0         195< f <= 280
	  1    1    1    0    0         195< f <= 280
	  1    1    1    1    0         280< f <= 460
	  1    1    0    0    1         460< f <= 770
	  1    1    1    0    1         770< f <= 1300
	  1    1    0    1    1        1300< f <= 1500
	  1    1    1    1    1        1500< f <= 3000
	 ---------------------------------------------


*/

// Reference clock default frequencies
#define MW2_CLK_INT_MHZ		((ULONG)50)		// 50 MHz internal clock 
#define MW2_CLK_EXT_MHZ		((ULONG)10)		// external clock, default 10 MHz
#define MW2_CLK_PXI_MHZ		((ULONG)10)		// 10 MHz PXI clock

// User commands for direct signal control
#define USR_CMD_CE			((ULONG)1)
#define USR_CMD_CLK_SELECT	((ULONG)2)
#define USR_CMD_FBANK_SELECT ((ULONG)3)
#define USR_CMD_RESET		((ULONG)6)
#define USR_CMD_AMP_SELECT ((ULONG)7)
// User commands for SPI device access
#define USR_CMD_READ_REG	((ULONG)4)
#define USR_CMD_WRITE_REG	((ULONG)5)

// PCI BAR0 interface memory layout 
//#define MW2_PHYSMEM_SIZE4		(0x0c00)	// 3K words (12 KBytes)
#define MW2_PHYSMEM_SIZE4		(0x0400)	// 3K words (12 KBytes)

// New host addresses of the PCI interface
// -- command registers
#define MW2_INTF_CARD_CMD_REG_ADDR4	(0)
#define MW2_INTF_CARD_SPI_WRITE_DATA (0x80)
#define MW2_INTF_CH0_CMD_REG_ADDR4	(0x100)
#define MW2_INTF_CH0_ADDR_REG_ADDR4	(0x101)
#define MW2_INTF_CH0_LEN_REG_ADDR4	(0x102)
// -- status registers
#define MW2_INTF_CARD_STATUS_REG_ADDR4	(0x200)
#define MW2_INTF_CARD_SPI_READ_DATA		(0x280)
#define MW2_INTF_CH0_STATUS_REG_ADDR4	(0x300)
#define MW2_INTF_CH0_INTR_REG_ADDR4		(0x301)
#define MW2_INTF_CARD_FWVERS_ADDR4	(0x804/4)

// Command and status register bits

#define MW2_CH_CARD			0xff				// means the card
#define MW2_CMD_CH_POS		8					// channel no at bit 8-15
#define MW2_CMD_CH_VAL(ch)	(ch << (MW2_CMD_CH_POS))

// PCI card control register bits
#define MW2_CMD_RESET		((ULONG)1 << 31)	// bit 31
#define MW2_CMD_FB1_LATCH	((ULONG)1 << 26)
#define MW2_CMD_FB0_LATCH	((ULONG)1 << 21)
#define MW2_CMD_CLKSEL_LATCH ((ULONG)1 << 18)	
#define MW2_CMD_AMP1_LATCH	((ULONG)1 << 17)	
#define MW2_CMD_AMP0_LATCH	((ULONG)1 << 16)	
#define MW2_CMD_CE_LATCH	((ULONG)1 << 8)		
#define MW2_CMD_REQ			((ULONG)1 << 0)		

// PCI channel control register bits
#define MW2_CTRL_FB3C	((ULONG)1 << 30)
#define MW2_CTRL_FB3B	((ULONG)1 << 29)
#define MW2_CTRL_FB3A	((ULONG)1 << 28)
#define MW2_CTRL_FB2B	((ULONG)1 << 27)
#define MW2_CTRL_FB2A	((ULONG)1 << 26)
#define MW2_CTRL_FB1C	((ULONG)1 << 25)
#define MW2_CTRL_FB1B	((ULONG)1 << 24)
#define MW2_CTRL_FB1A	((ULONG)1 << 23)
#define MW2_CTRL_FB0B	((ULONG)1 << 22)
#define MW2_CTRL_FB0A	((ULONG)1 << 21)
#define MW2_CTRL_FBCH1_ALL ((ULONG)MW2_CTRL_FB3C | MW2_CTRL_FB3B | MW2_CTRL_FB3A | MW2_CTRL_FB2B | MW2_CTRL_FB2A)
#define MW2_CTRL_FBCH0_ALL ((ULONG)MW2_CTRL_FB1C | MW2_CTRL_FB1B | MW2_CTRL_FB1A | MW2_CTRL_FB0B | MW2_CTRL_FB0A)
#define MW2_CTRL_CLKSEL2 ((ULONG)1 << 20)	
#define MW2_CTRL_CLKSEL1 ((ULONG)1 << 19)
#define MW2_CTRL_CLKSEL0 ((ULONG)1 << 18)
#define MW2_CTRL_AMPEN_1 ((ULONG)1 << 17)
#define MW2_CTRL_AMPEN_0 ((ULONG)1 << 16)
#define MW2_CTRL_CE_1	((ULONG)1 << 9)
#define MW2_CTRL_CE_0	((ULONG)1 << 8)
#define MW2_CMD_RD_FLAG	((ULONG)1)
#define MW2_CMD_WR_FLAG	((ULONG)0)
#define MW2_CE_ALL		((ULONG)0x07 << 8)

// 3-bit composite values for clock selection
//																  PO   CCCC CC
//																  XS   3322 11
//																  IC   BABA BA
//																  ||   |||| ||
//#define MW2_CTRL_CLK_OFFOFFOFF_VAL	0x00040800	// ---- ---- ---- 01-- 0000 10-- ---- ----
#define MW2_CTRL_CLK_INTINTOFF_VAL	0x00001400	// ---- ---- ---- 00-- 0001 01-- ---- ----
#define MW2_CTRL_CLK_INTINTINT_VAL	0x00005400	// ---- ---- ---- 00-- 0101 01-- ---- ----
#define MW2_CTRL_CLK_PXIPXIOFF_VAL	0x000C2000	// ---- ---- ---- 11-- 0010 00-- ---- ----
#define MW2_CTRL_CLK_EXTEXTOFF_VAL	0x0004AC00	// ---- ---- ---- 01-- 1010 11-- ---- ----
#define MW2_CTRL_CLK_EXTINTOFF_VAL	0x00009C00	// ---- ---- ---- 00-- 1001 11-- ---- ----
#define MW2_CTRL_CLK_PXIEXTOFF_VAL	0x000C5000	// ---- ---- ---- 11-- 0101 00-- ---- ----
/*
#define MW2_CTRL_CLK_NUE_VAL	(MW2_CTRL_CLKSEL1)						// Not Used
#define MW2_CTRL_CLK_PXI_VAL	(MW2_CTRL_CLKSEL1 | MW2_CTRL_CLKSEL0)
#define MW2_CTRL_CLK_EXTINT_VAL (MW2_CTRL_CLKSEL2)
#define MW2_CTRL_CLK_EXTEXT_VAL (MW2_CTRL_CLKSEL2 |					   MW2_CTRL_CLKSEL0)	// Not Used
#define MW2_CTRL_CLK_EXTNUE_VAL (MW2_CTRL_CLKSEL2 | MW2_CTRL_CLKSEL1)						// Not Used
#define MW2_CTRL_CLK_EXTPXI_VAL (MW2_CTRL_CLKSEL2 | MW2_CTRL_CLKSEL1 | MW2_CTRL_CLKSEL0)
*/
// PCI card status register bits
#define MW2_GA_POS			1					// slot no at bit 1-5
#define MW2_CMD_DONE		MW2_CMD_REQ

// PCI configuration info: vendor IDs and strings
#define VID_XILINX		0x10ee
#define VID_NI			0x1093
#define VID_MAGIQ		0xfb0b
#define STR_XILINX		"Xilinx"
#define STR_MAGIQ		"MagiQ"
// PCI configuration info: device IDs and strings
#define DID_MW4062		0x4062	
#define DID_MW4122		0x4122	
//#define DID_MW4062		0x4011	//%% temporarily MW3 board
//#define DID_MW4122		0x4011	//%% temporarily MW3 board

#define MW2_CALIB_CHANGE	-10.0	// Changing calibration table from hi to lo (-6dBm)

#define EEPROM_CMD_WREN	0x06

#define EEPROM_PAGE_SIZE	(USHORT)0x0020												// 32 bytes								

//=========================================
#define EEPROM_CARD_INFO_SIZE	(USHORT)0x0400
#define EEPROM_CHN_CALIB_SIZE	(USHORT)0x7C00
#define EEPROM_CARD_STAT_SIZE	(USHORT)0x0400

#define EEPROM_CARD_INFO	(USHORT)0x0000										//0x0000-0x03FF
#define EEPROM_CHN0			(USHORT)EEPROM_CARD_INFO	+ (USHORT)EEPROM_CARD_INFO_SIZE	//0x0400-0x7FFF
#define EEPROM_CHN1			(USHORT)EEPROM_CHN0			+ (USHORT)EEPROM_CHN_CALIB_SIZE	//0x8000-0xFBFF
#define EEPROM_CARD_STAT	(USHORT)EEPROM_CHN1			+ (USHORT)EEPROM_CHN_CALIB_SIZE	//0xFC00-0xFFFF

#define EEPROM_CARD_INFO_PAGE	EEPROM_CARD_INFO/EEPROM_PAGE_SIZE	// 0x0000
#define EEPROM_CHN0_PAGE		EEPROM_CHN0/EEPROM_PAGE_SIZE		// 0x0020
#define EEPROM_CHN1_PAGE		EEPROM_CHN1/EEPROM_PAGE_SIZE		// 0x0400
#define EEPROM_CARD_STAT_PAGE	EEPROM_CARD_STAT/EEPROM_PAGE_SIZE	// 0x07E0

// EEPROM CARD_INFO
#define EEPROM_DATE		0x0014												// 8 bytes								
#define EEPROM_TIME		0x001D												// 8 bytes								
#define EEPROM_FORMAT	0x0026												// 1 bytes								
#define EEPROM_CARD_REV	0x000B												// 1 bytes								

//Channel Calibration Data Offset is EEPROM_CH0 (0x0800-0x7FFF) or EEPROM_CH1 (0x8000-0xF7FF)							
#define EEPROM_FDAC_N	0x0000												// Address of Number of FDAC;	Max = 64;	Typical = 61					
#define EEPROM_PDAC_N	0x0001												// Address of Number of PDAC;	Max = 48;	Typical = 37					
#define EEPROM_FSTEP_N	0x0002												// Address of Number of FSTEP;	Max = 160;	Typical = 128

#define EEPROM_FDAC		0x0010												// FDAC Starting Address (0x0010)						
#define EEPROM_FDAC_L	0x0100												// FDAC Length	=256=	64 Freq*(2+2)					
#define EEPROM_FDAC_MAX	64

#define EEPROM_PDAC		EEPROM_FDAC+EEPROM_FDAC_L							// PDAD Address	0x0010+0x0100 = 0x0110					
#define EEPROM_PDAC_L	0x0060												// PDAC Length	=96	=	48 pdac * 2
#define EEPROM_PDAC_MAX	48

#define EEPROM_FSTEP	EEPROM_PDAC+EEPROM_PDAC_L							// FSTEP Starting Address 0x0110+0x0060 = 0x0170						
#define EEPROM_FSTEP_L	0x0140												// FSTEP Max Length	=320	160 Freq * 2					
#define EEPROM_FSTEP_MAX	160

#define EEPROM_CALIBH	EEPROM_FSTEP+EEPROM_FSTEP_L							// CalibData Address 0x0170+0x0140 = 0x02B0
#define EEPROM_CALIBH_L	EEPROM_FSTEP_L*EEPROM_PDAC_L/2						// Calibration Data Length 160*48*2= =15360(0x3C00)							

#define EEPROM_CALIBL	EEPROM_CALIBH+EEPROM_CALIBH_L						// CalibData Address 0x02B0+0x3C00 = 0x3EB0
#define EEPROM_CALIBL_L	EEPROM_FSTEP_L*EEPROM_PDAC_L/2						// Calibration Data Length 160*48*2= =15360(0x3C00)			
																			//
#define EEPROM_CH_DT_L	EEPROM_CALIBL+EEPROM_CALIBL_L						// (0x39B0+0x3700 = 0x7AB0) 						

//=========================================
#define FDAC_TABLE_LENGTH	3	// FDAC broken up into 3 pieces
#define PDAC_TABLE_LENGTH	37	// 25
#define CAL_TABLE_LENGTH	128	// 80

//#define POWER_TABLE_START	18
//#define POWER_TABLE_END		-28
//#define POWER_TABLE_LENGTH	48												// POWER_TABLE_START-POWER_TABLE_END-2

//#define PDAC_TABLE_INC	4095/(PDAC_TABLE_LENGTH-1)
#define INIT_FREQ_LENGTH 19
#define INIT_FREQ_LENGTH12 1

#define MW2_FLT_MAX		1E+37
#define MW2_POWER_MAX	30.0
#define MW2_POWER_MIN	-30.0

// PCI-PXI configuration space info
typedef struct  {
	USHORT	pciBusNo;
	USHORT	pciDevNo;
	USHORT	pciFuncNo;
	USHORT	vendorId;
	USHORT	devId;
	char	vendorName[100 + 1];
	char	deviceName[100 + 1];
//	ULONG	*barZero;
	ULONG	barZero;
} PCIInfo;

// Model-version info (temporary)
typedef struct {
	UCHAR	structVers;		// version of this structure
	UCHAR	filler[3];
	ULONG	fwvers;
	UCHAR	model_version[32];
	UCHAR	serialNo[32];
	ULONG	calibDataSize;	// in bytes
	UCHAR	calibDataFormat[128-76];	// 128 bytes for a page
} MODEL_VERS;

// Calibration info (temporary)
typedef struct {
	double	calibdata[4092];
} CALIB;

typedef struct {
	double	Power;
	USHORT	PDAC;
} PDACTBL;

typedef struct{
	double	Frequency;
	PDACTBL	PDACTable[PDAC_TABLE_LENGTH];
} CALDATA;

typedef struct {
	/// <summary>
	/// Addition is the addition (b) for the equation y = ax+b, where x = frequency, y = fdac
	///</summary>
	double Addition;
	/// <summary>
	/// Frequency is max frequency used for each equation
	///</summary>
	double	Frequency;
	/// <summary>
	/// Multiplier is the multiplier (a) for the equation y = ax+b, where x = frequency, y = fdac
	///</summary>
	double	Multiplier;

} FDACTBL;

// Channel information for the host
typedef struct  { 
	ViSession instr;
	USHORT	slot;			// 2 - 18
	USHORT	ch;				// 0 - 1
	PCIInfo	pciInfo;		// PCI configuration space info
	MODEL_VERS model_vers;
	CALDATA	CalData_Hi[CAL_TABLE_LENGTH];
	CALDATA	CalData_Lo[CAL_TABLE_LENGTH];
	FDACTBL FdacTbl[FDAC_TABLE_LENGTH];
	BOOL	bUseSEEPROMData;

	// interface registers on the card
	ULONG	*cardBaseVirtualAddr;
	ULONG	*cardCmdReg;
	ULONG	*cardStatusReg;
	ULONG	*chCmdReg;
	ULONG	*chAddr4Reg;
	ULONG	*chLen4Reg;
	ULONG	*chStatusReg;
	ULONG	*chIntrCode;

	ULONG	*cardSpiWriteData;
	ULONG	*cardSpiWriteData1;
	ULONG	*cardSpiWriteData2;
	ULONG	*cardSpiWriteData3;
	ULONG	*cardSpiWriteData4;
	ULONG	*cardSpiWriteData5;
	ULONG	*cardSpiWriteData6;
	ULONG	*cardSpiWriteData7;

	ULONG	*cardSpiReadData;
	ClockType	refClockSource; //ClockType
	double	refClockFreq;	// in MHz
	double	refClockSet;	// in MHz
	double	outputFreqMhz;	// RF output in MHz
	double	outputPower;	// dBm
	ULONG	refDivider;		// PLL reference clock divider
	BOOL	useFilterBanks;	// TRUE in normal case, FALSE for test path
	BOOL	rfOutputOn;		// TRUE if RF output should be ON
	USHORT	attenuatorDac;	// used if the DAC is directly set by the user
	USHORT	filterDac;		// used if the DAC is directly set by the user
} MW2ChannelInfo;


typedef struct {
	BOOL	bCheck;
	double	dPower;
	double	dNormalized;
} FREQTBL;

//#define FREQSTART 25
//#define FREQEND 6000
#define MAXDIFF 0.1

//---------------------------------------------------------
// Internal low-level functions for the API implementation
//---------------------------------------------------------
#ifdef __cplusplus
extern "C"
{
#endif
	static BOOL		_mw2WriteRegister(USHORT slot, USHORT dev, USHORT reg, ULONG value);
	static ULONG	_mw2ReadRegister(USHORT slot, USHORT dev, USHORT reg);
	static MW2ChannelInfo * _mw2GetChIntf(USHORT slot, USHORT ch);
	static void		_mw2InitHmc833(USHORT slot, USHORT dev);
	static BOOL		_mw2DoCommand(USHORT slot, USHORT dev, ULONG cmd, ULONG addr4, ULONG data, ULONG *pdata);
	static BOOL		_mw2WaitForDone(MW2ChannelInfo *info);
	static void		_mw2Log(char *logString);
	static void		_mw2LogOpen(void);
	static void		_mw2LogClose(void);
	static void		_mw2PrintPCIInfo(PCIInfo *info);
	static void		_mw2PrintChInfo(MW2ChannelInfo *info);
	static USHORT	_mw2Hmc882DacVal(double cuttoffFreqMHz);	// assume no device dependence
	static USHORT	_mw2Hmc346DacVal(USHORT slot, USHORT dev, double attenDb);
	static BOOL		_mw2PllChipEnable(USHORT slot, USHORT channel, BOOL enable);
	static BOOL		_mw2AmpEnable(USHORT slot, USHORT channel, BOOL enable);
	static void		_mw2CmdPulse(USHORT slot, ULONG bitflag);
	static BOOL		_mw2ReadEeProm(USHORT slot, USHORT byteOffset, USHORT nBytes, void *buffer);
	static BOOL		_mw2WriteEeProm(USHORT slot, USHORT byteOffset, USHORT nBytes, void *buffer);
	static BOOL		_mw2SetEePromWELatch(USHORT slot);

#ifdef __cplusplus
}
#endif
#endif  //__MW2DEFS_H