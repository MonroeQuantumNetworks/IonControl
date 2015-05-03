import sys
import os

sys.path.insert(0, os.path.abspath('..'))

import Timing

#create the test object whcih will control the niSync card
test = Timing.Timing()

#write to the object's data to configure the niSync card
test.sampleRate = 100e3

try:
    #initialize will connect all clock and trigger terminals
    test.init('PXI1Slot2')

    print 'A 100kHz signal is being output PFI0'

    while True:

        dataIn = raw_input("Type Go to send a trigger or type Stop: ")
        if dataIn == 'Go':
            #send a trigger programatically
            test.sendSoftwareTrigger()
        elif dataIn == 'Stop':
            break
        else:
            print 'Command not recognized...'
    


finally:
    #close when done with the object
    test.close()
