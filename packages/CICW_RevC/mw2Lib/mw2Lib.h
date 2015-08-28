#ifndef	__MW2_H
#define __MW2_H

#include <Shlwapi.h>
#pragma comment(lib, "Shlwapi.lib")
#include <ShlObj.h>
#pragma comment(lib, "shell32.lib")
#include <Wtypes.h>
#include <stdio.h>
#include <malloc.h>
#include <sys/stat.h> 
#include <sys/types.h>
#include "windows.h"
//#include "pmdll.h"
#include "visatype.h"
#include "visa.h"
#include "mw2Error.h"

#define QUOTE(str) #str
#define TOSTRING(x) QUOTE(x)
#define CICW_ERROR_CHECK(status,errString)  (cicw_Error(status, errString, __FILE__":"TOSTRING(__LINE__)))
/*
	MW2 SPI Device Numbers

	----------------------------------------------------
	Channel		HMC833	    AD5621 DAC	   AD5621 DAC
			  Synthesizer    (for VVA)      (for LPF)
	----------------------------------------------------
		0          0            2              4
	----------------------------------------------------
		1          1            3              5
	----------------------------------------------------
	EEPROM	253, 254
*/

typedef enum {UnknownType, MW4062Type, MW4122Type} CardType;

// card type strings
#define STR_MW4062		"CI4062"
#define STR_MW4122		"CI4122"
#define STR_UNKNOWN		"Unknown"

// chassis info
#define MAXSLOTS	18
#define FIRSTSLOT	2
#define LASTSLOT	18
#define BADADDR		0xffffffff

// data bounds
//#define MW2_MAX_CHANNELS 1 //%% for testing
#define MW2_MAX_CHANNELS 2
#define MW2_MAX_REGS 32
//#define MW2_POWER_MIN  ((double)-15.0)	// in dBm
//#define MW2_POWER_MAX  ((double)10.0)	// in dBm
// double the range temporarily
//#define MW2_POWER_MIN  ((double)-30.0)	// in dBm
//#define MW2_POWER_MAX  ((double)20.0)	// in dBm

#define MW2_4062_FREQ_MIN   ((double)25.0)	// in MHz
#define MW2_4062_FREQ_MAX   ((double)6000.0)	// in MHz
#define MW2_4122_CH0_FREQ_MIN   ((double)6000.0)	// in MHz
#define MW2_4122_CH0_FREQ_MAX   ((double)12000.0)	// in MHz
#define MW2_4122_CH1_FREQ_MIN   ((double)25.0)	// in MHz
#define MW2_4122_CH1_FREQ_MAX   ((double)6000.0)	// in MHz
#define MW2_4062_FREQ_DEFAULT	((double)2000.0)	//%%
#define MW2_4122_CH0_FREQ_DEFAULT	((double)8000.0)	//%%
#define MW2_4122_CH1_FREQ_DEFAULT	((double)2000.0)	//%%

#define STABLEPOWER ((double)0.01)
#define STABLEPOWER_0_5 ((double)0.04)

#define CH0_START 0x400
#define CH1_START 0x8000
// Header = 0x18, pmax data = 0x442, pdac data = 0x35A 
// Total = 0x18 + 0x35A + 0x442 = 0x7B4, rounded up to 0x800
#define CAL_DATA_LEN 0x800
// Length used for freq, gain0, gain9, gain0attn, and temp
#define FREQ_LEN 0xDA
// Same as HEADER_LEN_4122
#define HEADER_LEN 0x18
// Length used for pdac values, and temp values
#define PDAC_LEN 0x16
// PDAC Cal data starts this long after the starting point (HEADER_LEN + 5*FREQ_LEN)
#define PDAC_START 0x45A
// 37 frequencies at each pdac value
#define PDAC_FREQ_LEN 37
// 37 frequencies * 11 pdac values * 2 bytes each = 0x32E
#define PDAC_POW_LEN 0x32E

#define FREQ_LEN_4122 0x60
// Same as HEADER_LEN
#define HEADER_LEN_4122 0x18
#define PDAC_LEN_4122 0x16
//HEADER_LEN_4122 + 4*FREQ_LEN_4122
#define PDAC_START_4122 0x198
#define PDAC_FREQ_LEN_4122 48
#define PDAC_POW_LEN_4122 0x44C


