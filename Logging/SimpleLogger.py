'''
Created on May 16, 2014

@author: wolverine
'''
import datetime
import time
from MKSReader import MKSReader
from TerranovaReader import TerranovaReader
import os

if __name__=="__main__":
    mks = TerranovaReader() #MKSReader()
    mks.open()
    with open("pressurelog-ion.txt",'a') as f:
        while (True):
            try:
                value = mks.value()
                f.write("{0} {1}\n".format(datetime.datetime.now(), value))
                print "{0} {1}".format(datetime.datetime.now(), value)
                f.flush()
                os.fsync(f)
                time.sleep(10)
            except Exception as e:
                print e
                mks.close()
                mks.open()
            
            