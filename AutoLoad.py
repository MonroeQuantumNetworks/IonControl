# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 23:45:54 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore, QtNetwork
import functools
from modules import enum
from datetime import datetime
from functools import partial

UiForm, UiBase = PyQt4.uic.loadUiType(r'ui\AutoLoad.ui')

import MagnitudeSpinBox
from LoadingHistoryModel import LoadingHistoryModel 

class AutoLoadSettings:
    def __init__(self):
        self.counterChannel = 0
        self.shutterChannel = 0
        self.ovenChannel = 0
        self.laserDelay = 0
        self.maxTime = 0
        self.thresholdBare = 0
        self.thresholdOven = 0
        self.checkTime = 0
#        self.mynewvariable = 42
#
#    def __setstate__(self, state):
#        """this function ensures that the given fields are present in the class object
#        after unpickling. Only new class attributes need to be added here.
#        """
#        self.__dict__ = state
#        self.__dict__.setdefault('mynewvariable', 42)

def invert( logic, channel):
    """ returns logic for positive channel number, inverted for negative channel number """
    #print "invert", logic, channel, logic if channel>0 else not logic
    return (logic if channel>0 else not logic)

class LoadingEvent:
    def __init__(self,loading=None,trappedAt=None):
        self.loadingTime = loading
        self.trappedAt = trappedAt
        self.trappingTime = None