//============================================
// MW2 API functions
//============================================

#ifdef __cplusplus
extern "C"
{
#endif

		typedef enum {ClockIntIntOff, ClockIntIntInt, ClockPxiPxiOff, ClockExtExtOff, ClockExtIntOff, ClockPxiExtOff} ClockType;
		//#include "mw2DLL.h"

	// Following functions return requested information	//////////////////////////////////////////////
	BOOL			mw2Locked(unsigned short usSlot, unsigned short usChannel);						// Return TRUE if PLL being locked
	
	
	char* mw2GetCalibrationDir (void); // Return program root directory
	char* mw2GetValidationDir (void); // Return program root directory
	char* mw2GetDataDir (void); // Return program root directory

	unsigned long	mw2ReadRegister		(unsigned short usSlot, unsigned short usDev, unsigned short usReg);	// Return the register value

	unsigned short	mw2GetFirstSlot		(void);														// Return the first quantumWave card slot in the system 
	short* mw2GetSlotList (void);
	ViSession getDefaultRM();
	unsigned short	mw2GetLastSlot		(void);														// Return the last quantumWave card slot in the system

	CardType		mw2GetCardType(unsigned short usSlot);											// Return CardType (MW4062Type, MW4122Type, or UnknownType)
	char*			mw2GetCardName		(CardType ctType);											// Return CardName (STR_MW4062, STR_MW4122, or STR_Unknown)

	char			mw2GetCardRev		(unsigned short usSlot);									// Return Card Revision setting in SEEPROM
	char*			mw2GetCardDate		(unsigned short usSlot);									// Return date setting in SEEPROM
	char*			mw2GetCardTime		(unsigned short usSlot);									// Return time setting in SEEPROM
	unsigned long	mw2GetSerial		(unsigned short usSlot);									// Return the S/N set in the SEEPROM
	unsigned long	mw2GetTemperature	(unsigned short usSlot);	// Read Temperature
	double			mw2GetTemperatureInCelsius	(unsigned short usSlot);	// Read Temperature

	ClockType		mw2GetClockType(unsigned short usSlott);										// Return chInfo->refClockSource setting
	int				mw2GetBusNo			(unsigned short usSlot);									// Return chInfo->pciInfo.pciBusNo number
	int				mw2GetDevNo			(unsigned short usSlot);									// Return chInfo->pciInfo.pciDevNo number
	int				mw2GetFuncNo		(unsigned short usSlot);									// Return chInfo->pciInfo.pciFuncNo number
	unsigned short	mw2GetCardDevId		(unsigned short usSlot);									// Return chInfo->pciInfo.devId value
	unsigned short	mw2GetFilterDac		(unsigned short usSlot, unsigned short usChannel);			// Return chInfo->filterDac setting
	unsigned short	mw2GetAttenuatorDac	(unsigned short usSlot, unsigned short usChannel);			// Return chInfo->attenuatorDac setting
	unsigned long	mw2GetRefDivider	(unsigned short usSlot, unsigned short usChannel);			// Return chInfo->refDivider setting
	unsigned long	mw2GetFwVersion		(unsigned short usSlot);									// Return chInfo->model_vers.fwvers
	double			mw2GetClockMHz		(unsigned short usSlot, unsigned short usChannel);			// Return chInfo->refClockFreq
	double			mw2GetRefClockSet	(unsigned short usSlot, unsigned short usChannel);
	double			mw2GetOutputFreq	(unsigned short usSlot, unsigned short usChannel);			// Return chInfo->outputFreqMhz
	int mw2GetCalData(unsigned short slot,unsigned short channel, unsigned short pos, UCHAR* buffer);		

	// Following functions return error code specified in mw2errno.h /////////////////////////////////
	int mw2Init(BOOL engineering); // Initialize everything that needs to happen once at startup. 
	int mw2Connect(char* chResourceName, unsigned short* slot);
	int	mw2ScanSystem(unsigned int* pusSlot);		// Scan the PCI bus and then return the number of card in the system through *pusSlot
	int	mw2RescanSystem(unsigned short* pusSlot);	// ReScan the PCI bus and then return the number of card in the system through *pusSlot
	
	int	mw2SetRefDivider(unsigned short usSlot, unsigned short usChannel, unsigned long ulValue);					// Set chInfo->refDivider
	int	mw2ResetPll(unsigned short usSlot, unsigned short usChannel);												// Generate 2ms PLL disable pulse
	int	mw2SetOutputFreq(unsigned short usSlot, unsigned short usChannel, double freqMhz, BOOL b6dBAttenuation);	// Set Hmc833 frequency
	int	mw2SetOutputFreqC(unsigned short usSlot, unsigned short usChannel, double freqMhz, BOOL b6dBAttenuation, unsigned long AttnValue);	// Set Hmc833 frequency
	int	mw2Log(char *strbuff);																						// Print message to log file
	int mw2GetLastKnownFileName(char *path);
	int mw2WriteRegister(unsigned short usSlot, unsigned short usDev, unsigned short usReg, unsigned long ulValue);	// Write value to register
	int	mw2ReadEeProm		(unsigned short usSlot, unsigned short usByteOffset, unsigned short usNBytes, void *buffer);	// Read SEEPROM
	int	mw2WriteEeProm		(unsigned short usSlot, unsigned short usByteOffset, unsigned short usNBytes, void *buffer);	// Write SEEPROM
	int	mw2WriteEePromPage	(unsigned short usSlot, unsigned short usByteOffset, unsigned short usNPages, ULONG *buffer);	// Write SEEPROM Page

	int mw2Freq2FilterDac(unsigned short usSlot, unsigned short usChannel, double freqMHz, unsigned short * pusFdac);	// Get FDAC value from freqMHz and then return the value through *pusFdac
	BOOL mw2InitHw(unsigned short slot);																						// Reset all quantumWave cards					
	int mw2SelectClock(unsigned short usSlot, ClockType clock, unsigned long clockMHz, BOOL writeToCard);									// Select and set refclock
	int mw2ResetCard(unsigned short usSlot);																			// Reset a quantumWave card
	int mw2ShutDown(void);																								// Release all quantumWave cards and resources
	int mw2SetAttenuatorDac(unsigned short usSlot, unsigned short usChannel, unsigned short usDacValue);				// Set PDAC
	int mw2SetFilterDac(unsigned short usSlot, unsigned short usChannel, unsigned short usDacValue);					// Set FDAC
	int mw2SetChInfoFreq(unsigned short  usSlot, unsigned short usChannel, double dRequestfreqMhz);						// Set chInfo->outputFreqMhz
	int mw2SetFilterBanks (unsigned short usSlot, unsigned short usChannel, double dFreqMHz);							// Select and set Filter Bank
	int mw2SetFilterBanksVCO (unsigned short usSlot, unsigned short usChannel, double dFreqMHz, unsigned long iVal);							// Select and set Filter Bank
	int mw2OutputOff(unsigned short usSlot, unsigned short usChannel);													// Turn off output
	int mw2OutputOn(unsigned short usSlot, unsigned short usChannel, BOOL mute);							// Turn on Output
	int mw2OutputOnC(unsigned short usSlot, unsigned short usChannel, BOOL mute, unsigned long AttnValue);			// Turn on Output
	int mw2Get4122Card(unsigned short usSlot); // Returns if the card is a 4122 card. 
	// Old SEEPROM functions which no longer work. 
	//BOOL			mw2SEEPROMCalibDataAvailable(unsigned short usSlot, unsigned short usChannel);	// Return TRUE if CalibData is available in SEEPROM
	//int				mw2SEEPROMFDACStep	(unsigned short usSlot, unsigned short usChannel);			// Return FDACStep setting in SEEPROM
	//int				mw2SEEPROMPDACStep	(unsigned short usSlot, unsigned short usChannel);			// Return PDACStep setting in SEEPROM
	//int				mw2SEEPROMFreqStep	(unsigned short usSlot, unsigned short usChannel);			// Return FreqStep setting in SEEPROM
	//char			mw2GetSeepromFormat	(unsigned short usSlot);									// Return SEEPROM Format Revision setting in SEEPROM
	//BOOL			mw2UseSEEPROMData(unsigned short usSlot, unsigned short usChannel);				// Return chInfo->bUseSEEPROMData flag
	//int	mw2SetPowerSeeprom(unsigned short usSlot, unsigned short usChannel, double dFreqMHz, double dPowerdBm, BOOL bUseSeepromData);	// Set PDAC and FDAC
	//int	mw2Pwr2AttenuatorDacSeeprom(unsigned short usSlot, unsigned short usChannel, double freqMHz, double powerdBm, BOOL bUseSeepromData, unsigned short* pusPdac); // Convert requested power to PDAC value, and then return the value through *pusPdac
/*
//	obsoleted 13-02-15
	USHORT	mw2Pwr2AttenuatorDacB(USHORT slot, USHORT channel, double freqMHz, DOUBLE powerdBm, int iFormat); //%% stub
	BOOL	mw2SetPowerB(USHORT slot, USHORT channel, double freqMHz, double powerdBm, int iFormat);
	void    mw2PrintChannelInfo(USHORT slot, USHORT channel);

*/

#ifdef __cplusplus
}

