// PulserLib.c - The pulse programmer functions
//
// Revision
// 120710	Remove PCI "function" loop, assume func is always 0	C.W.
// 120710	Remove UnloadPhyMemDriver(). There isn't VISA replacement function;
// 120710	Add instr in typedef struct

// 120710	Add viOpen() in loops
// 120710	Replace LoadPhyMemDriver() with viOpenDefaultRM(&defaultRM)
// 120710	Replace ReadPCI() with viIn32()
// 120710	Replace MapPhyMem() with viMapAddress()
// 120710	Replace UnmapPhyMem() with viUnmapAddress()
// 120716	Update  mw2SetFilterBanks FB Select
// 120716	Add output frequency x2 and /2 on 4122 channel 0 
// 120716	Add USR_CMD_AMP_SELECT to _mw2DoCommand
// 120716	uncomment filterDac and powerDac in typedef
// 120716	Save filterDac and powerDac to chinfo typedef
// 120717	Print out _mw2DoCommand Command and other parameters for debugging
// 120717	Correct mw2SetFilterBanks 6-12GB path select
// 120717	Remove mw2OutputOn from mw2SetOutputFreq
// 120718	Change pciinfo.barzero from pointer to value in mw2Lib.c & mw2Defs.h
// 120718	Remove/replace _mw2DoCommand AMP setting by _mw2AmpEnable().
// 120722	comment out _mw2GetChIntf in mw2Locked, because ch1 always return false
// 120723	check  _mw2GetChIntf ch0 in mw2Locked only, because ch1 always return false
// 1207231	Swap id of mw2SetAttenuatorDac and mw2SetFilterDac 
// 1207231	Reverse AB select of 4122 Channel0  
// 120724a	Merge 120723a to 120724a
// 120730	Change 1500M 3000M switching frequecy from > to >=
// 120730	Remove the actual pwer setting in mw2setpower
// 120801	FB select change from 4.0G to 3.8G
// 120806	remove 10ms wait time in _mw2WaitForDone
// 120822	Does not write D88 to VCO R1 and 0 to R1 in mw2OutputOn
// 120822	Check only Device 0 of each PCI bus during mw2ScanSystem
// 120830	Add mw2GetVcoCore
// 120830	Add mw2GetSerial
// 120831	Update mw2SetPower
// 120914	Change freq fron int64 back to double
// 120917	Add 50uS btwn VCO R4 & R5
// 120921	Remove 50uS btwn VCO R4 & R5, limit PDAC in 0-4095
// 121116	Change Internal Attenuator setting 
// 121116	Change _mw2SetHmc833Freq function
// 121119	Change Filter Bank Switching point
// 121119	Change VCO internal Attenuator switching point
// 121119	Change Naming scheme (add rev)
// 121119	Change FDAC to a common file (Card independant)
// 121211	Change FDAC back to card dependant
// 121211	Add -6dBm when Power=-10dBm feature
// 121218	Change calib to _H _L; Pdacstep.dat to PdacstepB.dat
// 130110	Get RefDiv from mw2GetRefDevider instead of mw2GetRegister(2)
// 130110	mw2Init set Reg 2 by get value from mw2GetRefDevider
// 130110	Add channel as parameter to getclockfreq
// 130123	Add Timer
// 130204	Add viClose next to viUnmapAddress
// 130204	Add fclose(pLogFile) in mw2Shutdown()
// 130204	Change \CALIB to \Cambridge Instruments\Calibration
// 130204	Fix one sprintf(FileName, "\0") problem
// 130204	Add iSEEPROMFDACSTEP
// 130204	Add BusFile.dat Feature (Read only)
// 130207	Add Rescansystem() = shutdown+scansystem+initHw + Update BusFile
// 130214	Cleanup Function	Slot = unsigned short
// 130531	Test Code Need to change back 9000 <-> 8800
// 130531	Change Code n-6db to -9db in _mw2SetHmc833Freq


#include "mw2Defs.h"
//#include <string>

static char MW2Validation[MAX_PATH];
static char MW2Calibration[MAX_PATH];
static char MW2Data[MAX_PATH];
static MW2ChannelInfo MW2Channel[MAXSLOTS][MW2_MAX_CHANNELS];	//Modified
//static unsigned NumSlotsPresent, FirstSlot, LastSlot;
static unsigned short usFirstSlot, usLastSlot;
static ViUInt32 numInstruments;
FILE *pLogFile, *pCalFile, *pFdacFile, *pPdacstep, *pVerFile, *pBusFile;

static	ViSession defaultRM;	//Added 120710
static short slots[MAXSLOTS];
#define MW2_LOGBUF_SIZE 200
static char LogBuf[MW2_LOGBUF_SIZE];
#define PCI_BUS_SIZE 256

//std::clock_t start;
//double diff;
//clock_t startTime, endTime, clockTicksTaken;
//double timeInSeconds;

// startTime = clock();
// doSomeOperation();
// endTime = clock();
// clockTicksTaken = endTime - startTime;
// timeInSeconds = clockTicksTaken / (double) CLOCKS_PER_SEC;

//================================================
// MW2 API Functions
//================================================

//------------------------------------------------------------
// mw2Init(BOOL engineering) - Engineering is true if calibration / validation waveforms can be created. 
//------------------------------------------------------------
int mw2Init(BOOL engineering) {
		TCHAR szPath[MAX_PATH];
		BOOL handleClosed;
		int i, status;

		if(engineering) { // Regular users won't be calibrating or validating their cards, so it doesn't need to make the folders. 
				if ( SUCCEEDED( SHGetFolderPath( NULL, CSIDL_MYDOCUMENTS, NULL, 0, szPath ) ) )
				{
						// Create the initial folders in My Documents
						PathAppend( szPath, "\\Cambridge Instruments");
						CreateDirectory(szPath, NULL);
						PathAppend( szPath, "\\CI4000");
						CreateDirectory(szPath, NULL);
						PathAppend( szPath, "\\Validation");
						CreateDirectory(szPath, NULL);
				}
				for(i = 0; i < MAX_PATH; i++) MW2Validation[i] = (char)szPath[i];

				if ( SUCCEEDED( SHGetFolderPath( NULL, CSIDL_MYDOCUMENTS, NULL, 0, szPath ) ) )
				{
						// Create the calibration folder
						PathAppend( szPath, "\\Cambridge Instruments\\CI4000\\Calibration");
 						CreateDirectory(szPath, NULL);
				}
				for(i = 0; i < MAX_PATH; i++) MW2Calibration[i] = (char)szPath[i];

				if ( SUCCEEDED( SHGetFolderPath( NULL, CSIDL_MYDOCUMENTS, NULL, 0, szPath ) ) )
				{
						// Create the data collection folder
						PathAppend( szPath, "\\Cambridge Instruments\\CI4000\\Data Collection");
 						CreateDirectory(szPath, NULL);
				}
				for(i = 0; i < MAX_PATH; i++) MW2Data[i] = (char)szPath[i];
		}

		if ( SUCCEEDED( SHGetFolderPath( NULL, CSIDL_COMMON_APPDATA, NULL, 0, szPath ) ) )
		{
				// Create the application data folders where the log and busfile are saved
				PathAppend( szPath, "\\Cambridge Instruments");
				CreateDirectory(szPath, NULL);
				PathAppend( szPath, "\\CI4000");
				CreateDirectory(szPath, NULL);
				PathAppend( szPath, "\\InstrumentLog.txt");
		}
		fopen_s(&pLogFile, szPath, "w");
		fclose(pLogFile);
		mw2Log("Start Logging...\r\n");

		if ( SUCCEEDED( SHGetFolderPath( NULL, CSIDL_COMMON_APPDATA, NULL, 0, szPath ) ) )
		{
				// Because the startup involves a read, create the file if it doesn't exist. 
				PathAppend( szPath, "\\Cambridge Instruments\\CI4000\\LastKnownValues.txt");
				handleClosed = CloseHandle(CreateFile(szPath, GENERIC_READ|GENERIC_WRITE, FILE_SHARE_READ|FILE_SHARE_WRITE, NULL, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, NULL));
		}

		// Load physical memory  mapping driver
		status = viOpenDefaultRM(&defaultRM);
		if(status < VI_SUCCESS) { 	
				mw2Log("viOpenDefaultRM failed\r\n");
		} else mw2Log("viOpenDefaultRM successful\r\n");

		return status;
}

ViSession getDefaultRM(){
		return defaultRM;
}

char *mw2GetCalibrationDir(void) {
		return MW2Calibration;
}

char *mw2GetValidationDir(void) {
		return MW2Validation;
}

char *mw2GetDataDir(void) {
		return MW2Data;
}

//------------------------------------------------------------
// mw2WriteRegister() - writes a register of an SPI device.
//------------------------------------------------------------
int mw2WriteRegister(unsigned short usSlot, unsigned short usDev, unsigned short usReg, unsigned long ulValue){
	int mw2EC = MW2ECNOERR;
	if (!_mw2WriteRegister(usSlot, usDev, usReg, ulValue)) mw2EC = MW2ECIO;
	return (mw2EC);
}

//---------------------------------------------------------------
// mw2ReadRegister() - returns a register value of an SPI device.
//---------------------------------------------------------------
unsigned long mw2ReadRegister(unsigned short usSlot, unsigned short usDev, unsigned short usReg) {
//	int mw2EC = MW2ECNOERR;
	return _mw2ReadRegister(usSlot, usDev, usReg);
}

//---------------------------------------------------------------
// mw2ReadRegister() - returns a register value of an SPI device.
//---------------------------------------------------------------
unsigned long mw2GetTemperature(unsigned short usSlot) {
	unsigned long value = 0;
	//	int mw2EC = MW2ECNOERR;
	if (_mw2ReadTemperature(usSlot, &value) == 0)
		return value;
	else
		return value;
}

//---------------------------------------------------------------
// mw2ReadRegister() - returns a register value of an SPI device. 1 = 1/32 Celsius
//---------------------------------------------------------------
double mw2GetTemperatureInCelsius(unsigned short usSlot) {
	unsigned long value = 0;
	//	int mw2EC = MW2ECNOERR;
	if (_mw2ReadTemperature(usSlot, &value) == 0) {
		return (double)(value-3)/128.0;
	}
	else {
		return (double)(value-3)/128.0;
	}
}

