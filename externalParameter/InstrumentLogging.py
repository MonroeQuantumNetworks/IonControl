import logging

from InstrumentReader import wrapInstrument
LoggingInstruments = dict()

try:
    from MKSReader import MKSReader
    LoggingInstruments["MKS Vacuum Gauge"] = wrapInstrument( "MKSInstrumentReader", MKSReader)
except:
    logging.getLogger(__name__).info("MKS Vacuum gauge reader not available")
    
try:
    from TerranovaReader import TerranovaReader
    LoggingInstruments["Ion Gauge"] = wrapInstrument( "TerranovaInstrumentReader", TerranovaReader)
except:
    logging.getLogger(__name__).info("Ion gauge reader not available")
    
try:
    from MultiMeterReader import MultiMeterReader
    from Keithley2010Reader import Keithley2010Reader
    LoggingInstruments['Multi Meter'] = wrapInstrument( "MultiMeterInstrumentReader", MultiMeterReader )
    LoggingInstruments['Keithley 2010'] = wrapInstrument( "Keithley2010ReaderInstrumentReader", Keithley2010Reader )
except:
    logging.getLogger(__name__).info("Multi Meter reader not available")
    
try:
    from PhotodiodeReader import PhotoDiodeReader
    LoggingInstruments['Photodiode'] = wrapInstrument( "PhotodiodeInstrumentReader", PhotoDiodeReader )
except:
    logging.getLogger(__name__).info("Photodiode reader not available")

try:
    from OmegaCN7500Reader import OmegaCN7500Reader
    LoggingInstruments["Oven set point"] = wrapInstrument( "OmegaCN7500InstrumentReader", OmegaCN7500Reader)
except:
    logging.getLogger(__name__).info("oven set point not available")
    
from DummyReader import DummyReader
LoggingInstruments["Dummy"] = wrapInstrument( "DummyInstrumentReader", DummyReader ) 