# -*- coding: utf-8 -*-
"""
Created on Tue Oct 01 15:09:55 2013

@author: Jonathan Mizrahi
File for testing the wavemeter interlock code
"""

from PyQt4 import QtNetwork
import PyQt4.uic
from PyQt4 import QtCore, QtGui
from functools import partial
       
Form, Base = PyQt4.uic.loadUiType(r'ui\WavemeterInterlockTest.ui')

class WavemeterInterlockTest(Form, Base):
    def __init__(self,parent=None):
        Form.__init__(self)
        Base.__init__(self,parent)

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        self.am = QtNetwork.QNetworkAccessManager()
        self.useChannel = [self.useChannel0,
                           self.useChannel1,
                           self.useChannel2,
                           self.useChannel3,
                           self.useChannel4,
                           self.useChannel5,
                           self.useChannel6,
                           self.useChannel7]

        self.channelResult = [self.channelResult0, 
                              self.channelResult1, 
                              self.channelResult2, 
                              self.channelResult3,
                              self.channelResult4, 
                              self.channelResult5, 
                              self.channelResult6, 
                              self.channelResult7]
        
        self.channelMin  = [self.channel0min,
                            self.channel1min,
                            self.channel2min,
                            self.channel3min,
                            self.channel4min,
                            self.channel5min,
                            self.channel6min,
                            self.channel7min]
        
        self.channelMax  = [self.channel0max,
                            self.channel1max,
                            self.channel2max,
                            self.channel3max,
                            self.channel4max,
                            self.channel5max,
                            self.channel6max,
                            self.channel7max]
                            
        self.channelLabel = [self.channelLabel0,
                             self.channelLabel1,
                             self.channelLabel2,
                             self.channelLabel3,
                             self.channelLabel4,
                             self.channelLabel5,
                             self.channelLabel6,
                             self.channelLabel7]

        self.channelInRange = [True]*8

        for channel in range(0,8):
            self.useChannel[channel].stateChanged.connect(partial(self.useChannel_clicked, channel))

        self.check_freqs_in_range()

    def useChannel_clicked(self, channel):
        if self.useChannel[channel].isChecked():
            print "Now reading wavemeter channel {0}".format(channel)
            self.get_data(channel)
        else:
            print "Stopped reading wavemeter channel {0}".format(channel)
            self.channelInRange[channel] = True
            self.channelLabel[channel].setStyleSheet("QLabel {background-color: transparent}")
        
    def onError(self, e):
        print "Error {0}".format(e)
        
    def get_data(self, channel, addressStart = "http://132.175.165.36:8082/wavemeter/wavemeter/wavemeter-status?channel="):
        intchannel= int(channel)
        if 0 <= intchannel <= 7 and self.useChannel[channel].isChecked():
            address = addressStart + "{0}".format(intchannel)
            reply = self.am.get( QtNetwork.QNetworkRequest(QtCore.QUrl(address)))
            reply.error.connect( self.onError )
            reply.finished.connect(partial(self.onData, intchannel, reply))
        elif not self.useChannel[channel].isChecked():
            self.channelInRange[channel] = True
            self.channelLabel[channel].setStyleSheet("QLabel {background-color: transparent}")
        else:
            print "invalid wavemeter channel"

    def onData(self, channel, data):
        result = round(float(data.readAll()), 4)
        result_string = "{0:.4f}".format(result) + " GHz"
        print result_string
        self.channelResult[channel].setText(result_string)
        if self.channelMin[channel].value() < result < self.channelMax[channel].value():
            print "in range!"
            self.channelLabel[channel].setStyleSheet("QLabel {background-color: rgb(133, 255, 124)}")
            self.channelInRange[channel] = True
        else:
            print "out of range :("
            self.channelLabel[channel].setStyleSheet("QLabel {background-color: rgb(255, 123, 123)}")
            self.channelInRange[channel] = False
            
        QtCore.QTimer.singleShot(1000,partial(self.get_data, channel))
    
    def check_freqs_in_range(self):
        if all(self.channelInRange):
            self.all_freqs_in_range.setStyleSheet("QLabel {background-color: rgb(0, 198, 0)}")
        else:
            self.all_freqs_in_range.setStyleSheet("QLabel {background-color: rgb(255, 0, 0)}")
        QtCore.QTimer.singleShot(100, self.check_freqs_in_range)

if __name__=="__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = WavemeterInterlockTest()
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())