int mw2Connect(char* chResourceName, unsigned short* slot) {
		char * cardName;
		ViSession instr;
		int status, ch, bus;
		USHORT devId, venId;
		ULONG dev_ven, bar0;
		void *virAddr = 0;
		ULONG *cardStatusRegAddr, geoAddr, Serial;
		MW2ChannelInfo *chInfo;
		unsigned short pxiSlot;

		if ((status = viOpen(defaultRM, chResourceName, VI_NULL, VI_NULL, &instr)) != VI_SUCCESS) {
				mw2Log("viOpen failed\r\n");
				return status;
		}

		if ((status = viIn32(instr, VI_PXI_CFG_SPACE, 0, &dev_ven)) != VI_SUCCESS) {
				viClose(instr);
				mw2Log("viIn32 failed\r\n");																//Debug
				return status;
		}

		// Can read the config registers - check the vendor/dev ID
		devId = HIWORD(dev_ven);
		venId = LOWORD(dev_ven);
		if ((venId != VID_XILINX) || ((devId != DID_MW4062) && (devId != DID_MW4122))){
				viClose(instr);
				mw2Log("Vender ID wasn't 4062 or 4112\r\n");																//Debug
				return -1;
		}

		// Have an MW2 board. Read bar0.
		viIn32(instr, VI_PXI_CFG_SPACE, 0x10, &bar0);

		// check if bar0 is memory type
		if ((bar0 == 0) || ((ULONG)bar0 & 0x7) != 0) {
				viClose(instr);
				mw2Log("Memory type not 7\r\n");																//Debug
				return -1;
		}

		// Map the interface memory to the host virtual address
		if ((status = viMapAddress(instr, VI_PXI_BAR0_SPACE, 0, MW2_PHYSMEM_SIZE4*4, VI_FALSE, VI_NULL, &virAddr))  != VI_SUCCESS) {
				viClose(instr);
				mw2Log("Cannot map address\r\n");																//Debug
				return status;
		}

		// Get the slot number from the card status register of the board
		pxiSlot = 0;
		cardStatusRegAddr = (ULONG *)((char *)virAddr + MW2_INTF_CARD_STATUS_REG_ADDR4 * 4);
		geoAddr = ((*cardStatusRegAddr) >> 1) & 0x1f;
		if ((geoAddr > MAXSLOTS) || (geoAddr < 1)) {
				viUnmapAddress(instr);
				viClose(instr);
				mw2Log("Cannot find GA\r\n");																//Debug
				return status;
		} 
		else 
				pxiSlot = (unsigned short)geoAddr;

		viGetAttribute(instr, VI_ATTR_PXI_BUS_NUM, &bus);

		sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "\r\nFound card in slot %d\r\n", pxiSlot);	//Debug
		mw2Log(LogBuf);																//Debug

		//Setting the values for MW2Channel [slot of card] [both channels]
		for (ch = 0; ch < MW2_MAX_CHANNELS; ch++) {
				chInfo = _mw2GetChIntf(pxiSlot, ch);
				if(chInfo->slot != pxiSlot) {
						chInfo->refClockSource = ClockIntIntOff;
						chInfo->refClockFreq = MW2_CLK_INT_MHZ;
						chInfo->refClockSet = 10;
						chInfo->refDivider = 1;		
						chInfo->instr = instr;								// Added
						chInfo->slot = pxiSlot;
						chInfo->ch = ch;
						chInfo->outputPower = 10;
						if(devId == DID_MW4122 && ch == 0) chInfo->outputFreqMhz = 6000;
						else chInfo->outputFreqMhz = 2000;
						chInfo->pciInfo.pciBusNo = bus;
						chInfo->pciInfo.pciDevNo = 0;
						chInfo->pciInfo.pciFuncNo = 0;
						chInfo->pciInfo.vendorId = (USHORT)venId;
						chInfo->pciInfo.devId = (USHORT)devId;
						//	chInfo->pciInfo.barZero = &bar0;
						chInfo->pciInfo.barZero = bar0;

						cardName = mw2GetCardName(mw2GetCardType(pxiSlot));

						strncpy_s(chInfo->pciInfo.vendorName, MAX_PATH, STR_MAGIQ, strlen(STR_MAGIQ)); 
						strncpy_s(chInfo->pciInfo.deviceName, MAX_PATH, cardName, strlen(cardName)); 

						// Set up the FDAC values
						if(ch == 0 && devId == DID_MW4122) {
								chInfo->FdacTbl[0].Frequency = 6710.0;   // GR12172013 - this is the max frequency for this function
								chInfo->FdacTbl[0].Multiplier = 149.0/710.0;  // GR12172013 - this is the multiplied value
								chInfo->FdacTbl[0].Addition = -1259.1;  // GR12172013 - this is the added value
								chInfo->FdacTbl[1].Frequency = 10800.0;   // GR12172013 - this is the max frequency for this function
								chInfo->FdacTbl[1].Multiplier = 1732.0/4090.0;  // GR12172013 - this is the multiplied value
								chInfo->FdacTbl[1].Addition = -2692.5;  // GR12172013 - this is the added value
								chInfo->FdacTbl[2].Frequency = 12001.0;   // GR12172013 - this is the max frequency for this function
								chInfo->FdacTbl[2].Multiplier = 714.0/1200.0;  // GR12172013 - this is the multiplied value
								chInfo->FdacTbl[2].Addition = -4545.0;  // GR12172013 - this is the added value
						} else {
								chInfo->FdacTbl[0].Frequency = 5200;   // GR12172013 - this is the max frequency for this function
								chInfo->FdacTbl[0].Multiplier = 730.0/1400.0;  // GR12172013 - this is the multiplied value
								chInfo->FdacTbl[0].Addition = -1981.4;  // GR12172013 - this is the added value
								chInfo->FdacTbl[1].Frequency = 5250.0;   // GR12172013 - this is the max frequency for this function
								chInfo->FdacTbl[1].Multiplier = 421.0/50.0;  // GR12172013 - this is the multiplied value
								chInfo->FdacTbl[1].Addition = -43054.0;  // GR12172013 - this is the added value
								chInfo->FdacTbl[2].Frequency = 6001.0;   // GR12172013 - this is the max frequency for this function
								chInfo->FdacTbl[2].Multiplier = 789.0/750.0;  // GR12172013 - this is the multiplied value
								chInfo->FdacTbl[2].Addition = -4372.0;  // GR12172013 - this is the added value
						}
				}

				chInfo->cardBaseVirtualAddr = (ULONG *)virAddr;
				chInfo->cardCmdReg = chInfo->cardBaseVirtualAddr + MW2_INTF_CARD_CMD_REG_ADDR4;
				chInfo->cardStatusReg = chInfo->cardBaseVirtualAddr + MW2_INTF_CARD_STATUS_REG_ADDR4;
				chInfo->chCmdReg = chInfo->cardBaseVirtualAddr + MW2_INTF_CH0_CMD_REG_ADDR4;
				chInfo->chAddr4Reg = chInfo->chCmdReg + 1;
				chInfo->chLen4Reg = chInfo->chCmdReg + 2;
				chInfo->chStatusReg = chInfo->cardBaseVirtualAddr + MW2_INTF_CH0_STATUS_REG_ADDR4;
				chInfo->chIntrCode = chInfo->chStatusReg + 1;
				chInfo->model_vers.fwvers = *(chInfo->cardBaseVirtualAddr + MW2_INTF_CARD_FWVERS_ADDR4) & 0x0fff;

				// MW2 section
				chInfo->cardSpiWriteData = chInfo->cardBaseVirtualAddr + MW2_INTF_CARD_SPI_WRITE_DATA;
				chInfo->cardSpiWriteData1 = chInfo->cardBaseVirtualAddr + MW2_INTF_CARD_SPI_WRITE_DATA+1;
				chInfo->cardSpiWriteData2 = chInfo->cardBaseVirtualAddr + MW2_INTF_CARD_SPI_WRITE_DATA+2;
				chInfo->cardSpiWriteData3 = chInfo->cardBaseVirtualAddr + MW2_INTF_CARD_SPI_WRITE_DATA+3;
				chInfo->cardSpiWriteData4 = chInfo->cardBaseVirtualAddr + MW2_INTF_CARD_SPI_WRITE_DATA+4;
				chInfo->cardSpiWriteData5 = chInfo->cardBaseVirtualAddr + MW2_INTF_CARD_SPI_WRITE_DATA+5;
				chInfo->cardSpiWriteData6 = chInfo->cardBaseVirtualAddr + MW2_INTF_CARD_SPI_WRITE_DATA+6;
				chInfo->cardSpiWriteData7 = chInfo->cardBaseVirtualAddr + MW2_INTF_CARD_SPI_WRITE_DATA+7;
				chInfo->cardSpiReadData = chInfo->cardBaseVirtualAddr + MW2_INTF_CARD_SPI_READ_DATA;
		} // for -ch
		if(slot != NULL) *slot = pxiSlot;
		return status;
}

//-------------------------------------------------------------------
//mw2ScanSystem() - Loads the driver and scans the PCI space.
//		Returns mw2EC specified in mw2Error.h
//		Returns number of mw2 slots present in *piSlot.
//-------------------------------------------------------------------
int mw2ScanSystem(unsigned int * pusSlot) {
		int status = MW2ECNOERR;
		TCHAR szPath[MAX_PATH];
		int iSlot, ch, i;
		ViFindList fList;
		ViChar desc[VI_FIND_BUFLEN];
		ViUInt32 numInstrs;
		USHORT devId, venId;
		ULONG dev_ven, bar0;
		ViSession instr;
		void *virAddr = 0;
		unsigned short pxiSlot;
		ULONG *cardStatusRegAddr, geoAddr;

		// Initialize the MW2ChannelInfo structure
		for (iSlot = 0; iSlot < MAXSLOTS; iSlot++) {
				for (ch = 0; ch < MW2_MAX_CHANNELS; ch++) {
						MW2Channel[iSlot][ch].slot = 0;	// zero means empty slot
						MW2Channel[iSlot][ch].pciInfo.devId = 0xff;
				}
				slots[iSlot] = -1;
		}

		/*
		usFirstSlot = usLastSlot = 0;
		for (i = 0; i < MAXSLOTS; i++) {
				slots[i] = -1;
		}
		*/
		mw2Log("Starting search for cards...\r\n");

		status = viFindRsrc(defaultRM, "?*PXI?*INSTR", &fList, &numInstrs, desc);
		if(status < VI_SUCCESS) {
				mw2Log("Failed to list resources on system.\r\n");
				if (pusSlot != NULL) *pusSlot = 0;
				return status;
		} 
		mw2Log("Listed Resources, ");
		numInstruments = 0;
		
		for(i = 0; i < numInstrs; i++) {
				if (viOpen(defaultRM, desc, VI_NULL, 5000, &instr) != VI_SUCCESS) {
						sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "viOpen failed in %s\r\n", desc);
						mw2Log(LogBuf);
						viFindNext(fList, desc);
						continue;
				} else mw2Log("Opened Device, ");
				
				viSetAttribute(instr, VI_ATTR_TMO_VALUE, 5000);

				if (viIn32(instr, VI_PXI_CFG_SPACE, 0, &dev_ven) != VI_SUCCESS) {
						viClose(instr);
						sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "viIn32 failed for %s\r\n", desc);
						mw2Log(LogBuf);
						viFindNext(fList, desc);
						continue;
				} else mw2Log("viIn32, ");

				// Can read the config registers - check the vendor/dev ID
				devId = HIWORD(dev_ven);
				venId = LOWORD(dev_ven);
				if ((venId != VID_XILINX) || ((devId != DID_MW4062) && (devId != DID_MW4122))){
						viClose(instr);
						sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "Vender ID wasn't 4062 or 4112 for %s\r\n", desc);
						mw2Log(LogBuf);	
						viFindNext(fList, desc);
						continue;
				} else mw2Log("Correct device ID and vendor ID, ");

				// Have an MW2 board. Read bar0.
				viIn32(instr, VI_PXI_CFG_SPACE, 0x10, &bar0);

				// check if bar0 is memory type
				if ((bar0 == 0) || ((ULONG)bar0 & 0x7) != 0) {
						viClose(instr);
						sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "Memory type not 7 for %s\r\n", desc);
						mw2Log(LogBuf);	
						viFindNext(fList, desc);
						continue;
				} else mw2Log("and Correct bar0\r\n");

				// Map the interface memory to the host virtual address
				if ((status = viMapAddress(instr, VI_PXI_BAR0_SPACE, 0, MW2_PHYSMEM_SIZE4*4, VI_FALSE, VI_NULL, &virAddr))  != VI_SUCCESS) {
						viClose(instr);
						mw2Log("Cannot map address\r\n");																//Debug
						continue;
				}

				// Get the slot number from the card status register of the board
				pxiSlot = 0;
				cardStatusRegAddr = (ULONG *)((char *)virAddr + MW2_INTF_CARD_STATUS_REG_ADDR4 * 4);
				geoAddr = ((*cardStatusRegAddr) >> 1) & 0x1f;
				if ((geoAddr > MAXSLOTS) || (geoAddr < 1)) {
						viUnmapAddress(instr);
						viClose(instr);
						mw2Log("Cannot find Slot Number\r\n");																//Debug
						continue;
				} else 
						pxiSlot = (unsigned short)geoAddr;

				numInstruments++;
				slots[i] = pxiSlot;
				
				viUnmapAddress(instr);		
				viClose(instr);
				sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "    ->Card found at address %s\r\n", desc);
				mw2Log(LogBuf);	
				viFindNext(fList, desc);
		}

		if (pusSlot != NULL) *pusSlot = numInstruments;
		//fclose(pLogFile);
		return (status);
} //--mw2ScanSystem()

//-------------------------------------------------------------------
// mw2InitHw() - Initializes the card hardware
//-------------------------------------------------------------------
BOOL mw2InitHw(unsigned short slot) {
		unsigned long regValue = mw2ReadRegister(slot, 0, 0xA);
		return (regValue != 0x002046); 
}

//-------------------------------------------------------------------
// mw2Shutdown() - Releases all resources for program exit
//-------------------------------------------------------------------
int mw2ShutDown(void)
{
	int mw2EC = MW2ECNOERR;
	int mw2Error, i;
	unsigned short usSlot;

	mw2Log("In mw2Shutdown\r\n");

	for (i = 0; i < MAXSLOTS; i++) {
			if(slots[i] != -1) {
					usSlot = slots[i];
					if ((mw2GetCardType(usSlot) != MW4062Type) && (mw2GetCardType(usSlot) != MW4122Type))
							continue;

					// reset and configure the card
					//mw2Error = mw2ResetCard(usSlot);
					//if (mw2Error != MW2ECNOERR)
							//mw2EC = mw2Error;

					// Release virtual memory
					if (MW2Channel[usSlot-1][0].cardBaseVirtualAddr != NULL){
							viUnmapAddress(MW2Channel[usSlot-1][0].instr);
							viClose(MW2Channel[usSlot-1][0].instr);
					}
			}
	}	
	viClose(defaultRM);
	return (mw2EC);
}

//-------------------------------------------------------------------
// mw2Shutdown() - Releases all resources for program exit
//-------------------------------------------------------------------
int mw2RescanSystem(unsigned int * pusSlot)
{
		int mw2EC = MW2ECNOERR;
		mw2Log("In mw2RescanSystem\r\n");

		// Rescan system
		mw2ShutDown();
		// Load physical memory  mapping driver
		mw2EC = viOpenDefaultRM(&defaultRM);
		if(mw2EC < VI_SUCCESS) { 	
				mw2Log("viOpenDefaultRM failed\r\n");
		}
		mw2ScanSystem(pusSlot);

		return (mw2EC);
}

//---------------------------------------------------------------------
// mw2GetCardType() - returns installed card type for the slot
//---------------------------------------------------------------------
CardType mw2GetCardType(unsigned short usSlot)
{
//	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo;
	USHORT devtype;
	chInfo = _mw2GetChIntf(usSlot, 0);
	if ((chInfo == NULL) || (chInfo->slot != usSlot))
		return UnknownType;
	devtype = chInfo->pciInfo.devId;
	switch(devtype) {
		case DID_MW4062:	return MW4062Type;
		case DID_MW4122:	return MW4122Type;
		default:			return UnknownType;
	}
}

//---------------------------------------------------------------------
// mw2GetCardName() - returns card name string
//---------------------------------------------------------------------
char *mw2GetCardName(CardType ctType)
{
//	int mw2EC = MW2ECNOERR;
	switch(ctType) {
		case MW4062Type:		return STR_MW4062;
		case MW4122Type:		return STR_MW4122;
		default:				return STR_UNKNOWN;
	}
}

//---------------------------------------------------------------------
// mw2GetCardDevId() - returns installed card Device ID of the slot
//---------------------------------------------------------------------
unsigned short mw2GetCardDevId(unsigned short usSlot)
{
//	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo;
	chInfo = _mw2GetChIntf(usSlot, 0);

	if ((chInfo == NULL) || (chInfo->slot != usSlot))	return 0x0000;
	else return (chInfo->pciInfo.devId);
}

//------------------------------------------------------------
unsigned long mw2GetFwVersion(unsigned short usSlot)
{
//	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo;
	chInfo = _mw2GetChIntf(usSlot, 0);
	return chInfo->model_vers.fwvers;
}

//------------------------------------------------------------
int mw2GetBusNo(unsigned short usSlot)
{
//	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo;
	chInfo = _mw2GetChIntf(usSlot, 0);
	return chInfo->pciInfo.pciBusNo;
}

//------------------------------------------------------------
int mw2GetDevNo(unsigned short usSlot)
{
//	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo;
	chInfo = _mw2GetChIntf(usSlot, 0);
	return chInfo->pciInfo.pciDevNo;
}

//------------------------------------------------------------
int mw2GetFuncNo(unsigned short usSlot)
{
//	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo;
	chInfo = _mw2GetChIntf(usSlot, 0);
	return chInfo->pciInfo.pciFuncNo;
}

