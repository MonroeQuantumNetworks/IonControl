"""Provide a thin, ctypes interface over the CICW DLL"""
import ctypes
import warnings
import os.path

class CICW_RefClockSrc:
    """The CICW_RefClockSrc enumeration used in several of the DLL
    functions."""
    CICW_RefClockIntIntOff = 0                 #<    Ch 1 Internal, Ch2 Internal
    CICW_RefClockIntIntInt = 1                 #<    Ch 1 Internal, Ch2 Internal; Drive Internal out Ref SMA
    CICW_RefClockPxiPxiOff = 2                 #<    Ch 1 PXI,      Ch2 PXI
    CICW_RefClockExtExtOff = 3                 #<    Ch 1 External, Ch2 External
    CICW_RefClockIntExtOff = 4                 #<    Ch 1 Internal, Ch2 External
    CICW_RefClockExtPxiOff = 5                 #<    Ch 1 External, Ch2 PXI

0x80000000 | 0x3FFF0000 | 0x6000

# Use read_error() instead of this table directly
CICW_ErrorLookup = {
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x001 : 'CICW_INVALID_SESSION',
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x002 : 'CICW_CHINFO_NULL',
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x003 : 'CICW_NULL_RESOURCE_MANAGER',

    # 0x1-- are errors with the user input 
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x100 : 'CICW_FREQ_HIGH',
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x101 : 'CICW_FREQ_LOW',
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x102 : 'CICW_PDAC_HIGH',
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x103 : 'CICW_PDAC_LOW',
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x104 : 'CICW_FDAC_HIGH',
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x105 : 'CICW_FDAC_LOW',
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x106 : 'CICW_INVALID_REFCLOCK',
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x107 : 'CICW_NULL_INPUTS',
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x108 : 'CICW_GAIN_INVALID',
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x109 : 'CICW_POWER_HIGH',
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x10A : 'CICW_POWER_LOW',
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x10B : 'CICW_CAL_DATA_MISSING',

    # These are warnings caused by user input
    0x3FFF0000 | 0x6000 | 0x100 : 'CICW_PDAC_HIGH_WARNING',
    0x3FFF0000 | 0x6000 | 0x101 : 'CICW_PDAC_LOW_WARNING',

    # 0x2-- means something hardware related caused the issue, or something from CI4000Lib
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x201 : 'CICW_INVALID_VENDOR_ID',
    0x80000000 | 0x3FFF0000 | 0x6000 | 0x202 : 'CICW_MEMORY_TYPE_WRONG'
}

