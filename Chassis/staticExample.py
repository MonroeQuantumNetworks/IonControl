from itfParser import itfParser
from WaveformChassis import WaveformChassis
from DAQmxUtility import Mode

chassis = WaveformChassis()
itf = itfParser()

chassis.mode = Mode.Static
chassis.initFromFile(r'config\old_chassis.cfg')
print "read config"
itf.open(r'config\hoa_test.itf')
print "file opened"
itf.eMapFilePath = r'config\hoa_map.txt'
print "map file set"
for i in range(itf.getNumLines()):
    data = itf.eMapReadLine()
    print "data", data
    print type(data)
    chassis.writeAoBuffer(data)
chassis.close()