/*
//---------------------------------------------------------------------
// mw2PrintChannelInfo() - prints channel data
//---------------------------------------------------------------------
void mw2PrintChannelInfo(USHORT slot, USHORT channel)
{
	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo = _mw2GetChIntf(slot, channel);
	CardType type = mw2GetCardType(slot);
//	printf("\r\nChannel: %d-%d %s\r\n", slot, channel, mw2GetCardName(type));
		_mw2PrintChInfo(chInfo);

}
*/
//------------------------------------------------------------
// mw2ResetCard() - puts the card in a known reset state
//		Issues a reset command to the FPGA.
//		Reference divider = 1
//		Reinitializes the PLL device (HMC833)
//		Channel output frequency = default value
//		Channel output power = default value (10 dBm or minimum power)
//		RF AMP = disabled state
//------------------------------------------------------------
int mw2ResetCard(unsigned short usSlot)
{
	int mw2EC = MW2ECNOERR;

	USHORT channel;										
	CardType cardType = mw2GetCardType(usSlot);
	double outputFreq = MW2_4062_FREQ_DEFAULT;

	_mw2DoCommand(usSlot, 0, USR_CMD_RESET, 0, 0, NULL);
	sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "Slot %d reset.\r\n", usSlot);
	mw2Log(LogBuf);

	// configure devices to their default states
	for (channel = 0; channel < MW2_MAX_CHANNELS; channel++) {
		mw2SetRefDivider(usSlot, channel, 1);
		_mw2InitHmc833(usSlot, channel);
		_mw2AmpEnable(usSlot, channel, TRUE);
		//mw2OutputOn(usSlot, channel, TRUE);

		if ((cardType == MW4122Type) && (channel == 0))
			outputFreq = MW2_4122_CH0_FREQ_DEFAULT;
		else
			outputFreq = MW2_4062_FREQ_DEFAULT;

		mw2SetChInfoFreq(usSlot, channel, outputFreq);
		//mw2SetPowerSeeprom(usSlot, channel, outputFreq,  MW2_POWER_MIN, mw2UseSEEPROMData(usSlot, channel));	// 10 dBm

		sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "In mw2ResetCard() Output off S%dC%d\r\n", usSlot, channel);
		mw2Log(LogBuf);
		mw2OutputOff(usSlot, channel);
	}
	// select internal reference clock
	mw2SelectClock(usSlot, ClockIntIntOff, 0, TRUE);

	return (mw2EC);
}

//------------------------------------------------------------
int mw2OutputOnC(unsigned short usSlot, unsigned short usChannel, BOOL mute,  unsigned long AttnValue)
{
	int mw2EC = MW2ECNOERR;
	ULONG R8;

	mw2Log("In mw2OutputOn\r\n");

	//_mw2AmpEnable(usSlot, usChannel, TRUE);	// enable AMPs.

	/*/ Set bit-4 of the Analog EN register (R8)
	R8 = mw2ReadRegister(usSlot, usChannel, 8);
	if (R8 == 0xffffffff) {
		mw2Log("mw2ReadRegister failed\r\n");
		mw2EC = MW2ECIO;
		return (mw2EC);
	}

	R8 |= 0x10;		// set bit-4
	mw2WriteRegister(usSlot, usChannel, 8, R8);
	//*/
	
	// HMC833: write 0x0d88 to R5 (VCO r1)
	//mw2WriteRegister(usSlot, usChannel, 5, 0x0d88);	//	0 0001 1011 0001 000	R1 Enable		
	mw2SetOutputFreqC(usSlot, usChannel, mw2GetOutputFreq(usSlot, usChannel), mute, AttnValue);

	mw2Log("Leaving mw2OutputOn\r\n");
	return (mw2EC);
}

//------------------------------------------------------------
int mw2OutputOn(unsigned short usSlot, unsigned short usChannel, BOOL mute)
{
		return mw2OutputOnC(usSlot, usChannel, mute, 100);
}

//------------------------------------------------------------
int mw2OutputOff(unsigned short usSlot, unsigned short usChannel)
{	
	int mw2EC = MW2ECNOERR;
	ULONG R8; 
	BOOL r;

	sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "In mw2OutputOff  Output off S%dC%d\r\n", usSlot, usChannel);
	mw2Log(LogBuf);
	mw2OutputOn(usSlot, usChannel, TRUE); // Turn the output to muted

	//_mw2AmpEnable(usSlot, usChannel, FALSE);	// disable AMPs.

	//%%%%% next block of code may not be necessary
	/*/ Clear bit-4 of the Analog EN register (R8)
	R8 = mw2ReadRegister(usSlot, usChannel, 8);
	if (R8 == 0xffffffff) {
		sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "mw2ReadRegister failed. - S%dC%d\r\n", usSlot, usChannel);
		mw2Log(LogBuf);
		mw2EC = MW2ECIO;
		return (mw2EC);
	}
	R8 &= ~0x10;	// clear bit-4
	r = mw2WriteRegister(usSlot, usChannel, 8, R8);
	//*/

	// HMC833: write 0x0d08 to R5 (VCO r01)
	//mw2WriteRegister(usSlot, usChannel, 5, 0x0d08);	//	000011010 0001 000	Reg0 Enable
	//mw2WriteRegister(usSlot, usChannel, 5, 0);		//	000000000 0000 000	Reg1 Tune
	//mw2WriteRegister(usSlot, usChannel, 5, 0x6000);	//	011000000 0000 000	Reg1 Tune	go to muted state(Steve, June 11) ????????
 
	//_mw2AmpEnable(usSlot, usChannel, FALSE);	// enable AMPs.	Redundent ????

	return (mw2EC);
}

//------------------------------------------------------------
int mw2ResetPll(unsigned short usSlot, unsigned short usChannel)
{
	// Note (June 19, 2012): A 2 millisecond pulse keeps
	// the PLL in the lock state. A 2 second pulse causes
	// some channels to fail - needs a power cycling.

	int mw2EC = MW2ECNOERR;

	sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "[%d-%d] Reset PLL device\r\n", usSlot, usChannel);
	mw2Log(LogBuf);

	_mw2PllChipEnable(usSlot, usChannel, FALSE);
	Sleep(35L);												
	_mw2PllChipEnable(usSlot, usChannel, TRUE);
	return (mw2EC);
}
//------------------------------------------------------------
int mw2SelectClock(unsigned short usSlot, ClockType clock, unsigned long clockMHz, BOOL writeToCard)
{
	MW2ChannelInfo *chInfo;
	double ch0ClockFreq, ch1ClockFreq;
	int mw2EC = MW2ECNOERR;

	// clockFreq is used for external clock only.
	switch(clock) {
		case ClockIntIntOff:
			ch0ClockFreq = MW2_CLK_INT_MHZ;
			ch1ClockFreq = MW2_CLK_INT_MHZ;
			break;
		case ClockIntIntInt:
			ch0ClockFreq = MW2_CLK_INT_MHZ;
			ch1ClockFreq = MW2_CLK_INT_MHZ;
			break;
		case ClockPxiPxiOff:
			ch0ClockFreq = MW2_CLK_PXI_MHZ;
			ch1ClockFreq = MW2_CLK_PXI_MHZ;
			break;
		case ClockExtExtOff:
			ch0ClockFreq = clockMHz;
			ch1ClockFreq = clockMHz;
			break;
		case ClockExtIntOff:
			ch0ClockFreq = clockMHz;
			ch1ClockFreq = MW2_CLK_INT_MHZ;
			break;
		case ClockPxiExtOff:
			ch0ClockFreq = MW2_CLK_PXI_MHZ;
			ch1ClockFreq = clockMHz;
			break;
		default:
			clock = ClockIntIntOff;
			ch0ClockFreq = MW2_CLK_INT_MHZ;
			ch1ClockFreq = MW2_CLK_INT_MHZ;
			break;
	}

	if (usSlot != 0) {

		sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "\r\n[%d]  mw2SelectClock, clock= %d\r\n", usSlot, (ULONG)clock);
		mw2Log(LogBuf);

		chInfo = _mw2GetChIntf(usSlot, 0);
		chInfo->refClockSource = clock;
		chInfo->refClockFreq = ch0ClockFreq;
		chInfo->refClockSet = clockMHz;

		chInfo = _mw2GetChIntf(usSlot, 1);
		chInfo->refClockSource = clock;
		chInfo->refClockFreq = ch1ClockFreq;
		chInfo->refClockSet = clockMHz;

		if(writeToCard){
				_mw2DoCommand(usSlot, 0, USR_CMD_CLK_SELECT, 0, (ULONG)clock, NULL);
				_mw2DoCommand(usSlot, 1, USR_CMD_CLK_SELECT, 0, (ULONG)clock, NULL);
		}
	}
	
	return (mw2EC);
}

//------------------------------------------------------------
// mw2GetClockType() - Returns the reference clock type for the card.
//------------------------------------------------------------
ClockType mw2GetClockType(unsigned short usSlot)
{
//	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo;
	chInfo = _mw2GetChIntf(usSlot, 0);
	return chInfo->refClockSource;
}

//------------------------------------------------------------
// mw2GetClockMHz() - Returns the frequency of currently
//		selected reference clock (in MHz) for the card.
//------------------------------------------------------------
double mw2GetClockMHz(unsigned short usSlot, unsigned short usChannel)
{
//	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo;
	chInfo = _mw2GetChIntf(usSlot, usChannel);
	return chInfo->refClockFreq;
}

//------------------------------------------------------------
// mw2GetClockMHz() - Returns the frequency of currently
//		selected reference clock (in MHz) for the card.
//------------------------------------------------------------
double mw2GetRefClockSet(unsigned short usSlot, unsigned short usChannel)
{
//	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo;
	chInfo = _mw2GetChIntf(usSlot, usChannel);
	return chInfo->refClockSet;
}
//------------------------------------------------------------
BOOL mw2Locked(unsigned short usSlot, unsigned short usChannel) 
{
//	int mw2EC = MW2ECNOERR;

	MW2ChannelInfo *chInfo = _mw2GetChIntf(usSlot, usChannel);
	if (chInfo == NULL) {
		sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "[%d-%d] mw2Locked: chInfo = NULL *****\r\n", usSlot, usChannel);
		mw2Log(LogBuf);
	} 
	return ((mw2ReadRegister(usSlot, usChannel, 0x12) & 0x02) == 0x02);
}

//------------------------------------------------------------
// mw2SetRefDivider() - Sets the PLL reference clock divider
//		for the selected channel.
//------------------------------------------------------------

int mw2SetRefDivider(unsigned short usSlot, unsigned short usChannel, unsigned long ulValue)
{
	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo;
	chInfo = _mw2GetChIntf(usSlot, usChannel);
	chInfo->refDivider = ulValue;
	_mw2WriteRegister(usSlot, usChannel, 2, ulValue);
	return (mw2EC);
}

//------------------------------------------------------------
// mw2GetRefDivider() - Returns current value of the PLL 
//		reference clock divider.
//------------------------------------------------------------
ULONG mw2GetRefDivider(unsigned short usSlot, unsigned short usChannel)
{
//	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo;
	chInfo = _mw2GetChIntf(usSlot, usChannel);
	return chInfo->refDivider;
}

int	mw2GetVcoCore(USHORT slot, USHORT channel) {
	int mw2EC = MW2ECNOERR;
	return (int) ((_mw2ReadRegister(slot, channel, 0x10)>>6)&0x00000003);
}

//-----------------------------------------------------------------------
// mw2SetOutputFreq() - Configures the PLL for the RF output frequency
//		To get the RF output on the front-panel connector, you need to
//		do the following additional operations:
//			- Set filter banks
//			- Set Power DAC for the desired output power level
//			- Set the low-pass filter for the output frequency
//			- Enable RF output amplifiers
//		Note that the requestfreqMHz is twice the PLL output frequency
//		for 4122 channel 0.
//-----------------------------------------------------------------------
int mw2SetOutputFreq(unsigned short usSlot, unsigned short usChannel, double requestfreqMhz, BOOL mute)
{
		return mw2SetOutputFreqC(usSlot, usChannel, requestfreqMhz, mute, 100);
}

//-----------------------------------------------------------------------
// mw2SetOutputFreqC() - Configures the PLL for the RF output frequency
//		To get the RF output on the front-panel connector, you need to
//		do the following additional operations:
//			- Set filter banks
//			- Set Power DAC for the desired output power level
//			- Set the low-pass filter for the output frequency
//			- Enable RF output amplifiers
//		Note that the requestfreqMHz is twice the PLL output frequency
//		for 4122 channel 0.
//-----------------------------------------------------------------------
int mw2SetOutputFreqC(unsigned short usSlot, unsigned short usChannel, double requestfreqMhz, BOOL mute, unsigned long AttnValue)
{
	int mw2EC = MW2ECNOERR;

	MW2ChannelInfo *chInfo;
	double freqMhz;
	BOOL unused;

	chInfo = _mw2GetChIntf(usSlot, usChannel);
	chInfo->outputFreqMhz = requestfreqMhz;	// Becareful of this one.  will it be used as is or /2

	// Set PLL output frequency. Beware that there is an x2 multiplier
	// in 4122 channel 0.
	if ((chInfo->pciInfo.devId == DID_MW4122) && (usChannel==0)) {
		freqMhz = requestfreqMhz/2;
		unused = TRUE;
	}
	else {
		freqMhz = requestfreqMhz;
		unused = FALSE;
	}

	sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "\n[%d-%d] Setting %s frequency to %f MHz\r\n", usSlot, usChannel, mw2GetCardName(mw2GetCardType(usSlot)), requestfreqMhz);
	mw2Log(LogBuf);

	// Configure the PLL.
	if ( !_mw2SetHmc833Freq(usSlot, usChannel, freqMhz, mute, unused, AttnValue) ) {
		sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "[%d-%d] ERROR in setting up the PLL.\r\n", usSlot, usChannel);
		mw2Log(LogBuf);
		return FALSE;
	}

	mw2Log("Returnin TRUE from mw2SetOutputFreq\r\n");
	return (mw2EC);
}

int mw2SetChInfoFreq(unsigned short  usSlot, unsigned short usChannel, double dRequestfreqMhz) 
{
	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo;
	chInfo = _mw2GetChIntf(usSlot, usChannel);
	chInfo->outputFreqMhz = dRequestfreqMhz;	// Becareful of this one.  will it be used as is or /2
	return (mw2EC);
}

//------------------------------------------------------------
// mw2GetOutputFreq() - Returns the RF output frequency for
//		the channel.
//------------------------------------------------------------
double mw2GetOutputFreq(unsigned short usSlot, unsigned short usChannel)
{
//	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo;
	chInfo = _mw2GetChIntf(usSlot, usChannel);
	return chInfo->outputFreqMhz;
}

//---------------------------------------------------------------------------------------
//                                () - Sets the filter bank switches for the specified output frequency
//		Check mw2Defs.h for details of the filter bank info.

