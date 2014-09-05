import logging

from SerialInstrumentReader import wrapSerial
from VisaInstrumentReader import wrapVisa
from ModbusInstrumentReader import wrapModbus
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
    
try:
    from MultiMeterReader import MultiMeterReader
    LoggingInstruments['Multi Meter'] = wrapVisa( "MultiMeterInstrumentReader", MultiMeterReader )
except:
    logging.getLogger(__name__).info("Multi Meter reader not available")
    
try:
    from PhotodiodeReader import PhotoDiodeReader
    LoggingInstruments['Photodiode'] = wrapSerial( "PhotodiodeInstrumentReader", PhotoDiodeReader )
except:
    logging.getLogger(__name__).info("Multi Meter reader not available")

try:
    from OmegaCN7500Reader import OmegaCN7500Reader
    LoggingInstruments["Oven set point"] = wrapModbus( "OmegaCN7500InstrumentReader", OmegaCN7500Reader)
except:
    logging.getLogger(__name__).info("oven set point not available")
    
from DummyReader import DummyReader
LoggingInstruments["Dummy"] = wrapSerial( "DummyInstrumentReader", DummyReader ) 