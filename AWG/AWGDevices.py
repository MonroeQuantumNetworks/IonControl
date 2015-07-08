'''
Created on Jul 2, 2015

@author: Geoffrey Ji

AWG Devices are defined here. If a new AWG needs to be added, 
it must inherit AWGDevice and implement open, program, and close.
'''

from ctypes import *
import logging

#from magnitude import Magnitude

from externalParameter.ExternalParameterBase import ExternalParameterBase
#import magnitude as magnitude
from modules.Observable import Observable




class AWGDevice(ExternalParameterBase):
    """
    The AWG does not fit into the external parameter framework,
    but given a waveform, the variables can act as external
    parameters. This class wraps a waveform into an external
    parameter-based device.
    """
    className = "Generic AWG"
    _outputChannels = {}
    _waveform = None
    enabled = False
    
    # parent should be the AWGUi, which we read whether or not to modify the internal scan as well
    def __init__(self,name,config,waveform,parent=None):
        ExternalParameterBase.__init__(self,name,config)
        self.open()
        self.setWaveform(waveform)
        self.parent = parent
        
    def setWaveform(self, waveform):
        self._waveform = waveform
        self.setDefaults()
        self.displayValueObservable = dict([(name,Observable()) for name in self._outputChannels])
        vardict = {k: "" if (not isinstance(v['value'], Magnitude)) or v['value'].dimensionless() else \
                      str(v['value']).split(" ")[1] for (k, v) in self._waveform.vars.iteritems()}
        self._outputChannels = vardict
        for (k, v) in vardict.iteritems():
            self.settings.value[k] = self._waveform.vars[k]['value']
    
    def fullName(self, channel):
        return "{0}".format(channel)
    
    def scanParam(self):
        return (self.parent.parameters.setScanParam, str(self.parent.parameters.scanParam))

    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
        self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1,''))
                
    def _setValue(self, channel, v, continuous):
        self._waveform.vars[channel]['value'] = v
        self.program(continuous)
        
    def setValue(self, channel, value, continuous=False):
        """
        This function returns True if the value is reached. Otherwise
        it should return False. The user should call repeatedly until the intended value is reached
        and True is returned.
        """
        self._setValue(channel, value, continuous)
        
        #self.setWaveform(self._waveform)
        
        return True
        
    def paramDef(self):
        """
        return the parameter definition used by pyqtgraph parametertree to show the gui
        """
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
        return superior
        
    def isEnabled(self):
        return self.parent.parameters.enabled
    
    def open(self):
        raise NotImplementedError("Method must be implemented by specific AWG device class!")
    
    def program(self, continuous):
        raise NotImplementedError("Method must be implemented by specific AWG device class!")
        
    def close(self):
        raise NotImplementedError("Method must be implemented by specific AWG device class!")
 
class ChaseDA12000(AWGDevice):
    className = "Chase DA12000 AWG"
    _dllName = "DA12000_DLL64.dll"
 
    class SEGMENT(Structure):
        _fields_ = [("SegmentNum", c_ulong),
                    ("SegmentPtr", POINTER(c_ulong)),
                    ("NumPoints", c_ulong),
                    ("NumLoops", c_ulong),
                    ("BeginPadVal ", c_ulong), # Not used
                    ("EndingPadVal", c_ulong), # Not used
                    ("TrigEn", c_ulong),
                    ("NextSegNum", c_ulong)]
    
    try:
        da = WinDLL (_dllName)
        enabled = True
    except Exception:
        logging.getLogger(__name__).info("{0} unavailable. Unable to open {1}.".format(className, _dllName))
        enabled = False

    def open(self):
        logger = logging.getLogger(__name__)
        try:
            ChaseDA12000.da.da12000_Open(1)
            self.enabled = True
        except Exception:
            logger.info("Unable to open {0}.".format(self.className))
            self.enabled = False
    
    def program(self, continuous):
        logger = logging.getLogger(__name__)
        if self.enabled:
            pts = self._waveform.evaluate()
            logger.info("writing " + str(len(pts)) + " points to AWG")
            seg_pts = (c_ulong * len(pts))(*pts)
            seg0 = ChaseDA12000.SEGMENT(0, seg_pts, len(pts), 0, 2048, 2048, 1, 0)
            seg = (ChaseDA12000.SEGMENT*1)(seg0)

            ChaseDA12000.da.da12000_CreateSegments(1, 1, 1, seg)
            ChaseDA12000.da.da12000_SetTriggerMode(1, 1 if continuous else 2, 0)
        else:
            logger.warning("{0} unavailable. Unable to program.".format(self.className)) 

    def close(self):
        if self.enabled:
            ChaseDA12000.da.da12000_Close(1)
        
class DummyAWG(AWGDevice):
    className = "Dummy AWG"
    
    def open(self): pass
    def close(self): pass
    def program(self, continuous): pass
        
        
AWGDeviceList = [ChaseDA12000,
                 DummyAWG
                 ]