////---------------------------------------------------------------------------------------
int mw2SetFilterBanksVCO (unsigned short usSlot, unsigned short usChannel, double dFreqMHz, unsigned long iVal)
{
	int mw2EC = MW2ECNOERR;
							 
	unsigned long vco, cap;
	ULONG fb0, fb1, fbAll;
	MW2ChannelInfo *chInfo = _mw2GetChIntf(usSlot, usChannel);

	fb0 = fb1 = fbAll = 0;

	// If it is the high-frequency channel of 4122, set filter bank 0.
	if ((chInfo->pciInfo.devId == DID_MW4122) && (usChannel==0))
//		if (dFreqMHz > 9000.0)	fb0 = MW2_CTRL_FB0A;
		if (dFreqMHz >8800.0)	fb0 = MW2_CTRL_FB0A;	// Test Code 130531
		else					fb0 = MW2_CTRL_FB0B;

	else {
//		if		(dFreqMHz > 3600.0)		fb0 = 0;
//		if		(dFreqMHz > 3750.0)		fb0 = 0;					// For RevC Hardware

		if (dFreqMHz > 4000) fb0 = 0;
		else if		(dFreqMHz >= 3910.0) {	
				//iVal = mw2ReadRegister(usSlot, usChannel, 0x10);
				vco = (iVal>>6)&0x00000003;
				cap = iVal&0x0000001F;
				if(cap > 15)
						fb0 = MW2_CTRL_FB0A;
				else
						fb0 = 0;
		}
		else if (dFreqMHz >= 3000.0)	fb0 = MW2_CTRL_FB0A;
		else if (dFreqMHz >2320) fb0 = MW2_CTRL_FB0B;
		else if (dFreqMHz >= 2230.0) 	{
				//iVal = mw2ReadRegister(usSlot, usChannel, 0x10);
				vco = (iVal>>6)&0x00000003;
				cap = iVal&0x0000001F;
				if(vco == 2){
						fb0 = (MW2_CTRL_FB0A | MW2_CTRL_FB0B);
						fb1 = (MW2_CTRL_FB1C | MW2_CTRL_FB1B | MW2_CTRL_FB1A	);
				}
				else
						fb0 = MW2_CTRL_FB0B;
		}
		else {
				fb0 = (MW2_CTRL_FB0A | MW2_CTRL_FB0B);
				// Second filter bank switch if f <= 2250 MHz
				if	(dFreqMHz >= 1500.0)	fb1 = (MW2_CTRL_FB1C | MW2_CTRL_FB1B | MW2_CTRL_FB1A	);
				else if (dFreqMHz >  1200.0)	fb1 = (MW2_CTRL_FB1C | MW2_CTRL_FB1B					);
				else if (dFreqMHz >   750.0)	fb1 = (MW2_CTRL_FB1C |				   MW2_CTRL_FB1A	);
				else if (dFreqMHz >   460.0)	fb1 = (MW2_CTRL_FB1C									);
				else if (dFreqMHz >   280.0)	fb1 = (				   MW2_CTRL_FB1B | MW2_CTRL_FB1A	);
				else if (dFreqMHz >   195.0)	fb1 = (				   MW2_CTRL_FB1B					);
				else if (dFreqMHz >	  145.0)	fb1 = (								   MW2_CTRL_FB1A	);
				else fb1 = 0;
		}
	}
	fbAll = fb0 | fb1;

	if (usChannel == 1) fbAll = fbAll << 5;
	
	// save info
	chInfo->useFilterBanks = FALSE;

	sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "\n[%d-%d] FBank = 0x%x\r\n", usSlot, usChannel, fbAll);
	mw2Log(LogBuf);

	// command to FPGA
	if (!_mw2DoCommand(usSlot, usChannel, USR_CMD_FBANK_SELECT, 0, fbAll, NULL)) {
		mw2Log("ERROR: FBank selection failed.\r\n");
		mw2EC = MW2ECIO;
	}
	return (mw2EC);
}

int mw2SetFilterBanks (unsigned short usSlot, unsigned short usChannel, double dFreqMHz)
{
	int mw2EC = MW2ECNOERR;
	ULONG fb0, fb1, fbAll;
	MW2ChannelInfo *chInfo = _mw2GetChIntf(usSlot, usChannel);

	fb0 = fb1 = fbAll = 0;

	// If it is the high-frequency channel of 4122, set filter bank 0.
	if ((chInfo->pciInfo.devId == DID_MW4122) && (usChannel==0))
//		if (dFreqMHz > 9000.0)	fb0 = MW2_CTRL_FB0A;
		if (dFreqMHz >8800.0)	fb0 = MW2_CTRL_FB0A;	// Test Code 130531
		else					fb0 = MW2_CTRL_FB0B;

	else {
//		if		(dFreqMHz > 3600.0)		fb0 = 0;
//		if		(dFreqMHz > 3750.0)		fb0 = 0;					// For RevC Hardware
		if		(dFreqMHz >= 3665.0)		fb0 = 0;					// Changed 130605
		else if (dFreqMHz >= 3000.0)	fb0 = MW2_CTRL_FB0A;
		else if (dFreqMHz >= 2259.0)	fb0 = MW2_CTRL_FB0B;
		else {
										fb0 = (MW2_CTRL_FB0A | MW2_CTRL_FB0B);
			// Second filter bank switch if f <= 3000 MHz
			if		(dFreqMHz >= 1500.0)	fb1 = (MW2_CTRL_FB1C | MW2_CTRL_FB1B | MW2_CTRL_FB1A	);
			else if (dFreqMHz >  1200.0)	fb1 = (MW2_CTRL_FB1C | MW2_CTRL_FB1B					);
			else if (dFreqMHz >   750.0)	fb1 = (MW2_CTRL_FB1C |				   MW2_CTRL_FB1A	);
			else if (dFreqMHz >   460.0)	fb1 = (MW2_CTRL_FB1C									);
			else if (dFreqMHz >   280.0)	fb1 = (				   MW2_CTRL_FB1B | MW2_CTRL_FB1A	);
			else if (dFreqMHz >   195.0)	fb1 = (				   MW2_CTRL_FB1B					);
			else if (dFreqMHz >	  145.0)	fb1 = (								   MW2_CTRL_FB1A	);
			else							fb1 = 0;
		}
	}
	fbAll = fb0 | fb1;

	if (usChannel == 1) fbAll = fbAll << 5;
	
	// save info
	chInfo->useFilterBanks = FALSE;

	sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "\n[%d-%d] FBank = 0x%x\r\n", usSlot, usChannel, fbAll);
	mw2Log(LogBuf);

	// command to FPGA
	if (!_mw2DoCommand(usSlot, usChannel, USR_CMD_FBANK_SELECT, 0, fbAll, NULL)) {
		mw2Log("ERROR: FBank selection failed.\r\n");
		mw2EC = MW2ECIO;
	}
	return (mw2EC);
}

//---------------------------------------------------------
// mw2GetFirstSlot() returns the first slot with an MW2 card
//---------------------------------------------------------
unsigned short mw2GetFirstSlot(void)
{
//	int mw2EC = MW2ECNOERR;
	return usFirstSlot;
}

///---------------------------------------------------------
// mw2GetLastSlot() returns the last slot with an MW2 card
//---------------------------------------------------------
unsigned short mw2GetLastSlot(void)
{
//	int mw2EC = MW2ECNOERR;
	return usLastSlot;
}

///---------------------------------------------------------
// mw2GetSlotList() returns a list of slots that have cards in them. 
//---------------------------------------------------------
short* mw2GetSlotList(void)
{
//	int mw2EC = MW2ECNOERR;
	return slots;
}

///-----------------------------------------------------------------------------
// mw2SetAttenuatorDac() - writes to the attenuator DAC (a.k.a., PDAC (AD5621))
//		The DAC value 0 is for no attenuation, 0xfff is for the maximum 
//		attenuation.
//-----------------------------------------------------------------------------
int mw2SetAttenuatorDac(unsigned short usSlot, unsigned short usChannel, unsigned short usDacValue)
{
	int mw2EC = MW2ECNOERR;
	unsigned short usDevice = (usChannel== 0)? 4 : 5;

	MW2ChannelInfo *chInfo = _mw2GetChIntf(usSlot, usChannel);
	chInfo->attenuatorDac = usDacValue;
	mw2EC = mw2WriteRegister(usSlot, usDevice, 0, usDacValue);

	return (mw2EC);
}

USHORT mw2GetAttenuatorDac(unsigned short usSlot, unsigned short usChannel)
{
//	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo;
	chInfo = _mw2GetChIntf(usSlot, usChannel);
	return chInfo->attenuatorDac;
}

//----------------------------------------------------------------
// mw2SetFilterDac() - writes to the Low-pass Filter DAC (AD5621)
//		The value 0 is for lowest cutoff frequency, 
//		0xfff is for the highest cutoff frequency.
//----------------------------------------------------------------
int mw2SetFilterDac(unsigned short usSlot, unsigned short usChannel, unsigned short usDacValue)
{
	int mw2EC = MW2ECNOERR;
	unsigned short usDevice = (usChannel== 0)? 2 : 3;

	MW2ChannelInfo *chInfo = _mw2GetChIntf(usSlot, usChannel);
	chInfo->filterDac = usDacValue;
	mw2WriteRegister(usSlot, usDevice, 0, usDacValue);

	return(mw2EC);
}

unsigned short mw2GetFilterDac(unsigned short usSlot, unsigned short usChannel)
{
//	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo;
	chInfo = _mw2GetChIntf(usSlot, usChannel);
	return chInfo->filterDac;
}
//----------------------------------------------------------------------------------------------------------------
// mw2GetCalData() - Reads from the EeProm and gets back the cal data for the specified channel and position
//		channel can be 0 or 1 
//		pos can be 0-9, and represents the 10 available temperature profiles for each channel
//		if buffer[0] == (short)0xFFFF, then cal data wasn't found at that channel/pos
//		else cal data exists at that position, and buffer can be used to create an Estimation object.  
//----------------------------------------------------------------------------------------------------------------
int mw2GetCalData(unsigned short slot,unsigned short channel, unsigned short pos, UCHAR* buffer) {
		unsigned short start;
		BOOL found = FALSE;
		short buf[CAL_DATA_LEN];
		int err = MW2ECNOERR;
		unsigned short devId;
		if(pos < 10) {
				// ====================================================================
				// Channel 0 data
				// ====================================================================
				start = (channel == 0)? CH0_START+pos*CAL_DATA_LEN : CH1_START+pos*CAL_DATA_LEN;
				if(found == FALSE && (err = mw2ReadEeProm(slot, start, HEADER_LEN, buf)) == MW2ECNOERR) {
						if((devId = mw2GetCardDevId(slot)) != (unsigned short)0x4122 && 
								buf[0] == (short)FREQ_LEN && buf[1] == (short)PDAC_LEN && buf[2] == (short)PDAC_POW_LEN) {
										err = mw2ReadEeProm(slot, start, CAL_DATA_LEN, buffer);
										if(buffer[7] != 4062) { // Making sure the added values to Header are present (needed for CalculateEstimates to work)
												*(buffer+8) = HEADER_LEN;
												*(buffer+10) = PDAC_START;
												*(buffer+11) = PDAC_START >> 8;
												*(buffer+12) = PDAC_FREQ_LEN;
												*(buffer+13) = PDAC_FREQ_LEN >> 8;
												*(buffer+14) = 4062;
												*(buffer+15) = 4062>>8;
										}
										found = TRUE;
						} else if(channel == 0 && devId == (unsigned short)0x4122 && 
								buf[0] == (short)FREQ_LEN_4122 && buf[1] == (short)PDAC_LEN_4122 && buf[2] == (short)PDAC_POW_LEN_4122) {
										err = mw2ReadEeProm(slot, start, CAL_DATA_LEN, buffer);
										if(buffer[7] != 4122) {
												*(buffer+8) = HEADER_LEN_4122;
												*(buffer+10) = PDAC_START_4122;
												*(buffer+11) = PDAC_START_4122 >> 8;
												*(buffer+12) = PDAC_FREQ_LEN_4122;
												*(buffer+13) = PDAC_FREQ_LEN_4122 >> 8;
												*(buffer+14) = 4122;
												*(buffer+15) = 4122>>8;
										}
										found = TRUE;
						} else if(channel == 1 && devId == (unsigned short)0x4122 && 
								buf[0] == (short)FREQ_LEN && buf[1] == (short)PDAC_LEN && buf[2] == (short)PDAC_POW_LEN) {
										err = mw2ReadEeProm(slot, start, CAL_DATA_LEN, buffer);
										if(buffer[7] != 4062) {
												*(buffer+8) = HEADER_LEN;
												*(buffer+10) = PDAC_START;
												*(buffer+11) = PDAC_START >> 8;
												*(buffer+12) = PDAC_FREQ_LEN;
												*(buffer+13) = PDAC_FREQ_LEN >> 8;
												*(buffer+14) = 4062;
												*(buffer+15) = 4062>>8;
										}
										found = TRUE;
						} 
				}
		}
		if(found == FALSE) {
				*buffer = 0xFFFF;
				*(buffer+1) = 0xFFFF>>8;
		}
		return err;
}

//=========================================================
// Low level functions
//=========================================================

//----------------------------------------------------------
// _mw2GetChIntf() - returns  pointer or NULL
//----------------------------------------------------------
MW2ChannelInfo * _mw2GetChIntf(USHORT slot, USHORT ch)
{
	USHORT iCh;
	MW2ChannelInfo *info;

	if ((slot > MAXSLOTS) || ((ch >= MW2_MAX_CHANNELS) && (ch != MW2_CH_CARD))) {
		sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "_mw2GetChIntf[%d-%d]: Bad slot-channel\r\n", slot, ch);
		mw2Log(LogBuf);
//		mw2Log(LogBuf);
//		printf("%s", LogBuf);
		return NULL;
	}
	iCh = (ch == MW2_CH_CARD)? 0 : ch;
	info = &MW2Channel[slot - 1][iCh];
	return info;
} //--_mw2GetChIntf()

//------------------------------------------------------------
// _mw2WriteRegister() - writes a register of the SPI device.
//------------------------------------------------------------
BOOL _mw2WriteRegister(USHORT slot, USHORT dev, USHORT reg, ULONG value)
{

//	sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "[%d-%d:%d] 0x%06x\n", slot, dev, reg, value);
//	mw2Log(LogBuf);
	return _mw2DoCommand(slot, dev, USR_CMD_WRITE_REG, reg, value, NULL);
}

//------------------------------------------------------------
// _mw2ReadRegister() - reads a register of the SPI device
//------------------------------------------------------------
ULONG _mw2ReadRegister(USHORT slot, USHORT dev, USHORT reg)
{
	ULONG value = 0xffffffff;
	if (_mw2DoCommand(slot, dev, USR_CMD_READ_REG, reg, 0, &value))
		return value;
	else {
		fprintf(stderr,"_mw2ReadRegister: _mw2DoCommand failed.");
		return value;
	}
}

