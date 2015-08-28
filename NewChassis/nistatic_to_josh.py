'''
Created on Jul 20, 2012

@author: Boyan Tabakov

based on    http://www.scipy.org/Cookbook/Data_Acquisition_with_NIDAQmx
                http://stackoverflow.com/a/3788243
various ancillae for NI interfacing, mostly found in NIDAQmx.h
'''
import ctypes

class NiStatic(object):
    def __init__(self):
        self.nidll = ctypes.windll.nicaiu#the NI dll
        #type conversions
        self.int32 = ctypes.c_long
        self.uInt32 = ctypes.c_ulong
        self.uInt64 = ctypes.c_ulonglong
        self.float64 = ctypes.c_double
        self.TaskHandle = self.uInt32
        #constants
        self.DAQmx_Val_Volts = 10348
        self.DAQmx_Val_Rising = 10280
        self.DAQmx_Val_FiniteSamps = 10178
        self.DAQmx_Val_ContSamps = 10123
        self.DAQmx_Val_HWTimedSinglePoint  = 12522
        self.DAQmx_Val_GroupByChannel = 0
        self.DAQmx_Val_GroupByScanNumber = 1
        self.DAQmx_Val_HighFreq2Ctr = 10157
        self.DAQmx_Val_Hz = 10373
        self.DAQmx_Val_AllowRegen = 10097
        self.DAQmx_Val_DoNotAllowRegen = 10158
    #functions
    def tryTo(self, err):
        '''
        error checking
        '''
        if err < 0:
            buf_size = 256
            buf = ctypes.create_string_buffer('\000' * buf_size)
            self.nidll.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
            raise RuntimeError('nidaq call failed with error %d: %s' % (err, repr(buf.value)))
        if err > 0:
            buf_size = 256
            buf = ctypes.create_string_buffer('\000' * buf_size)
            self.nidll.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
            raise RuntimeError('nidaq generated warning %d: %s' % (err, repr(buf.value)))
