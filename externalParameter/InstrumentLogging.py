
from SerialInstrumentReader import wrapSerial
#from MKSReader import MKSReader
from DummyReader import DummyReader

LoggingInstruments = { #"MKS Vacuum Gauge": wrapSerial( "MKSInstrumentReader", MKSReader),
                       "Dummy": wrapSerial( "DummyInstrumentReader", DummyReader ) }