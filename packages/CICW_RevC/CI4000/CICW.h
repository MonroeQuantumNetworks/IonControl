// $Id: CICW.h 228 2014-09-30 20:13:23Z  $
// $HeadURL: http://192.168.254.234:1080/svn/CI/4000/4062_4122/Branches/PassViSession/CI4000/CICW.h $
//
// Cambridge Instruments 4000 series CW Signal Generator
// core driver  (straight C, not IVI)
//
// (C) 2014 MagiQ Technologies, Inc.

// Depends on NI-VISA.
//
// NOTE:  Must
//      #define      NIVISA_PXI
// before
//      #include <visa.h>
// to use PXI instruments.


#ifndef CICW_H_INCLUDED
#define CICW_H_INCLUDED

#ifdef _MSC_VER
#pragma once
#endif

#ifdef CI4000_RELEASE
#define CICW_EXPORT
#elif defined(CICW_DLL_EXPORT)
#define CICW_EXPORT __declspec(dllexport)
#else
#define CICW_EXPORT __declspec(dllimport)
#endif

#ifdef __cplusplus
extern "C" {
#endif

/// Reference Clock Source
///
/// The Reference clock sources are not independent for each channel.
/// 
/// The reference sources for both channels must be set at the
/// same time.
typedef enum {
    CICW_RefClockIntIntOff = 0,                 ///<    Ch 1 Internal, Ch2 Internal
    CICW_RefClockIntIntInt = 1,                 ///<    Ch 1 Internal, Ch2 Internal; Drive Internal out Ref SMA
    CICW_RefClockPxiPxiOff = 2,                 ///<    Ch 1 PXI,      Ch2 PXI
    CICW_RefClockExtExtOff = 3,                 ///<    Ch 1 External, Ch2 External
    CICW_RefClockIntExtOff = 4,                 ///<    Ch 1 Internal, Ch2 External
    CICW_RefClockExtPxiOff = 5                  ///<    Ch 1 External, Ch2 PXI
} CICW_RefClockSrc;

// Interface testing function, to make sure the user of the DLL has done everything
// right
ViStatus CICW_EXPORT CICW_RevC_IfaceTest(ViChar *strIn, ViChar *strOut, unsigned int strLen, unsigned short statusIn);

// Init is the starting function, which opens a session and reads off the Calibration data from the card
ViStatus CICW_EXPORT CICW_RevC_Init(ViChar* name, unsigned short *slotNumber);
ViStatus CICW_EXPORT CICW_RevC_Close();

// Frequency and Power control 
ViStatus CICW_EXPORT CICW_RevC_Configure(unsigned short slotNumber, unsigned short channel,  double freqMHz, double power_dBm, CalculateEstimates *CalcEst);
ViStatus CICW_EXPORT CICW_RevC_SignalLocked(unsigned short slotNumber, unsigned short channel,  ViBoolean* locked); 
ViStatus CICW_EXPORT CICW_RevC_GetOutputEnabled(unsigned short slotNumber, unsigned short channel,  ViBoolean *enabled);
ViStatus CICW_EXPORT CICW_RevC_SetOutputEnabled(unsigned short slotNumber, unsigned short channel,  ViBoolean enabled);
ViStatus CICW_EXPORT CICW_RevC_DisableOutput(unsigned short slotNumber, unsigned int channel);
ViStatus CICW_EXPORT CICW_RevC_GetCalculateEstimates(unsigned short slotNumber, CalculateEstimates *ch1CalcEst, CalculateEstimates *ch2CalcEst);

// Ref Clock options
ViStatus CICW_EXPORT CICW_RevC_SelectClock(unsigned short slotNumber, unsigned short channel,  CICW_RefClockSrc clockSrc, double clockMHz);
ViStatus CICW_EXPORT CICW_RevC_GetClock(unsigned short slotNumber, unsigned short channel,  CICW_RefClockSrc* clockSrc);
ViStatus CICW_EXPORT CICW_RevC_GetClockMHz(unsigned short slotNumber, unsigned short channel,  double* clockMHz);
ViStatus CICW_EXPORT CICW_RevC_GetExtRefMHz(unsigned short slotNumber, unsigned short channel,  double* clockMHz);
ViStatus CICW_EXPORT CICW_RevC_GetRefDivider(unsigned short slotNumber, unsigned short channel,  unsigned long *refDivider);
ViStatus CICW_EXPORT CICW_RevC_SetRefDivider(unsigned short slotNumber, unsigned short channel,  unsigned long refDivider);

// Revision Information
ViStatus CICW_EXPORT CICW_RevC_GetBoardIDString(unsigned short slotNumber, unsigned short channel,  ViChar* boardID, ViUInt32 maxBoardIDLen);
ViStatus CICW_EXPORT CICW_RevC_GetCardType(unsigned short slotNumber, unsigned short channel,  ViChar *cardType, ViUInt32 maxCardTypeLen ); // 4062 or 4122
ViStatus CICW_EXPORT CICW_RevC_GetFirmwareRev(unsigned short slotNumber, unsigned short channel,  ViChar* FWRev, ViUInt32 maxFWRevLen);
ViStatus CICW_EXPORT CICW_RevC_GetSerialNumber(unsigned short slotNumber, unsigned short channel, unsigned long *serial);

// Reset functions
ViStatus CICW_EXPORT CICW_RevC_ResetCard(unsigned short slotNumber);     // Both channels; Internal reference
ViStatus CICW_EXPORT CICW_RevC_ResetChannel(unsigned short slotNumber, unsigned int channel);  // does NOT affect reference or other channel

// Other functions
ViStatus CICW_EXPORT CICW_RevC_GetTemperature(unsigned short slotNumber, unsigned short channel,  double* temp_C);
// This is a raw set for frequency and power, choose the pdac and gain values yourself
/// \cond DOXYGEN_SHOULD_SKIP_THIS
ViStatus CICW_EXPORT CICW_RevC_GetCardRev(unsigned short slotNumber, unsigned short channel,  ViChar *cardRev, ViUInt32 maxCardRevLen); // A, B, C...
ViStatus CICW_EXPORT CICW_RevC_SetFrequencyAttn(unsigned short slotNumber, unsigned short channel,  double freqMHz, ViUInt16 pdac, ViUInt16 gain);
ViStatus CICW_EXPORT CICW_RevC_GetFDAC(unsigned short slotNumber, unsigned short channel,  double freqMHz, unsigned short* fdac);
ViStatus CICW_EXPORT CICW_RevC_GetPDAC(unsigned short slotNumber, unsigned short channel,  unsigned short* pdac);
/// \endcond

#ifdef __cplusplus
};      // extern "C"
#endif


