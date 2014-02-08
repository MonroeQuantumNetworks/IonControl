# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 23:45:54 2013

@author: pmaunz

This is the GUI for the autoload program. Includes start/stop button for loading,
a record of all loads, and an interlock to the laser frequencies returned by
the wavemeter.
"""

from datetime import datetime
import functools
import logging

from PyQt4 import QtCore, QtNetwork
import PyQt4.uic

from dedicatedCounters.LoadingHistoryModel import LoadingHistoryModel
from dedicatedCounters.WavemeterInterlockTableModel import WavemeterInterlockTableModel
from modules import enum
from modules.SequenceDict import SequenceDict
from modules.Utility import unique
from modules.formatDelta import formatDelta
from modules.magnitude import Magnitude
from uiModules.KeyboardFilter import KeyFilter


UiForm, UiBase = PyQt4.uic.loadUiType(r'ui\AutoLoad.ui')


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
        self.useInterlock = False
        self.interlock = SequenceDict()
        self.wavemeterAddress = ""

    def __setstate__(self, state):
        """this function ensures that the given fields are present in the class object
        after unpickling. Only new class attributes need to be added here.
        """
        self.__dict__ = state

def invert( logic, channel):
    """ returns logic for positive channel number, inverted for negative channel number """
    return (logic if channel>0 else not logic)

class LoadingEvent:
    def __init__(self,loading=None,trappedAt=None):
        self.loadingTime = loading
        self.trappedAt = trappedAt
        self.trappingTime = None

class AutoLoad(UiForm,UiBase):
    StatusOptions = enum.enum('Idle','Preheat','Load','Check','Trapped','Disappeared', 'Frozen' )
    def __init__(self, config, pulser, dataAvailableSignal, parent=None):
        UiBase.__init__(self,parent)
        UiForm.__init__(self)
        self.config = config
        self.settings = self.config.get('AutoLoad.Settings',AutoLoadSettings())
        self.loadingHistory = self.config.get('AutoLoad.History',list())
        self.status = self.StatusOptions.Idle
        self.timer = None
        self.pulser = pulser
        self.dataSignalConnected = False
        self.outOfRangeCount=0
        self.dataSignal = dataAvailableSignal
    
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
        self.laserDelayBox.dimension = Magnitude(1,s=1)
        self.laserDelayBox.valueChanged.connect( functools.partial( self.onValueChanged, 'laserDelay' ))
        self.maxTimeBox.setValue( self.settings.maxTime )
        self.maxTimeBox.dimension = Magnitude(1,s=1)
        self.maxTimeBox.valueChanged.connect( functools.partial( self.onValueChanged, 'maxTime' ))
        self.thresholdBareBox.setValue( self.settings.thresholdBare )
        self.thresholdBareBox.dimension = Magnitude(1,s=-1)
        self.thresholdBareBox.valueChanged.connect( functools.partial( self.onValueChanged, 'thresholdBare' ))
        self.thresholdOvenBox.setValue( self.settings.thresholdOven )
        self.thresholdOvenBox.dimension = Magnitude(1,s=-1)
        self.thresholdOvenBox.valueChanged.connect( functools.partial( self.onValueChanged, 'thresholdOven' ))
        self.checkTimeBox.setValue( self.settings.checkTime )
        self.checkTimeBox.dimension = Magnitude(1,s=1)
        self.checkTimeBox.valueChanged.connect( functools.partial( self.onValueChanged, 'checkTime' ))
        self.startButton.clicked.connect( self.onStart )
        self.stopButton.clicked.connect( self.onStop )
        self.historyTableModel = LoadingHistoryModel(self.loadingHistory)
        self.historyTableView.setModel(self.historyTableModel)
        self.keyFilter = KeyFilter(QtCore.Qt.Key_Delete)
        self.keyFilter.keyPressed.connect( self.deleteFromHistory )
        self.historyTableView.installEventFilter( self.keyFilter )
        #Wavemeter interlock setup        
        self.am = QtNetwork.QNetworkAccessManager()
        self.useInterlockGui.setChecked(self.settings.useInterlock)
        self.useInterlockGui.stateChanged.connect(self.onUseInterlockClicked)
        self.wavemeterAddressLineEdit.setText( self.settings.wavemeterAddress )
        self.wavemeterAddressLineEdit.editingFinished.connect( self.onWavemeterAddress )
        self.tableModel = WavemeterInterlockTableModel( self.settings.interlock )
        self.tableModel.getWavemeterData.connect( self.getWavemeterData )
        self.tableModel.getWavemeterData.connect( self.checkFreqsInRange )
        self.interlockTableView.setModel( self.tableModel )
        self.interlockTableView.resizeColumnsToContents()
        self.interlockTableView.setSortingEnabled(True)
        self.addChannelButton.clicked.connect( self.tableModel.addChannel )        
        self.removeChannelButton.clicked.connect( self.onRemoveChannel )        
        self.checkFreqsInRange() #Begins the loop which continually checks if frequencies are in range
        for ilChannel in self.settings.interlock.values():
            self.getWavemeterData(ilChannel.channel)
        #end wavemeter interlock setup      
        self.setIdle()
        self.pulser.ppActiveChanged.connect( self.setDisabled )
        
    def deleteFromHistory(self):
        for row in sorted(unique([ i.row() for i in self.historyTableView.selectedIndexes() ]),reverse=True):
            self.historyTableModel.removeRow(row)
        
    def onRemoveChannel(self):
        for index in sorted(unique([ i.row() for i in self.interlockTableView.selectedIndexes() ]),reverse=True):
            self.tableModel.removeChannel(index)
        
    def onWavemeterAddress(self):
        value = str(self.wavemeterAddressLineEdit.text())
        self.settings.wavemeterAddress = value if value.find("http://")==0 else "http://" +value
        self.wavemeterAddressLineEdit.setText(self.settings.wavemeterAddress)
        
    def onUseInterlockClicked(self):
        """Run if useInterlock button is clicked. Change settings to match."""
        self.settings.useInterlock = self.useInterlockGui.isChecked()

    def onWavemeterError(self, error):
        """Print out received error"""
        logging.getLogger(__name__).error( "Error {0} accessing wavemeter at '{1}'".format(error, self.settings.wavemeterAddress) )

    def getWavemeterData(self, channel):
        """Get the data from the wavemeter at the specified channel."""
        if channel in self.settings.interlock:
            if self.settings.interlock[channel].enable:
                address = self.settings.wavemeterAddress + "/wavemeter/wavemeter/wavemeter-status?channel={0}".format(int(channel))
                reply = self.am.get( QtNetwork.QNetworkRequest(QtCore.QUrl(address)))
                reply.error.connect(self.onWavemeterError)
                reply.finished.connect(functools.partial(self.onWavemeterData, int(channel), reply))
            else:
                self.checkFreqsInRange()

    def onWavemeterData(self, channel, data):
        """Execute when data is received from the wavemeter. Display it on the
           GUI, and check whether it is in range."""
        if channel in self.settings.interlock:
            ilChannel = self.settings.interlock[channel]
            if data.error()==0:
                self.tableModel.setCurrent( channel, round(float(data.readAll()), 4) )
            #freq_string = "{0:.4f}".format(self.channelResult[channel]) + " GHz"
        #read the wavemeter channel once per second
            if ilChannel.enable:
                QtCore.QTimer.singleShot(1000,functools.partial(self.getWavemeterData, channel))
        self.checkFreqsInRange()
        
    def checkFreqsInRange(self):
        """Check whether all laser frequencies being used by the interlock are in range.
        
            If they are not, loading is stopped/prevented, and the lock status bar turns
            from green to red. If the lock is not being used, the status bar is black."""
        enabledChannels = sum(1 if x.enable else 0 for x in self.settings.interlock.values() )
        outOfRangeChannels = sum(1 if x.enable and not x.inRange else 0 for x in self.settings.interlock.values() )
        if enabledChannels==0:
            #if no channels are checked, set bar on GUI to black
            self.allFreqsInRange.setStyleSheet("QLabel {background-color: rgb(0, 0, 0)}")
            self.allFreqsInRange.setToolTip("No channels are selected")
            self.outOfRangeCount = 0
        elif outOfRangeChannels==0:
            #if all channels are in range, set bar on GUI to green
            self.allFreqsInRange.setStyleSheet("QLabel {background-color: rgb(0, 198, 0)}")
            self.allFreqsInRange.setToolTip("All laser frequencies are in range")
            self.outOfRangeCount = 0
        else:
            #Because of the bug where the wavemeter reads incorrectly after calibration,
            #Loading is only inhibited after 10 consecutive bad measurements
            if self.outOfRangeCount < 20: #Count how many times the frequency measures out of range. Stop counting at 20. (why count forever?)
                self.outOfRangeCount += 1
#                 self.allFreqsInRange.setStyleSheet("QLabel {background-color: rgb(255, 255, 0)}")
#                 self.allFreqsInRange.setToolTip("There are laser frequencies temporarily of range")
            if (self.outOfRangeCount >= 10):
                #set bar on GUI to red
                self.allFreqsInRange.setStyleSheet("QLabel {background-color: rgb(255, 0, 0)}")
                self.allFreqsInRange.setToolTip("There are laser frequencies out of range")
                #This is the interlock: loading is inhibited if frequencies are out of range
                if ((self.status != self.StatusOptions.Idle) & self.settings.useInterlock):
                    self.setIdle() 
        
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
        logger = logging.getLogger(__name__)
        logger.info(  "Loading Idle" )
        self.setIdle()

    def setIdle(self):
        """Execute when the loading process is set to idle. Disable timer, do not
           pay attention to the count rate, and turn off the ionization laser and oven."""
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        if self.timer:
            self.timer = None
        self.elapsedLabel.setStyleSheet("QLabel { color:black; }")
        self.status = self.StatusOptions.Idle
        self.statusLabel.setText("Idle")
        if self.dataSignalConnected:
            self.dataSignal.disconnect( self.onData )
            self.dataSignalConnected = False
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invert(False,self.settings.ovenChannel) )
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invert(False,self.settings.shutterChannel ))
    
    def setPreheat(self):
        """Execute when the loading process begins. Turn on timer, turn on oven."""
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        logger = logging.getLogger(__name__)
        logger.info( "Loading Preheat" )
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect( self.onTimer )
        self.timer.start(100)
        self.started = datetime.now()
        self.elapsedLabel.setText(formatDelta(datetime.now()-self.started)) #Set time display to zero
        self.elapsedLabel.setStyleSheet("QLabel { color:red; }")
        self.status = self.StatusOptions.Preheat
        self.statusLabel.setText("Preheating")
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invert(True,self.settings.ovenChannel) )
    
    def setLoad(self):
        """Execute after preheating. Turn on ionization laser, and begin
           monitoring count rate."""
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        logger = logging.getLogger(__name__)
        logger.info( "Loading Load" )
        self.elapsedLabel.setStyleSheet("QLabel { color:purple; }")
        self.status = self.StatusOptions.Load
        self.statusLabel.setText("Loading")
        self.dataSignal.connect( self.onData )
        self.dataSignalConnected = True
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invert(True,self.settings.shutterChannel) )
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invert(True,self.settings.ovenChannel) )
    
    def setCheck(self):
        """Execute when count rate goes over threshold."""
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        logger = logging.getLogger(__name__)
        logger.info(  "Loading Check" )
        self.elapsedLabel.setStyleSheet("QLabel { color:blue; }")
        self.status = self.StatusOptions.Check
        self.checkStarted = datetime.now()
        self.statusLabel.setText("Checking for ion")
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invert(False,self.settings.shutterChannel) )
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invert(False,self.settings.ovenChannel) )
        
    def setTrapped(self,reappeared=False):
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        if not reappeared:
            logger = logging.getLogger(__name__)
            logger.info(  "Loading Trapped" )
            self.loadingTime = datetime.now() - self.started
            self.started = self.checkStarted
            self.historyTableModel.append( LoadingEvent(self.loadingTime,self.checkStarted) )
        self.status=self.StatusOptions.Trapped
        self.elapsedLabel.setStyleSheet("QLabel { color:green; }")
        self.statusLabel.setText("Trapped :)")       
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invert(False,self.settings.ovenChannel) )
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invert(False,self.settings.shutterChannel) )
    
    def setFrozen(self):
        self.startButton.setEnabled( False )
        self.stopButton.setEnabled( False )       
        self.elapsedLabel.setStyleSheet("QLabel { color:grey; }")
        self.statusLabel.setText("Currently running pulse program")       
        self.status=self.StatusOptions.Frozen        
    
    def setDisappeared(self):
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
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
            if data.data[self.settings.counterChannel]/data.integrationTime > self.settings.thresholdOven:
                self.setCheck()
        elif self.status==self.StatusOptions.Check:
            if data.data[self.settings.counterChannel]/data.integrationTime < self.settings.thresholdBare:
                self.setLoad()
            elif (datetime.now()-self.checkStarted).total_seconds() > self.settings.checkTime.toval('s'):
                self.setTrapped()
        elif self.status==self.StatusOptions.Trapped:
            if data.data[self.settings.counterChannel]/data.integrationTime < self.settings.thresholdBare:
                self.setDisappeared()
        elif self.status==self.StatusOptions.Disappeared:
            if data.data[self.settings.counterChannel]/data.integrationTime > self.settings.thresholdBare:
                self.setTrapped(True)
            
    
    def onClose(self):
        if not self.status==self.StatusOptions.Idle:
            self.setIdle()
            
    def saveConfig(self):
        self.config['AutoLoad.Settings'] = self.settings
        self.config['AutoLoad.History'] = self.loadingHistory

    def setDisabled(self, disable):
        if disable:
            if self.status in [ self.StatusOptions.Preheat, self.StatusOptions.Load ]:
                self.setIdle()   # if we are loading we interrupt
            elif self.status == self.StatusOptions.Check:
                self.setTrapped()
                self.setFrozen()
            elif self.status in [self.StatusOptions.Trapped, self.StatusOptions.Disappeared ]:
                self.setFrozen()
        else:
            if self.status == self.StatusOptions.Frozen:
                self.setTrapped(True)

