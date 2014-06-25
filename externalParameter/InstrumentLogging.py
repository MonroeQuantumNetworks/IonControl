import logging

from SerialInstrumentReader import wrapSerial
LoggingInstruments = dict()

try:
    from MKSReader import MKSReader
    LoggingInstruments["MKS Vacuum Gauge"] = wrapSerial( "MKSInstrumentReader", MKSReader)
except:
    logging.getLogger(__name__).info("MKS Vacuum gauge reader not available")
    
try:
    from TerranovaReader import TerranovaReader
    LoggingInstruments["Ion Gauge"] = wrapSerial( "TerranovaInstrumentReader", TerranovaReader)
except:
    logging.getLogger(__name__).info("Ion gauge reader not available")
    
from DummyReader import DummyReader
LoggingInstruments["Dummy"] = wrapSerial( "DummyInstrumentReader", DummyReader ) 