//---------------------------------------------------------
// _mw2PrintPCIInfo() - Prints PCIInfo data structure
//---------------------------------------------------------
void _mw2PrintPCIInfo(PCIInfo *info)
{
//	printf("PCI=%d.%d.%d  BAR0=0x%x ", 
//		info->pciBusNo, info->pciDevNo, info->pciFuncNo, info->barZero);
//	printf("Vendor=0x%04x(%s) Device=0x%04x(%s)\r\n",
//		info->vendorId, info->vendorName, info->devId, info->deviceName);
}

//--------------------------------------------------------------
// _mw2InitHmc833() - Initializes HMC833 PLL device to 2000 MHz
//---------------------------------------------------..---------
static void _mw2InitHmc833(USHORT slot, USHORT channel) 
{
	_mw2WriteRegister(slot, channel, 5, 0x000d88);	//	0000  [4]:1  [3]:1  [2]:0  [1]:1  [0]:1 0001 000	R1 Enable 
	_mw2WriteRegister(slot, channel, 5, 0x008010);	//	100000001 0010 000	R2 Biases	Fo Max Gain
	_mw2WriteRegister(slot, channel, 5, 0x002898);	//	001010001 0011 000	R3 Config	2xxx ?
	_mw2WriteRegister(slot, channel, 5, 0x0060A0);	//	011000001 0100 000	R4 Cal/Bias	Default
//	Sleep(40L);
	_mw2WriteRegister(slot, channel, 5, 0x001628);	//	000101100 0101 000	R5 CF_Cal Default
	_mw2WriteRegister(slot, channel, 5, 0);			//	000000000 0000 000	R0 Tune
	_mw2WriteRegister(slot, channel, 6, 0x2003CA); // Set to always use fractional mode, autocal occurs on write to fractional register (Reg 04h)
	// [23:12]:110000011011  [11]:1  [10]:1  [9]:1  [8]:0  [7]:1  [6]:1  [5]:1  [4]:1  [3]:1  [2]:1  [1]:1  [0]:1  
	_mw2WriteRegister(slot, channel, 8, 0xC1BEFF);  // 11OO OOO1 1O11 111O 1111 1111
	_mw2WriteRegister(slot, channel, 9, 0x153E7C);
	//                   [16]:0  [15]:0  [14:13]:01 [12]:0  [11]:0  [10]:0  [9:8]:00  [7:6]:01  [5:3]:000  [2:0]:110
	// DEFAULT- [16]:0  [15]:0  [14:13]:01 [12]:0  [11]:0  [10]:0  [9:8]:10  [7:6]:00  [5:3]:000  [2:0]:101
	_mw2WriteRegister(slot, channel, 0xA, 0x002046); 
	//                   [23:22]:00  [21:20]:00  [19]:1  [18:17]:11  [16:15]:11  [14:12]:100  [11]:0  [10]:0  [9]:0  [8:7]:00  [6]:1  [5]:1  [4]:0  [3]:0  [2:0]:001  
	// DEFAULT- [23:22]:00  [21:20]:00  [19]:1  [18:17]:11  [16:15]:11  [14:12]:000  [11]:0  [10]:0  [9]:0  [8:7]:00  [6]:1  [5]:1  [4]:0  [3]:0  [2:0]:001  
	_mw2WriteRegister(slot, channel, 0xB, 0x07C061);
	//                   [9]:0  [8]:0  [7]:1  [6]:0  [5]:0  [4:0]:00001  
	// DEFAULT- [9]:0  [8]:0  [7]:0  [6]:0  [5]:0  [4:0]:00001  
	_mw2WriteRegister(slot, channel, 0xF, 0x000081);
	_mw2WriteRegister(slot, channel, 2, mw2GetRefDivider(slot, channel));
	_mw2WriteRegister(slot, channel, 3, 0x000028);
	_mw2WriteRegister(slot, channel, 4, 0x0);
}

//----------------------------------------------------------------------------
// _mw2SetHmc833Freq() - Configures HMC833 PLL device for specified frequency
//----------------------------------------------------------------------------
static BOOL _mw2SetHmc833Freq(USHORT slot, USHORT channel, double freqMHz, BOOL mute, BOOL unused, ULONG AttnValue) {
	// Configure HMC833 for a frequency and attenuation.
	// All frequencies in MHz.
	
	double K, FreqExtRef, F_frac, Tvco, FullChPump, FreqComp, B25, x, f;
	ULONG RefDivide, F_int, n, cpDnGain, cpUpGain, cpOffset, R6, R9, r2, r3, B31;

	sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "In _mw2SetHmc833Freq: freq=%f\r\n", freqMHz);
	mw2Log(LogBuf);
//	mw2Log(LogBuf);

	// calculate K (0.5 for doubler, 1 for fundamental, then 2, 4, ... 62.
	if ((freqMHz < 25.0) || (freqMHz > 6000.0))
		return FALSE;

	if (freqMHz >= 3000.0)
		K = 0.5;		// doubler
	else if (freqMHz >= 1500.0)
		K = 1.0;		// fundamental
	else {
		// divider case
		x = (double)1500.0/freqMHz;
		n = (ULONG)x;
		if (n > 31)
			n = 31;
		K = 2 * n;
	}

//	RefDivide = _mw2ReadRegister(slot, channel, 2);	// reference divider
	RefDivide = mw2GetRefDivider(slot, channel);	// reference divider

	if (RefDivide == 0){
		mw2Log("R=0\r\n");
		return FALSE;
	}
	FreqExtRef = mw2GetClockMHz(slot, channel);		// reference freq.
	if (FreqExtRef < 1.0){
		mw2Log("F-xtal < 1.0\r\n");
		return FALSE;
	}

	// calculate integer and fractional frequency
	f =  K * RefDivide * freqMHz / FreqExtRef;
	F_int = (ULONG)(f);	
	F_frac = (f - F_int) * (1 << 24);
	// Register 06
	R6 = ((ULONG)F_frac == 0)? 0x2003ca : 0x200b4a; 
	// 200b4a default= (001000000000) 1autocal_on_frac (0clk 1clk 1autoseed) 0dont_bypass (100reserved 10order 10seed)
	// 2003ca alt =         (001000000000) 0autocal_on_int  (0      1      1)                 1bypass_frac   (100                10          10) (same)

	// calculate charge pump register (R09)
	//Tvco = 1.0 / ((double)2250 * (double)1000000L);
	Tvco = 1.0 / (f *FreqExtRef* (double)1000000L);
	FullChPump = 0.0025;
	FreqComp = FreqExtRef*1000000/RefDivide;	// in Hz
	x = (0.0000000025+4*Tvco)*FreqComp*FullChPump;
	B25 = (x < 0.25*FullChPump)? x : 0.25*FullChPump;	// smaller of the two
	n = (ULONG)(B25/0.000005 + 0.5); 
	cpDnGain = (ULONG)(FullChPump/0.00002);
	cpUpGain = cpDnGain;
	R9 = 0;
	if (F_frac == 0) {
		cpOffset = 0;
	} else {
		cpOffset = (n > 127)? 127 : n;	// R09[20:14]
		R9 |= 1 << 22;
	}
	R9 |= ((cpOffset & 0x7f) << 14);
	R9 |= ((cpUpGain & 0x7f) << 7);
	R9 |= (cpDnGain & 0x7f);

	sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "Hmc833 freq=%f, ref=%f, K=%f, cpOffset=0x%x, R9=0x%x\r\n",
			freqMHz, FreqExtRef, K, cpOffset, R9);
	mw2Log(LogBuf);
//	mw2Log(LogBuf);

	// VCO subsystem reg 02 (Biases)
	r2 = 0;
	// bit-8
	if (K <= 2)
		r2 = 0x0100;

	// bit-0, mute leaves this value as a 0, else set it to the value of K
	if(mute == FALSE) {
			if (K < 1)
					r2 |= 0x0001;
			else
					r2 |= ((ULONG)K & 0x3f);
	}
	if ((AttnValue==0)||(AttnValue==3)||(AttnValue==6)||(AttnValue==9))
			B31 = AttnValue;
	else 
			B31 = 9;
	
	//*/

	if (B31 == 0)					// >3000M 0
		r2 |= (0x0003 << 6);		// 11
	else if (B31 == 3)
		r2 |= (0x0002 << 6);		// 10
	else if (B31 == 6)				// 25M-1500M	// 1500M-3000M
		r2 |= (0x0001 << 6);		// 01
	else
		r2 |= 0;

	r2 = (r2 << 7) | (2 << 3);		// address = 2

	// r3
	r3 = (K == 0.5)? 0x40 : 0x51; // should be 0x40 : 0x51,  left alone for closer estimate to range [8:5]:0010  [4:3]:00 [2]:0  [1]:0  [0]:0  or  [8:5]:0010  [4:3]:10  [2]:0  [1]:0  [0]:1
	r3 = (r3 << 7) | (3 << 3);		// address = 3

	if(mute == FALSE)
			_mw2WriteRegister(slot, channel, 7, 0x14D);		// Turn on lock detect
	else
			_mw2WriteRegister(slot, channel, 7, 0x145);		// Turn off lock detect	
	// write to the device in the following order:
	_mw2WriteRegister(slot, channel, 5, r2);		// R2 Bias	
	_mw2WriteRegister(slot, channel, 5, r3);		// R3 Config
	//_mw2WriteRegister(slot, channel, 5, 0x60a0);	// 01 10 00 001 0100 000 R4 CalBas
	//	Sleep(50L);
	//_mw2WriteRegister(slot, channel, 5, 0x1628);	// 0 00 10 11 00 0101 000 R5 CF_Cal
	//	_mw2WriteRegister(slot, channel, 5, 0x0080);	// R0 Tune temperature compensated calibration voltage

	_mw2WriteRegister(slot, channel, 5, 0);			// R0 Tune
	_mw2WriteRegister(slot, channel, 6, R6);
	_mw2WriteRegister(slot, channel, 9, R9);
	//_mw2WriteRegister(slot, channel, 0xa, 0x002046);
	//_mw2WriteRegister(slot, channel, 0xb, 0x07C061);
	//_mw2WriteRegister(slot, channel, 0xf, 0x000081);

	// Why write back the value read from the device in the first place?
	//_mw2WriteRegister(slot, channel, 2, RefDivide); 
	_mw2WriteRegister(slot, channel, 3, F_int);
	_mw2WriteRegister(slot, channel, 4, (ULONG)(F_frac + 0.5));
	
	sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "%d %f r2: %d r3: %d\r\n", F_int, F_frac, r2, r3);
	mw2Log(LogBuf);
	mw2Log("Leaving _mw2SetHmc833Freq\r\n");
	return TRUE;
}


//----------------------------------------------------------
// _mw2DoCommand() - Issues a command to MW2device
//	dev: device number (0-5) or channel number
//  cmd:
//		USR_CMD_RESET
//		USR_CMD_CLK_SELECT	(data = MW2_CLK_INT, MW2_CLK_ENT or MW2_CLK_PXI10)
//		USR_CMD_FBANK_SELECT (dev = channel, data = channel control register image)
//		USR_CMD_AMP_SELECT (output on/off)
//		USR_CMD_RERAD_REG
//		USR_CMD_WRITE_REG
//  All unused arguments should be set to zero.
//
// %%% Replace this function with separate functions for
//     each device (PLL, DAC, EEPROM, FPGA, etc.)
//----------------------------------------------------------
static BOOL _mw2DoCommand(USHORT slot, USHORT dev, ULONG cmd, ULONG addr4, ULONG data, ULONG *pdata)
{
	MW2ChannelInfo *info = _mw2GetChIntf(slot, 0);
	static ULONG clockSelect;
	ULONG reg;

	if (dev > (MW2_MAX_CHANNELS * 3 - 1)) {
		return FALSE;
	}

	// handle card RESET request
	if (cmd == USR_CMD_RESET) {
		*(info->cardCmdReg) = 0;	// clear the command register
		Sleep(5L);
		*(info->cardCmdReg) = MW2_CMD_RESET;
		Sleep(5L);					// 5 millisecond 
		*(info->cardCmdReg) = 0;	// clear the command register
		Sleep(5L);					// 45 millisecond 

		mw2Log("_mw2DoCommand - USR_CMD_RESET\r\n");
//		mw2Log("_mw2DoCommand - USR_CMD_RESET\n");

		return TRUE;		
	}
	
	//------------------------------------------------------
	// Check the request bit in the card command register
	//------------------------------------------------------
	if (*(info->cardCmdReg) & MW2_CMD_REQ) {
		*(info->cardCmdReg) = 0;
	}
	
	// Process the command
	//		USR_CMD_CLK_SELECT
	//		USR_CMD_FBANK_SELECT
	//		USR_CMD_RERAD_REG
	//		USR_CMD_WRITE_REG

	if (cmd == USR_CMD_CLK_SELECT) {

		if		(data == ClockIntIntOff) *info->chCmdReg = MW2_CTRL_CLK_INTINTOFF_VAL;
		else if (data == ClockIntIntInt) *info->chCmdReg = MW2_CTRL_CLK_INTINTINT_VAL;
		else if (data == ClockPxiPxiOff) *info->chCmdReg = MW2_CTRL_CLK_PXIPXIOFF_VAL;
		else if (data == ClockExtExtOff) *info->chCmdReg = MW2_CTRL_CLK_EXTEXTOFF_VAL;
		else if (data == ClockExtIntOff) *info->chCmdReg = MW2_CTRL_CLK_EXTINTOFF_VAL;
		else if (data == ClockPxiExtOff) *info->chCmdReg = MW2_CTRL_CLK_PXIEXTOFF_VAL;
		else							 *info->chCmdReg = MW2_CTRL_CLK_INTINTOFF_VAL;
		
		*info->chAddr4Reg = 0;
		*info->chLen4Reg = 32;

		// Generate a short pulse of bit-18
		*info->cardCmdReg = MW2_CMD_CLKSEL_LATCH; 

		sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "_mw2DoCommand - USR_CMD_CLK_SELECT - %08X - %08X\r\n", *info->chCmdReg, *info->cardCmdReg);
		mw2Log(LogBuf);

		Sleep(1L);

		*info->cardCmdReg = 0;
		return TRUE;
	} 


