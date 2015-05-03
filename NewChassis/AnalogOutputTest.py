import sys
import os

sys.path.insert(0, os.path.abspath('..'))

import AnalogOutput as ao
import DAQmxUtility as dutil

physicalChannel = 'PXI1Slot3/ao0:7'

#################### Static Mode ######################
print 'Running Static Mode...'
test = ao.AnalogOutput()
test.mode = dutil.Mode.Static

try:
    test.init(physicalChannel)
    print "Number of Channels: " + str(test.numChannels)
    print "Samples Per Channel: {0}".format(test.samplesPerChannel)
    print "Sample Rate: {0}".format(test.sampleRate)
    testBuffer = test.createSineTestBuffer()
    test.writeToBuffer(testBuffer)
    test.start()
    print test.done
    test.waitUntilDone()
    test.stop()
    print test.done

finally:
    test.close()
    
print 'Static Mode Complete'

################### Finite Mode ########################
print 'Testing Finite Mode...'
test.mode = dutil.Mode.Finite
samples = raw_input('How many samples: ')
test.samplesPerChannel = int(samples)
test.sampleRate = 100000

try:
    test.init(physicalChannel)
    print "Samples Per Channel: {0}".format(test.samplesPerChannel)
    print "Sample Rate: {0}".format(test.sampleRate)
    testBuffer = test.createSineTestBuffer()
    test.writeToBuffer(testBuffer)
    test.start()
    print test.done
    test.waitUntilDone()
    test.stop()

finally:
    test.close()
print 'Finite Mode Complete'

################## Continuous Mode #####################
print 'Testing Continuous Mode'
test.mode = dutil.Mode.Continuous
try:
    test.init(physicalChannel)
    test.pauseTriggerSource = 'PFI0'
    test.writeToBuffer(testBuffer)
    test.start()
    raw_input('Press enter to stop...')
    test.stop()
    
finally:
    test.close()
print 'Continuous Mode Complete'
