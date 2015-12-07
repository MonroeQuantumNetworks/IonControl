'''
Created on Jul 2, 2015

@author: Geoffrey Ji

AWG Devices are defined here. If a new AWG needs to be added,
it must inherit AWGDeviceBase and implement:

- __init__
   to initialize whatever libraries it needs

- open, program, trigger, and close
   to interface with the AWG

- devicePropertiesDict
   To specify fixed properties of the AWG device (e.g. sampleRate, maxSamples, etc.) see existing AWGs for examples

- paramDef
   To define dynamic properties and actions of the AWG, which are shown in the GUI and can be modified in the program.
'''

from ctypes import *
import logging
from modules.magnitude import mg, Magnitude, new_mag
from ProjectConfig.Project import getProject
from AWG.AWGWaveform import AWGWaveform
from pyqtgraph.parametertree.Parameter import Parameter
from PyQt4 import QtCore
from functools import partial
from AWG.VarAsOutputChannel import VarAsOutputChannel


class AWGDeviceBase(object):
    """base class for AWG Devices"""
    def __init__(self, settings, globalDict, awgUi):
        self.open()
        self.awgUi = awgUi
        self.enabled = False
        self.settings = settings
        self.globalDict = globalDict
        if not self.settings.waveform:
            self.settings.waveform = AWGWaveform('A*sin(w*t+phi) + offset', self.devicePropertiesDict)
        self.settings.waveform.devicePropertiesDict = self.devicePropertiesDict #make sure these match
        self.project = getProject()
        sample = 1/self.devicePropertiesDict['sampleRate']
        new_mag('sample', sample)
        new_mag('samples', sample)
        self._varAsOutputChannelDict = dict()

    @property
    def varAsOutputChannelDict(self):
        for name in self.settings.waveform.varDict:
            if name not in self._varAsOutputChannelDict:
                self._varAsOutputChannelDict[name] = VarAsOutputChannel(self.awgUi, name, self.globalDict)
        return self._varAsOutputChannelDict

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
                self.awgUi.saveIfNecessary()
            elif change=='activated':
                getattr( self, param.opts['key'] )()

    #functions and attributes that must be defined by inheritors
    def open(self): raise NotImplementedError("'open' method must be implemented by specific AWG device class")
    def program(self): raise NotImplementedError("'program' method must be implemented by specific AWG device class")
    def trigger(self): raise NotImplementedError("'trigger' method must be implemented by specific AWG device class")
    def close(self): raise NotImplementedError("'close' method must be implemented by specific AWG device class")
    @property
    def devicePropertiesDict(self): raise NotImplementedError("'devicePropertiesDict' must be set by specific AWG device class")
    @property
    def displayName(self): raise NotImplementedError("'displayName' must be set by specific AWG device class")

class ChaseDA12000(AWGDeviceBase):
    """Class for programming a ChaseDA12000 AWG"""
    displayName = "Chase DA12000 AWG"
    devicePropertiesDict = dict(
        sampleRate = mg(1, 'GHz'), #rate at which the samples programmed are output by the AWG
        minSamples = 128, #minimum number of samples to program
        maxSamples = 4000000, #maximum number of samples to program
        sampleChunkSize = 64, #number of samples must be a multiple of sampleCnunkSize
        padValue = 2047, #the waveform will be padded with this number ot make it a multiple of sampleChunkSize, or to make it the length of minSamples
        minAmplitude = 0, #minimum amplitude value (raw)
        maxAmplitude = 4095 #maximum amplitude value (raw)
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

    def __init__(self, settings, awgUi=None):
        super(ChaseDA12000, self).__init__(settings, awgUi)
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
            pts = self.settings.waveform.evaluate()
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
    devicePropertiesDict = dict(
        sampleRate = mg(1, 'GHz'), #rate at which the samples programmed are output by the AWG
        minSamples = 128, #minimum number of samples to program
        maxSamples = 4000000, #maximum number of samples to program
        sampleChunkSize = 64, #number of samples must be a multiple of sampleCnunkSize
        padValue = 2047, #the waveform will be padded with this number ot make it a multiple of sampleChunkSize, or to make it the length of minSamples
        minAmplitude = 0, #minimum amplitude value (raw)
        maxAmplitude = 4095 #maximum amplitude value (raw)
    )
    
    def open(self): pass
    def close(self): pass
    def program(self): pass
    def trigger(self): pass


AWGDeviceDict = {
    ChaseDA12000.displayName : ChaseDA12000.__name__,
    DummyAWG.displayName : DummyAWG.__name__
}