/*
	else if (cmd == USR_CMD_FBANK_SELECT) {
		// dev = channel, data = fb bit fields
		reg = *info->chCmdReg;	// read current value and clear FB bits
		reg &= (dev == 0)? MW2_CTRL_FBCH0_ALL : MW2_CTRL_FBCH1_ALL;
		reg |= data;	// set new FB bits
		*info->chCmdReg = reg;	// tell the FPGA
		*info->chAddr4Reg = 0;
		*info->chLen4Reg = 32;*info->chCmdReg = data;
		if (dev == 0)
			*info->chCmdReg = MW2_CMD_FB0_LATCH;
		else
			*info->chCmdReg = MW2_CMD_FB1_LATCH;
		Sleep(1L);
		*info->chCmdReg = 0;

		sprintf_s(buff, 200, "_mw2DoCommand - USR_CMD_FBANK_SELECT - %08X\n", data);
		mw2Log(buff);

		return TRUE;
	}
*/
	else if (cmd == USR_CMD_FBANK_SELECT) {
		// dev = channel, data = fb bit fields
		reg = *info->chCmdReg;	// read current value and clear FB bits
//		reg &= (dev == 0)? MW2_CTRL_FBCH0_ALL : MW2_CTRL_FBCH1_ALL;
		reg &= (dev == 0)? (~MW2_CTRL_FBCH0_ALL) : (~MW2_CTRL_FBCH1_ALL);
		reg |= (dev == 0)? (MW2_CTRL_FBCH0_ALL & data) : (MW2_CTRL_FBCH1_ALL & data);   ;	// set new FB bits
		*info->chCmdReg = reg;	// tell the FPGA
//		*info->chCmdReg = data;
		*info->chAddr4Reg = 0;
		*info->chLen4Reg = 32;
		if (dev == 0)
//		*info->chCmdReg = MW2_CMD_FB0_LATCH; ???
			*info->cardCmdReg = MW2_CMD_FB0_LATCH;
		else
//			*info->chCmdReg = MW2_CMD_FB1_LATCH;
			*info->cardCmdReg = MW2_CMD_FB1_LATCH;
		Sleep(1L);
//		*info->chCmdReg = 0;
		*info->cardCmdReg = 0;

		sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "_mw2DoCommand - USR_CMD_FBANK_SELECT - %08X\r\n", reg);
		mw2Log(LogBuf);
//		mw2Log(LogBuf);

		return TRUE;
	}


	else if (cmd == USR_CMD_AMP_SELECT) {
		// dev = channel, 
//		reg = *info->chCmdReg;	// read current value and clear FB bits
		reg = (dev == 0)? MW2_CTRL_AMPEN_0 : MW2_CTRL_AMPEN_1;
		reg |= data;	// set new AMP bits

		*info->chCmdReg = reg;	// tell the FPGA
		*info->chAddr4Reg = 0;
		*info->chLen4Reg = 32;
		*info->chCmdReg = data;
		if (dev == 0)
			*info->chCmdReg = MW2_CMD_AMP0_LATCH;
		else
			*info->chCmdReg = MW2_CMD_AMP1_LATCH;
		Sleep(1L);
		*info->chCmdReg = 0;

		sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "_mw2DoCommand - USR_CMD_AMP_SELECT - %08X\r\n", data);
		mw2Log(LogBuf);
//		mw2Log(LogBuf);

		return TRUE;
	}
	else if (cmd == USR_CMD_READ_REG) {
		// Read a register of an SPI device.
		// The length is 32 bits for the PLL device.
		// AD5621 does not support read operation.
		if (dev >= MW2_MAX_CHANNELS)
			return FALSE;
		*info->chAddr4Reg = (dev << 16) | addr4;
		*info->chLen4Reg = 32;
		*info->chCmdReg = MW2_CMD_RD_FLAG;
		*info->cardCmdReg = MW2_CMD_REQ;
		if (_mw2WaitForDone(info)) {
			*info->cardCmdReg = 0;
			*pdata = *info->cardSpiReadData;
			return TRUE;
		}
		*info->cardCmdReg = 0;
		*pdata = *info->cardSpiReadData;

		sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "_mw2DoCommand - USR_CMD_READ_REG - DevAddr:%08X; Data:%08X, Len:%08X\r\n", *info->chAddr4Reg, *pdata, *info->chLen4Reg);
		mw2Log(LogBuf);
//		mw2Log(LogBuf);

		return FALSE;
	}
	else if (cmd == USR_CMD_WRITE_REG) {
		if (dev < MW2_MAX_CHANNELS) {
			// PLL device
			*info->chAddr4Reg = (dev << 16) | addr4;
			*info->cardSpiWriteData = data;
			*info->chLen4Reg = 32;
		}
		else {
			// AD5621: no register address, 12-bit data left-shifted by 2 bits
			*info->chAddr4Reg = dev << 16;
			*info->cardSpiWriteData = (data & 0x0fff) << 2;
			*info->chLen4Reg = 16;
		}
		*info->chCmdReg = MW2_CMD_WR_FLAG;
		*info->cardCmdReg = MW2_CMD_REQ;
		if (_mw2WaitForDone(info)) {
			*info->cardCmdReg = 0;
			return TRUE;
		}
		*info->cardCmdReg = 0;

		sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "_mw2DoCommand - USR_CMD_WRITE_REG - DevAddr:%08X; Data:%08X, Len:%08X\r\n", *info->chAddr4Reg, *info->cardSpiWriteData, *info->chLen4Reg);
		mw2Log(LogBuf);
//		mw2Log(LogBuf);

		return FALSE;
	}
	return TRUE;
} //-- _mw2DoCommand()

//-------------------------------------------------------
static BOOL _mw2WaitForDone(MW2ChannelInfo *info) 
{
	int i;
	for (i = 0; i < 10000; i++) {
//	for (i = 0; i < 65535; i++) {
		if (*info->cardStatusReg & MW2_CMD_REQ)
			break;
//		Sleep(10L);		// 10 msec
		Sleep(1L);		// 1 msec
	}
	return TRUE;
}

static BOOL _mw2WaitForEePromDone5L(MW2ChannelInfo *info) 
{
	int i;
	for (i = 0; i < 100; i++) {
//	for (i = 0; i < 65535; i++) {
		if (*info->cardStatusReg & MW2_CMD_REQ)
			break;
		Sleep(5L);		// 5 msec
	}
	return TRUE;
}

static BOOL _mw2WaitForEePromDone1L(MW2ChannelInfo *info) 
{
	int i;
	for (i = 0; i < 100; i++) {
//	for (i = 0; i < 65535; i++) {
		if (*info->cardStatusReg & MW2_CMD_REQ)
			break;
		Sleep(1L);		// 1 msec
	}
	return TRUE;
}

/*
//-------------------------------------------------------
static BOOL _mw2WaitForEePromDone(MW2ChannelInfo *info) 
{
	long i;
	BOOL bResult = FALSE;

//	for (i = 0; i < 100; i++) {
//	for (j = 0; j < 65535; j++) {
		for (i = 0; i < 65535; i++) {
			if (*info->cardStatusReg & MW2_CMD_REQ) {
				bResult = TRUE;
				break;
			}
//			Sleep(1L);		// 1 msec
			Sleep(0L);		// 1 msec
		}
//		if (bResult == TRUE) break;
//	}
//	while ((*info->cardStatusReg & MW2_CMD_REQ) != MW2_CMD_REQ) {	
//		Assuming firmware will always return a "Ready" status sooner or later.
//
//		Sleep(10L);		// 10 msec
	return bResult;
}
*/
//---------------------------------------------------------
static void _mw2PrintChInfo(MW2ChannelInfo *info)
{
	char *status = (mw2Locked(info->slot, info->ch))? "Lock OK" : "Lock Lost";
//	printf("Frequency = %.5f MHz\r\n", info->outputFreqMhz);
//	printf("Attenuation = %.2f dB\r\n", info->outputPower);
//	printf("PLL status = %s\r\n", status);
}

//---------------------------------------------------------
// _mw2Hmc882DacVal() - returns the DAC value for the
//	specified cutoff frequency of the low-pass filter.
//	Assume no slot/channel dependence for now.
//
//  v in volts, f in MHz
//
//  v = 5.0e-7 f^2 - 0.0024f + 1.9159
//
//  v = 10 * D/4096, D = 409.6 * v
//---------------------------------------------------------
static USHORT	_mw2Hmc882DacVal(double cutoffFreqMHz)
{
	// assume no device dependence
	double f = cutoffFreqMHz;
	double volts;
	USHORT D;
	if (f < 4.25)
		D = 0;
	if (f > 7980.0)
		D = 4095;

	volts = f * (5.0e-7 * f - 0.0024) + 1.916;
	D = (USHORT)(409.6 * volts);
	if (D == 4096)
		D = 4095;
	return D;
}

//---------------------------------------------------------
// _mw2Hmc346DacVal() - returns the DAC value for the
// specified attenuation value.
//
//	att <= 5.0 dB: a = -2.2222v, v = a / (-2.2222)
//  att <= 10.0 dB: a = -16.667v - 32.5, v = (a + 32.5) / (-16.667)
//  att > 10.0 dB: a = -57.143v - 135.71, v = (a + 135.71) / (-57.143)
//
//  v = -5.0 * D/4096,  D = -v * 4096/5 = -819.2 * v
//---------------------------------------------------------
static USHORT _mw2Hmc346DacVal(USHORT slot, USHORT dev, double attenDb)
{
	USHORT D;
	if (attenDb <= 0.0)
		D = 0;
	else if (attenDb <= 5.0)
		D = (USHORT)((-819.2) * attenDb / (-2.222));
	else if (attenDb <= 10.0)
		D = (USHORT) ((-819.2) * (attenDb + 32.5) / (-16.667));
	else if (attenDb <= 30.0)
		D = (USHORT)((-819.2) * (attenDb + 135.71) / (-57.143));
	else
		D = 4095;
	if (D = 4096)
		D = 4095;
	return D;
}

//---------------------------------------------------------------------
static BOOL _mw2PllChipEnable(USHORT slot, USHORT channel, BOOL enable)
{
	MW2ChannelInfo *info = _mw2GetChIntf(slot, 0);
	ULONG ceSel = MW2_CE_ALL;

	// latch in all ones first
	*(info->chCmdReg) = ceSel;
	// Generate a short pulse of CE_LATCH bit
	_mw2CmdPulse(slot, MW2_CMD_CE_LATCH);

	if (!enable)	
		ceSel &= ~((MW2_CMD_CE_LATCH) << channel);
	*(info->chCmdReg) = ceSel;

	// Generate a short pulse of CE_LATCH bit
	_mw2CmdPulse(slot, MW2_CMD_CE_LATCH);

	// log channel control register
	sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "[%d-%d] PllChipEnable(%s) Reg=0x%x\r\n",
		slot, channel, (enable)? "enable" : "disable", ceSel);
	mw2Log(LogBuf);
//	mw2Log(LogBuf);

	return TRUE;
}

//------------------------------------------------------------------
static BOOL _mw2AmpEnable(USHORT slot, USHORT channel, BOOL enable)
{
	MW2ChannelInfo *info = _mw2GetChIntf(slot, 0);
	ULONG reg = *(info->chCmdReg);	// current channel control reg
	ULONG bit = MW2_CMD_AMP0_LATCH << channel;

	if (enable)
		reg |= bit;		// enable AMP
	else
		reg &= ~bit;	// disable AMP
	*(info->chCmdReg) = reg;	// channel control
	_mw2CmdPulse(slot, bit);

	// save the status
	info->rfOutputOn = enable;

	sprintf_s(LogBuf, MW2_LOGBUF_SIZE, "_mw2AmpEnable - %08X - %s\r\n", reg, (enable)? "enable" : "disable");
	mw2Log(LogBuf);
//	mw2Log(LogBuf);

	return TRUE;
}

//-------------------------------------------------------
// Generate a 1 ms pulse of the card command register.
// bitflag is the image of the card command register
// where it is expected that one bit is set.
//-------------------------------------------------------
static void _mw2CmdPulse(USHORT slot, ULONG bitflag)
{
	MW2ChannelInfo *info = _mw2GetChIntf(slot, 0);
	*info->cardCmdReg = 0; 
	Sleep(2L);
	*info->cardCmdReg = bitflag; 
	Sleep(2L);
	*info->cardCmdReg = 0;
	Sleep(2L);
}


//------------------------------------------------------------
// _mw2ReadRegister() - reads a register of the SPI device
//------------------------------------------------------------
static BOOL _mw2ReadTemperature(USHORT slot, ULONG *Temp)
{
	ULONG value = 0xffff;
	USHORT dev = 239;
	MW2ChannelInfo *info = _mw2GetChIntf(slot, 0);
	*info->chAddr4Reg = (dev << 16);
	*info->chLen4Reg = 16;		// 16 bits in an SPI frame
	*info->chCmdReg = MW2_CMD_RD_FLAG;
	*info->cardCmdReg = MW2_CMD_REQ;
	if (_mw2WaitForDone(info)) {
		*info->cardCmdReg = 0;
		*Temp = *info->cardSpiReadData & value;
		return TRUE;
	}
	else {
		*info->cardCmdReg = 0;
		*Temp = *info->cardSpiReadData;
		return FALSE;
	}
}


//
// Read nBytes starting byte-offset byteOffset.
//
static BOOL _mw2ReadEeProm(USHORT slot, USHORT byteOffset, USHORT nBytes, char *buffer)
{
	USHORT dev = 254;
	MW2ChannelInfo *info = _mw2GetChIntf(slot, 0);
	int i;
	ULONG data4;
	for (i = 0; i < nBytes; i++) {
		*info->chAddr4Reg = (dev << 16) + byteOffset + i;
		*info->chLen4Reg = 32;		// 32 bits in an SPI frame
		*info->chCmdReg = MW2_CMD_RD_FLAG;
		*info->cardCmdReg = MW2_CMD_REQ;
		if (_mw2WaitForDone(info)) {
			data4 = *((UCHAR *)info->cardSpiReadData);
			*(buffer + i) = (UCHAR)data4;
			*info->cardCmdReg = 0;

//			fprintf(pLogFile, "Done\n");
		}
		else {
			// timeout on DONE flag
			*info->cardCmdReg = 0;
			return FALSE;

			mw2Log("Time Out\r\n");
//			fprintf(pLogFile, "Time Out\n");
		}
	}
	return TRUE;
}

//
// Write nBytes starting byte-offset from the beginning
//
static BOOL _mw2WriteEeProm(USHORT slot, USHORT byteOffset, USHORT nBytes, char *buffer)
{
	USHORT dev = 254;
	MW2ChannelInfo *info = _mw2GetChIntf(slot, 0);
	int i;

//	fprintf(pLogFile, "mw2WriteEePromWE() Slot %d; Addr %04X; Length=%d\n", slot, byteOffset, nBytes);		// Debug


	for (i = 0; i < nBytes; i++) {
		// set the write enable latch first
		_mw2SetEePromWELatch(slot);

		*info->chAddr4Reg = (dev << 16) + byteOffset + i;	
		*info->chLen4Reg = 32;		// 32 bits in an SPI frame
		*(info->cardSpiWriteData) = *(buffer + i);

//		fprintf(pLogFile, "%02X %02X\n", *info->chAddr4Reg, *(info->cardSpiWriteData));		// Debug

		*info->chCmdReg = MW2_CMD_WR_FLAG;
		*info->cardCmdReg = MW2_CMD_REQ;

		Sleep(5L);	// failed at 2L; 3L OK 

		if (_mw2WaitForDone(info))
			*info->cardCmdReg = 0;
		else {
			// timeout on DONE flag
			*info->cardCmdReg = 0;
			return FALSE;
		}
	}
	return TRUE;
}

