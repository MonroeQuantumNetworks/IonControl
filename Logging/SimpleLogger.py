'''
Created on May 16, 2014

@author: wolverine
'''
import datetime
import time
from externalParameter.MKSReader import MKSReader
from externalParameter.TerranovaReader import TerranovaReader
import os
from modules.RunningStat import RunningStatHistogram

MaxRecordingInterval = 120
QueryInterval = 0

if __name__=="__main__":
    mks = TerranovaReader() #MKSReader()
    mks.open()
    HistogramStat = RunningStatHistogram()
    LastRecordingTime = 0
    with open("pressurelog-ion.txt",'a') as f:
        while (True):
            try:
                value = mks.value()
                HistogramStat.add( value )
                if time.time()-LastRecordingTime > MaxRecordingInterval or len(HistogramStat.histogram)>2:
                    LastRecordingTime = time.time()
                    message = "{0} {1} {2} {3} {4}".format(datetime.datetime.now(), HistogramStat.mean, HistogramStat.count, HistogramStat.min, HistogramStat.max )
                    f.write(message + "\n")
                    print message
                    f.flush()
                    os.fsync(f)
                    HistogramStat.clear()
                time.sleep(QueryInterval)
            except Exception as e:
                print e
                mks.close()
                mks.open()
            
            