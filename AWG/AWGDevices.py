'''
Created on Jul 2, 2015

@author: Geoffrey Ji

AWG Devices are defined here. If a new AWG needs to be added,
it must inherit AWGDeviceBase and implement:

- __init__
   to initialize whatever libraries it needs

- open, program, trigger, and close
   to interface with the AWG

- deviceProperties
   To specify fixed properties of the AWG device. Required keys:

   - sampleRate (magnitude)
      rate at which the samples programmed are output by the AWG (e.g. mg(1, 'GHz'))

    - minSamples (int)
       minimum number of samples to program

    - maxSamples (int)
       maximum number of samples to program

    - sampleChunkSize (int)
       number of samples must be a multiple of sampleChunkSize

    - padValue (int)
       the waveform will be padded with this number to make it a multiple of sampleChunkSize, or to make it the length of minSamples

    - minAmplitude (int)
       minimum amplitude value (raw)

    - maxAmplitude (int)
       maximum amplitude value (raw)

    - numChannels (int)
       Number of channels

- paramDef
   To define dynamic properties and actions of the AWG, which are shown in the GUI and can be modified in the program.
'''

import inspect
import logging
import sys
from ctypes import *

from PyQt4 import QtCore
from pyqtgraph.parametertree.Parameter import Parameter

from ProjectConfig.Project import getProject
from modules.magnitude import mg, new_mag


class AWGDeviceBase(object):
    """base class for AWG Devices"""
    def __init__(self, settings, globalDict):
        self.open()
        self.settings = settings
        self.globalDict = globalDict
        for channel in range(self.deviceProperties['numChannels']):
            if channel >= len(self.settings.channelSettingsList): #create new channels if it's necessary
                self.settings.channelSettingsList.append({'equation' : 'A*sin(w*t+phi) + offset',
                                                          'plotEnabled' : True})
        self.project = getProject()
        sample = 1/self.deviceProperties['sampleRate']
        new_mag('sample', sample)
        new_mag('samples', sample)

    def paramDef(self):
        """return the parameter definition used by pyqtgraph parametertree to show the gui"""
        self.settings.deviceSettings.setdefault('programOnScanStart', False)
        return [
            {'name': 'Program on scan start', 'type': 'bool', 'value': self.settings.deviceSettings['programOnScanStart'], 'tip': "", 'key': 'programOnScanStart'},
            {'name': 'Program now', 'type': 'action', 'key':'program'},
            {'name': 'Trigger now', 'type': 'action', 'key':'trigger'}
        ]

    def parameter(self):
        # re-create the parameters each time to prevent a exception that says the signal is not connected
        self._parameter = Parameter.create(name='Programming Options', type='group', children=self.paramDef())
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        return self._parameter

    def update(self, param, changes):
        """update the parameter, called by the signal of pyqtgraph parametertree"""
        for param, change, data in changes:
            if change=='value':
                self.settings.deviceSettings[param.opts['key']] = data
                self.settings.saveIfNecessary()
            elif change=='activated':
                getattr( self, param.opts['key'] )()

    #functions and attributes that must be defined by inheritors
    def open(self): raise NotImplementedError("'open' method must be implemented by specific AWG device class")
    def program(self): raise NotImplementedError("'program' method must be implemented by specific AWG device class")
    def trigger(self): raise NotImplementedError("'trigger' method must be implemented by specific AWG device class")
    def close(self): raise NotImplementedError("'close' method must be implemented by specific AWG device class")
    @property
    def deviceProperties(self): raise NotImplementedError("'deviceProperties' must be set by specific AWG device class")
    @property
    def displayName(self): raise NotImplementedError("'displayName' must be set by specific AWG device class")