static BOOL _mw2WriteEePromPage(USHORT slot, USHORT byteOffset, USHORT nPages, ULONG *buffer)
{
	unsigned short dev = 254;
	ULONG data4;

	MW2ChannelInfo *info = _mw2GetChIntf(slot, 0);
	int i, j;

//	fprintf(pLogFile, "_mw2WriteEePromPage: A:%04X, N:%01X\n", (unsigned short) byteOffset, nPages);

	for (i = 0; i < nPages; i++) {

		// set the write enable latch first
		if (_mw2SetEePromWELatch(slot)) {

			*info->chAddr4Reg			= (dev << 16) + byteOffset + i * EEPROM_PAGE_SIZE;	
			*info->chLen4Reg			= 24+EEPROM_PAGE_SIZE*8;		//24bit + data bitstream bytex8 = 278bits
			*(info->cardSpiWriteData)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 0);
			*(info->cardSpiWriteData1)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 1);
			*(info->cardSpiWriteData2)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 2);
			*(info->cardSpiWriteData3)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 3);
			*(info->cardSpiWriteData4)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 4);
			*(info->cardSpiWriteData5)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 5);
			*(info->cardSpiWriteData6)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 6);
			*(info->cardSpiWriteData7)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 7);

/*
			*(info->cardSpiWriteData8)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 8);
			*(info->cardSpiWriteData9)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 9);
			*(info->cardSpiWriteData10)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 10);
			*(info->cardSpiWriteData11)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 11);
			*(info->cardSpiWriteData12)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 12);
			*(info->cardSpiWriteData13)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 13);
			*(info->cardSpiWriteData14)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 14);
			*(info->cardSpiWriteData15)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 15);
			*(info->cardSpiWriteData16)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 16);
			*(info->cardSpiWriteData17)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 17);
			*(info->cardSpiWriteData18)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 18);
			*(info->cardSpiWriteData19)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 19);
			*(info->cardSpiWriteData20)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 20);
			*(info->cardSpiWriteData21)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 21);
			*(info->cardSpiWriteData22)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 22);
			*(info->cardSpiWriteData23)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 23);
			*(info->cardSpiWriteData24)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 24);
			*(info->cardSpiWriteData25)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 25);
			*(info->cardSpiWriteData26)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 26);
			*(info->cardSpiWriteData27)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 27);
			*(info->cardSpiWriteData28)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 28);
			*(info->cardSpiWriteData29)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 29);
			*(info->cardSpiWriteData30)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 30);
			*(info->cardSpiWriteData31)	= (ULONG) *(buffer + i*EEPROM_PAGE_SIZE/4+ 31);
*/
			*info->chCmdReg				= MW2_CMD_WR_FLAG;
			*info->cardCmdReg			= MW2_CMD_REQ;
			mw2Log("Command Sent\r\n");
//			sprintf(LogBuf, "Command Sent\n");	mw2Log(LogBuf);


			if (_mw2WaitForEePromDone5L(info)) {
				*info->cardCmdReg = 0;
				Sleep(1L);
			}
			else {
				// timeout on DONE flag
				*info->cardCmdReg = 0;
//				fprintf(pLogFile, "Exiting _mw2WriteEePromWE() = Timeout\n");
				return FALSE;
			}
		}
		else {
//			fprintf(pLogFile, "Exiting _mw2WriteEePromWE() = Cannot turn on Write Latch\n");
			return FALSE;
		}
	}
	return TRUE;
}


static BOOL _mw2SetEePromWELatch(USHORT slot)
{
	USHORT dev = 253;
	MW2ChannelInfo *info = _mw2GetChIntf(slot, 0);

	*info->chAddr4Reg = dev << 16;	
	*info->chLen4Reg = 8;
	*(info->cardSpiWriteData) = (EEPROM_CMD_WREN);
	*info->chCmdReg = MW2_CMD_WR_FLAG;
	*info->cardCmdReg = MW2_CMD_REQ;
	if (_mw2WaitForDone(info))
		*info->cardCmdReg = 0;
	else {
		// timeout on DONE flag
		*info->cardCmdReg = 0;
		return FALSE;
	}
	return TRUE;
}

int mw2ReadEeProm(unsigned short usSlot, unsigned short usByteOffset, unsigned short usNBytes, UCHAR *buffer)
{
	int mw2EC = MW2ECNOERR;
	if (!_mw2ReadEeProm(usSlot, usByteOffset, usNBytes, buffer)) mw2EC = MW2ECIO;
	return (mw2EC);
}

int mw2WriteEeProm(unsigned short usSlot, unsigned short usByteOffset, unsigned short usNBytes, UCHAR *buffer)
{
	int mw2EC = MW2ECNOERR;
	if (!_mw2WriteEeProm(usSlot, usByteOffset, usNBytes, buffer)) mw2EC = MW2ECIO;
	return (mw2EC);
}

int mw2WriteEePromPage(unsigned short usSlot, unsigned short usByteOffset, unsigned short usNPages, ULONG *buffer)
{
	int mw2EC = MW2ECNOERR;
	if (!_mw2WriteEePromPage(usSlot, usByteOffset, usNPages, buffer)) mw2EC = MW2ECIO;
	return (mw2EC);
}

//---------------------------------------------------------
// _mw2PrintPCIInfo() - Prints PCIInfo data structure
//---------------------------------------------------------
int mw2Log(char *strbuff)
{
		int mw2EC = MW2ECNOERR;
		TCHAR szPath[MAX_PATH];
		if ( SUCCEEDED( SHGetFolderPath( NULL, CSIDL_COMMON_APPDATA, NULL, 0, szPath ) ) )
		{
				// Append product-specific path
				PathAppend( szPath, "\\Cambridge Instruments\\CI4000\\InstrumentLog.txt");
		}

		if (fopen_s(&pLogFile, szPath, "a")==0) {
				fwrite(strbuff, 1, strlen(strbuff), pLogFile);
				fflush(pLogFile);
				fclose(pLogFile);
		}
		else mw2EC = MW2ECBADF;
		return mw2EC;
}

int mw2GetLastKnownFileName(char* path) {
		if ( SUCCEEDED( SHGetFolderPath( NULL, CSIDL_COMMON_APPDATA, NULL, 0, path ) ) )
		{
				// Append product-specific path
				PathAppend( path, "\\Cambridge Instruments\\CI4000\\LastKnownValues.txt");
		}
		return 0;
}

int mw2Freq2FilterDac(unsigned short usSlot, unsigned short usChannel, double freqMHz, unsigned short * pusFdac)
{
	int mw2EC = MW2ECNOERR;
	unsigned short FDAC;
	MW2ChannelInfo *chInfo = _mw2GetChIntf(usSlot, usChannel);
	CardType cardType = mw2GetCardType(usSlot);
	int hFile;
	char FileName[300];
	double freq[200];
	int fdac[200];
	char text[101];
	int count,i,n;
	double deltaf;
	unsigned short ul;

	if ((cardType == MW4122Type) && (usChannel == 0)) {		// 6-12G		
			for(i = 0; i < FDAC_TABLE_LENGTH; i++){
					if(chInfo->FdacTbl[i].Frequency > freqMHz) {
							*pusFdac = (unsigned short)(chInfo->FdacTbl[i].Multiplier*freqMHz + chInfo->FdacTbl[i].Addition);
							return (mw2EC);
					}
			}
	}

	else {													// 25-3G
		if(freqMHz < 3800.) {
			*pusFdac = (unsigned short)0;
			return (mw2EC);
		}
		else {
				for(i = 0; i < FDAC_TABLE_LENGTH; i++){
						if(chInfo->FdacTbl[i].Frequency > freqMHz) {
								*pusFdac = (unsigned short)(chInfo->FdacTbl[i].Multiplier*freqMHz + chInfo->FdacTbl[i].Addition);
								return (mw2EC);
						}
				}
		}
	}
}

unsigned long mw2GetSerial(unsigned short usSlot) {

		//	int mw2EC = MW2ECNOERR;
		char *end;
		char wbuffer[0x40];
		unsigned long ulResult = 0;

		if(mw2ReadEeProm(usSlot, EEPROM_CARD_INFO, sizeof(wbuffer), wbuffer)==MW2ECNOERR)
				if (((wbuffer[0xB]>='a')&&(wbuffer[0xB]<='z'))||((wbuffer[0xB]>='A')&&(wbuffer[0xB]<='Z')))
						ulResult = (unsigned long) strtol(wbuffer+0xC, &end, 10);
		return (ulResult);
}

char mw2GetCardRev(unsigned short usSlot) {

//	int mw2EC = MW2ECNOERR;
	char wbuffer[0x40];

	if(mw2ReadEeProm(usSlot, EEPROM_CARD_INFO, sizeof(wbuffer), wbuffer)==MW2ECNOERR)
		if (((wbuffer[EEPROM_CARD_REV]>='a')&&(wbuffer[EEPROM_CARD_REV]<='z'))||((wbuffer[EEPROM_CARD_REV]>='A')&&(wbuffer[EEPROM_CARD_REV]<='Z')))
			return (wbuffer[EEPROM_CARD_REV]);
	return ('0');
}

char* mw2GetCardDate(unsigned short usSlot) {

//	int mw2EC = MW2ECNOERR;
	char wbuffer[0x40];

	if(mw2ReadEeProm(usSlot, EEPROM_CARD_INFO, sizeof(wbuffer), wbuffer)==MW2ECNOERR)
		if (((wbuffer[EEPROM_CARD_REV]>='a')&&(wbuffer[EEPROM_CARD_REV]<='z'))||((wbuffer[EEPROM_CARD_REV]>='A')&&(wbuffer[EEPROM_CARD_REV]<='Z')))
		{
			wbuffer[EEPROM_DATE+8] = '\0';
			return wbuffer+EEPROM_DATE;
		}
	return (NULL);
}

char* mw2GetCardTime(unsigned short usSlot) {

//	int mw2EC = MW2ECNOERR;
	char wbuffer[0x40];

	if(mw2ReadEeProm(usSlot, EEPROM_CARD_INFO, sizeof(wbuffer), wbuffer)==MW2ECNOERR)
		if (((wbuffer[EEPROM_CARD_REV]>='a')&&(wbuffer[EEPROM_CARD_REV]<='z'))||((wbuffer[EEPROM_CARD_REV]>='A')&&(wbuffer[EEPROM_CARD_REV]<='Z')))
		{
			wbuffer[EEPROM_TIME+8] = '\0';
			return wbuffer+EEPROM_TIME;
		}
	return (NULL);
}

