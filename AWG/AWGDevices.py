'''
Created on Jul 2, 2015

@author: Geoffrey Ji

AWG Devices are defined here. If a new AWG needs to be added, 
it must inherit AWGDeviceBase and implement open, program, and close.
'''

from ctypes import *
import logging
from modules.magnitude import mg, Magnitude, new_mag
from ProjectConfig.Project import getProject
from AWG.AWGWaveform import AWGWaveform
from pyqtgraph.parametertree.Parameter import Parameter
from PyQt4 import QtCore
from functools import partial

class AWGDeviceBase(object):
    """base class for AWG Devices"""
    # parent should be the AWGUi, which we read whether or not to modify the internal scan as well
    def __init__(self, settings, parent=None):
        self.open()
        self.parent = parent
        self.enabled = False
        self.settings = settings
        if not self.settings.waveform:
            self.settings.waveform = AWGWaveform('A*sin(w*t+phi) + offset', self.sampleRate, self.maxSamples, self.maxAmplitude)
        self.settings.waveform.sampleRate = self.sampleRate
        self.settings.waveform.maxSamples = self.maxSamples
        self.settings.waveform.maxAmplitude = self.maxAmplitude
        self.project = getProject()
        new_mag('sample', 1/self.sampleRate)
        new_mag('samples', 1/self.sampleRate)

    def scanParam(self):
        return self.parent.settings.setScanParam, str(self.parent.settings.scanParam)

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
                self.parent.saveIfNecessary()
            elif change=='activated':
                getattr( self, param.opts['key'] )()


    #functions and attributes that must be defined by inheritors
    def open(self): raise NotImplementedError("'open' method must be implemented by specific AWG device class")
    def program(self, continuous): raise NotImplementedError("'program' method must be implemented by specific AWG device class")
    def trigger(self): raise NotImplementedError("'trigger' method must be implemented by specific AWG device class")
    def close(self): raise NotImplementedError("'close' method must be implemented by specific AWG device class")
    @property
    def displayName(self): raise NotImplementedError("'displayName' field must be defined by specific AWG device class")
    @property
    def sampleRate(self): raise NotImplementedError("'sampleRate' field must be defined by specific AWG device class")
    @property
    def maxSamples(self): raise NotImplementedError("'maxSamples' field must be defined by specific AWG device class")
    @property
    def maxAmplitude(self): raise NotImplementedError("'maxAmplitude' field must be defined by specific AWG device class")


class ChaseDA12000(AWGDeviceBase):
    """Class for programming a ChaseDA12000 AWG"""
    displayName = "Chase DA12000 AWG"
    sampleRate = mg(1, 'GHz')
    maxSamples = 4000000
    maxAmplitude = 4095

    class SEGMENT(Structure):
        _fields_ = [("SegmentNum", c_ulong),
                    ("SegmentPtr", POINTER(c_ulong)),
                    ("NumPoints", c_ulong),
                    ("NumLoops", c_ulong),
                    ("BeginPadVal ", c_ulong), # Not used
                    ("EndingPadVal", c_ulong), # Not used
                    ("TrigEn", c_ulong),
                    ("NextSegNum", c_ulong)]

    def __init__(self, settings, parent=None):
        super(ChaseDA12000, self).__init__(settings, parent)
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
    
    def program(self, continuous):
        logger = logging.getLogger(__name__)
        if self.enabled:
            pts = self.settings.waveform.evaluate()
            logger.info("writing " + str(len(pts)) + " points to AWG")
            seg_pts = (c_ulong * len(pts))(*pts)
            seg0 = self.SEGMENT(0, seg_pts, len(pts), 0, 2048, 2048, 1, 0)
            seg = (self.SEGMENT*1)(seg0)

            self.lib.da12000_CreateSegments(1, 1, 1, seg)
            self.lib.da12000_SetTriggerMode(1, 1 if continuous else 2, 0)
        else:
            logger.warning("{0} unavailable. Unable to program.".format(self.displayName))

    def trigger(self):
        pass #need to put code for triggering here

    def close(self):
        if self.enabled:
            self.lib.da12000_Close(1)
        
class DummyAWG(AWGDeviceBase):
    displayName = "Dummy AWG"
    sampleRate = mg(1, 'GHz')
    maxSamples = 4000000
    maxAmplitude = 4095
    
    def open(self): pass
    def close(self): pass
    def program(self, continuous): pass
    def trigger(self): pass


AWGDeviceDict = {
    ChaseDA12000.displayName : ChaseDA12000.__name__,
    DummyAWG.displayName : DummyAWG.__name__
}