// Error values - Based on IVI Error definitions from IVI 3.1 section 5.12
// Bit 31: Success or failure
//      0 = success or warning
//      1 = error
// Bit 30 : Reserved(always 0)
// Bits 29 - 16 : Driver type or IO definition
//      3FFA = IVI drivers and components
//      3FFF = VISA
// Bits 15 - 12 : Type of error
//      0x6 = CI4000 errors
// Bits 11 - 0 : Identify a particular error within the specified type
/// \cond DOXYGEN_SHOULD_SKIP_THIS
#define ERROR_BIT           0x80000000
#define IVI_DRIVER_ERROR    0x3FFA0000
#define VISA_DRIVER_ERROR   0x3FFF0000
#define CICW_ERROR              0x6000

#define CICW_IVI_COMBINED(num)  (ERROR_BIT | IVI_DRIVER_ERROR  | CICW_ERROR | (num & 0xFFF))
#define CICW_VISA_COMBINED(num) (ERROR_BIT | VISA_DRIVER_ERROR | CICW_ERROR | (num & 0xFFF))
#define CICW_IVI_COMBINED_WARNING(num)      (IVI_DRIVER_ERROR  | CICW_ERROR | (num & 0xFFF))
#define CICW_VISA_COMBINED_WARNING(num)     (VISA_DRIVER_ERROR | CICW_ERROR | (num & 0xFFF))

// 0x0-- refers to incorrect values read to or from VISA 
#define CICW_INVALID_SESSION        CICW_VISA_COMBINED(0x001)
#define CICW_CHINFO_NULL            CICW_VISA_COMBINED(0x002)
#define CICW_NULL_RESOURCE_MANAGER  CICW_VISA_COMBINED(0x003)

// 0x1-- are errors with the user input 
#define CICW_FREQ_HIGH              CICW_VISA_COMBINED(0x100)
#define CICW_FREQ_LOW               CICW_VISA_COMBINED(0x101)
#define CICW_PDAC_HIGH              CICW_VISA_COMBINED(0x102)
#define CICW_PDAC_LOW               CICW_VISA_COMBINED(0x103)
#define CICW_FDAC_HIGH              CICW_VISA_COMBINED(0x104)
#define CICW_FDAC_LOW               CICW_VISA_COMBINED(0x105)
#define CICW_INVALID_REFCLOCK       CICW_VISA_COMBINED(0x106)
#define CICW_NULL_INPUTS            CICW_VISA_COMBINED(0x107)
#define CICW_GAIN_INVALID           CICW_VISA_COMBINED(0x108)
#define CICW_POWER_HIGH             CICW_VISA_COMBINED(0x109)
#define CICW_POWER_LOW              CICW_VISA_COMBINED(0x10A)
#define CICW_CAL_DATA_MISSING       CICW_VISA_COMBINED(0x10B)

// These are warnings caused by user input
#define CICW_PDAC_HIGH_WARNING      CICW_VISA_COMBINED_WARNING(0x100)
#define CICW_PDAC_LOW_WARNING       CICW_VISA_COMBINED_WARNING(0x101)

// 0x2-- means something hardware related caused the issue, or something from CI4000Lib
#define CICW_INVALID_VENDOR_ID      CICW_VISA_COMBINED(0x201)
#define CICW_MEMORY_TYPE_WRONG      CICW_VISA_COMBINED(0x202)
/// \endcond
#endif // CICW_H_INCLUDED