/*
char mw2GetSeepromFormat(unsigned short usSlot) {

//	int mw2EC = MW2ECNOERR;
	char wbuffer[0x40];

	if(mw2ReadEeProm(usSlot, EEPROM_CARD_INFO, sizeof(wbuffer), wbuffer)==MW2ECNOERR)
		return (wbuffer[EEPROM_FORMAT]);
	return (0);
}

int mw2SEEPROMFDACStep(unsigned short usSlot, unsigned short usChannel) {
//	int mw2EC = MW2ECNOERR;
	unsigned char wbuffer[EEPROM_FSTEP_N+1];
	int iChannelOffset = EEPROM_CHN0;
	if (usChannel == 1) iChannelOffset = EEPROM_CHN1;

	if(mw2ReadEeProm(usSlot, iChannelOffset, sizeof(wbuffer), wbuffer)==MW2ECNOERR)
		return (wbuffer[EEPROM_FDAC_N]);
	else return (0);
}

int mw2SEEPROMPDACStep(unsigned short usSlot, unsigned short usChannel) {
//	int mw2EC = MW2ECNOERR;
	unsigned char wbuffer[EEPROM_FSTEP_N+1];
	int iChannelOffset = EEPROM_CHN0;
	if (usChannel == 1) iChannelOffset = EEPROM_CHN1;

	if(mw2ReadEeProm(usSlot, iChannelOffset, sizeof(wbuffer), wbuffer)==MW2ECNOERR)
		return (wbuffer[EEPROM_PDAC_N]);
	else return (0);
}

int mw2SEEPROMFreqStep(unsigned short usSlot, unsigned short usChannel) {
//	int mw2EC = MW2ECNOERR;
	unsigned char wbuffer[EEPROM_FSTEP_N+1];
	int iChannelOffset = EEPROM_CHN0;
	if (usChannel == 1) iChannelOffset = EEPROM_CHN1;

	if(mw2ReadEeProm(usSlot, iChannelOffset, sizeof(wbuffer), wbuffer)==MW2ECNOERR)
		return (wbuffer[EEPROM_FSTEP_N]);
	else return (0);
}

BOOL mw2SEEPROMCalibDataAvailable(unsigned short usSlot, unsigned short usChannel) {

//	int mw2EC = MW2ECNOERR;

	unsigned char wbuffer[EEPROM_FSTEP_N+1];
	BOOL bResult = FALSE;

	int iChannelOffset = EEPROM_CHN0;
	if (usChannel == 1) iChannelOffset = EEPROM_CHN1;

	if(mw2ReadEeProm(usSlot, iChannelOffset, sizeof(wbuffer), wbuffer)==MW2ECNOERR)
		if ((wbuffer[EEPROM_PDAC_N] == PDAC_TABLE_LENGTH) && (wbuffer[EEPROM_FDAC_N] == FDAC_TABLE_LENGTH) && (wbuffer[EEPROM_FSTEP_N] == CAL_TABLE_LENGTH))
			bResult = TRUE;

	return (bResult);
}

BOOL mw2UseSEEPROMData(unsigned short usSlot, unsigned short usChannel) {
//	int mw2EC = MW2ECNOERR;

	MW2ChannelInfo *chInfo;
	chInfo = _mw2GetChIntf(usSlot, usChannel);
	return chInfo->bUseSEEPROMData;
}


int mw2Pwr2AttenuatorDacSeeprom(unsigned short usSlot, unsigned short usChannel, double freqMHz, double powerdBm, BOOL bUseSeepromData, unsigned short * pusPdac)
{
	int mw2EC = MW2ECNOERR;
	MW2ChannelInfo *chInfo = _mw2GetChIntf(usSlot, usChannel);
	USHORT PDAC = 4095;
	double dPDAC, dPDAC1, dPDAC2;
	USHORT usAddr;
	int h,i,j, offset, FStep, PStep, iStart, iEnd;
	unsigned int iBuffer2[2];
	short siBuffer2[2];
	float fP0, fP1;

	if ((mw2GetCardType(usSlot) == MW4122Type) && (usChannel == 0)) {		// 6-12G
		iStart	= 6000;
		iEnd	= 12000;
	}
	else {
		iStart	= 25;
		iEnd	= 6000;
	}

	if ((freqMHz >= iStart)&&(freqMHz <= iEnd)) {
		if (!bUseSeepromData) {
			if (powerdBm > MW2_CALIB_CHANGE) {
				i=0;
				while ((chInfo->CalData_Hi[i].Frequency<=freqMHz) && (i<CAL_TABLE_LENGTH)) i++;
				if (i==CAL_TABLE_LENGTH) i= i-1;
				h= i-1;																						// h < freqMHz < i

				j=0;
				while ((chInfo->CalData_Hi[h].PDACTable[j].Power>powerdBm) && (j<PDAC_TABLE_LENGTH)) j++;		// j-1< powerdBm < j
				if (j==PDAC_TABLE_LENGTH)	dPDAC1 = (USHORT)(chInfo->CalData_Hi[h].PDACTable[j-1].PDAC);
				else if (j==0)				dPDAC1 = (USHORT)(chInfo->CalData_Hi[h].PDACTable[0].PDAC);
				else						dPDAC1 = (USHORT)((powerdBm-chInfo->CalData_Hi[h].PDACTable[j-1].Power)/(chInfo->CalData_Hi[h].PDACTable[j].Power-chInfo->CalData_Hi[h].PDACTable[j-1].Power)*(chInfo->CalData_Hi[h].PDACTable[j].PDAC-chInfo->CalData_Hi[h].PDACTable[j-1].PDAC)+chInfo->CalData_Hi[h].PDACTable[j-1].PDAC);

				j=0;
				while ((chInfo->CalData_Hi[i].PDACTable[j].Power>powerdBm) && (j<PDAC_TABLE_LENGTH)) j++;		// j-1< powerdBm < j
				if (j==PDAC_TABLE_LENGTH)	dPDAC2 = (USHORT)(chInfo->CalData_Hi[i].PDACTable[j-1].PDAC);
				else if (j==0)				dPDAC2 = (USHORT)(chInfo->CalData_Hi[i].PDACTable[0].PDAC);
				else						dPDAC2 = (USHORT)((powerdBm-chInfo->CalData_Hi[i].PDACTable[j-1].Power)/(chInfo->CalData_Hi[i].PDACTable[j].Power-chInfo->CalData_Hi[i].PDACTable[j-1].Power)*(chInfo->CalData_Hi[i].PDACTable[j].PDAC-chInfo->CalData_Hi[i].PDACTable[j-1].PDAC)+chInfo->CalData_Hi[i].PDACTable[j-1].PDAC);

				dPDAC = ((freqMHz-chInfo->CalData_Hi[h].Frequency)*dPDAC2+(chInfo->CalData_Hi[i].Frequency-freqMHz)*dPDAC1)/(chInfo->CalData_Hi[i].Frequency-chInfo->CalData_Hi[h].Frequency);
			}
			else {
				i=0;
				while ((chInfo->CalData_Lo[i].Frequency<=freqMHz) && (i<CAL_TABLE_LENGTH)) i++;
				if (i==CAL_TABLE_LENGTH) i= i-1;
				h= i-1;																						// h < freqMHz < i

				j=0;
				while ((chInfo->CalData_Lo[h].PDACTable[j].Power>powerdBm) && (j<PDAC_TABLE_LENGTH)) j++;		// j-1< powerdBm < j
				if (j==PDAC_TABLE_LENGTH)	dPDAC1 = (USHORT)(chInfo->CalData_Lo[h].PDACTable[j-1].PDAC);
				else if (j==0)				dPDAC1 = (USHORT)(chInfo->CalData_Lo[h].PDACTable[0].PDAC);
				else						dPDAC1 = (USHORT)((powerdBm-chInfo->CalData_Lo[h].PDACTable[j-1].Power)/(chInfo->CalData_Lo[h].PDACTable[j].Power-chInfo->CalData_Lo[h].PDACTable[j-1].Power)*(chInfo->CalData_Lo[h].PDACTable[j].PDAC-chInfo->CalData_Lo[h].PDACTable[j-1].PDAC)+chInfo->CalData_Lo[h].PDACTable[j-1].PDAC);

				j=0;
				while ((chInfo->CalData_Lo[i].PDACTable[j].Power>powerdBm) && (j<PDAC_TABLE_LENGTH)) j++;		// j-1< powerdBm < j
				if (j==PDAC_TABLE_LENGTH)	dPDAC2 = (USHORT)(chInfo->CalData_Lo[i].PDACTable[j-1].PDAC);
				else if (j==0)				dPDAC2 = (USHORT)(chInfo->CalData_Lo[i].PDACTable[0].PDAC);
				else						dPDAC2 = (USHORT)((powerdBm-chInfo->CalData_Lo[i].PDACTable[j-1].Power)/(chInfo->CalData_Lo[i].PDACTable[j].Power-chInfo->CalData_Lo[i].PDACTable[j-1].Power)*(chInfo->CalData_Lo[i].PDACTable[j].PDAC-chInfo->CalData_Lo[i].PDACTable[j-1].PDAC)+chInfo->CalData_Lo[i].PDACTable[j-1].PDAC);

				dPDAC = ((freqMHz-chInfo->CalData_Lo[h].Frequency)*dPDAC2+(chInfo->CalData_Lo[i].Frequency-freqMHz)*dPDAC1)/(chInfo->CalData_Lo[i].Frequency-chInfo->CalData_Lo[h].Frequency);
			}
		}

		else {	// Use SEEPROM Data

			offset = EEPROM_CHN0;
			if (usChannel==1) offset = EEPROM_CHN1;
			FStep =  mw2SEEPROMFreqStep(usSlot, usChannel);
			PStep =  mw2SEEPROMPDACStep(usSlot, usChannel);

//			fprintf(pLogFile, "FSTep = %d; PStep = %d\n",FStep, PStep);								// Debug

			if (powerdBm > MW2_CALIB_CHANGE) {			// Check Hi Power side
				i=0;
				while ((chInfo->CalData_Hi[i].Frequency<=freqMHz) && (i<FStep)) {
//					fprintf(pLogFile, "Frequency Step %d = %f\n", i, chInfo->CalData_Hi[i].Frequency);		// Debug
					i++;
				}
				if (i==FStep) i= i-1;
				h= i-1;										// h < freqMHz < i
//				fprintf(pLogFile, "Frequency = %f; Frequency Step %d = %f\n", freqMHz, h, chInfo->CalData_Hi[h].Frequency);		// Debug
//				fprintf(pLogFile, "Frequency = %f; Frequency Step %d = %f\n", freqMHz, i, chInfo->CalData_Hi[i].Frequency);		// Debug

				j=0; fP0 = MW2_FLT_MAX ; fP1 = MW2_FLT_MAX;
				if (mw2ReadEeProm (usSlot, offset + EEPROM_CALIBH + (h*PStep+j)*2, 2, siBuffer2)==MW2ECNOERR) {
					fP1 = fP0;
					fP0 = siBuffer2[0]/100.0;
				}
				while ((fP0 > powerdBm) && (j<PStep)) {
//					fprintf(pLogFile, "Power Step %d = %f\n", j, fP0);		// Debug
					j++;
					if (mw2ReadEeProm (usSlot, offset + EEPROM_CALIBH + (h*PStep+j)*2, 2, siBuffer2)==MW2ECNOERR) {
						fP1 = fP0;
						fP0 = siBuffer2[0]/100.0;
					}
				}
				if		(j==PStep)	dPDAC1 = (USHORT)(chInfo->CalData_Hi[h].PDACTable[j-1].PDAC);
				else if (j==0)		dPDAC1 = (USHORT)(chInfo->CalData_Hi[h].PDACTable[0].PDAC);
				else				dPDAC1 = (USHORT)((powerdBm-fP1)/(fP0-fP1)*(chInfo->CalData_Hi[h].PDACTable[j].PDAC-chInfo->CalData_Hi[h].PDACTable[j-1].PDAC)+chInfo->CalData_Hi[h].PDACTable[j-1].PDAC);
//				fprintf(pLogFile, "dPDAC1 Power Step %d = %f\n", j, dPDAC1);				// Debug

				j=0; fP0 = MW2_FLT_MAX; fP1 = MW2_FLT_MAX;
				if (mw2ReadEeProm (usSlot, offset + EEPROM_CALIBH + i*2*PStep + j*2, 2, siBuffer2)==MW2ECNOERR) {
					fP1 = fP0;
					fP0 = siBuffer2[0]/100.0;
				}
				while ((fP0 > powerdBm) && (j<PStep)) {
//					fprintf(pLogFile, "Power Step %d = %f\n", j, fP0);		// Debug
					j++;
					if (mw2ReadEeProm (usSlot, offset + EEPROM_CALIBH + i*2*PStep + j*2, 2, siBuffer2)==MW2ECNOERR) {
						fP1 = fP0;
						fP0 = siBuffer2[0]/100.0;
					}
				}
				if		(j==PStep)	dPDAC2 = (USHORT)(chInfo->CalData_Hi[i].PDACTable[j-1].PDAC);
				else if (j==0)		dPDAC2 = (USHORT)(chInfo->CalData_Hi[i].PDACTable[0].PDAC);
				else				dPDAC2 = (USHORT)((powerdBm-fP1)/(fP0-fP1)*(chInfo->CalData_Hi[i].PDACTable[j].PDAC-chInfo->CalData_Hi[i].PDACTable[j-1].PDAC)+chInfo->CalData_Hi[i].PDACTable[j-1].PDAC);
//				fprintf(pLogFile, "dPDAC2 Power Step %d = %f\n", j, dPDAC2);				// Debug

				dPDAC = ((freqMHz-chInfo->CalData_Hi[h].Frequency)*dPDAC2+(chInfo->CalData_Hi[i].Frequency-freqMHz)*dPDAC1)/(chInfo->CalData_Hi[i].Frequency-chInfo->CalData_Hi[h].Frequency);
//				fprintf(pLogFile, "dPDAC = %f\n", dPDAC);				// Debug
			}
			else {										// Check low Power side
				i=0;
				while ((chInfo->CalData_Lo[i].Frequency<=freqMHz) && (i<FStep)) i++;
				if (i==FStep) i= i-1;
				h= i-1;										// h < freqMHz < i

				j=0; fP0 = MW2_FLT_MAX ; fP1 = MW2_FLT_MAX;
				if (mw2ReadEeProm (usSlot, offset + EEPROM_CALIBL + (h*PStep+j)*2, 2, siBuffer2)==MW2ECNOERR) {
					fP1 = fP0;
					fP0 = siBuffer2[0]/100.0;
				}
				while ((fP0 > powerdBm) && (j<PStep)) {
//					fprintf(pLogFile, "Power Step %d = %f\n", j, fP0);		// Debug
					j++;
					if (mw2ReadEeProm (usSlot, offset + EEPROM_CALIBL + (h*PStep+j)*2, 2, siBuffer2)==MW2ECNOERR) {
						fP1 = fP0;
						fP0 = siBuffer2[0]/100.0;
					}
				}
				if		(j==PStep)	dPDAC1 = (USHORT)(chInfo->CalData_Lo[h].PDACTable[j-1].PDAC);
				else if (j==0)		dPDAC1 = (USHORT)(chInfo->CalData_Lo[h].PDACTable[0].PDAC);
				else				dPDAC1 = (USHORT)((powerdBm-fP1)/(fP0-fP1)*(chInfo->CalData_Lo[h].PDACTable[j].PDAC-chInfo->CalData_Lo[h].PDACTable[j-1].PDAC)+chInfo->CalData_Lo[h].PDACTable[j-1].PDAC);
//				fprintf(pLogFile, "dPDAC1 Power Step %d = %f\n", j, dPDAC1);				// Debug


				j=0; fP0 = MW2_FLT_MAX; fP1 = MW2_FLT_MAX;
				if (mw2ReadEeProm (usSlot, offset + EEPROM_CALIBL + i*2*PStep + j*2, 2, siBuffer2)==MW2ECNOERR) {
					fP1 = fP0;
					fP0 = siBuffer2[0]/100.0;
				}
				while ((fP0 > powerdBm) && (j<PStep)) {
//					fprintf(pLogFile, "Power Step %d = %f\n", j, fP0);		// Debug
					j++;
					if (mw2ReadEeProm (usSlot, offset + EEPROM_CALIBL + i*2*PStep + j*2, 2, siBuffer2)==MW2ECNOERR) {
						fP1 = fP0;
						fP0 = siBuffer2[0]/100.0;
					}
				}
				if		(j==PStep)	dPDAC2 = (USHORT)(chInfo->CalData_Lo[i].PDACTable[j-1].PDAC);
				else if (j==0)		dPDAC2 = (USHORT)(chInfo->CalData_Lo[i].PDACTable[0].PDAC);
				else				dPDAC2 = (USHORT)((powerdBm-fP1)/(fP0-fP1)*(chInfo->CalData_Lo[i].PDACTable[j].PDAC-chInfo->CalData_Lo[i].PDACTable[j-1].PDAC)+chInfo->CalData_Lo[i].PDACTable[j-1].PDAC);
//				fprintf(pLogFile, "dPDAC2 Power Step %d = %f\n", j, dPDAC2);				// Debug

				dPDAC = ((freqMHz-chInfo->CalData_Lo[h].Frequency)*dPDAC2+(chInfo->CalData_Lo[i].Frequency-freqMHz)*dPDAC1)/(chInfo->CalData_Lo[i].Frequency-chInfo->CalData_Lo[h].Frequency);
//				fprintf(pLogFile, "dPDAC = %f\n", dPDAC);				// Debug
			}
		}

		if (dPDAC < 0.0) PDAC = 0;
		else if (dPDAC > 4094.9) PDAC = 4095;
		else PDAC = (USHORT) dPDAC;
//		fprintf(pLogFile, "%.2f\t%d\t%d\n",dPDAC, (USHORT)dPDAC, PDAC);
	}
	*pusPdac = PDAC;
	return (mw2EC);
}
*/