/*
{
#endif
	BOOL	mw2WriteRegister(USHORT slot, USHORT dev, USHORT reg, ULONG value);
	ULONG	mw2ReadRegister(USHORT slot, USHORT dev, USHORT reg);
	void	mw2PrintChannelInfo(USHORT slot, USHORT channel);
	CardType mw2GetCardType(USHORT slot);
	char	*mw2GetCardName(CardType type);
	ULONG	mw2GetFwVersion(USHORT slot);
	BOOL	mw2OutputOff(USHORT slot, USHORT channel);
	BOOL	mw2ResetPll(USHORT slot, USHORT channel);
	ClockType mw2GetClockType(USHORT slot);
	double	mw2GetClockMHz(USHORT slot);
	BOOL	mw2Locked(USHORT slot, USHORT channel);
//	USHORT	mw2LockedD(USHORT slot);
	BOOL	mw2SetRefDivider(USHORT slot, USHORT channel, ULONG value);
	ULONG	mw2GetRefDivider(USHORT slot, USHORT channel);
	double	mw2GetOutputFreq(USHORT slot, USHORT channel);
	BOOL	mw2SetPower(USHORT slot, USHORT channel, double freqMHz, double powerdBm); //%% stub
	double	mw2GetPower(USHORT slot, USHORT channel);
	BOOL	mw2SetFilterBanks (USHORT slot, USHORT channel, double freqMHz, BOOL useFilterBanks); // stub
	BOOL	mw2SetLPFilter(USHORT slot, USHORT channel, double cutoffFreq); // stub
	USHORT	mw2GetFirstSlot(void);
	USHORT	mw2GetLastSlot(void);
	BOOL	mw2SetAttenuatorDac(USHORT slot, USHORT channel, USHORT dacValue);
	USHORT	mw2GetAttenuatorDac(USHORT slot, USHORT channel);
	BOOL	mw2SetFilterDac(USHORT slot, USHORT channel, USHORT dacValue);
	USHORT	mw2GetFilterDac(USHORT slot, USHORT channel);
	BOOL	mw2ReadEeProm(USHORT slot, USHORT byteOffset, USHORT nBytes, void *buffer);
	BOOL	mw2WriteEeProm(USHORT slot, USHORT byteOffset, USHORT nBytes, void *buffer);
	void	mw2Log(char *strbuff);
	char *	mw2GetRootDir(void);
	USHORT	mw2Pwr2AttenuatorDac(USHORT slot, USHORT channel, double freqMHz, DOUBLE powerdBm); //%% stub
	USHORT	mw2Freq2FilterDac(USHORT slot, USHORT channel, double freqMHz); //%% stub

	ini		mw2InitHw(void);
	int		mw2SelectClock(USHORT slot, ClockType clock, ULONG clockMHz);
	int		mw2ResetCard(unsigned short usSlot);

#ifdef __cplusplus
}
*/
#endif
#endif  //__MW2_H