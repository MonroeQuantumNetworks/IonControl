# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 16:43:58 2013

@author: Jonathan Mizrahi
"""

import httplib


class WavemeterReadException(Exception):
    pass

def GetWavemeterFrequency(channel, address = "132.175.165.36:8082", MaxAttempts = 10):
    """Return the frequency measured by the wavemeter at the indicated channel"""
    
    requeststr = "/wavemeter/wavemeter/wavemeter-status?channel=%d" % channel #URL of wavemeter channel
    attempts = 0    
    while attempts < MaxAttempts:
        try:    
            connection = httplib.HTTPConnection(address, timeout = 5) #Create connection to the specified address
            connection.request("GET", requeststr)
            frequency = float(connection.getresponse().read().strip())
            connection.close()
            break
        except Exception as e:
            print "Exception:", e
            attempts += 1
            if attempts == MaxAttempts:
                raise WavemeterReadException("Connection failed.")
    return frequency

if __name__ == '__main__':
    import timeit
    def speed():
        print GetWavemeterFrequency(4)
    t = timeit.Timer("speed()", "from __main__ import speed")
    print t.timeit(number = 10)