# Use read_error() instead of this table directly
VI_ErrorLookup = {
    0x3FFF000CL : 'VI_WARN_QUEUE_OVERFLOW',
    0x3FFF0077L : 'VI_WARN_CONFIG_NLOADED',
    0x3FFF0082L : 'VI_WARN_NULL_OBJECT',
    0x3FFF0084L : 'VI_WARN_NSUP_ATTR_STATE',
    0x3FFF0085L : 'VI_WARN_UNKNOWN_STATUS',
    0x3FFF0088L : 'VI_WARN_NSUP_BUF',
    0x3FFF00A9L : 'VI_WARN_EXT_FUNC_NIMPL',
    0x80000000 | 0x3FFF0000L : 'VI_ERROR_SYSTEM_ERROR',
    0x80000000 | 0x3FFF000EL : 'VI_ERROR_INV_OBJECT',
    0x80000000 | 0x3FFF000FL : 'VI_ERROR_RSRC_LOCKED',
    0x80000000 | 0x3FFF0010L : 'VI_ERROR_INV_EXPR',
    0x80000000 | 0x3FFF0011L : 'VI_ERROR_RSRC_NFOUND',
    0x80000000 | 0x3FFF0012L : 'VI_ERROR_INV_RSRC_NAME',
    0x80000000 | 0x3FFF0013L : 'VI_ERROR_INV_ACC_MODE',
    0x80000000 | 0x3FFF0015L : 'VI_ERROR_TMO',
    0x80000000 | 0x3FFF0016L : 'VI_ERROR_CLOSING_FAILED',
    0x80000000 | 0x3FFF001BL : 'VI_ERROR_INV_DEGREE',
    0x80000000 | 0x3FFF001CL : 'VI_ERROR_INV_JOB_ID',
    0x80000000 | 0x3FFF001DL : 'VI_ERROR_NSUP_ATTR',
    0x80000000 | 0x3FFF001EL : 'VI_ERROR_NSUP_ATTR_STATE',
    0x80000000 | 0x3FFF001FL : 'VI_ERROR_ATTR_READONLY',
    0x80000000 | 0x3FFF0020L : 'VI_ERROR_INV_LOCK_TYPE',
    0x80000000 | 0x3FFF0021L : 'VI_ERROR_INV_ACCESS_KEY',
    0x80000000 | 0x3FFF0026L : 'VI_ERROR_INV_EVENT',
    0x80000000 | 0x3FFF0027L : 'VI_ERROR_INV_MECH',
    0x80000000 | 0x3FFF0028L : 'VI_ERROR_HNDLR_NINSTALLED',
    0x80000000 | 0x3FFF0029L : 'VI_ERROR_INV_HNDLR_REF',
    0x80000000 | 0x3FFF002AL : 'VI_ERROR_INV_CONTEXT',
    0x80000000 | 0x3FFF002DL : 'VI_ERROR_QUEUE_OVERFLOW',
    0x80000000 | 0x3FFF002FL : 'VI_ERROR_NENABLED',
    0x80000000 | 0x3FFF0030L : 'VI_ERROR_ABORT',
    0x80000000 | 0x3FFF0034L : 'VI_ERROR_RAW_WR_PROT_VIOL',
    0x80000000 | 0x3FFF0035L : 'VI_ERROR_RAW_RD_PROT_VIOL',
    0x80000000 | 0x3FFF0036L : 'VI_ERROR_OUTP_PROT_VIOL',
    0x80000000 | 0x3FFF0037L : 'VI_ERROR_INP_PROT_VIOL',
    0x80000000 | 0x3FFF0038L : 'VI_ERROR_BERR',
    0x80000000 | 0x3FFF0039L : 'VI_ERROR_IN_PROGRESS',
    0x80000000 | 0x3FFF003AL : 'VI_ERROR_INV_SETUP',
    0x80000000 | 0x3FFF003BL : 'VI_ERROR_QUEUE_ERROR',
    0x80000000 | 0x3FFF003CL : 'VI_ERROR_ALLOC',
    0x80000000 | 0x3FFF003DL : 'VI_ERROR_INV_MASK',
    0x80000000 | 0x3FFF003EL : 'VI_ERROR_IO',
    0x80000000 | 0x3FFF003FL : 'VI_ERROR_INV_FMT',
    0x80000000 | 0x3FFF0041L : 'VI_ERROR_NSUP_FMT',
    0x80000000 | 0x3FFF0042L : 'VI_ERROR_LINE_IN_USE',
    0x80000000 | 0x3FFF0046L : 'VI_ERROR_NSUP_MODE',
    0x80000000 | 0x3FFF004AL : 'VI_ERROR_SRQ_NOCCURRED',
    0x80000000 | 0x3FFF004EL : 'VI_ERROR_INV_SPACE',
    0x80000000 | 0x3FFF0051L : 'VI_ERROR_INV_OFFSET',
    0x80000000 | 0x3FFF0052L : 'VI_ERROR_INV_WIDTH',
    0x80000000 | 0x3FFF0054L : 'VI_ERROR_NSUP_OFFSET',
    0x80000000 | 0x3FFF0055L : 'VI_ERROR_NSUP_VAR_WIDTH',
    0x80000000 | 0x3FFF0057L : 'VI_ERROR_WINDOW_NMAPPED',
    0x80000000 | 0x3FFF0059L : 'VI_ERROR_RESP_PENDING',
    0x80000000 | 0x3FFF005FL : 'VI_ERROR_NLISTENERS',
    0x80000000 | 0x3FFF0060L : 'VI_ERROR_NCIC',
    0x80000000 | 0x3FFF0061L : 'VI_ERROR_NSYS_CNTLR',
    0x80000000 | 0x3FFF0067L : 'VI_ERROR_NSUP_OPER',
    0x80000000 | 0x3FFF0068L : 'VI_ERROR_INTR_PENDING',
    0x80000000 | 0x3FFF006AL : 'VI_ERROR_ASRL_PARITY',
    0x80000000 | 0x3FFF006BL : 'VI_ERROR_ASRL_FRAMING',
    0x80000000 | 0x3FFF006CL : 'VI_ERROR_ASRL_OVERRUN',
    0x80000000 | 0x3FFF006EL : 'VI_ERROR_TRIG_NMAPPED',
    0x80000000 | 0x3FFF0070L : 'VI_ERROR_NSUP_ALIGN_OFFSET',
    0x80000000 | 0x3FFF0071L : 'VI_ERROR_USER_BUF',
    0x80000000 | 0x3FFF0072L : 'VI_ERROR_RSRC_BUSY',
    0x80000000 | 0x3FFF0076L : 'VI_ERROR_NSUP_WIDTH',
    0x80000000 | 0x3FFF0078L : 'VI_ERROR_INV_PARAMETER',
    0x80000000 | 0x3FFF0079L : 'VI_ERROR_INV_PROT',
    0x80000000 | 0x3FFF007BL : 'VI_ERROR_INV_SIZE',
    0x80000000 | 0x3FFF0080L : 'VI_ERROR_WINDOW_MAPPED',
    0x80000000 | 0x3FFF0081L : 'VI_ERROR_NIMPL_OPER',
    0x80000000 | 0x3FFF0083L : 'VI_ERROR_INV_LENGTH',
    0x80000000 | 0x3FFF0091L : 'VI_ERROR_INV_MODE',
    0x80000000 | 0x3FFF009CL : 'VI_ERROR_SESN_NLOCKED',
    0x80000000 | 0x3FFF009DL : 'VI_ERROR_MEM_NSHARED',
    0x80000000 | 0x3FFF009EL : 'VI_ERROR_LIBRARY_NFOUND',
    0x80000000 | 0x3FFF009FL : 'VI_ERROR_NSUP_INTR',
    0x80000000 | 0x3FFF00A0L : 'VI_ERROR_INV_LINE',
    0x80000000 | 0x3FFF00A1L : 'VI_ERROR_FILE_ACCESS',
    0x80000000 | 0x3FFF00A2L : 'VI_ERROR_FILE_IO',
    0x80000000 | 0x3FFF00A3L : 'VI_ERROR_NSUP_LINE',
    0x80000000 | 0x3FFF00A4L : 'VI_ERROR_NSUP_MECH',
    0x80000000 | 0x3FFF00A5L : 'VI_ERROR_INTF_NUM_NCONFIG',
    0x80000000 | 0x3FFF00A6L : 'VI_ERROR_CONN_LOST',
    0x80000000 | 0x3FFF00A7L : 'VI_ERROR_MACHINE_NAVAIL',
    0x80000000 | 0x3FFF00A8L : 'VI_ERROR_NPERMISSION'
}