class AutoLoad(UiForm,UiBase):
    Status = enum.enum('Idle','Preheat','Load','Check','Trapped','Disappeared')
    def __init__(self, config, pulser, parent=None):
        UiBase.__init__(self,parent)
        UiForm.__init__(self)
        self.config = config
        self.settings = self.config.get('AutoLoad.Settings',AutoLoadSettings())
        self.loadingHistory = self.config.get('AutoLoad.History',list())
        self.status = self.Status.Idle
        self.timer = None
        self.pulser = pulser
        self.dataSignalConnected = False
    
    def setupUi(self,widget):
        UiForm.setupUi(self,widget)
        self.counterChannelBox.setValue( self.settings.counterChannel )
        self.counterChannelBox.valueChanged.connect( functools.partial( self.onValueChanged, 'counterChannel' ))
        self.shutterChannelBox.setValue( self.settings.shutterChannel )
        self.shutterChannelBox.valueChanged.connect( functools.partial( self.onValueChanged, 'shutterChannel' ))
        self.ovenChannelBox.setValue( self.settings.ovenChannel )
        self.ovenChannelBox.valueChanged.connect( functools.partial( self.onValueChanged, 'ovenChannel' ))
        self.laserDelayBox.setValue( self.settings.laserDelay )
        self.laserDelayBox.valueChanged.connect( functools.partial( self.onValueChanged, 'laserDelay' ))
        self.maxTimeBox.setValue( self.settings.maxTime )
        self.maxTimeBox.valueChanged.connect( functools.partial( self.onValueChanged, 'maxTime' ))
        self.thresholdBareBox.setValue( self.settings.thresholdBare )
        self.thresholdBareBox.valueChanged.connect( functools.partial( self.onValueChanged, 'thresholdBare' ))
        self.thresholdOvenBox.setValue( self.settings.thresholdOven )
        self.thresholdOvenBox.valueChanged.connect( functools.partial( self.onValueChanged, 'thresholdOven' ))
        self.checkTimeBox.setValue( self.settings.checkTime )
        self.checkTimeBox.valueChanged.connect( functools.partial( self.onValueChanged, 'checkTime' ))
        self.startButton.clicked.connect( self.onStart )
        self.stopButton.clicked.connect( self.onStop )
        self.historyTableModel = LoadingHistoryModel(self.loadingHistory)
        self.historyTableView.setModel(self.historyTableModel)
        #Wavemeter interlock setup        
        self.am = QtNetwork.QNetworkAccessManager()
        self.useChannel = [self.use_channel0,
                           self.use_channel1,
                           self.use_channel2,
                           self.use_channel3,
                           self.use_channel4,
                           self.use_channel5,
                           self.use_channel6,
                           self.use_channel7]
        self.channelResult = [self.channel_result0, 
                              self.channel_result1, 
                              self.channel_result2, 
                              self.channel_result3,
                              self.channel_result4, 
                              self.channel_result5, 
                              self.channel_result6, 
                              self.channel_result7]
        self.channelMin  = [self.channel_min0,
                            self.channel_min1,
                            self.channel_min2,
                            self.channel_min3,
                            self.channel_min4,
                            self.channel_min5,
                            self.channel_min6,
                            self.channel_min7]
        self.channelMax  = [self.channel_max0,
                            self.channel_max1,
                            self.channel_max2,
                            self.channel_max3,
                            self.channel_max4,
                            self.channel_max5,
                            self.channel_max6,
                            self.channel_max7]
        self.channelLabel = [self.channel_label0,
                             self.channel_label1,
                             self.channel_label2,
                             self.channel_label3,
                             self.channel_label4,
                             self.channel_label5,
                             self.channel_label6,
                             self.channel_label7]
        self.channelInRange = [True]*8 #indicates whether each channel is in range
        for num, channel in enumerate(self.useChannel): #Connect up each checkbox signal
            channel.stateChanged.connect(partial(self.onUseChannelClicked, num))
        self.checkFreqsInRange()
        #end wavemeter interlock setup      
        self.setIdle()

    def onUseChannelClicked(self, channel):
        """Run if one of the wavemeter channel checkboxes is clicked. Begin reading that channel."""        
        if self.useChannel[channel].isChecked():
            self.getWavemeterData(channel)
        else:
            self.channelInRange[channel] = True #deactivated channel should be considered in range
            self.channelLabel[channel].setStyleSheet(
            "QLabel {background-color: transparent}") #remove green/red coloring on label

    def onWavemeterError(self, error):
        """Print out received error"""
        print "Error {0}".format(error)

    def getWavemeterData(self, channel, addressStart="http://132.175.165.36:8082/wavemeter/wavemeter/wavemeter-status?channel="):
        """Get the data from the wavemeter at the specified channel."""
        intchannel= int(channel) #makes sure the channel is an integer
        if 0 <= intchannel <= 7 and self.useChannel[channel].isChecked():
            address = addressStart + "{0}".format(intchannel)
            reply = self.am.get( QtNetwork.QNetworkRequest(QtCore.QUrl(address)))
            reply.error.connect(self.onWavemeterError)
            reply.finished.connect(partial(self.onWavemeterData, intchannel, reply))
        elif not self.useChannel[channel].isChecked():
            self.channelInRange[channel] = True
            self.channelLabel[channel].setStyleSheet(
            "QLabel {background-color: transparent}")
        else:
            print "invalid wavemeter channel"

    def onWavemeterData(self, channel, data):
        """Execute when data is received from the wavemeter. Display it on the
           GUI, and check whether it is in range."""
        freq = round(float(data.readAll()), 4)
        freq_string = "{0:.4f}".format(freq) + " GHz"
        self.channelResult[channel].setText(freq_string) #Display freq on GUI
        if self.channelMin[channel].value() < freq < self.channelMax[channel].value():
            self.channelLabel[channel].setStyleSheet("QLabel {background-color: rgb(133, 255, 124)}") #set label bg to green
            self.channelInRange[channel] = True
        else:
            self.channelLabel[channel].setStyleSheet("QLabel {background-color: rgb(255, 123, 123)}") #set label bg to red
            self.channelInRange[channel] = False
        #read the wavemeter channel once per second
        QtCore.QTimer.singleShot(1000,partial(self.getWavemeterData, channel))
        
    def checkFreqsInRange(self):
        if all([not self.useChannel[channel].isChecked() for channel in range(0,8)]):
            #if no channels are checked, set bar on GUI to black
            self.all_freqs_in_range.setStyleSheet("QLabel {background-color: rgb(0, 0, 0)}")
        elif all(self.channelInRange):
            #if all channels are in range, set bar on GUI to green
            self.all_freqs_in_range.setStyleSheet("QLabel {background-color: rgb(0, 198, 0)}")
        else:
            #if not all channels are in range, set bar on GUI to red
            self.all_freqs_in_range.setStyleSheet("QLabel {background-color: rgb(255, 0, 0)}")
        #check if channels are in range once per second
        QtCore.QTimer.singleShot(1000, self.checkFreqsInRange)
        
    def onValueChanged(self,attr,value):
        setattr( self.settings, attr, value)
        
    def onStart(self):
        if (self.status == self.Status.Idle):
            self.setPreheat()

    def onStop(self):
        print "Loading Idle"
        self.setIdle()

    def formatDelta(self, delta):
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        hours = hours + delta.days*24
        seconds = seconds + delta.microseconds*1e-6
        components = list()
        if (hours>0): components.append("{0}".format(hours))
        components.append("{0:02d}:{1:04.1f}".format(int(minutes),seconds))
        return ":".join(components)
        
    def timedeltaseconds(self,delta):
        return delta.days*24*3600.0 + delta.seconds + delta.microseconds*1e-6
    
    def setIdle(self):
        if self.timer:
            del self.timer
            self.timer = None
        self.elapsedLabel.setStyleSheet("QLabel { color:black; }")
        self.status = self.Status.Idle
        self.statusLabel.setText("Idle")
        if self.dataSignalConnected:
            self.pulser.dedicatedDataAvailable.disconnect( self.onData )
            self.dataSignalConnected = False
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invert(False,self.settings.ovenChannel) )
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invert(False,self.settings.shutterChannel ))
    
    def setPreheat(self):
        print "Loading Preheat"
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect( self.onTimer )
        self.timer.start(100)
        self.started = datetime.now()
        self.elapsedLabel.setText(self.formatDelta(datetime.now()-self.started))
        self.elapsedLabel.setStyleSheet("QLabel { color:red; }")
        self.status = self.Status.Preheat
        self.statusLabel.setText("Preheating")
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invert(True,self.settings.ovenChannel) )
    
    def setLoad(self):
        print "Loading Load"
        self.elapsedLabel.setStyleSheet("QLabel { color:purple; }")
        self.status = self.Status.Load
        self.statusLabel.setText("Loading")
        self.pulser.dedicatedDataAvailable.connect( self.onData )
        self.dataSignalConnected = True
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invert(True,self.settings.shutterChannel) )
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invert(True,self.settings.ovenChannel) )
    
    def setCheck(self):
        print "Loading Check"
        self.elapsedLabel.setStyleSheet("QLabel { color:blue; }")
        self.status = self.Status.Check
        self.checkStarted = datetime.now()
        self.statusLabel.setText("Checking for ion")
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invert(False,self.settings.shutterChannel) )
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invert(False,self.settings.ovenChannel) )
        
    def setTrapped(self,reappeared=False):
        if not reappeared:
            print "Loading Trapped"
            self.loadingTime = datetime.now() - self.started
            self.started = self.checkStarted
            self.historyTableModel.append( LoadingEvent(self.loadingTime,self.checkStarted) )
        self.status=self.Status.Trapped
        self.elapsedLabel.setStyleSheet("QLabel { color:green; }")
        self.statusLabel.setText("Trapped :)")       
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invert(False,self.settings.ovenChannel) )
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invert(False,self.settings.shutterChannel) )
    
    def setDisappeared(self):
        self.status = self.Status.Disappeared
        self.disappearedAt = datetime.now()
        self.statusLabel.setText("Disappeared :(")       
    
    def onTimer(self):
        self.elapsed = datetime.now()-self.started
        self.elapsedLabel.setText(self.formatDelta(self.elapsed) )
        if self.status==self.Status.Preheat:
            if self.timedeltaseconds(self.elapsed)>self.settings.laserDelay.toval('s'):
                self.setLoad()
        elif self.status==self.Status.Load:
            if self.timedeltaseconds(self.elapsed)>self.settings.maxTime.toval('s'):
                self.setIdle()
        elif self.status==self.Status.Disappeared:
            if self.timedeltaseconds(datetime.now()-self.disappearedAt)>self.settings.checkTime.toval('s'):
                self.historyTableModel.updateLast('trappingTime',self.disappearedAt-self.started)
                self.setIdle()
    
    def onData(self, data ):
        if self.status==self.Status.Load:
            if data.data[self.settings.counterChannel]>self.settings.thresholdOven:
                self.setCheck()
        elif self.status==self.Status.Check:
            if data.data[self.settings.counterChannel]<self.settings.thresholdBare:
                self.setLoad()
            elif self.timedeltaseconds(datetime.now()-self.checkStarted)>self.settings.checkTime.toval('s'):
                self.setTrapped()
        elif self.status==self.Status.Trapped:
            if data.data[self.settings.counterChannel]<self.settings.thresholdBare:
                self.setDisappeared()
        elif self.status==self.Status.Disappeared:
            if data.data[self.settings.counterChannel]>self.settings.thresholdBare:
                self.setTrapped(True)
            
    
    def close(self):
        if not self.status==self.Status.Idle:
            self.setIdle()
        self.config['AutoLoad.Settings'] = self.settings
        self.config['AutoLoad.History'] = self.loadingHistory
