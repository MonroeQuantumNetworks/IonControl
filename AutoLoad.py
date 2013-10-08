# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 23:45:54 2013

@author: pmaunz

This is the GUI for the autoload program. Includes start/stop button for loading,
a record of all loads, and an interlock to the laser frequencies returned by
the wavemeter.
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore, QtNetwork
import functools
from modules import enum
from datetime import datetime

UiForm, UiBase = PyQt4.uic.loadUiType(r'ui\AutoLoad.ui')

import MagnitudeSpinBox
from LoadingHistoryModel import LoadingHistoryModel 

def formatDelta(delta):
    """Return a string version of a datetime time difference object (timedelta),
       formatted as: HH:MM:SS.S. If hours = 0, returns MM:SS.S"""
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    hours = hours + delta.days*24
    seconds = seconds + delta.microseconds*1e-6
    components = list()
    if (hours > 0): components.append("{0}".format(hours))
    components.append("{0:02d}:{1:04.1f}".format(int(minutes),seconds))
    return ":".join(components)

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
        self.useChannel = [False]*8
        self.channelMin = [0.0]*8
        self.channelMax = [0.0]*8

    def __setstate__(self, state):
        """this function ensures that the given fields are present in the class object
        after unpickling. Only new class attributes need to be added here.
        """
        self.__dict__ = state
        self.__dict__.setdefault('useChannel', [False]*8)
        self.__dict__.setdefault('channelMin', [0.0]*8)
        self.__dict__.setdefault('channelMax', [0.0]*8)

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
    StatusOptions = enum.enum('Idle','Preheat','Load','Check','Trapped','Disappeared')
    def __init__(self, config, pulser, parent=None):
        UiBase.__init__(self,parent)
        UiForm.__init__(self)
        self.config = config
        self.settings = self.config.get('AutoLoad.Settings',AutoLoadSettings())
        self.loadingHistory = self.config.get('AutoLoad.History',list())
        self.status = self.StatusOptions.Idle
        self.timer = None
        self.pulser = pulser
        self.dataSignalConnected = False
    
    def setupUi(self,widget):
        UiForm.setupUi(self,widget)
        #Set the GUI values from the settings stored in the config files, and
        #connect the valueChanged events of each button to the appropriate method
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
        self.useChannelGui = [self.useChannelGui0, #These are the checkboxes
                              self.useChannelGui1,
                              self.useChannelGui2,
                              self.useChannelGui3,
                              self.useChannelGui4,
                              self.useChannelGui5,
                              self.useChannelGui6,
                              self.useChannelGui7]
        self.channelResultGui = [self.channelResultGui0, #Frequency result display
                                 self.channelResultGui1, 
                                 self.channelResultGui2, 
                                 self.channelResultGui3,
                                 self.channelResultGui4, 
                                 self.channelResultGui5, 
                                 self.channelResultGui6, 
                                 self.channelResultGui7]
        self.channelMinGui  = [self.channelMinGui0, #Min frequency value
                               self.channelMinGui1,
                               self.channelMinGui2,
                               self.channelMinGui3,
                               self.channelMinGui4,
                               self.channelMinGui5,
                               self.channelMinGui6,
                               self.channelMinGui7]
        self.channelMaxGui  = [self.channelMaxGui0, #Max frequency value
                               self.channelMaxGui1,
                               self.channelMaxGui2,
                               self.channelMaxGui3,
                               self.channelMaxGui4,
                               self.channelMaxGui5,
                               self.channelMaxGui6,
                               self.channelMaxGui7]
        self.channelLabelGui = [self.channelLabelGui0, #Labels, turn green/red if in range/out of range
                                self.channelLabelGui1,
                                self.channelLabelGui2,
                                self.channelLabelGui3,
                                self.channelLabelGui4,
                                self.channelLabelGui5,
                                self.channelLabelGui6,
                                self.channelLabelGui7]
        self.channelInRange = [True]*8 #indicates whether each channel is in range
        self.channelResult = [0.0]*8 #The frequency measured on each channel
        for channel in range(0,8): #Connect each GUI signal
            #For checkboxes, connection is made before setting from file, so that onUseChannelClicked is executed
            self.useChannelGui[channel].stateChanged.connect(functools.partial(self.onUseChannelClicked,channel))
            self.useChannelGui[channel].setChecked(self.settings.useChannel[channel])
            self.channelMinGui[channel].setValue(self.settings.channelMin[channel])            
            self.channelMinGui[channel].valueChanged.connect(functools.partial(self.onArrayValueChanged,channel, 'channelMin'))
            self.channelMaxGui[channel].setValue(self.settings.channelMax[channel])            
            self.channelMaxGui[channel].valueChanged.connect(functools.partial(self.onArrayValueChanged,channel, 'channelMax'))
        self.checkFreqsInRange() #Begins the loop which continually checks if frequencies are in range
        #end wavemeter interlock setup      
        self.setIdle()

    def onUseChannelClicked(self, channel):
        """Run if one of the wavemeter channel checkboxes is clicked. Begin reading that channel."""
        self.settings.useChannel[channel] = self.useChannelGui[channel].isChecked()
        if self.settings.useChannel[channel] == True:
            self.getWavemeterData(channel)
        else:
            self.channelInRange[channel] = True #deactivated channel should be considered in range
            self.channelLabelGui[channel].setStyleSheet(
            "QLabel {background-color: transparent}") #remove green/red coloring on label

    def onWavemeterError(self, error):
        """Print out received error"""
        print "Error {0}".format(error)

    def getWavemeterData(self, channel, addressStart="http://132.175.165.36:8082/wavemeter/wavemeter/wavemeter-status?channel="):
        """Get the data from the wavemeter at the specified channel."""
        intchannel= int(channel) #makes sure the channel is an integer
        if 0 <= intchannel <= 7 and self.settings.useChannel[channel] == True:
            address = addressStart + "{0}".format(intchannel)
            reply = self.am.get( QtNetwork.QNetworkRequest(QtCore.QUrl(address)))
            reply.error.connect(self.onWavemeterError)
            reply.finished.connect(functools.partial(self.onWavemeterData, intchannel, reply))
        elif self.settings.useChannel[channel] == False:
            self.channelInRange[channel] = True
            self.channelLabelGui[channel].setStyleSheet(
            "QLabel {background-color: transparent}")
        else:
            print "invalid wavemeter channel"

    def onWavemeterData(self, channel, data):
        """Execute when data is received from the wavemeter. Display it on the
           GUI, and check whether it is in range."""
        self.channelResult[channel] = round(float(data.readAll()), 4)
        freq_string = "{0:.4f}".format(self.channelResult[channel]) + " GHz"
        self.channelResultGui[channel].setText(freq_string) #Display freq on GUI
        if self.settings.channelMin[channel] < self.channelResult[channel] < self.settings.channelMax[channel]:
            self.channelLabelGui[channel].setStyleSheet("QLabel {background-color: rgb(133, 255, 124)}") #set label bg to green
            self.channelInRange[channel] = True
        else:
            self.channelLabelGui[channel].setStyleSheet("QLabel {background-color: rgb(255, 123, 123)}") #set label bg to red
            self.channelInRange[channel] = False
        #read the wavemeter channel once per second
        QtCore.QTimer.singleShot(1000,functools.partial(self.getWavemeterData, channel))
        
    def checkFreqsInRange(self):
        """Check whether all laser frequencies being used by the interlock are 
           in range. If they are not, loading is stopped/prevented, and the 
           lock status bar turns from green to red. If the lock is not being
           used, the status bar is black."""
        if all([not self.settings.useChannel[channel] for channel in range(0,8)]):
            #if no channels are checked, set bar on GUI to black
            self.allFreqsInRange.setStyleSheet("QLabel {background-color: rgb(0, 0, 0)}")
            self.allFreqsInRange.setToolTip("Wavemeter interlock is not in use")
        elif all(self.channelInRange):
            #if all channels are in range, set bar on GUI to green
            self.allFreqsInRange.setStyleSheet("QLabel {background-color: rgb(0, 198, 0)}")
            self.allFreqsInRange.setToolTip("All laser frequencies are in range")
        else:
            #if not all channels are in range, set bar on GUI to red
            self.allFreqsInRange.setStyleSheet("QLabel {background-color: rgb(255, 0, 0)}")
            self.allFreqsInRange.setToolTip("There are laser frequencies out of range")
            if (self.status != self.StatusOptions.Idle):
                self.setIdle() #This is the actual interlock: loading is inhibited if frequency are out of range
        #check if channels are in range once per second
        QtCore.QTimer.singleShot(1000, self.checkFreqsInRange)
        
    def onValueChanged(self,attr,value):
        """Change the value of attr in settings to value"""
        setattr( self.settings, attr, value)
        
    def onArrayValueChanged(self, index, attr, value):
        """Change the value of attr[index] in settings to value"""
        a = getattr(self.settings, attr)
        a[index] = value
        
    def onStart(self):
        """Execute when start button is clicked. Begin loading if idle."""
        if (self.status == self.StatusOptions.Idle):
            self.setPreheat()

    def onStop(self):
        """Execute when stop button is clicked. Stop loading."""
        print "Loading Idle"
        self.setIdle()

    def setIdle(self):
        """Execute when the loading process is set to idle. Disable timer, do not
           pay attention to the count rate, and turn off the ionization laser and oven."""
        if self.timer:
            self.timer = None
        self.elapsedLabel.setStyleSheet("QLabel { color:black; }")
        self.status = self.StatusOptions.Idle
        self.statusLabel.setText("Idle")
        if self.dataSignalConnected:
            self.pulser.dedicatedDataAvailable.disconnect( self.onData )
            self.dataSignalConnected = False
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invert(False,self.settings.ovenChannel) )
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invert(False,self.settings.shutterChannel ))
    
    def setPreheat(self):
        """Execute when the loading process begins. Turn on timer, turn on oven."""
        print "Loading Preheat"
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect( self.onTimer )
        self.timer.start(100)
        self.started = datetime.now()
        self.elapsedLabel.setText(formatDelta(datetime.timedelta(0))) #Set time display to zero
        self.elapsedLabel.setStyleSheet("QLabel { color:red; }")
        self.status = self.StatusOptions.Preheat
        self.statusLabel.setText("Preheating")
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invert(True,self.settings.ovenChannel) )
    
    def setLoad(self):
        """Execute after preheating. Turn on ionization laser, and begin
           monitoring count rate."""
        print "Loading Load"
        self.elapsedLabel.setStyleSheet("QLabel { color:purple; }")
        self.status = self.StatusOptions.Load
        self.statusLabel.setText("Loading")
        self.pulser.dedicatedDataAvailable.connect( self.onData )
        self.dataSignalConnected = True
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invert(True,self.settings.shutterChannel) )
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invert(True,self.settings.ovenChannel) )
    
    def setCheck(self):
        """Execute when count rate goes over threshold."""
        print "Loading Check"
        self.elapsedLabel.setStyleSheet("QLabel { color:blue; }")
        self.status = self.StatusOptions.Check
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
        self.status=self.StatusOptions.Trapped
        self.elapsedLabel.setStyleSheet("QLabel { color:green; }")
        self.statusLabel.setText("Trapped :)")       
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invert(False,self.settings.ovenChannel) )
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invert(False,self.settings.shutterChannel) )
    
    def setDisappeared(self):
        self.status = self.StatusOptions.Disappeared
        self.disappearedAt = datetime.now()
        self.statusLabel.setText("Disappeared :(")
    
    def onTimer(self):
        """Execute whenever the timer sends a timeout signal, which is every 100 ms.
           Trigger status changes based on elapsed time. This controls the flow
           of the loading process."""
        self.elapsed = datetime.now()-self.started
        self.elapsedLabel.setText(formatDelta(self.elapsed) )
        if self.status==self.StatusOptions.Preheat:
            if self.elapsed.total_seconds() > self.settings.laserDelay.toval('s'):
                self.setLoad()
        elif self.status==self.StatusOptions.Load:
            if self.elapsed.total_seconds() > self.settings.maxTime.toval('s'):
                self.setIdle()
        elif self.status==self.StatusOptions.Disappeared:
            if (datetime.now()-self.disappearedAt).total_seconds() > self.settings.checkTime.toval('s'):
                self.historyTableModel.updateLast('trappingTime',self.disappearedAt-self.started)
                self.setIdle()
    
    def onData(self, data ):
        """Execute when count rate data is received. Change state based on count rate."""
        if self.status==self.StatusOptions.Load:
            if data.data[self.settings.counterChannel] > self.settings.thresholdOven:
                self.setCheck()
        elif self.status==self.StatusOptions.Check:
            if data.data[self.settings.counterChannel] < self.settings.thresholdBare:
                self.setLoad()
            elif (datetime.now()-self.checkStarted).total_seconds() > self.settings.checkTime.toval('s'):
                self.setTrapped()
        elif self.status==self.StatusOptions.Trapped:
            if data.data[self.settings.counterChannel] < self.settings.thresholdBare:
                self.setDisappeared()
        elif self.status==self.StatusOptions.Disappeared:
            if data.data[self.settings.counterChannel] > self.settings.thresholdBare:
                self.setTrapped(True)
            
    
    def close(self):
        if not self.status==self.StatusOptions.Idle:
            self.setIdle()
        self.config['AutoLoad.Settings'] = self.settings
        self.config['AutoLoad.History'] = self.loadingHistory
