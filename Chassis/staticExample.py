from itfParser import itfParser
from WaveformChassis import WaveformChassis
from DAQmxUtility import Mode

chassis = WaveformChassis()
itf = itfParser()

chassis.mode = Mode.Static
chassis.initFromFile('C:\\Experiments\\Thunderbird\\chassis.cfg')
itf.open('C:\\Experiments\\Thunderbird\\voltage_test.txt')
itf.eMapFilePath = 'C:\\Experiments\\Thunderbird\\thunderbird_map.txt'
for i in range(itf.getNumLines())
    data = itf.eMapReadLine()
    chassis.writeAoBuffer(data)
chasis.close()
