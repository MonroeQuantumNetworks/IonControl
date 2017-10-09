import ctypes
import numpy as np
import logging

class DmError(Exception):
    pass



class DeformableMirror():

    tldfm_dll = ctypes.WinDLL(r'C:\Program Files\IVI Foundation\VISA\Win64\Bin\TLDFM_64.dll')
    tldfmx_dll = ctypes.WinDLL(r'C:\Program Files\IVI Foundation\VISA\Win64\Bin\TLDFMX_64.dll')

    def __init__(self):  # deviceNum must be less than the total number of devices - 1 and can be 0
        logger = logging.getLogger(__name__)
        self.errmsg = ''
        self.instHdl = 0
        self.deviceNum = 0
        self.get_device_information()
        if self.deviceAvailable == 0:
            logger.warning('Device {0} is not available'.format(int(self.deviceNum + 1)))
        else:
            logger.info('Initializing device session with device {0}'.format(int(self.deviceNum + 1)))
            IDquery = ctypes.c_bool(1)
            resetDevice = ctypes.c_bool(False) # Sets voltages on all actuators to 100 V, giving a flat mirror
            instHdl = ctypes.c_int(0)
            try:
                err = self.tldfmx_dll.TLDFMX_init(self.rsrcName, IDquery, resetDevice, ctypes.byref(instHdl))
                # This is set up so that it is always an extended session, so we will always have access to the direct
                # Zernike polynomial control, and since all basic functions can still be used.
                self.instHdl = instHdl
                if err != 0:
                    msg = 'Problem initializing session with deformable mirror.'
                    self.error_exit(err, msg, True)
            except:
                raise
            else:
                try:
                    self.device_config()
                except:
                    raise
                else:
                    try:
                        self.get_extended_parameters()
                    except:
                        raise
                    else:
                        self.mirror_reset()

    def get_device_information(self):
        # Calls the TLDFM_get_device_information function, and decodes the results from the function
        # to make them usable in Python.

        manufacturer = ctypes.create_string_buffer(256)  # Manufacturer name initialization
        instName = ctypes.create_string_buffer(28)  # Instrument name initialization
        serialNum = ctypes.create_string_buffer(28)  # Serial Number initialization
        deviceAvailable = ctypes.c_bool(0)
        # Initialization for C-type Boolean that says whether the device is available
        rsrcName = ctypes.create_string_buffer(256)
        # Initialization for resource name to be used as an argument in the TLDFM_init function
        n = ctypes.c_int(0)
        try:
            err = (self.tldfm_dll.TLDFM_get_device_information(ctypes.c_long(0), n, ctypes.byref(manufacturer),
                                                          ctypes.byref(instName),ctypes.byref(serialNum),
                                                          ctypes.byref(deviceAvailable), ctypes.byref(rsrcName)))
            # Call TLDFM_get_device_information(Null, device index) and passing the manufacturer name, instrument name,
            # serial number, device availability and resource name by reference.
            if err != 0:  # Error will be 0 if TLDFM_get_device_information is successful
                msg = 'Problem getting deformable mirror device information'
                self.error_exit(err, msg, False)  # err != 0 => an error occurred, so exit program
        except:
            raise
        else:
            self.manufacturer = manufacturer
            self.instName = instName
            self.serialNum = serialNum
            self.deviceAvailable = deviceAvailable
            self.rsrcName = rsrcName

    def device_config(self):
        segNum = ctypes.c_int(1)
        minVolt = ctypes.c_double(0)
        maxVolt = ctypes.c_double(1)
        comVolt = ctypes.c_double(1)
        tiltNum = ctypes.c_uint32(1)
        minTiltVolt = ctypes.c_double(0)
        maxTiltVolt = ctypes.c_double(1)
        comTiltVolt = ctypes.c_double(1)
        try:
            err = (self.tldfm_dll.TLDFM_get_device_configuration(self.instHdl, ctypes.byref(segNum), ctypes.byref(minVolt),
                                                            ctypes.byref(maxVolt), ctypes.byref(comVolt),
                                                            ctypes.byref(tiltNum), ctypes.byref(minTiltVolt),
                                                            ctypes.byref(maxTiltVolt), ctypes.byref(comTiltVolt)))
            if err != 0:
                msg = 'Problem getting deformable mirror device configuration.'
                self.error_exit(err, msg, False)
        except:
            raise
        else:
            self.segNum = segNum
            self.minVolt = minVolt
            self.maxVolt = maxVolt
            self.tiltNum = tiltNum
            self.minTiltVolt = minTiltVolt
            self.maxTiltVolt = maxTiltVolt

    def get_extended_parameters(self):
        # Find parameters for extended session--number of Zernike polynomials, min/max amplitudes of Zernikes, and
        # steps to relax mirror
        minZAmp = ctypes.c_double(-1)
        maxZAmp = ctypes.c_double(1)
        maxZCount = ctypes.c_int(0)
        measSteps = ctypes.c_int(0)
        relaxSteps = ctypes.c_int(0)
        try:
            err = (self.tldfmx_dll.TLDFMX_get_parameters(self.instHdl, ctypes.byref(minZAmp), ctypes.byref(maxZAmp),
                                                    ctypes.byref(maxZCount),
                                                    ctypes.byref(measSteps), ctypes.byref(relaxSteps)))
            if err != 0:
                print('Problem getting deformable mirror extended parameters.')
                self.error_exit(err, True)
        except:
            raise
        else:
            self.minZAmp = minZAmp
            self.maxZAmp = maxZAmp
            self.maxZCount = maxZCount
            self.measSteps = measSteps
            self.relaxSteps = relaxSteps

    def relax_mirror(self):
        # "Relax" mirror--minimizes piezo drift. Loops through number of steps to relax determined by mirror

        mirror_rlx_init = ctypes.c_double * (int(self.segNum.value))
        rlx_array_py = np.zeros(int(self.segNum.value))
        rlx_array = mirror_rlx_init(*rlx_array_py)
        rlx_part = ctypes.c_uint(0)
        firstStep = ctypes.c_bool(1)
        reload = ctypes.c_bool(1)
        rem_steps = ctypes.c_int(0)
        try:
            err = (self.tldfmx_dll.TLDFMX_relax(self.instHdl, rlx_part, firstStep, reload, ctypes.byref(rlx_array),
                                                ctypes.c_int(0), ctypes.byref(rem_steps)))  # Calculate voltage pattern to relax mirror
            if err != 0:
                msg = 'Problem relaxing deformable mirror.'
                self.error_exit(err, msg, True)
        except:
            raise
        else:
            try:
                err = self.tldfm_dll.TLDFM_set_segment_voltages(self.instHdl, rlx_array)  # Apply voltage pattern
                if err != 0:
                    msg = 'Problem setting actuator voltages when relaxing deformable mirror.'
                    self.error_exit(err, msg, False)
            except:
                raise
            else:
                firstStep = ctypes.c_bool(0)
                while rem_steps.value > 0:  # Loop until no more steps remaining
                    try:
                        err = (self.tldfmx_dll.TLDFMX_relax(self.instHdl, rlx_part, firstStep, reload, ctypes.byref(rlx_array),
                                                       ctypes.c_int(0), ctypes.byref(rem_steps)))
                        if err != 0:
                            msg = 'Problem relaxing deformable mirror.'
                            self.error_exit(err, msg, True)
                    except:
                        raise
                    else:
                        try:
                            err = self.tldfm_dll.TLDFM_set_segment_voltages(self.instHdl, rlx_array)
                            if err != 0:
                                msg = 'Problem setting actuator voltages when relaxing deformable mirror.'
                                self.error_exit(err, msg, False)
                        except:
                            raise

    def relax_tilt(self):  # Relaxes tip/tilt arms of mirror similarl to relax_mirror
        tilt_rlx_init = ctypes.c_double * (int(self.tiltNum.value))
        rlx_array_py = np.zeros(int(self.tiltNum.value))
        rlx_array = tilt_rlx_init(*rlx_array_py)
        rlx_part = ctypes.c_uint(1)
        firstStep = ctypes.c_bool(1)
        reload = ctypes.c_bool(1)
        rem_steps = ctypes.c_int(0)
        try:
            err = (self.tldfmx_dll.TLDFMX_relax(self.instHdl, rlx_part, firstStep, reload, ctypes.c_int(0),
                                                ctypes.byref(rlx_array), ctypes.byref(rem_steps)))
            if err != 0:
                msg = 'Problem relaxing deformable mirror tip/tilt.'
                self.error_exit(err, msg, True)
        except:
            raise
        else:
            try:
                err = self.tldfm_dll.TLDFM_set_tilt_voltages(self.instHdl, rlx_array)
                if err != 0:
                    msg = 'Problem setting tip/tilt voltages while relaxing deformable mirror tip/tilt arms.'
                    self.error_exit(err, msg, False)
            except:
                raise
            else:
                firstStep = ctypes.c_bool(0)
                while rem_steps.value > 0:
                    try:
                        err = (self.tldfmx_dll.TLDFMX_relax(self.instHdl, rlx_part, firstStep, reload, ctypes.c_int(0),
                                                       ctypes.byref(rlx_array), ctypes.byref(rem_steps)))
                        if err != 0:
                            msg = 'Problem relaxing deformable mirror tip/tilt arms after first step.'
                            self.error_exit(err, msg, True)
                    except:
                        raise
                    else:
                        try:
                            err = self.tldfm_dll.TLDFM_set_tilt_voltages(self.instHdl, rlx_array)
                            if err != 0:
                                msg = 'Problem setting tip/tilt voltages while relaxing tip/tilt arms after first step.'
                                self.error_exit(err, msg, False)
                        except:
                            raise

    def calculate_single_zernike_pattern(self, zernike, amp):
        # Calculates voltages necessary to produce a paattern corresponding to one Zernike polynomial.
        # Zernike should be given as a string 'z (number of Zernike polynomial starting at 4)'. Order is: Ast45, Defocus,
        # Ast0, TreY, ComX, ComY, TreX, TetY, Secondary AstY, Spherical Aberration, Secondary AstX, TetX

        zernike_flags = {'z4': ctypes.c_uint(0x00000001), 'z5': ctypes.c_uint(0x00000002),
                         'z6': ctypes.c_uint(0x00000004), 'z7': ctypes.c_uint(0x00000008),
                         'z8': ctypes.c_uint(0x00000010), 'z9': ctypes.c_uint(0x00000020),
                         'z10': ctypes.c_uint(0x00000040), 'z11': ctypes.c_uint(0x00000080),
                         'z12': ctypes.c_uint(0x00000100), 'z13': ctypes.c_uint(0x00000200),
                         'z14': ctypes.c_uint(0x00000400), 'z15': ctypes.c_uint(0x00000800)}
        if self.minZAmp.value <= amp <= self.maxZAmp.value:
            zAmp = ctypes.c_double(amp)
            voltPattern_init = ctypes.c_double * (int(self.segNum.value))
            voltArray_init = np.zeros(int(self.segNum.value))
            voltPattern = voltPattern_init(*voltArray_init)
            try:
                err = self.tldfmx_dll.TLDFMX_calculate_single_zernike_pattern(self.instHdl, zernike_flags[zernike], zAmp,
                                                                         ctypes.byref(voltPattern))
                if err != 0:
                    msg = 'Problem calculating the voltage pattern for a single Zernike polynomial.'
                    self.error_exit(err, msg, True)
            except:
                raise
            else:
                return voltPattern
        else:
            print('Zernike amplitude out of range')

    def calculate_zernike_pattern(self, amp_array):
        # amp_array should be numpy array with the number of elements given by the maximum number of Zernike polynomials
        # to use (12)
        logger = logging.getLogger(__name__)
        if np.amin(amp_array) >= self.minZAmp.value and np.amax(amp_array) <= self.maxZAmp.value:
            zAmp_array_init = ctypes.c_double * 12
            zAmp_array = zAmp_array_init(*amp_array)
            voltPattern_init = ctypes.c_double * (int(self.segNum.value))
            voltArray_init = np.zeros(int(self.segNum.value))
            voltPattern = voltPattern_init(*voltArray_init)
            try:
                err = (self.tldfmx_dll.TLDFMX_calculate_zernike_pattern(self.instHdl, ctypes.c_uint(0xFFFFFFFF), zAmp_array,
                                                                   ctypes.byref(voltPattern)))
                if err != 0:
                    msg = 'Problem calculating voltage patterns for all Zernike polynomials.'
                    self.error_exit(err, msg, True)
            except:
                return voltPattern
        else:
            logger.warning('At least one Zernike amplitude out of range.')

    def single_segment_setpoint(self, segment, voltage, change_voltage):
        # Sets setpoint voltage of one segment, after which Zernike polynomial patterns can be calculated with that voltage
        # set. Only actually changes voltage if set_voltage = True.
        logger = logging.getLogger(__name__)
        if segment < self.segNum.value and voltage >= self.minVolt.value and voltage <= self.maxVolt.value:
            seg_idx = ctypes.c_int(segment)
            voltage_c = ctypes.c_double(voltage)
            try:
                err = self.tldfmx_dll.TLDFMX_set_single_voltage_setpoint(self.instHdl, seg_idx, voltage_c)
                if err != 0:
                    msg = 'Problem setting voltage setpoint.'
                    self.error_exit(err, msg, True)
            except:
                raise
            else:
                if change_voltage:
                    try:
                        self.set_segment_voltage(segment, voltage)
                    except:
                        raise

        else:
            logger.warning('Either segment index or voltage out of range.')

    def all_segment_setpoints(self, voltArray, change_voltages):
        # Sets setpoint voltage for all segments. Only changes voltages if set_voltages = True.
        logger = logging.getLogger(__name__)
        if np.amax(voltArray) <= self.maxVolt.value and np.amin(voltArray) >= self.minVolt.value:
            c_array = ctypes.c_double * (int(self.segNum.value))
            voltages = c_array(*voltArray)
            try:
                err = self.tldfmx_dll.TLDFMX_set_voltages_setpoints(self.instHdl, voltages)
                if err != 0:
                    msg = 'Problem setting all voltage setpoints.'
                    self.error_exit(err, msg, True)
            except:
                raise
            else:
                if change_voltages:
                    try:
                        self.set_all_voltages(voltArray)
                    except:
                        raise
        else:
            logger.info('At least one voltage out of range.')

    def get_segment_voltage(self, seg_idx):
        logger = logging.getLogger(__name__)
        if seg_idx < int(self.segNum.value):
            seg_idx = ctypes.c_int(seg_idx)
            segVolt = ctypes.c_double(0)
            try:
                err = self.tldfm_dll.TLDFM_get_segment_voltage(self.instHdl, seg_idx, ctypes.byref(segVolt))
                if err != 0:
                    msg = 'Problem getting segment voltage.'
                    self.error_exit(err, msg, False)
            except:
                raise
            else:
                self.segment_voltage = segVolt
        else:
            logger.warning('Segment index out of range.')

    def get_all_voltages(self):
        init_list = np.ones(int(self.segNum.value))
        c_array = ctypes.c_double * init_list.shape[0]
        voltages = c_array(*init_list)
        try:
            err = self.tldfm_dll.TLDFM_get_segment_voltages(self.instHdl, ctypes.byref(voltages))
            if err != 0:
                msg = 'Problem getting actuator voltages.'
                self.error_exit(err, msg, False)
        except:
            raise
        else:
            self.segment_voltages_set = voltages

    def get_tilt_voltage(self, tilt_idx):
        logger = logging.getLogger(__name__)
        if tilt_idx < int(self.tiltNum.value):
            tilt_idx = ctypes.c_int(tilt_idx)
            tiltVolt = ctypes.c_double(0)
            try:
                err = self.tldfm_dll.TLDFM_get_tilt_voltage(self.instHdl, tilt_idx, ctypes.byref(tiltVolt))
                if err != 0:
                    msg = 'Problem getting tilt voltage.'
                    self.error_exit(err, msg, False)
            except:
                raise
            else:
                self.tiptilt_volt = tiltVolt
        else:
            logger.warning('Tilt segment index out of range.')

    def get_tilt_voltages(self):
        c_voltArray = ctypes.c_double * 3
        voltArray = c_voltArray(0, 0, 0)
        try:
            err = self.tldfm_dll.TLDFM_get_tilt_voltages(self.instHdl, ctypes.byref(voltArray))
            if err != 0:
                msg = 'Problem getting all tilt arm voltages.'
                self.error_exit(err, msg, False)
        except:
            raise
        else:
            self.tilt_voltages_set = voltArray

    def set_segment_voltage(self, seg_idx, volt):
        logger = logging.getLogger(__name__)
        volt_min = self.minVolt.value
        volt_max = self.maxVolt.value
        if seg_idx < int(self.segNum.value):
            if volt >= volt_min and volt <= volt_max:
                seg_idx = ctypes.c_int(seg_idx)
                seg_volt = ctypes.c_double(volt)
                try:
                    err = self.tldfm_dll.TLDFM_set_segment_voltage(self.instHdl, seg_idx, seg_volt)
                    if err != 0:
                        msg = 'Problem setting voltage on single actuator.'
                        self.error_exit(err, msg, False)
                except:
                    raise
            else:
                logger.warning('Voltage out of range.')
        else:
            logger.warning('Segment index out of range.')


    def set_all_voltages(self, voltList):
        # voltList must be a numpy array with length equal to the number of segments
        logger = logging.getLogger(__name__)
        if np.amax(voltList) <= self.maxVolt.value and np.amin(voltList) >= self.minVolt.value:
            c_array = ctypes.c_couble * int(self.segNum.value)
            setVoltages = c_array(*voltList)
            try:
                err = self.tldfm_dll.TLDFM_set_segment_voltages(self.instHdl, setVoltages)
                if err != 0:
                    msg = 'Problem setting voltage on all actuators.'
                    self.error_exit(err, msg, False)
            except:
                raise
        else:
            logger.warning('At least one voltage out of range.')

    def set_tilt_voltage(self, tilt_idx, volt):
        logger = logging.getLogger(__name__)
        if tilt_idx < int(self.tiltNum.value):
            tilt_idx = ctypes.c_int(tilt_idx)
            if volt >= self.minTiltVolt.value and volt <= self.maxTiltVolt.value:
                voltage = ctypes.c_double(volt)
                try:
                    err = self.tldfm_dll.TLDFM_set_tilt_voltage(self.instHdl, tilt_idx, voltage)
                    if err != 0:
                        msg = 'Problem setting tilt voltage on single arm.'
                        self.error_exit(err, msg, False)
                except:
                    raise
            else:
                logger.warning('Tilt voltage out of range.')
        else:
            logger.warning('Tilt segment index out of range.')

    def set_tilt_voltages(self, voltList):  # voltList should be numpy array with tiltNum elements
        logger = logging.getLogger(__name__)
        if self.minTiltVolt.value <= np.amin(voltList) <= self.maxTiltVolt.value:
            c_voltArray = ctypes.c_double * (self.tiltNum.value)
            voltArray = c_voltArray(*voltList)
            try:
                err = self.tldfm_dll.TLDFM_set_tilt_voltages(self.instHdl, voltArray)
                if err != 0:
                    msg = 'Problem setting tilt voltages on all arms.'
                    self.error_exit(err, msg, False)
            except:
                raise
        else:
            logger.warning('At least one tilt voltage out of range.')

    def set_tilt_amplitude_angle(self, amplitude, angle):
        logger = logging.getLogger(__name__)
        if 0.0 <= amplitude <= 1.0 and -180.0 <= angle <= 180.0:
            amplitude = ctypes.c_double(amplitude)
            angle = ctypes.c_double(angle)
            try:
                err = self.tldfm_dll.TLDFM_set_tilt_amplitude_angle(self.instHdl, amplitude, angle)
                if err != 0:
                    msg = 'Problem setting tip/tilt amplitude and angle.'
                    self.error_exit(err, msg, False)
            except:
                raise
        elif (0.0 <= amplitude <= 1.0) and -180.0 <= angle <= 180.0:
            logger.warning('Tilt amplitude out of range.')
        else:
            logger.warning('Tilt angle out of range.')

    def set_mirror_shape(self, zernikes, amp):
        # Calculates voltage pattern needed to put (a) certain Zernike polynomial(s) on mirror, and then applies that voltage.
        # Zernikes is an array of which Zernikes (by number only) to set voltages for. Amp is an array of the amplitudes
        # for each Zernike.
        try:
            if type(zernikes) is str:  # If only one zernike to fit
                voltPattern = self.calculate_single_zernike_pattern(zernikes, amp)
            else:
                amp_array = np.zeros(12)
                for i in range(4, 16):
                    if i in zernikes:
                        idx = np.where(zernikes == i)[0][0]
                        amp_array[i - 4] = amp[idx]
                voltPattern = self.calculate_zernike_pattern(amp_array)
            err = self.tldfm_dll.TLDFM_set_segment_voltages(self.instHdl, voltPattern)
            if err != 0:
                msg = 'Problem setting segment voltages while attempting to set Zernike pattern.'
                self.error_exit(err, msg, False)
        except:
            raise

    def hysteresis_compensation_status(self, target):  # Target is 0 for mirror or 1 for tilt
        logger = logging.getLogger(__name__)
        if target == 0 or target == 1:
            target = ctypes.c_uint(target)
            hyst_state = ctypes.c_bool(1)
            try:
                err = self.tldfm_dll.TLDFM_enabled_hysteresis_compensation(self.instHdl, target, ctypes.byref(hyst_state))
                if err != 0:
                    msg = 'Problem checking hysteresis compensation status.'
                    self.error_exit(err, msg, False)
            except:
                raise
            else:
                if target == 0:
                    self.mirr_hyst_state = hyst_state
                else:
                    self.tilt_hyst_state = hyst_state
        else:
            logger.warning('Invalid target for checking hysteresis compensation status.')

    def enable_hysteresis_compensation(self, target, on_or_off):
        # Target is 0 for mirror, 1 for tilt, 2 for both. on_or_off is a Boolean--True for on, False for off
        try:
            if target == 0 or target == 1:
                target = ctypes.c_uint(target)
                on_or_off = ctypes.c_bool(on_or_off)
                err = self.tldfm_dll.TLDFM_enable_hysteresis_compensation(self.instHdl, target, on_or_off)
                if err != 0:
                    msg = 'Problem setting hysteresis compensation status.'
                    self.error_exit(err, msg, False)
            else:
                self.hysteresis_compensation_status(0)
                self.hysteresis_compensation_status(1)
                if on_or_off == self.mirr_hyst_state.value and on_or_off == self.tilt_hyst_state.value:
                    if on_or_off:
                        print('Hysteresis compensation is already enabled for both the mirror and tilt.')
                    else:
                        print('Hysteresis compensation is already disabled for both the mirror and tilt.')
                elif on_or_off == self.mirr_hyst_state.value and on_or_off != self.tilt_hyst_state.value:
                    err = (self.tldfm_dll.TLDFM_enable_hysteresis_compensation(self.instHdl, ctypes.c_uint(1),
                                                                          ctypes.c_bool(on_or_off)))
                    if err != 0:
                        msg = 'Problem setting hysteresis compensation status.'
                        self.error_exit(err, msg, False)
                elif on_or_off != self.mirr_hyst_state.value and on_or_off == self.tilt_hyst_state.value:
                    err = (self.tldfm_dll.TLDFM_enable_hysteresis_compensation(self.instHdl, ctypes.c_uint(0),
                                                                          ctypes.c_bool(on_or_off)))
                    if err != 0:
                        msg = 'Problem setting hysteresis compensation status.'
                        self.error_exit(err, msg, False)
                else:
                    err = (self.tldfm_dll.TLDFM_enable_hysteresis_compensation(self.instHdl, ctypes.c_uint(target),
                                                                          ctypes.c_bool(on_or_off)))
                    if err != 0:
                        msg = 'Problem setting hysteresis compensation status.'
                        self.error_exit(err, msg, False)
        except:
            raise

    def measured_segment_voltage(self, seg_idx):
        logger = logging.getLogger(__name__)
        if seg_idx < self.segNum.value:
            seg_idx = ctypes.c_uint(seg_idx)
            volt = ctypes.c_double(0)
            try:
                err = self.tldfm_dll.TLDFM_get_measured_segment_voltage(self.instHdl, seg_idx, ctypes.byref(volt))
                if err != 0:
                    msg = 'Problem measuring single actuator voltage.'
                    self.error_exit(err, msg, False)
            except:
                raise
            else:
                self.meas_segVolt = volt.value
        else:
            logger.warning('Segment index is out of range.')

    def measured_segment_voltages(self):
        init_list = np.zeros(int(self.segNum.value))
        seg_meas_volt = ctypes.c_double * (init_list.shape[0])
        meas_volts = seg_meas_volt(*init_list)
        try:
            err = self.tldfm_dll.TLDFM_get_measured_segment_voltages(self.instHdl, ctypes.byref(meas_volts))
            if err != 0:
                msg = 'Problem measuring actuator voltages.'
                self.error_exit(err, msg, False)
        except:
            raise
        else:
            self.segment_voltages_meas = np.array(meas_volts)

    def measured_tilt_voltage(self, tilt_idx):
        logger = logging.getLogger(__name__)
        if tilt_idx < self.tiltNum.value:
            tilt_idx = ctypes.c_uint(tilt_idx)
            tiltVolt = ctypes.c_double(0)
            try:
                err = self.tldfm_dll.TLDFM_get_measured_tilt_voltage(self.instHdl, tilt_idx, ctypes.byref(tiltVolt))
                if err != 0:
                    msg = 'Problem measuring tilt voltage.'
                    self.error_exit(err, msg, False)
            except:
                raise
            else:
                self.meas_tiptilt_volt = tiltVolt.value
        else:
            logger.warning('Tilt segment index is out of range')

    def measured_tilt_voltages(self):
        init_list = np.zeros(int(self.tiltNum.value))
        c_meas_tilt_array = ctypes.c_double * (self.tiltNum.value)
        meas_tilt_array = c_meas_tilt_array(*init_list)
        try:
            err = self.tldfm_dll.TLDFM_get_measured_tilt_voltages(self.instHdl, ctypes.byref(meas_tilt_array))
            if err != 0:
                msg = 'Problem measuring tilt voltages.'
                self.error_exit(err, msg, False)
        except:
            raise
        else:
            self.tilt_voltages_meas = np.array(meas_tilt_array)

    def mirror_temps(self):
        ic1_temp = ctypes.c_double(1)
        ic2_temp = ctypes.c_double(1)
        mirror_temp = ctypes.c_double(1)
        elec_temp = ctypes.c_double(1)
        try:
            err = (self.tldfm_dll.TLDFM_get_temperatures(self.instHdl, ctypes.byref(ic1_temp), ctypes.byref(ic2_temp),
                                                    ctypes.byref(mirror_temp), ctypes.byref(elec_temp)))
            if err != 0:
                msg = 'Problem measuring mirror temperature.'
                self.error_exit(err, msg, False)
        except:
            raise
        else:
            self.ic1_temp = ic1_temp.value
            self.ic2_temp = ic2_temp.value
            self.mirror_temp = mirror_temp.value
            self.electronics_temp = elec_temp.value

    def mirror_reset(self):
        logger = logging.getLogger(__name__)
        try:
            err = self.tldfm_dll.TLDFM_reset(self.instHdl)
            if err != 0:
                msg = 'Problem resetting mirror.'
                self.error_exit(err, msg, False)
        except:
            raise
        else:
            logger.info('Deformable mirror was reset.')

    def end_session(self):
        logger = logging.getLogger(__name__)
        err = self.tldfmx_dll.TLDFMX_close(self.instHdl)
        if err != 0:
            msg = 'Problem ending deformable mirror session.'
            self.error_exit(err, msg, True)
        else:
            logger.info('Extended communication with mirror {0} successfully closed'.format(int((self.instHdl).value)))

    def error_exit(self, err, msg, extended):
        logger = logging.getLogger(__name__)
        buf = ctypes.create_string_buffer(512)
        if extended:
            err_errmsg = self.tldfmx_dll.TLDFMX_error_message(self.instHdl, err, ctypes.byref(buf))
        else:
            err_errmsg = self.tldfm_dll.TLDFM_error_message(self.instHdl, err, ctypes.byref(buf))

        if err_errmsg != 0:
            msg2 = msg + ' No error message from DLL available.'
        else:
            msg2 = msg + str(buf)
        try:
            err = self.tldfmx_dll.TLDFMX_close(self.instHdl)
            if err != 0:
                close_msg = 'DM session could not be closed.'
                self.errmsg = msg2 + close_msg
                raise DmError
        except:
            raise
        else:
            try:
                self.errmsg = msg2
                raise DmError
            except:
                raise

        #if self.instHdl != None and self.instHdl != 0:
        #    try:
        #        err = self.tldfmx_dll.TLDFMX_close(self.instHdl)
        #        if err != 0:
        #            raise Exception('Problem ending mirror session after error')
        #    except:
        #        pass
        #print('Exiting program.')

