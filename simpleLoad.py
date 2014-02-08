import os.path

from  Chassis.DAQmxUtility import Mode
from Chassis.WaveformChassis import WaveformChassis
from Chassis.itfParser import itfParser


base_dir = r'C:\Users\Public\Documents\aaAQC_FPGA\Chassis\config'

data_dir = os.path.join(base_dir, "Data")

voltage_file = 'Load-HOA.txt'

# Create waveform chassis
chassis = WaveformChassis()
chassis.mode = Mode.Static
chassis.initFromFile(os.path.join(base_dir, 'old_chassis.cfg'))
#chassis.initFromFile(r'Chassis\config\old_chassis.cfg')


# Read voltage file 
itf = itfParser()
itf.eMapFilePath = os.path.join(base_dir, 'HOA-Sandia96-Map.txt')
itf.open(os.path.join(base_dir, voltage_file))

line = itf.eMapReadLine()
line = itf.eMapReadLine()
line = itf.eMapReadLine()

itf.close()

# Load first line

scaleFactor = 1.0
chassis.writeAoBuffer( scaleFactor*line )
print "Loaded line of voltage file " + voltage_file + ", scaled by " \
        + str(scaleFactor)
#chassis.close()