def read_error(error_code):
    """Return a string representing the name of the error from its code.

    error_code -- The error code returned by the DLL. This will accept
    either a positive or negative integer.

    Return a string representing the error code, or the string
    UNKNOWN_ERROR if no string could be found.
    """
    if error_code < 0:
        # This works because error codes are intended to be 32-bit
        # signed integers
        error_code += 0x100000000
    error_code = long(error_code)
    if CICW_ErrorLookup.has_key(error_code):
        return CICW_ErrorLookup[error_code]
    if VI_ErrorLookup.has_key(error_code):
        return VI_ErrorLookup[error_code]
    return 'UNKNOWN_ERROR'

class CICW_ThinInterface(object):
    """Provide a thin interface over the CICW DLL. This is organized as a
    class (as opposed to a bunch of functions) so that using this
    locally or an RPC server remotely can be made to look the same.
    """

    # The default path of the DLL.
    DLL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'bin', 'x64', 'Release', 'CICW_RevC.dll'))

    # A list of functions that we expect to be present in the DLL. If
    # any of these are not present, we will present a warning on
    # initialization.
    FUNCTIONS = ['CICW_RevC_IfaceTest',
                 'CICW_RevC_Init', 'CICW_RevC_Close', 'CICW_RevC_Configure', 'CICW_RevC_SignalLocked',
                 'CICW_RevC_GetOutputEnabled', 'CICW_RevC_SetOutputEnabled', 'CICW_RevC_DisableOutput',
                 'CICW_RevC_GetCalculateEstimates', 'CICW_RevC_SelectClock', 'CICW_RevC_GetClock',
                 'CICW_RevC_GetClockMHz', 'CICW_RevC_GetExtRefMHz', 'CICW_RevC_GetRefDivider',
                 'CICW_RevC_SetRefDivider', 'CICW_RevC_GetBoardIDString', 'CICW_RevC_GetCardType',
                 'CICW_RevC_GetFirmwareRev', 'CICW_RevC_GetSerialNumber', 'CICW_RevC_ResetCard',
                 #'CICW_RevC_ResetChannel',
                 'CICW_RevC_GetTemperature', 'CICW_RevC_GetCardRev',
                 'CICW_RevC_SetFrequencyAttn', 'CICW_RevC_GetFDAC', 'CICW_RevC_GetPDAC']

    # A dictionary supporting the reuse of DLL objects for this class
    _dll_dict = {}

    @classmethod
    def get_dll(cls, dll_path = None):
        """Return an instance of this class corresponding to the DLL
        given. Use this preferentially to __init__, since this will cache the
        DLL for use later and only ever open the DLL once.

        cls -- Ignore this like you would with self

        dll_path -- The path to the DLL. If not given, use the default
        from this class.

        Return an instance of the CICW_ThinInterface class.

        """
        if dll_path is None:
            dll_path = cls.DLL_PATH
        if not cls._dll_dict.has_key(dll_path):
            cls._dll_dict[dll_path] = cls(dll_path)
        return cls._dll_dict[dll_path]

    def __init__(self, dll_path = None):
        """Create a new interface to the CICW DLL. This provides no more than
        a thin wrapper around the functions it exports. Please
        consider using the classmethod get_dll instead of directly
        using this constructor, since get_dll will cache the returned
        object so you don't open the DLL multiple times.

        dll_path -- The path to the DLL. If not given, use the default
        from this class.

        Note that this does not call the Init function, it merely
        initializes the DLL.
        """
        if dll_path is None:
            dll_path = self.DLL_PATH
        try:
            self._dll = ctypes.CDLL(dll_path)
        except Exception as e:
            if not os.path.exists(dll_path):
                raise ValueError('Could not open DLL {} because the path does not exist'.format(dll_path))
            raise ValueError('Could not open DLL {}: {}'.format(dll_path, e))

        for funcname in self.FUNCTIONS:
            try:
                func = getattr(self._dll, funcname)
                # All functions have ViStatus return type, which seems
                # to boil down to a signed 32-bit integer.
                func.restype = ctypes.c_int
            except:
                warnings.warn('The DLL loaded successfully, but does not have function {}'.format(funcname),
                              RuntimeWarning)

        # Test the interface
        try:
            tstrIn = ctypes.create_string_buffer('a'*23, 24)
            tstrOut = ctypes.create_string_buffer(24)
            status = self._dll.CICW_RevC_IfaceTest(tstrIn, tstrOut, ctypes.c_uint(24), 12);
            if status != 12:
                warnings.warn('The DLL test was unsuccessful, return code was {}, expected 12'.format(status))
            if tstrIn.value != tstrOut.value:
                warnings.warn('The DLL test was unsuccessful, string out was {}, expected {}'.format(tstrIn.value, tstrOut.value))
        except Exception as e:
            warnings.warn('The DLL test was unsuccessful: {}'.format(e))

    def Init(self, name):
        """Initialize the connection to the instrument

        name -- The VISA resource name. e.g. PXI32::0::INSTR

        Returns (status, slotNumber). The slotNumber is passed to
        all other functions to identify the instrument initialized
        with this function.

        JWV: The header signature of this function has the slotNumber
        as an input variable, but the source code uses it as an output
        variable and takes a pointer. Since ctypes ignores the header,
        this is not a problem.

        """
        slotNumber = ctypes.c_ushort()
        status = self._dll.CICW_RevC_Init(str(name), ctypes.byref(slotNumber))
        return status, slotNumber

    def Close(self):
        """Closes the VISA connection and deletes VISA session resources used by the system.

        Return the status.

        JWV: Since this does not take a slotNumber argument, I'm
        really not sure when you call this.
        """
        return int(self._dll.CICW_RevC_Close().value)

    def Configure(self, slotNumber, channel, freqMHz, power_dBm, CalcEst):
        """Set the frequency and power. Setting Frequency and Power at the
        same time is more efficient than setting them separately since
        changing frequency requires changing attenuators to compensate
        for frequency response. NOTE: This method doesn't work.

        slotNumber -- The number returned from Init identifying the slot.

        channel -- Undocumented

        freqMHz -- Desired output frquency in MHz

        power_dBm -- Output power in dBm

        CalcEst -- A CalculateEstimates object. The achilles heel of
        this function. It is required, but there is currently no way
        to produce these through the DLL. Sorry.

        Return status.

        JWV: Don't call this method. There is no way to make it work
        with the DLL set up as it is.
        """
        # Return VI_ERROR_NENABLED
        return -1073807313

    def SignalLocked(self, slotNumber, channel):
        """Ping the lock detect bit to check if the selected channel is
        outputting signal.

        slotNumber -- The number returned from Init identifying the slot.

        channel -- Undocumented

        Return (status, locked). Locked is True if the channel is
        locked (outputting signal) or False otherwise.

        JWV: This is a different function from GetOutputEnabled, but
        they have identical source code.

        """
        locked = ctypes.c_ushort()
        status = self._dll.CICW_RevC_SignalLocked(ctypes.c_ushort(slotNumber),
                                                  ctypes.c_ushort(channel),
                                                  ctypes.byref(locked))
        return status, bool(locked.value)

    def GetOutputEnabled(self, slotNumber, channel):
        """Return whether the instrument is currently outputting signal.

        slotNumber -- The number returned from Init identifying the slot.

        channel -- Undocumented

        Return (status, enabled). Enabled is True if the channel is
        locked (outputting signal) or False otherwise.

        JWV: This is a different function from SignalLocked, but they
        have identical source code.
        """
        enabled = ctypes.c_ushort()
        status = self._dll.CICW_RevC_GetOutputEnabled(ctypes.c_ushort(slotNumber),
                                                      ctypes.c_ushort(channel),
                                                      ctypes.byref(enabled))
        return status, bool(enabled.value)

    def SetOutputEnabled(self, slotNumber, channel, enabled):
        """Turn all output power on or off on the selected channel.

        slotNumber -- The number returned from Init identifying the slot.

        channel -- Undocumented

        enabled -- True turns the output on, False turns it off (Mute).

        Return status.
        """
        status = self._dll.CICW_RevC_SetOutputEnabled(ctypes.c_ushort(slotNumber),
                                                      ctypes.c_ushort(channel),
                                                      ctypes.c_ushort(bool(enabled)))
        return status

    def DisableOutput(self, slotNumber, channel):
        """Places the instrument in a minimal output power state. Dissable is
        a more time-consuming function than SetOutputEnabled but also
        brings the signal level down to the absolute minimum.

        slotNumber -- The number returned from Init identifying the slot.

        channel -- Undocumented

        Return status.
        """
        # The interface for this function requires channel to be an
        # unsigned int, unlike all the others where it is an unsigned
        # short
        status = self._dll.CICW_RevC_DisableOutput(ctypes.c_ushort(slotNumber),
                                                   ctypes.c_uint(channel))
        return status

    def GetCalculateEstimates(self, slotNumber, ch1CalcEst, ch2CalcEst):
        """Return CalculateEstimate objects for two channels. NOTE: Don't use
        this function.

        slotNumber -- The number returned from Init identifying the slot.

        ch1CalcEst -- The CalculateEstimate object for channel 1.

        ch2CalcEst -- The CalculateEstimate object for channel 0 [sic].

        JWV: This function is broken in the DLL in several ways. Most
        importantly, it does not actually return the objects. Do not
        use this function. Since this function is the only way to get
        these objects, it also precludes using Configure.
        """
        # Return VI_ERROR_NENABLED
        return -1073807313

    def SelectClock(self, slotNumber, channel, clockSrc, clockMHz):
        """Set the reference clock to the selected Clock type.

        slotNumber -- The number returned from Init identifying the slot.

        channel -- For this function, the only effect of this seems to
        be that no change is made if the new frequency to set to is
        similar enough (< 1Hz difference) to the frequency on this
        channel. Even though the frequency is applied to all channels
        per the documentation.

        clockSrc -- Use the CICW_RefClockSrc enumeration.

        clockMHz -- The frequency in MHz to set the Reference Clock
        to. Only applies to Ext channels. Floating point.

        The references for the two channels are not completely
        independent so this function sets the state of both channels
        at the same time. There is only one External reference SMA
        connector so this value applies to both channels.

        Return status.
        """
        # I'm assuming, and pretty sure I'm right, that enumeration
        # types are int's.
        status = self._dll.CICW_RevC_SelectClock(ctypes.c_ushort(slotNumber),
                                                 ctypes.c_ushort(channel),
                                                 ctypes.c_int(clockSrc),
                                                 ctypes.c_double(clockMHz))
        return status

    def GetClock(self, slotNumber, channel):
        """Return the current reference clock setting for the connected
        instrument.

        slotNumber -- The number returned from Init identifying the slot.

        channel -- Unused.

        Return (status, refClock). refClock is a value from the
        CICW_RefClockSrc enumeration.

        The reference clock sources are Internal, External (SMA), and
        PXI 10MHz.  The references for the two channels are not
        completely independent so this function reports the state of
        both channels at the same time.

        """
        refClock = ctypes.c_int()
        status = self._dll.CICW_RevC_GetClock(ctypes.c_ushort(slotNumber),
                                              ctypes.c_ushort(channel),
                                              ctypes.byref(refClock))
        return status, int(refClock.value)

    def GetClockMHz(self, slotNumber, channel):
        """Return the current Reference Clock Frequency setting for the
        connected instrument.

        slotNumber -- The number returned from Init identifying the slot.

        channel -- Undocumented

        Return (status, clockMHz). clockMHz is the current Reference
        Clock Frequency in MHz, regardless of source.

        The reference clock provides the basis for frequency accuracy.
        
        By tying all of your instruments to the same reference clock,
        even with the knowledge that its frequency is not perfect, all
        of the instruments will agree, to within the limits of their
        resoltion, on what a particular frequency is supposed to be.
        
        If the reference source is Internal clockMHz will be 50.
        
        If the reference source is PXI clockMHz will be 10.
        
        If the reference source is External clockMHz will be whatever
        it is programmed to.
        """
        clockMHz = ctypes.c_double()
        status = self._dll.CICW_RevC_GetClockMHz(ctypes.c_ushort(slotNumber),
                                                 ctypes.c_ushort(channel),
                                                 ctypes.byref(clockMHz))
        return status, float(clockMHz.value)

    def GetExtRefMHz(self, slotNumber, channel):
        """Return the External Reference Clock Frequency

        slotNumber -- The number returned from Init identifying the slot.

        channel -- Undocumented

        Return (status, clockMHz). clockMHz is the External Reference
        Clock Frequency in MHz.

        The reference clock provides the basis for frequency accuracy.
        
        By tying all of your instruments to the same reference clock,
        even with the knowledge that its frequency is not perfect, all
        of the instruments will agree, to within the limits of their
        resolution, on what a particular frequency is supposed to be.
        
        This is always the External reference, regardless of which
        reference is actually being used.
        
        Note there is only one External reference SMA connector so
        this value applies to both channels.
        """
        clockMHz = ctypes.c_double()
        status = self._dll.CICW_RevC_GetExtRefMHz(ctypes.c_ushort(slotNumber),
                                                ctypes.c_ushort(channel),
                                                ctypes.byref(clockMHz))
        return status, float(clockMHz.value)

    def GetRefDivider(self, slotNumber, channel):
        """Return the Reference Frequency divider.

        slotNumber -- The number returned from Init identifying the slot.

        channel -- Undocumented

        Return (status, refDivider). refDivier reduces the reference
        frequency applied to the PLL.

        Reads the Reference Divider.  Should always be 1 for the
        Internal or PXI clock sources.
        
        The optimal frequency for the PLL is 50MHz (lowest phase
        noise) and the maximum is 80MHz.
        """
        refDivider = ctypes.c_ulong()
        status = self._dll.CICW_RevC_GetRefDivider(ctypes.c_ushort(slotNumber),
                                                   ctypes.c_ushort(channel),
                                                   ctypes.byref(refDivider))
        return status, long(refDivider.value)

    def SetRefDivider(self, slotNumber, channel, refDivider):
        """Set the Reference Frequency divider.

        slotNumber -- The number returned from Init identifying the slot.

        channel -- Undocumented

        refDivider -- The reference divider reduces the reference
        frequency applied to the PLL.  1 to 16383.

        Return status

        Sets the Reference Divider.  Should generally be 1 for the
        Internal or PXI clock sources.
        
        The optimal frequency for the PLL is 50MHz (lowest phase
        noise) and the maximum is 80MHz.
        
        A value of one avoids reference phase ambiguity.  (On power
        up, or when the divide ratio changes to a non-1 value, it is
        possible for the divider phase to be randomized, affecting
        coherency between sources.)
        """
        status = self._dll.CICW_RevC_SetRefDivider(ctypes.c_ushort(slotNumber),
                                                   ctypes.c_ushort(channel),
                                                   ctypes.c_ulong(refDivider))
        return status

    def GetBoardIDString(self, slotNumber, channel):
        """Return the Board ID string

        slotNumber -- The number returned from Init identifying the slot.

        channel -- Unused

        Return (status, boardId) boardID is a string that has the
        following format: <card type><serial number>.

        > Example: "4062C000005" is a 4062 board with serial number
          C000005
        
        NOTE: This string is subject to change.  Call \link
        CICW_GetCardType \endlink, \link CICW_GetCardRev \endlink, or
        \link CICW_GetSerialNumber \endlink direcly instead of
        extracting them from this string in case the field lengths
        change.

        Serial number format changing from 32 bit integer --> 9 digits
        theoretical max to RBBSSSE format.  (BOM Rev (letter), Batch
        code (letters), Serial (3 numbers), ECN code (1 digit)) -->
        serial goes from intended 6 digits to 7 digits.  Also, VSG
        uses a 5 digit model number --> consistency across product
        lines is a good thing.
        """
        # In C-style this requires a maximum length of the string. The
        # documentation recommends at least 16, the source code
        # requires at least 12.
        length = 1024
        maxBoardIDLength = ctypes.c_uint(length)
        boardID = ctypes.create_string_buffer(length)
        status = self._dll.CICW_RevC_GetBoardIDString(ctypes.c_ushort(slotNumber),
                                                      ctypes.c_ushort(channel),
                                                      boardID,
                                                      maxBoardIDLength)
        return status, str(boardID.value)

    def GetCardType(self, slotNumber, channel):
        """Return a string representing the card type.

        slotNumber -- The number returned from Init identifying the slot.

        channel -- Unused

        Return (status, cardType). cardType is a string representing
        the model number.

        Currently returns 4062 or 4122 for a CI4062 or CI4122
        respectively.

        Note:  Future revs may have an alpha suffix.

        The VSG uses a 5 digit model.  May start putting a letter
        suffix after the numeric part.
        """
        length = 1024
        maxCardTypeLen = ctypes.c_uint(length)
        cardType = ctypes.create_string_buffer(length)
        status = self._dll.CICW_RevC_GetCardType(ctypes.c_ushort(slotNumber),
                                                 ctypes.c_ushort(channel),
                                                 cardType,
                                                 maxCardTypeLen)
        return status, str(cardType.value)

    def GetFirmwareRev(self, slotNumber, channel):
        """Return the Firmware Revision string.

        slotNumber -- The number returned from Init identifying the
        slot.

        channel -- Unused

        Return (status, fwRev). fwRev is the firmware revision as a
        string.

        NOTE: The firmware rev format is subject to change and may
        contain letters and multiple numbers in the future.

        Anticpated fimware rev changes: Firmware for rider boards -->
        another 32 bit int plus separator.  May also want to support
        branching.  For instance, a "D" to indicate Rev D specific.
        Encoding svnversion or build time is also possible.  10 digits
        handles 32 bit -1 plus terminating 0.
        """
        length = 1024
        maxFWRevLen = ctypes.c_uint(length)
        fwRev = ctypes.create_string_buffer(length)
        status = self._dll.CICW_RevC_GetFirmwareRev(ctypes.c_ushort(slotNumber),
                                                    ctypes.c_ushort(channel),
                                                    fwRev,
                                                    maxFWRevLen)
        return status, str(fwRev.value)

    def GetSerialNumber(self, slotNumber, channel):
        """Return the serial number as a long int.

        slotNumber -- The number returned from Init identifying the
        slot.

        channel -- Unused

        Return (status, serial). serial is the Serial Number as a
        long.

        JWV: The comments in this function indicate that the string
        format is alphanumeric. This obviously can't support
        that. It's unclear how useful this function is then.
        """
        serial = ctypes.u_long()
        status = self._dll.CICW_RevC_GetSerialNumber(ctypes.c_ushort(slotNumber),
                                                     ctypes.c_ushort(channel),
                                                     ctypes.byref(serial))
        return status, long(serial.value)

    def ResetCard(self, slotNumber):
        """Resets all settings on the instrument, including the frequency
        reference for both channels to internal.

        slotNumber -- The number returned from Init identifying the
        slot.

        Return status.

        This runs CICW_ResetChannel on both channels, and sets the
        reference oscillator to Internal for both channels.

        JWV: I'm dubious of the claims of this function to run
        CICW_ResetChannel on both channels, since the source code does
        not actually do that. In any event, ResetChannel is clearly
        broken, so that is a meaningless claim.
        """
        status = self._dll.CICW_RevC_ResetCard(ctypes.c_ushort(slotNumber))
        return status

    def ResetChannel(self, slotNumber, channel):
        """Reset all settings on the channel.  Does not affect the shared
        frequency reference.

        slotNumber -- The number returned from Init identifying the
        slot.

        channel -- Undocumented

        Return status

        Sets the frequency and power levels to their default states,
        and turns off the output. The reference oscillator is left
        alone however because that affects both channels. To also
        reset that to default, call CICW_ResetCard.

        JWV: This function is missing from the DLL. It is in the
        header, but there exists no code for it. Do not call this.
        """
        # Return VI_ERROR_NENABLED
        return -1073807313

    def GetTemperature(self, slotNumber, channel):
        """Return the current temperature of the board in Celsius

        slotNumber -- The number returned from Init identifying the
        slot.

        channel -- Unused

        Return (status, temp_C). temp_C is the floating point
        temperature of the board in Celsius.
        """
        temp_C = ctypes.c_double()
        status = self._dll.CICW_RevC_GetTemperature(ctypes.c_ushort(slotNumber),
                                                    ctypes.c_ushort(channel),
                                                    ctypes.byref(temp_C))
        return status

    def GetCardRev(self, slotNumber, channel):
        """Return the board revision letter (D, E, F, etc.)

        slotNumber -- The number returned from Init identifying the
        slot.

        channel -- Unused

        Return (status, cardRev). cardRev is a one-character string
        representing the hardware revision.

        This driver does not support Rev C or older hardware.
        """
        # Really we just need two characters, one for the rev and
        # another for the null
        length = 1024
        maxCardRevLen = ctypes.c_uint(length)
        cardRev = ctypes.create_string_buffer(length)
        status = self._dll.CICW_RevC_GetCardRev(ctypes.c_ushort(slotNumber),
                                                ctypes.c_ushort(channel),
                                                cardRev,
                                                maxCardRevLen)
        return status, str(cardRev.value)

    def SetFrequencyAttn(self, slotNumber, channel, freqMHz, pdac, gain):
        """Set frequency, pdac value, and gain.

        slotNumber -- The number returned from Init identifying the
        slot.

        channel -- Undocumented

        freqMHz -- The desired floating point output frequency in MHz

        pdac -- What to set the attenuator value to. Acceptable values
        are from 0 to 4095 (Default = 3000)

        gain -- What internal gain setting to use of the 833
        chip. Acceptable values are 0, 3, 6, and 9 (Default = 9)

        Return status
        """
        status = self._dll.CICW_RevC_SetFrequencyAttn(ctypes.c_ushort(slotNumber),
                                                      ctypes.c_ushort(channel),
                                                      ctypes.c_double(freqMHz),
                                                      ctypes.c_ushort(pdac),
                                                      ctypes.c_ushort(gain))
        return status

    def GetFDAC(self, slotNumber, channel, freqMHz):
        """Run the freq2FilterDac function and return the FDAC value based on frequency.

        slotNumber -- The number returned from Init identifying the slot.

        channel -- Undocumented

        freqMHz -- FDAC is specific to frequency, this returns the
        FDAC value based on the floating point input freq (in MHz)

        Return (status, fdac). fdac is the FDAC value, which is
        between 0 and 16383.
        """
        fdac = ctypes.c_ushort()
        status = self._dll.CICW_RevC_GetFDAC(ctypes.c_ushort(slotNumber),
                                             ctypes.c_ushort(channel),
                                             ctypes.c_double(freqMHz),
                                             ctypes.byref(fdac))
        return status, int(fdac.value)

    def GetPDAC(self, slotNumber, channel):
        """Return the Power fine attenuation DAC value.

        slotNumber -- The number returned from Init identifying the
        slot.

        channel -- Undocumented

        Return (status, pdac). pdac is the current PDAC value, which
        will be between 0 and 16383.
        """
        pdac = ctypes.c_ushort()
        status = self._dll.CICW_RevC_GetPDAC(ctypes.c_ushort(slotNumber),
                                             ctypes.c_ushort(channel),
                                             ctypes.byref(pdac))
        return status, int(pdac.value)
