'''
Created on Jul 2, 2015

@author: Geoffrey Ji

AWG Devices are defined here. If a new AWG needs to be added, 
it must inherit AWGDeviceBase and implement open, program, and close.
'''

from ctypes import *
import logging

from modules.magnitude import Magnitude
from modules.Observable import Observable
from ProjectConfig.Project import getProject

class AWGDeviceBase(object):
    """base class for AWG Devices"""
    displayName = "Generic AWG"

    # parent should be the AWGUi, which we read whether or not to modify the internal scan as well
    def __init__(self, waveform, parent=None):
        self.open()
        self.parent = parent
        self.varDict = dict()
        self.enabled = False
        self._waveform = None
        self.waveform = waveform
        self.project = getProject()

    @property
    def waveform(self):
        return self._waveform

    @waveform.setter
    def waveform(self, waveform):
        self._waveform = waveform
        self.varDict = {k: "" if (not isinstance(v['value'], Magnitude)) or v['value'].dimensionless() else \
                      str(v['value']).split(" ")[1] for (k, v) in self._waveform.vars.iteritems()}

    def scanParam(self):
        return (self.parent.parameters.setScanParam, str(self.parent.parameters.scanParam))

    def isEnabled(self):
        return self.parent.parameters.enabled
    
    def open(self):
        raise NotImplementedError("Method must be implemented by specific AWG device class!")
    
    def program(self, continuous):
        raise NotImplementedError("Method must be implemented by specific AWG device class!")
        
    def close(self):
        raise NotImplementedError("Method must be implemented by specific AWG device class!")
 
class ChaseDA12000(AWGDeviceBase):
    """Class for programming a ChaseDA12000 AWG"""
    displayName = "Chase DA12000 AWG"

    class SEGMENT(Structure):
        _fields_ = [("SegmentNum", c_ulong),
                    ("SegmentPtr", POINTER(c_ulong)),
                    ("NumPoints", c_ulong),
                    ("NumLoops", c_ulong),
                    ("BeginPadVal ", c_ulong), # Not used
                    ("EndingPadVal", c_ulong), # Not used
                    ("TrigEn", c_ulong),
                    ("NextSegNum", c_ulong)]

    def __init__(self, waveform, parent=None):
        super(ChaseDA12000, self).__init__(waveform, parent)
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
            pts = self.waveform.evaluate()
            logger.info("writing " + str(len(pts)) + " points to AWG")
            seg_pts = (c_ulong * len(pts))(*pts)
            seg0 = self.SEGMENT(0, seg_pts, len(pts), 0, 2048, 2048, 1, 0)
            seg = (self.SEGMENT*1)(seg0)

            self.lib.da12000_CreateSegments(1, 1, 1, seg)
            self.lib.da12000_SetTriggerMode(1, 1 if continuous else 2, 0)
        else:
            logger.warning("{0} unavailable. Unable to program.".format(self.displayName))

    def close(self):
        if self.enabled:
            self.lib.da12000_Close(1)
        
class DummyAWG(AWGDeviceBase):
    displayName = "Dummy AWG"
    
    def open(self): pass
    def close(self): pass
    def program(self, continuous): pass


AWGDeviceDict = {
    ChaseDA12000.displayName : ChaseDA12000.__name__,
    DummyAWG.displayName : DummyAWG.__name__
}