class ChaseDA12000(AWGDeviceBase):
    """Class for programming a ChaseDA12000 AWG"""
    displayName = "Chase DA12000 AWG"
    deviceProperties = dict(
        sampleRate = mg(1, 'GHz'), #rate at which the samples programmed are output by the AWG
        minSamples = 128, #minimum number of samples to program
        maxSamples = 4000000, #maximum number of samples to program
        sampleChunkSize = 64, #number of samples must be a multiple of sampleCnunkSize
        padValue = 2047, #the waveform will be padded with this number to make it a multiple of sampleChunkSize, or to make it the length of minSamples
        minAmplitude = 0, #minimum amplitude value (raw)
        maxAmplitude = 4095, #maximum amplitude value (raw)
        numChannels = 1 #Number of channels
    )

    class SEGMENT(Structure):
        _fields_ = [("SegmentNum", c_ulong),
                    ("SegmentPtr", POINTER(c_ulong)),
                    ("NumPoints", c_ulong),
                    ("NumLoops", c_ulong),
                    ("BeginPadVal ", c_ulong), # Not used
                    ("EndingPadVal", c_ulong), # Not used
                    ("TrigEn", c_ulong),
                    ("NextSegNum", c_ulong)]

    def __init__(self, settings, globalDict):
        super(ChaseDA12000, self).__init__(settings, globalDict)
        if not self.project.isEnabled('hardware', self.displayName):
            self.enabled = False
        else:
            dllName = self.project.hardware[self.displayName]['DLL']
            try:
                self.lib = WinDLL(dllName)
                self.enabled = True
            except Exception:
                logging.getLogger(__name__).info("{0} unavailable. Unable to open {1}.".format(self.displayName, dllName))
                self.enabled = False

    def paramDef(self):
        """return the parameter definition used by pyqtgraph parametertree to show the gui"""
        self.settings.deviceSettings.setdefault('continuous', False)
        paramList = [
            {'name': 'Run continuously', 'type': 'bool', 'value': self.settings.deviceSettings['continuous'], 'tip': "Restart sequence at sequence end, continuously (no trigger)", 'key': 'continuous'}
        ]
        paramList.extend( super(ChaseDA12000, self).paramDef() )
        return paramList

    def open(self):
        logger = logging.getLogger(__name__)
        try:
            self.lib.da12000_Open(1)
            self.enabled = True
        except Exception:
            logger.info("Unable to open {0}.".format(self.displayName))
            self.enabled = False
    
    def program(self):
        logger = logging.getLogger(__name__)
        if self.enabled:
            pts = self.settings.channelSettingsList[0]['waveform'].evaluate()
            logger.info("writing " + str(len(pts)) + " points to AWG")
            seg_pts = (c_ulong * len(pts))(*pts)
            seg0 = self.SEGMENT(0, seg_pts, len(pts), 0, 2048, 2048, 1, 0)
            seg = (self.SEGMENT*1)(seg0)

            self.lib.da12000_CreateSegments(1, 1, 1, seg)
            self.lib.da12000_SetTriggerMode(1, 1 if self.settings.deviceSettings['continuous'] else 2, 0)
        else:
            logger.warning("{0} unavailable. Unable to program.".format(self.displayName))

    def trigger(self):
        if self.enabled:
            self.lib.da12000_SetSoftTrigger(1)

    def close(self):
        if self.enabled:
            self.lib.da12000_Close(1)


class DummyAWG(AWGDeviceBase):
    displayName = "Dummy AWG"
    deviceProperties = dict(
        sampleRate = mg(1, 'GHz'), #rate at which the samples programmed are output by the AWG
        minSamples = 128, #minimum number of samples to program
        maxSamples = 4000000, #maximum number of samples to program
        sampleChunkSize = 64, #number of samples must be a multiple of sampleCnunkSize
        padValue = 2047, #the waveform will be padded with this number ot make it a multiple of sampleChunkSize, or to make it the length of minSamples
        minAmplitude = 0, #minimum amplitude value (raw)
        maxAmplitude = 4095, #maximum amplitude value (raw)
        numChannels = 2  #Number of channels
    )
    
    def open(self): pass
    def close(self): pass
    def program(self): pass
    def trigger(self): pass

def isAWGDevice(obj):
    """Determine if obj is an AWG device.
    returns True if obj inherits from AWGDeviceBase, but is not itself AWGDeviceBase"""
    try:
        inheritance = inspect.getmro(obj)
        return True if AWGDeviceBase in inheritance and AWGDeviceBase!=inheritance[0] else False
    except:
        return False

#Extract the AWG device classes
current_module = sys.modules[__name__]
AWGDeviceClasses = inspect.getmembers(current_module, isAWGDevice)
AWGDeviceDict = {cls.displayName:clsName for clsName, cls in AWGDeviceClasses}
