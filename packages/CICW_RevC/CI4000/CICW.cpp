// $Id: CICW.cpp 259 2014-10-28 18:58:14Z greg $
// $HeadURL: http://192.168.254.234:1080/svn/CI/4000/4062_4122/Trunk/CI4000/CICW.cpp $
//
// Cambridge Instruments 4000 series CW Signal Generator driver
//
// (C) 2014 MagiQ Technologies, Inc.

// viLock() strategy:  Do all locks at the CICW_ (published interface) level.
// May not be optimal, but easy to verify by inspection, and avoids many nested locks.
// CICW_ functions should not call other CICW_ functions for performance reasons.
// Wrap viLock() in an object so it automagically gets released when fn exits?

// This is the main DLL file.
#include "Stdafx.h"

// Calibration code
#include "../Estimation/Estimation.h"
using namespace Estimation;

// HW control
#include "../mw2Lib/mw2Defs.h"
#include "../mw2Lib/mw2Lib.h"

#include <visa.h>
#include <visatype.h>

#include "CICW.h"

// Get SVN version info for this build.
// svnversion is installed with the command line tools.
// The Tortoise SVN installer has a checkbox for installing the command line tools (default unchecked)
// Add the following to the project as a pre-build (as opposed to custom build) step:
// for /f %%a in ('svnversion -n ..') do echo const char* const svn_ver = "%%a"; > ..\version.h
// (May need to specify ..\version.h depending on where your project file is located.)

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \mainpage CICW C Interface Guide
/// \tableofcontents
/// \par Reason for CICW - 
/// The CI4000.dll can be used to control CI 4061/4062/4122 synthesizers. The CICW functions provide a straight "C" 
/// interface which can be used from environments such as NI LabWindows, MinGW, or Visual C++. The CICW interface does 
/// not depend on the IVI infrastructure and may therefore be easier to set up and deploy. 
/// \par Including CICW into your project - 
/// Make sure your project can find CI4000.dll. Include the provided CICW.h and CI4000.lib fileinto your project.
/// the latter library is in COFF format, and will work with MS Visual Studio. If you want to use the library with 
/// Borland/Embarcadero environment you will need to convert it to an OMF formatted library; that can be done 
/// with the coff2omf.exe utility which comes with Borland/Embarcadero products. 
///
/// \section ivi_vs_cicw Choosing the Right Interface : IVI or CICW ?
/// The CI4000 signal generators have multiple interfaces to choose from. Depending on the language you are using, 
/// the choice may be relatively straight forward.For instance, if you are using a.NET oriented language you may 
/// find the IVI.NET interface to be most useful.If you are using C or C++ and want the additional standardization 
/// of IVI then IVI - C may be your interface of choice.If you are using C or C++ and want a minimum of overhead and
/// additional software to configure, then the CICW(Cambridge Instruments Continuous Wave) interface may be the best choice.
/// 
/// IVI stands for "Interchangeable Virtual Instruments" and it addresses many concerns of large automated test floors, 
/// including support for inconsistent equipment models from one test stand to the next.www.ivifoundation.org lists many 
/// other benefits.However, IVI requires additional software and complexity to support this.The IVI.NET and IVI - C 
/// interfaces are built on IVI - COM which requires the driver to be properly registered, IVI style, in order for it to be
/// recognized.Compatible versions of the IVI Shared Components(IVI 2.0 + ) and VISA must be installed.Because the CI4000
/// IVI drivers are installed in the path, in the registry, and in the Global Assembly Cache, multiple versions of the 
/// same driver are not supported on the same machine.
///
/// The CICW interface is a thin, minimal driver with few configuration options and few dependencies.It is possible to 
/// deploy a CICW driver by copying CI4000.dll into the same directory as the rest of the project binaries.The hardware 
/// must still be recognized by the test system(requires VISA and the CI4000 Driver to be installed) but different programs
/// can use different versions of CI4000.dll on the same system as needed, whether when trying new software or just to 
/// ensure existing programs continue to work *exactly* the same way.
/// \n
/// \section Examples Example Code using CICW
/// \subsection demo1 Simple demo demonstrating opening a session to a single channel, setting frequency and power, and closing the session.
/// \include Example2.h
/// \subsection demo2 Simple demo demonstrating opening a session to a both channels, setting frequency and power, and closing the session.
/// \include Example3.h
/// \subsection Init Initializing a session in C++/clr
/// This is a simple example of how to get a list of all instruments connected to the system, add them to a combo box,
/// connect to the first one on the list, and then clear the memory. This example is in C++/clr, so to use native pointers
/// pin_ptr<ViSession> needs to be used. 
/// \include Example.h 
/// \subsection GetConnectStrings Using GetConnectStrings to find all connected instruments
/// The following is a snippit of how to use \link CICW_GetConnectStrings \endlink in a C or C++ program:
/// \code{.c}
///     #include <visa.h>
///     #include <stdio.h>
///     #include <CICW.h>
///     
///     main()
///     {
///          unsigned    count;
///          char        (*desc)[/*count*/][256];
///          unsigned    iii;
///          ViStatus    err;
///     
///          err = CICW_GetConnectStrings(&count, &desc);
///          if (VI_ERROR_RSRC_NFOUND == err || 0 == count) {
///              printf("No CI4062/4122s found\n");
///              return err;
///          }
///          if (err < 0) {
///              printf("Something else wrong: 0%x\n", err);
///              return err;
///          }
///          printf("VISA Connect Strings:\n");
///          for (iii = 0; iii < count; ++iii)
///              printf("\t%d: %s\n", iii, (*desc)[iii]);
///          
///          CICW_ReleaseConnectStrings(&desc);
///     
///          return err;
///     }
/// \endcode
/// \section ErrorsAndWarnings Error Codes
/// \subsection Errors Table of Custom Error Codes:
/// \htmlonly
#ifdef DOXYGEN_INCLUDE
<style>
table { border:1px solid black; }
tr:nth-child(2n) { background-color: #f1f1f1; }
</style>
<table>
	<tr> <th width="250px">Error Name</th> <th width="150px">Error Value</th>	</tr>
	<tr>		<td>CICW_INVALID_SESSION</td>		<th>-1073782783</th>	</tr>
	<tr>		<td>CICW_CHINFO_NULL</td>			<th>-1073782782</th>	</tr>
	<tr>		<td>CICW_NULL_RESOURCE_MANAGER</td>	<th>-1073782781</th>	</tr>
	<tr>		<td>CICW_FREQ_HIGH</td>				<th>-1073782528</th>	</tr>
	<tr>		<td>CICW_FREQ_LOW</td>				<th>-1073782527</th>	</tr>
	<tr>		<td>CICW_PDAC_HIGH</td>				<th>-1073782526</th>	</tr>
	<tr>		<td>CICW_PDAC_LOW</td>				<th>-1073782525</th>	</tr>
	<tr>		<td>CICW_FDAC_HIGH</td>				<th>-1073782524</th>	</tr>
	<tr>		<td>CICW_FDAC_LOW</td>				<th>-1073782523</th>	</tr>
	<tr>		<td>CICW_INVALID_REFCLOCK</td>		<th>-1073782522</th>	</tr>
	<tr>		<td>CICW_NULL_INPUTS</td>			<th>-1073782521</th>	</tr>
	<tr>		<td>CICW_GAIN_INVALID</td>			<th>-1073782520</th>	</tr>
	<tr>		<td>CICW_POWER_HIGH</td>			<th>-1073782519</th>	</tr>
	<tr>		<td>CICW_POWER_LOW</td>				<th>-1073782518</th>	</tr>
	<tr>		<td>CICW_CAL_DATA_MISSING</td>		<th>-1073782517</th>	</tr>
	<tr>		<td>CICW_INVALID_VENDOR_ID</td>		<th>-1073782271</th>	</tr>
	<tr>		<td>CICW_MEMORY_TYPE_WRONG</td>		<th>-1073782270</th>	</tr>
</table>
#endif
/// \endhtmlonly
/// \subsection Warnings Table of Custom Warning Codes:
/// \htmlonly
#ifdef DOXYGEN_INCLUDE
<table>
	<tr> <th width="250px">Error Name</th> <th width="150px">Error Value</th> </tr>
	<tr> <td>CICW_PDAC_HIGH_WARNING</td> <th>1073701120</th> </tr>
	<tr> <td>CICW_PDAC_LOW_WARNING</td> <th>1073701121</th> </tr>
</table>
#endif
/// \endhtmlonly 
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////*/


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \internal
/// \brief This logs errors that occur
///
/// \param status This is the ViStatus, which should either be from a failed VISA command, or defined in CICW.h
/// \param errString This is just a short string explaining what went wrong
/// \param location The file and line number that the error was returned from
///
/// \endinternal
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus cicw_Error(ViStatus status, char* errString, char* location) {
    // Added check for empty log path to mw2Log to make sure logPath initialized
    char log[260];
    sprintf_s(log, sizeof(log), "Error in %s=> %d : %s\r\n", location, status, errString);
    mw2Log(log);

	return status;
}

ViStatus CICW_RevC_IfaceTest(ViChar *strIn, ViChar *strOut, unsigned int strLen, unsigned short statusIn) {
	memcpy(strOut, strIn, strLen);
	return statusIn;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Initializes the connection to the instrument. 
///
/// \param name The VISA resource name 
/// > Ex: PXI32::0::INSTR 
/// \param reset This will reset the selected channel, and set all values back to defaults. See \link CICW_ResetChannel \endlink
/// for more info. 
/// \param channel This channel gets saved into the session and cannot be changed. To control both channels,
/// this function must be called twice, and one session handle is created per channel.
/// \param session session is the ViSession that is used in all other functions. 
///
/// This must be called every time you want to access a different instrument. The pointer to the 
/// sessionHandle is used in all subsequent functions. If this function fails, all future functions calls using the returned session
/// will return the CICW_INVALID_SESSION error (-1073782783). 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_Init(ViChar* name, unsigned short *slotNumber) {
	int err = 0;
    char LogBuf[256];

    // Initializes log file path
    err = mw2Init(false);
	if (err < 0)
        return CICW_ERROR_CHECK(err, "Problem Initializing the log file.");

    sprintf_s(LogBuf, sizeof(LogBuf), "CICI_Init(\"%s\") Starting\r\n",name);
    mw2Log(LogBuf);


    // Really talk to hardware now.
    // Read cal data while initializing chInfo.
    // The "!!" converts reset to a boolean form the compiler recognizes to suppress warnings
    // about truncating to an unsigned short.  (Why reset is an unsigned short I do not know.)
	err = mw2Connect(name, slotNumber);
	if (err < 0)
        return err;

 	if (err == -1) {
		err = CICW_ERROR_CHECK(CICW_INVALID_VENDOR_ID, "Vendor ID was not 4062 or 4122.");
	} else if (err == -2) {
		err = CICW_ERROR_CHECK(CICW_MEMORY_TYPE_WRONG, "Memory type was not equal to 7");
	} else if (err == CICW_NULL_RESOURCE_MANAGER) {
        err = CICW_ERROR_CHECK(err, "Problem Initializing the defaultRM.");
	}

    sprintf_s(LogBuf, sizeof(LogBuf), "CICW_Init(\"%s\") Ending with code 0x%x\r\n",name, err);
    mw2Log(LogBuf);

	return err;
}


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Close the connection to the instrument
///
/// \param session The ViSession handle.
///
/// Closes the VISA connection and deletes VISA session resources used by the system. 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_Close() {
	ViStatus err = 0;

    mw2ShutDown();

	return err;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Sets the Reference Frequency divider.
///
/// \param session      The ViSession handle.
/// \param refDivider   The reference divider reduces the reference frequency applied to the PLL.  1 to 16383.
///
/// Sets the Reference Divider.  Should generally be 1 for the Internal or PXI clock sources.
///
/// The optimal frequency for the PLL is 50MHz (lowest phase noise) and the maximum is 80MHz.
///
/// A value of one avoids reference phase ambiguity.  (On power up, or when the divide ratio
/// changes to a non-1 value, it is possible for the divider phase to be randomized, affecting
/// coherency between sources.)
///
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_SetRefDivider(unsigned short slotNumber, unsigned short channel,  unsigned long refDivider) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

	
	mw2SetRefDivider(slotNumber, channel, refDivider);
	

	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Reads the Reference Frequency divider.
///
/// \param session      The ViSession handle.
/// \param refDivider   The reference divider reduces the reference frequency applied to the PLL.
/// 
/// Reads the Reference Divider.  Should always be 1 for the Internal or PXI clock sources.
///
/// The optimal frequency for the PLL is 50MHz (lowest phase noise) and the maximum is 80MHz.
///
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_GetRefDivider(unsigned short slotNumber, unsigned short channel,  unsigned long *refDivider) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

	
	*refDivider = mw2GetRefDivider(slotNumber, channel);
	

	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \internal
/// \brief Set frequency, pdac value, and gain. 
///
/// \param session The ViSession handle.
/// \param freq The desired output frequency
/// \param pdac What to set the attenuator value to. Acceptable values are from 0 to 4095 (Default = 3000)
/// \param gain What internal gain setting to use of the 833 chip. Acceptable values are 0, 3, 6, and 9 (Default = 9) 
///
/// This is an uncalibrated set of the frequency and power. 
/// \endinternal
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_SetFrequencyAttn(unsigned short slotNumber, unsigned short channel,  double freq, ViUInt16 pdac, ViUInt16 gain) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

	unsigned short fDac;
	unsigned long iVal;
	ViSession err = 0;

	if (pdac > 16383)
        return CICW_ERROR_CHECK(CICW_PDAC_HIGH, "PDAC greater than 16383.");
	if (pdac < 0)
        return CICW_ERROR_CHECK(CICW_PDAC_LOW, "PDAC must be > 0.");
	if (gain != 0 && gain != 3 && gain != 6 && gain != 9)
        return CICW_ERROR_CHECK(CICW_GAIN_INVALID, "Gain must be 0, 3, 6, or 9.");

    CardType cardType = mw2GetCardType(slotNumber);
	if (channel != 1 && cardType == MW4122Type) {
		if (freq > 12000)
            return CICW_ERROR_CHECK(CICW_FREQ_HIGH, "Frequency greater than max (12000)");
		if (freq < 6000)
            return CICW_ERROR_CHECK(CICW_FREQ_LOW, "Frequency less than min (6000)");
	} else {
		if (freq > 6000)
            return CICW_ERROR_CHECK(CICW_FREQ_HIGH, "Frequency greater than max (6000)");
		if (freq < 75)
            return CICW_ERROR_CHECK(CICW_FREQ_LOW, "Frequency less than min (75)");
	}
	mw2SetChInfoFreq(slotNumber, channel, freq);
	mw2OutputOnC(slotNumber, channel, TRUE/*mute*/, gain);
	iVal = mw2ReadRegister(slotNumber, channel, 0x10);
	mw2SetFilterBanksVCO(slotNumber, channel, freq, iVal);
	mw2Freq2FilterDac(slotNumber, channel, freq, &fDac);
	mw2SetFilterDac(slotNumber, channel, fDac);
	if (pdac >= 0 && pdac <= 16383)
		mw2SetAttenuatorDac(slotNumber, channel, pdac);
	else
		mw2SetAttenuatorDac(slotNumber, channel, 3000);
    

	if (pdac == 16383)
        err = CICW_PDAC_HIGH_WARNING;
	else if (pdac == 0)
        err = CICW_PDAC_LOW_WARNING;

	return err;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \internal
/// \brief Sets the frequency to the desired output, and attempts to guess settings to set the power level
///
/// \param session          The ViSession handle.
/// \param freq             Desired output frequency in MHz
/// \param power            Output power in dBm
/// \param outputEnabled    Drive the RF Output if true
/// 
/// This function estimates what to set the PDAC and Gain setting to, and turns the output on. This function will 
/// always output the same power level if the current slot has not had CI4000NET::CICW_Init called on it. 
/// \endinternal
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// NOTE: This is an internal function - ViLock guaranteed to be called before this function
ViStatus ConfigureRF(unsigned short slotNumber, unsigned short channel, double freq, double power, ViBoolean outputEnable, CalculateEstimates *CalcEst) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");
    if (power < MW2_POWER_MIN)
        return CICW_ERROR_CHECK(CICW_POWER_LOW,  "Power too low [-15, +15dBm]");
    if (power > MW2_POWER_MAX)
        return CICW_ERROR_CHECK(CICW_POWER_HIGH, "Power too high [-15, +15dBm]");

	unsigned long iVal;
	unsigned short gain, pdac, fdac;
    unsigned short pdac_in;
	vector<unsigned short> est;
	ViStatus err = 0;

    if (!CalcEst) {
        // No cal data.
        return CICW_ERROR_CHECK(CICW_CAL_DATA_MISSING,"Cal Data Missing");
    }

    unsigned long cardTemp = mw2GetTemperature(slotNumber);
	est = CalcEst->GetPdacValue(freq, power, cardTemp);
	gain = est[1];
	pdac = est[0];

    // VERY IMPORTANT:  When changing frequency, make sure that if the attenuator
    // value is increasing it gets programmed BEFORE the frequency change.
    // Otherwise the power level will go up, glitching whatever is on the output,
    // before it goes down to the programmed power.  This can DAMAGE devices
    // connected to the output.
    pdac_in = mw2GetAttenuatorDac(slotNumber, channel);
    if (pdac_in < pdac)
        mw2SetAttenuatorDac(slotNumber, channel, pdac);
    else
        pdac = pdac_in;

// @TODO Programming frequency is an expensive operation - do not touch if only changing power.
// Optimization - delay until later
	
	mw2SetChInfoFreq(slotNumber, channel, freq);
	mw2OutputOnC(slotNumber, channel, !outputEnable, gain);


	iVal = mw2ReadRegister(slotNumber, channel, 0x10);
	unsigned long vco = (iVal >> 6) & 0x00000003;
	unsigned long cap = iVal & 0x0000001F;

	est = CalcEst->GetPdacValue(freq, power, cardTemp, vco, cap);
	gain = est[1];

	mw2SetFilterBanksVCO(slotNumber, channel, freq, iVal);
	mw2Freq2FilterDac(slotNumber, channel, freq, &fdac);
	mw2SetFilterDac(slotNumber, channel, fdac);

    // pdac value results in more gain or error in estimate --> program it now
    if (pdac != est[0]) {
        pdac = est[0];
        mw2SetAttenuatorDac(slotNumber, channel, pdac);
    }

	if (pdac == 16383)
        err = CICW_PDAC_HIGH_WARNING;
	else if (pdac == 0)
        err = CICW_PDAC_LOW_WARNING;

	return err;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Sets the frequency and power.
///
/// \param session  The ViSession handle.
/// \param freqMHz     Desired output frequency in MHz
/// \param power_dBm    Output power in dBm
/// 
/// Setting Frequency and Power at the same time is more efficient than setting them separately
/// since changing frequency requires changing attenuators to compensate for frequency response.
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_Configure(unsigned short slotNumber, unsigned short channel, double freqMHz, double power_dBm, CalculateEstimates *CalcEst) {
	ViStatus err;

	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

    ViBoolean outputEnabled = mw2Locked(slotNumber, channel);
	err = ConfigureRF(slotNumber, channel, freqMHz, power_dBm, outputEnabled, CalcEst);
    

    return err;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \internal
/// \brief This runs the freq2FilterDac function, and returns the FDAC value based on frequency. 
///
/// \param session The ViSession handle.
/// \param freqMHz FDAC is specific to frequency, this returns the FDAC value based on the input freq (in MHz)
/// \param fdac Returns the FDAC value, which is between 0 and 16383. 
/// \endinternal
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_GetFDAC(unsigned short slotNumber, unsigned short channel,  double freqMHz, unsigned short* fdac) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

 	mw2Freq2FilterDac(slotNumber, channel, freqMHz, fdac);
    

	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \internal
/// \brief Read Power fine attenuation DAC value
///
/// \param session  The ViSession handle.
/// \param pdac     Returns the current pdac value, which will be between 0 and 16383
/// 
/// \endinternal
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_GetPDAC(unsigned short slotNumber, unsigned short channel,  unsigned short* pdac) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

   *pdac = mw2GetAttenuatorDac(slotNumber, channel);
    

	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Sets the reference clock to the selected Clock type
///
/// \param session  The ViSession handle.
/// \param clockSrc      Enumerated type.
/// \param clockMHz What frequency in MHz to set the Reference Clock to.  Only applies to Ext channels.
///
/// NOTE: Changing the Reference affects both channels.  The channel used to change the
///       reference does not have enough information to re-program the other channel.
///       Both channels are muted during the reference change to prevent undesirable output.
///
/// The reference clock sources are Internal, External (SMA), and PXI 10MHz.
/// The references for the two channels are not completely independent so
/// this function sets the state of both channels at the same time.
///
/// There is only one External reference SMA connector so this value
/// applies to both channels.
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_SelectClock(unsigned short slotNumber, unsigned short channel,  CICW_RefClockSrc clockSrc, double clockMHz) {
    ViStatus err = 0;
    bool ext;

	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

	//typedef enum {ClockIntInt, ClockExtExt, ClockPxiPxi, ClockExtInt, ClockExtPxi} ClockType;
	if (clockSrc == CICW_RefClockIntIntOff || clockSrc == CICW_RefClockIntIntInt || clockSrc == CICW_RefClockPxiPxiOff) {
        ext = false;
		clockMHz = 0;
	} else {
		if (clockMHz > 350 || clockMHz < 10)
            return CICW_ERROR_CHECK(CICW_INVALID_REFCLOCK, "Reference Clock out of range (10-350 MHz)");
        ext = true;
	}
    ClockType newType = (ClockType)clockSrc;

    // Need a lock from as soon as we start reading from HW until after stop writing
    
    ClockType oldType = mw2GetClockType(slotNumber);

    bool changed = false;
	double oldFreq = mw2GetClockMHz(slotNumber, channel);
	if (newType != oldType || (ext && fabs(oldFreq - clockMHz) > 1e-9)) {
        // Clock source gets changed below, before turning back on signal, unnecessary here
        // mw2SelectClock(slotNumber, channel, newType, clockMHz);
        changed = true;
    } 
	
    if (changed) {
        // Reference really changed.
        // Need to re-program both channels for both HMC833 and (possibly) atten.
        // Problem:  This session only has cal data for its channel.
        // The actual output freq hasn't changed, but the VCO gain could have.
        // Mute other output for safety.  Actually, do it first for both chans.

        for (channel = 0; channel < MW2_MAX_CHANNELS; channel++) {
            mw2OutputOff(slotNumber, channel);
        }

        // Clock source changed
        mw2SelectClock(slotNumber, newType, clockMHz, TRUE);
    }
    

	return err;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Turns all output power off on the selected channel
///
/// \param session The ViSession handle.
/// \param enabled True turns the output on, false turns it off (Mute).
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_SetOutputEnabled(unsigned short slotNumber, unsigned short channel,  ViBoolean enabled)
{
    HRESULT hr = 0;
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");
    
    if(VI_TRUE == enabled) {
		mw2OutputOn(slotNumber, channel, enabled);
	} else {
		mw2OutputOff(slotNumber, channel);
    }
    

	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Gets whether the instrument is currently outputting signal
///
/// \param session The ViSession handle.
/// \param enabled This is set to true if outputting, false if not.  
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_GetOutputEnabled(unsigned short slotNumber, unsigned short channel,  ViBoolean *enabled) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

    
	*enabled = mw2Locked(slotNumber, channel);
    

	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Pings the lock detect bit to check if the selected channel is outputting signal.
///
/// \param session The ViSession handle.
/// \param locked Returns true if locked (Outputting Signal) or false if not locked. 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_SignalLocked(unsigned short slotNumber, unsigned short channel,  ViBoolean* locked) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

    
	*locked = mw2Locked(slotNumber, channel);
    

	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Disables output on the selected session 
///
/// \param session The ViSession handle.
///
/// Places the instrument in a minimal output power state. 
/// Disable is a more time consuming function than \link CICW_SetOutputEnabled \endlink
/// but also brings the signal level down to the absolute minimum. 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_DisableOutput(unsigned short slotNumber, unsigned int channel) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

    
	mw2SetAttenuatorDac(slotNumber, channel, 16383);
	if (mw2GetCardType(slotNumber) == MW4122Type && channel != 1) {

		mw2SetChInfoFreq(slotNumber, channel, 8000);
		mw2OutputOnC(slotNumber, channel, TRUE, 9);
		mw2SetFilterBanksVCO(slotNumber, channel, 10000, 0);
		mw2SetFilterDac(slotNumber, channel, 0);
	} else {
		mw2SetChInfoFreq(slotNumber, channel, 2000);
		mw2OutputOnC(slotNumber, channel, TRUE, 9);
		mw2SetFilterBanksVCO(slotNumber, channel, 800, 0);
		mw2SetFilterDac(slotNumber, channel, 0);
	}
    
	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Resets all settings on the instrument, including the frequency reference for both channels to internal.
///
/// \param session The ViSession handle.
/// 
/// This runs \link CICW_ResetChannel \endlink on both channels, and sets the reference oscillator to Internal for both channels. 
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_ResetCard(unsigned short slotNumber) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

    
	ViStatus err = mw2ResetCard(slotNumber);
    

	return err;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Resets all settings on the channel.  Does not affect the shared frequency reference.
///
/// \param session The ViSession handle.
///
/// Sets the frequency and power levels to their default states, and turns off the output. The reference oscillator is left alone 
/// however because that affects both channels. To also reset that to default, call \link CICW_ResetCard \endlink
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_ResetChannel(unsigned short slotNumber) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "CICW_ResetChannel(): Session not valid");

    
	ViStatus err = mw2ResetCard(slotNumber);
    

	return err;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Returns the Board ID string
///
/// \param session              The ViSession handle.
/// \param boardID              Returns a string that has the following format: \<card type\>\<serial number\>
/// \param maxBoardIDLength     sizeof(boardID) buffer.  16 bytes min
///
/// > Example: "4062C000005" is a 4062 board with serial number C000005
///
/// NOTE: This string is subject to change.  Call \link CICW_GetCardType \endlink,
///       \link CICW_GetCardRev \endlink, or \link CICW_GetSerialNumber \endlink direcly
///       instead of extracting them from this string in case the field lengths change.
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Serial number format changing from 32 bit integer --> 9 digits theoretical max to RBBSSSE format.
// (BOM Rev (letter), Batch code (letters), Serial (3 numbers), ECN code (1 digit)) --> serial goes
// from intended 6 digits to 7 digits.
// Also, VSG uses a 5 digit model number --> consistency across product lines is a good thing.
ViStatus CICW_RevC_GetBoardIDString(unsigned short slotNumber, unsigned short channel,  ViChar* boardID, ViUInt32 maxBoardIDLength) {
    unsigned short usCardDevId;
    char rev;
    
    if (maxBoardIDLength < 12)
        return CICW_ERROR_CHECK(CICW_INVALID_SESSION,"CICW_GetBoardIDString: maxBoardLength must be at least 12");

    
	usCardDevId = mw2GetCardDevId(slotNumber);
	
	unsigned long serial = mw2GetSerial(slotNumber);
    rev = mw2GetCardRev(slotNumber);
    

	sprintf_s(boardID, maxBoardIDLength, "%04x%c%06d", usCardDevId, rev, serial);

	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Read the Firmware Revision
///
/// \param session      The ViSession handle.
/// \param fwRev        String firmware revision
/// \param maxFWRevLen  sizeof(fwRev) buffer; 25 bytes min 
/// 
/// NOTE:  The firmware rev format is subject to change and may contain
///        letters and multiple numbers in the future.
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Anticpated fimware rev changes:  Firmware for rider boards --> another 32 bit int plus
// separator.  May also want to support branching.  For instance, a "D" to indicate Rev D specific.
// Encoding svnversion or build time is also possible.  10 digits handles 32 bit -1 plus terminating 0.
ViStatus CICW_RevC_GetFirmwareRev(unsigned short slotNumber, unsigned short channel,  ViChar* fwRev, ViUInt32 maxFWRevLen) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

    
	unsigned rev = mw2GetFwVersion(slotNumber);
    
    sprintf_s(fwRev, maxFWRevLen, "%d", rev);

	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief 4062 or 4122 for a CI4062 or CI4122 respectively.
///
/// \param session          The ViSession handle.
/// \param cardType         Model Number
/// \param maxCardTypeLen   sizeof(cardType); 7 bytes min 
/// 
/// Note:  Future revs may have an alpha suffix.
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// The VSG uses a 5 digit model.
// May start putting a letter suffix after the numeric part.
ViStatus CICW_RevC_GetCardType(unsigned short slotNumber, unsigned short channel,  ViChar *cardType, ViUInt32 maxCardTypeLen) { // Returns 0x4062 or 0x4122
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

    
	unsigned ccc = mw2GetCardDevId(slotNumber);
    
    sprintf_s(cardType, maxCardTypeLen, "%04x", ccc);

	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \internal
/// \brief Board revision letter (D, E, F, etc.)
///
/// \param session          The ViSession handle.
/// \param cardRev          A letter representing the hardware revision.
/// \param maxCardRevLen    sizeof(cardRev) buffer;  3 bytes min 
///
/// This driver does not support Rev C or older hardware.
/// \endinternal
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_GetCardRev(unsigned short slotNumber, unsigned short channel,  ViChar *cardRev, ViUInt32 maxCardRevLen) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

    
	char ccc = mw2GetCardRev(slotNumber);
    
    if (maxCardRevLen > 2) {
        cardRev[0] = ccc;
        cardRev[1] = 0;
    }

	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Read Serial Number
///
/// \param session          The ViSession handle.
/// \param serial           Serial Number.
/// \param maxSerialLen     sizeof(serial) buffer.  (Recommend 10; currently use 7 or 8)
/// 
/// > Example: "000001"
/// > Example: "KAB0010"
///
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_GetSerialNumber(unsigned short slotNumber, unsigned short channel,  unsigned long *serial) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");
// @TODO new serial # fmt is alphanumeric -- need a string

    
	*serial = mw2GetSerial(slotNumber);
    

	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Gets the current temperature of the board
///
/// \param session  The ViSession handle.
/// \param temp_C     The temperature of the board in Celsius.
///
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_GetTemperature(unsigned short slotNumber, unsigned short channel,  double* temp_C) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

    
    *temp_C = (unsigned short)mw2GetTemperature(slotNumber)/32.0;
    

	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Gets the current Reference Clock setting for the connected instrument
///
/// \param session The ViSession handle.
/// \param refClock This returns the currently selected Reference Clock 
///
/// The reference clock sources are Internal, External (SMA), and PXI 10MHz.
/// The references for the two channels are not completely independent so
/// this function reports the state of both channels at the same time.
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_GetClock(unsigned short slotNumber, unsigned short channel,  CICW_RefClockSrc* refClock) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

    
	*refClock = (CICW_RefClockSrc)mw2GetClockType(slotNumber);
    

	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Gets the current Reference Clock Frequency setting for the connected instrument
///
/// \param session The ViSession handle.
/// \param clockMHz Returns the current Reference Clock Frequency in MHz, regardless of source.
/// 
/// The reference clock provides the basis for frequency accuracy.
///
/// By tying all of your instruments to the same reference clock, even with the knowledge
/// that its frequency is not perfect, all of the instruments will agree, to within the
/// limits of their resoltion, on what a particular frequency is supposed to be.
///
/// If the reference source is Internal clockMHz will be 50.
///
/// If the reference source is PXI clockMHz will be 10.
///
/// If the reference source is External clockMHz will be whatever it is programmed to.
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_GetClockMHz(unsigned short slotNumber, unsigned short channel,  double* clockMHz) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

    
	*clockMHz = mw2GetClockMHz(slotNumber, channel);
    

	return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Gets the External Reference Clock Frequency
///
/// \param session  The ViSession handle.
/// \param clockMHz Returns the External Reference Clock Frequency in MHz. 
/// 
/// The reference clock provides the basis for frequency accuracy.
///
/// By tying all of your instruments to the same reference clock, even with the knowledge
/// that its frequency is not perfect, all of the instruments will agree, to within the
/// limits of their resolution, on what a particular frequency is supposed to be.
///
/// This is always the External reference, regardless of which reference
/// is actually being used.
///
/// Note there is only one External reference SMA connector so this value
/// applies to both channels.
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_GetExtRefMHz(unsigned short slotNumber, unsigned short channel,  double* clockMHz) {
	if(slotNumber < 0)
		return CICW_ERROR_CHECK(CICW_INVALID_SESSION, "Session was not valid");

    
	*clockMHz = mw2GetClockMHz(slotNumber, channel);
    

	return 0;
}


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// \brief Gets the CICW DLL version number in single number format.
///
/// \param buff     Buffer to write characters into
/// \param buffsz   sizeof(buff)  Allocate 6 or more characters.
/// 
/// The channel number is set by CICW_Init().
///
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
ViStatus CICW_RevC_GetDLLVersion(char* buff, size_t buffsz) {
    //sprintf_s(buff, buffsz, "%s", svn_ver);
    return 0;
}

ViStatus CICW_RevC_GetCalculateEstimates(unsigned short slotNumber, CalculateEstimates *ch1CalcEst, CalculateEstimates *ch2CalcEst) {
	short buffer[0x800];
	bool ch0found = false, ch1found = false;
	int ch0Num = 0, ch1Num = 0;
	int err = 0;
	
	if ((mw2GetCardType(slotNumber) == MW4062Type) || (mw2GetCardType(slotNumber) == MW4122Type)){
		// Loop through all of the possible cal channels and create calibrations for every card
		ch0found = false; ch1found = false;
		ch0Num = 0; ch1Num = 0;
		for (int i = 0; i < 10; i++) {
			//load->labelProcessing->Text = "Reading Slot "+Slot+" Calibration...";
			err = mw2GetCalData(slotNumber, 0, i, (UCHAR*)buffer);
			//tbStatus->AppendText("Loop "+i+" ch0 err: "+err+"  buffer[0]: "+buffer[0]+"\r\n");
			if (err != MW2ECNOERR || buffer[0] != (short)0xFFFF) {
				std::vector<short> buf(buffer, buffer + sizeof(buffer) / sizeof(buffer[0]));
				if (ch0found == false) {
					ch2CalcEst = new CalculateEstimates(buf);
					ch0found = true;
				}
				else ch2CalcEst->AddNewValues(buf);
				ch0Num++;
			}
			err = mw2GetCalData(slotNumber, 1, i, (UCHAR*)buffer);
			//tbStatus->AppendText("Loop "+i+" ch1 err: "+err+"  buffer[0]: "+buffer[0]+"\r\n");
			if (err != MW2ECNOERR || buffer[0] != (short)0xFFFF) {
				std::vector<short> buf(buffer, buffer + sizeof(buffer) / sizeof(buffer[0]));
				if (ch1found == false) {
					ch1CalcEst = new CalculateEstimates(buf);
					ch1found = true;
				}
				else ch1CalcEst->AddNewValues(buf);
				ch1Num++;
			}
		}
	}

	return 0;
}
