# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:22:09 2013

@author: wolverine
"""


import logging

import StandardExternalParameter  
from externalParameter import InterProcessParameters
        
ExternalParameter = { StandardExternalParameter.LaserWavemeterLockScan.className: StandardExternalParameter.LaserWavemeterLockScan, 
                              StandardExternalParameter.HP8672A.className: StandardExternalParameter.HP8672A,
                              StandardExternalParameter.AgilentPowerSupply.className: StandardExternalParameter.AgilentPowerSupply,
                              StandardExternalParameter.LaserWavemeterScan.className : StandardExternalParameter.LaserWavemeterScan,
                              StandardExternalParameter.DummyParameter.className: StandardExternalParameter.DummyParameter,
                              StandardExternalParameter.N6700BPowerSupply.className: StandardExternalParameter.N6700BPowerSupply,
                              StandardExternalParameter.MicrowaveSynthesizerScan.className : StandardExternalParameter.MicrowaveSynthesizerScan,
                              InterProcessParameters.LockOutputFrequency.className:  InterProcessParameters.LockOutputFrequency}

try:
    import MotionParameter
    ExternalParameter[ MotionParameter.ConexLinear.className ] = MotionParameter.ConexLinear 
    ExternalParameter[ MotionParameter.ConexRotation.className ] = MotionParameter.ConexRotation 
    ExternalParameter[ MotionParameter.PowerWaveplate.className ] = MotionParameter.PowerWaveplate 
except Exception as ex:
    #logging.getLogger(__name__).exception(ex)
    logging.getLogger(__name__).error("Motion control devices are not available")
    

