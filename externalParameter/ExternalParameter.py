# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 15:22:09 2013

@author: wolverine
"""

# The dictionary of External Instrument classes is maintained using a metaclass
# To define a new External Instrument you need to
# * define the class with a class attribute __metaclass__ = InstrumentMeta
# * import the module containing the class in this module
# * the dictionary of classes is InstrumentMeta.InstrumentDict

import logging

import StandardExternalParameter     #@UnusedImport
from externalParameter import InterProcessParameters  #@UnusedImport
        
try:
    import MotionParameter  #@UnusedImport
except Exception as ex:
    logging.getLogger(__name__).info("Motion control devices are not available: {0}".format(ex))
    

try:
    import APTInstruments #@UnusedImport
except Exception as ex:
    logging.getLogger(__name__).info("Thorlabs APT devices are not available: {0}".format(ex))
    
