'''
Created on Sep 28, 2012

@author: Boyan Tabakov

'''
import logging
from functools import partial
from PyQt4 import QtCore, QtNetwork
from time import time
from collections import defaultdict

from modules.magnitude import mg

class WavemeterReadException(Exception):
    pass

class Wavemeter(object):
    resultReceived = QtCore.pyqtSignal( object, object )
    
    def __init__(self, address = "132.175.165.36:8082"):
        self.address = address
        self.nAttempts = 0
        self.nMaxAttempts = 100
        #self.connection.set_debuglevel(5)
        self.lastResult = dict()
        self.queryRunning = defaultdict( lambda: False )
        self.am = QtNetwork.QNetworkAccessManager()
        
    def onWavemeterError(self, channel, error):
        """Print out received error"""
        self.queryRunning[channel] = False
        logging.getLogger(__name__).error( "Error {0} accessing wavemeter at '{1}'".format(error, self.settings.wavemeterAddress) )

    def getWavemeterData(self, channel, course=None):
        """Get the data from the wavemeter at the specified channel."""
        if not self.queryRunning[channel]:
            address = self.settings.wavemeterAddress + "/wavemeter/wavemeter/wavemeter-status?channel={0}".format(int(channel))
            if course is not None:
                address += "&course={0}".format(course)
            reply = self.am.get( QtNetwork.QNetworkRequest(QtCore.QUrl(address)))
            reply.error.connect( partial(self.onWavemeterError, int(channel) ) )
            reply.finished.connect(partial(self.onWavemeterData, int(channel), reply))
            self.queryRunning[channel] = True

    def onWavemeterData(self, channel, data):
        """Execute when data is received from the wavemeter."""
        self.queryRunning[channel] = False
        result = mg( round(float(data.readAll()), 4), 'GHz' )
        self.resultReceived.emit( channel, result ) 
        self.lastResult[channel] = (result, time())
        
    def get_frequency(self, channel, max_age = 3):
        return self.set_frequency(self, None, channel, max_age )
                   
    def set_frequency(self, freq, channel, max_age=3):
        self.getWavemeterData(channel, freq)
        if channel in self.lastResult:
            result, measure_time = self.lastResult[channel]
            if time.time()-measure_time < max_age:
                return result
        return None                    


if __name__ == '__main__':
    import timeit
    fg = Wavemeter()
    def speed():
        print fg.get_frequency(4)
    t = timeit.Timer("speed()", "from __main__ import speed")
    print t.timeit(number = 10)
    del fg    
