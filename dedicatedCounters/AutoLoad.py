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

from PyQt4 import QtCore, QtNetwork, QtGui
import PyQt4.uic

from dedicatedCounters.LoadingHistoryModel import LoadingHistoryModel
from dedicatedCounters.WavemeterInterlockTableModel import WavemeterInterlockTableModel
from modules.SequenceDict import SequenceDict
from modules.Utility import unique
from modules.formatDelta import formatDelta
from modules.magnitude import Magnitude, mg
from uiModules.KeyboardFilter import KeyFilter
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.mymath import max_iterable
from modules.statemachine import Statemachine

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
        self.ovenChannelActiveLow = False
        self.shutterChannelActiveLow = False
        self.autoReload = False
        self.waitForComebackTime =  mg( 60, 's' )
        self.minLaserScatter = mg( 0.1, 'kHz' )
        self.maxFailedAutoload = 0
        self.postSequenceWaitTime = mg( 5, 's' )
        self.loadAlgorithm = 0
        self.shuttleLoadTime = mg( 500, 'ms')
        self.shuttleCheckTime = mg( 1, 's')

    def __setstate__(self, state):
        """this function ensures that the given fields are present in the class object
        after unpickling. Only new class attributes need to be added here.
        """
        self.__dict__ = state
        self.__dict__.setdefault( 'ovenChannelActiveLow', False)
        self.__dict__.setdefault( 'shutterChannelActiveLow', False )
        self.__dict__.setdefault( 'autoReload', False )
        self.__dict__.setdefault( 'waitForComebackTime', mg( 60, 's' ) )
        self.__dict__.setdefault( 'minLaserScatter', mg( 0.1, 'kHz' ) )
        self.__dict__.setdefault( 'maxFailedAutoload', 0 )
        self.__dict__.setdefault( 'postSequenceWaitTime', mg( 5, 's' ) )
        self.__dict__.setdefault( 'loadAlgorithm', 0 )
        self.__dict__.setdefault( 'shuttleLoadTime', mg( 500, 'ms') )
        self.__dict__.setdefault( 'shuttleCheckTime', mg( 1, 's') )

def invertIf( logic, invert ):
    """ returns logic for positive channel number, inverted for negative channel number """
    return (not logic if invert else logic)

class LoadingEvent:
    def __init__(self,loading=None,trappedAt=None):
        self.loadingTime = loading
        self.trappedAt = trappedAt
        self.trappingTime = None

class AutoLoad(UiForm,UiBase):
    ionReappeared = QtCore.pyqtSignal()
    def __init__(self, config, pulser, dataAvailableSignal, parent=None):
        UiBase.__init__(self,parent)
        UiForm.__init__(self)
        self.config = config
        self.settings = self.config.get('AutoLoad.Settings',AutoLoadSettings())
        self.loadingHistory = self.config.get('AutoLoad.History',list())
        self.timer = None
        self.pulser = pulser
        self.dataSignalConnected = False
        self.outOfRangeCount=0
        self.dataSignal = dataAvailableSignal
        self.numFailedAutoload = 0
        self.constructStatemachine()
        self.timerNullTime = datetime.now()
        self.trappingTime = None
        self.voltageControl = None
        
    def constructStatemachine(self):
        self.statemachine = Statemachine('AutoLoad')
        self.statemachine.addState( 'Idle' , self.setIdle, self.exitIdle )
        self.statemachine.addState( 'Preheat', self.setPreheat )
        self.statemachine.addState( 'Load', self.setLoad )
        self.statemachine.addState( 'Check', self.setCheck )
        self.statemachine.addState( 'Trapped', self.setTrapped, self.exitTrapped )
        self.statemachine.addState( 'Disappeared', self.setDisappeared )
        self.statemachine.addState( 'Frozen', self.setFrozen )
        self.statemachine.addState( 'WaitingForComeback', self.setWaitingForComeback )
        self.statemachine.addState( 'AutoReloadFailed', self.setAutoReloadFailed )
        self.statemachine.addState( 'CoolingOven', self.setCoolingOven )
        self.statemachine.addState( 'PostSequenceWait', self.setPostSequenceWait )
        self.statemachine.addState( 'ShuttleLoad', self.setShuttleLoad, self.exitShuttleLoad )
        self.statemachine.addState( 'ShuttleCheck' , self.setShuttleCheck )

        self.statemachine.addTransition( 'timer', 'Preheat', 'Load', 
                                         lambda state: state.timeInState() > self.settings.laserDelay and
                                                       self.settings.loadAlgorithm==0, description="laserDelay" )
        self.statemachine.addTransition( 'timer', 'Preheat', 'ShuttleLoad', 
                                         lambda state: state.timeInState() > self.settings.laserDelay and
                                                       self.settings.loadAlgorithm==1, description='laserDelay' )
        self.statemachine.addTransition( 'timer', 'ShuttleLoad', 'ShuttleCheck', 
                                         lambda state: state.timeInState() > self.settings.shuttleLoadTime,
                                         description="shuttleLoadTime" )
        self.statemachine.addTransition( 'timer', 'ShuttleCheck', 'ShuttleLoad', 
                                         lambda state: state.timeInState() > self.settings.shuttleCheckTime,
                                         description="shuttleCheckTime" )
        self.statemachine.addTransition( 'timer', 'ShuttleCheck', 'AutoReloadFailed', 
                                         lambda state: self.statemachine.states['Preheat'].timeInState() > self.settings.maxTime and 
                                                       self.settings.autoReload and 
                                                       self.numFailedAutoload>=self.settings.maxFailedAutoload,
                                         description="maxTime" ) 
        self.statemachine.addTransition( 'timer', 'ShuttleCheck', 'CoolingOven',
                                         lambda state: self.statemachine.states['Preheat'].timeInState() > self.settings.maxTime and
                                                       self.settings.autoReload and
                                                       self.numFailedAutoload<self.settings.maxFailedAutoload,
                                         description="maxTime" )                                         
        self.statemachine.addTransition( 'timer', 'ShuttleCheck', 'Idle',
                                         lambda state: self.statemachine.states['Preheat'].timeInState() > self.settings.maxTime and
                                                       not self.settings.autoReload,
                                         description="maxTime"  )                                         
        self.statemachine.addTransition( 'timer', 'Check', 'Trapped',
                                         lambda state: state.timeInState() > self.settings.checkTime,
                                         self.loadingToTrapped,
                                         description="checkTime" )
        self.statemachine.addTransition( 'timer', 'Load', 'AutoReloadFailed', 
                                         lambda state: state.timeInState() > self.settings.maxTime and 
                                                       self.settings.autoReload and 
                                                       self.numFailedAutoload>=self.settings.maxFailedAutoload,
                                         description="maxTime" ) 
        self.statemachine.addTransition( 'timer', 'Load', 'CoolingOven',
                                         lambda state: state.timeInState() > self.settings.maxTime and
                                                       self.settings.autoReload and
                                                       self.numFailedAutoload<self.settings.maxFailedAutoload,
                                         description="maxTime"  )                                         
        self.statemachine.addTransition( 'timer', 'Load', 'Idle',
                                         lambda state: state.timeInState() > self.settings.maxTime and 
                                                       not self.settings.autoReload,
                                         description="maxTime" )
        self.statemachine.addTransition( 'timer', 'Disappeared', 'WaitingForComeback',
                                         lambda state: state.timeInState() > self.settings.checkTime,
                                         description="checkTime" )
        self.statemachine.addTransition( 'timer', 'WaitingForComeback', 'Preheat',
                                         lambda state: state.timeInState() > self.settings.waitForComebackTime and
                                                       self.settings.autoReload and 
                                                       self.numFailedAutoload<=self.settings.maxFailedAutoload,
                                         description="waitForComebackTime")                                         
        self.statemachine.addTransition( 'timer', 'WaitingForComeback', 'Idle',
                                         lambda state: state.timeInState() > self.settings.waitForComebackTime,
                                         description="waitForComebackTime")                                         
        self.statemachine.addTransition( 'timer', 'CoolingOven', 'Preheat',
                                        lambda state: state.timeInState() > self.settings.waitForComebackTime and
                                                      self.settings.autoReload,
                                         description="waitForComebackTime" )
        self.statemachine.addTransition( 'data', 'PostSequenceWait', 'Trapped', 
                                         lambda state, data: state.timeInState() > self.settings.postSequenceWaitTime and
                                                             data.data[self.settings.counterChannel]/data.integrationTime >= self.settings.thresholdBare,
                                         description="postSequenceWaitTime" )
        self.statemachine.addTransition( 'data', 'PostSequenceWait', 'Disappeared', 
                                         lambda state, data: state.timeInState() > self.settings.postSequenceWaitTime and
                                                             data.data[self.settings.counterChannel]/data.integrationTime < self.settings.thresholdBare,
                                         description="postSequenceWaitTime" )
        self.statemachine.addTransition( 'data', 'Load', 'Check', lambda state, data: data.data[self.settings.counterChannel]/data.integrationTime > self.settings.thresholdOven,
                                         description="thresholdOven"  )
        self.statemachine.addTransition( 'data', 'Check', 'Load', lambda state, data: data.data[self.settings.counterChannel]/data.integrationTime < self.settings.thresholdBare,
                                         description="thresholdBare"  )
        self.statemachine.addTransition( 'data', 'Trapped', 'Disappeared', lambda state, data: data.data[self.settings.counterChannel]/data.integrationTime < self.settings.thresholdBare,
                                         description="thresholdBare" )
        self.statemachine.addTransition( 'data', 'Disappeared', 'Trapped', lambda state, data: data.data[self.settings.counterChannel]/data.integrationTime > self.settings.thresholdBare,
                                         description="thresholdBare" )
        self.statemachine.addTransition( 'data', 'WaitingForComeback', 'Trapped', lambda state, data: data.data[self.settings.counterChannel]/data.integrationTime > self.settings.thresholdBare,
                                         description="thresholdBare" )
        self.statemachine.addTransition( 'data', 'ShuttleCheck', 'Trapped', lambda state, data: data.data[self.settings.counterChannel]/data.integrationTime > self.settings.thresholdOven,
                                         self.loadingToTrapped,
                                         description="thresholdOven" )
        self.statemachine.addTransitionList( 'stopButton', ['Preheat','Load','Check','Trapped','Disappeared', 'Frozen', 'WaitingForComeback', 'AutoReloadFailed', 'CoolingOven', 'ShuttleCheck', 'ShuttleLoad'], 'Idle',
                                         description="stopButton" )
        self.statemachine.addTransitionList( 'startButton', ['Idle', 'AutoReloadFailed'], 'Preheat',
                                         description="startButton" )
        self.statemachine.addTransitionList( 'ppStarted', ['Trapped','PostSequenceWait','WaitingForComeback','Disappeared','Check'], 'Frozen',
                                         description="ppStarted"  )
        self.statemachine.addTransition( 'ppStopped', 'Frozen', 'PostSequenceWait' ,
                                         description="ppStopped" )
        self.statemachine.addTransitionList( 'outOfLock', ['Preheat', 'Load', 'ShuttleLoad', 'ShuttleCheck'], 'Idle',
                                         description="outOfLock"  )
        self.statemachine.addTransition( 'ionStillTrapped', 'Idle', 'Trapped', lambda state: len(self.historyTableModel.history)>0 and not self.pulser.ppActive ,
                                         description="ionStillTrapped" )
        self.statemachine.addTransition( 'ionStillTrapped', 'Idle', 'Frozen', lambda state: len(self.historyTableModel.history)>0 and self.pulser.ppActive ,
                                         description="ionStillTrapped" )
        self.statemachine.addTransition( 'ionTrapped', 'Idle', 'Trapped',
                                         transitionfunc = self.loadingToTrapped,
                                         description="ionTrapped"  )
        
    def initMagnitude(self, ui, settingsname, dimension=None  ):
        ui.setValue( getattr( self.settings, settingsname  ) )
        ui.valueChanged.connect( functools.partial( self.onValueChanged, settingsname ) )
        if dimension:
            ui.dimension = dimension     
    
    def initCheckBox(self, ui, settingsname):
        ui.setChecked( getattr( self.settings, settingsname  ) )
        ui.stateChanged.connect( functools.partial( self.onStateChanged, settingsname ) )
    
    def setupUi(self,widget):
        UiForm.setupUi(self,widget)
        #Set the GUI values from the settings stored in the config files, and
        #connect the valueChanged events of each button to the appropriate method
        self.initMagnitude( self.counterChannelBox, 'counterChannel' )
        self.initMagnitude( self.shutterChannelBox, 'shutterChannel' )
        self.initMagnitude( self.ovenChannelBox, 'ovenChannel' )
        self.initCheckBox( self.ovenChannelActiveLowBox, 'ovenChannelActiveLow') 
        self.initCheckBox( self.shutterChannelActiveLowBox, 'shutterChannelActiveLow') 
        self.initMagnitude( self.laserDelayBox, 'laserDelay', Magnitude(1,s=1) )
        self.initMagnitude( self.maxTimeBox, 'maxTime', Magnitude(1,s=1) )
        self.initMagnitude( self.thresholdBareBox, 'thresholdBare', Magnitude(1,s=-1) )
        self.initMagnitude( self.thresholdOvenBox, 'thresholdOven', Magnitude(1,s=-1) )
        self.initMagnitude( self.checkTimeBox, 'checkTime', Magnitude(1,s=1) )
        self.initCheckBox( self.autoReloadBox, 'autoReload') 
        self.initMagnitude( self.minLaserScatterBox, 'minLaserScatter', Magnitude(1,s=-1) )
        self.initMagnitude( self.waitForComebackBox, 'waitForComebackTime', Magnitude(1,s=1) )
        self.initMagnitude( self.maxFailedAutoloadBox, 'maxFailedAutoload' )
        self.initMagnitude( self.postSequenceWaitTimeBox, 'postSequenceWaitTime' )
        self.initMagnitude( self.shuttleLoadTimeBox, 'shuttleLoadTime',  Magnitude(1,s=1) )
        self.initMagnitude( self.shuttleCheckTimeBox, 'shuttleCheckTime',  Magnitude(1,s=1) )
       
        self.loadAlgorithmBox.addItems( ['Static','Shuttling'])
        self.loadAlgorithmBox.setCurrentIndex( self.settings.loadAlgorithm )
        self.loadAlgorithmBox.currentIndexChanged[int].connect( self.onLoadAlgorithmChanged )
       
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
        self.delegate = MagnitudeSpinBoxDelegate()
        self.interlockTableView.setItemDelegateForColumn(3, self.delegate ) 
        self.interlockTableView.setItemDelegateForColumn(4, self.delegate ) 
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
        self.pulser.ppActiveChanged.connect( self.setDisabled )
        self.statemachine.initialize( 'Idle' )
        
        # Actions
        self.createAction("Last ion is still trapped", self.onIonIsStillTrapped )
        self.createAction("Trapped an ion now", self.onTrappedIonNow )
        self.autoLoadTab.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        
    def setVoltageControl(self, voltageControl ):
        self.voltageControl = voltageControl
        
    def createAction(self, text, slot ):
        action = QtGui.QAction( text, self )
        action.triggered.connect( slot )
        self.autoLoadTab.addAction( action )
        
    def deleteFromHistory(self):
        for row in sorted(unique([ i.row() for i in self.historyTableView.selectedIndexes() ]),reverse=False):
            self.historyTableModel.removeRow(row)
        
    def onRemoveChannel(self):
        for index in sorted(unique([ i.row() for i in self.interlockTableView.selectedIndexes() ]),reverse=True):
            self.tableModel.removeChannel(index)
            
    def onStateChanged(self, name, state):
        setattr( self.settings, name, state==QtCore.Qt.Checked )
        
    def onWavemeterAddress(self):
        value = str(self.wavemeterAddressLineEdit.text())
        self.settings.wavemeterAddress = value if value.find("http://")==0 else "http://" +value
        self.wavemeterAddressLineEdit.setText(self.settings.wavemeterAddress)
        
    def onUseInterlockClicked(self):
        """Run if useInterlock button is clicked. Change settings to match."""
        self.settings.useInterlock = self.useInterlockGui.isChecked()

    def onWavemeterError(self, channel, reply, error):
        """Print out received error"""
        logging.getLogger(__name__).error( "Error {0} accessing wavemeter at '{1}'".format(error, self.settings.wavemeterAddress) )
        reply.finished.disconnect()  # necessary to make reply garbage collectable
        reply.error.disconnect()

    def getWavemeterData(self, channel):
        """Get the data from the wavemeter at the specified channel."""
        if channel in self.settings.interlock:
            if self.settings.interlock[channel].enable:
                address = self.settings.wavemeterAddress + "/wavemeter/wavemeter/wavemeter-status?channel={0}".format(int(channel))
                reply = self.am.get( QtNetwork.QNetworkRequest(QtCore.QUrl(address)))
                reply.error.connect(functools.partial(self.onWavemeterError, int(channel),  reply) )
                reply.finished.connect(functools.partial(self.onWavemeterData, int(channel), reply))
            else:
                self.checkFreqsInRange()

    def onWavemeterData(self, channel, reply):
        """Execute when reply is received from the wavemeter. Display it on the
           GUI, and check whether it is in range."""
        if channel in self.settings.interlock:
            ilChannel = self.settings.interlock[channel]
            if reply.error()==0:
                value = float(reply.readAll())
                self.tableModel.setCurrent( channel, round(value, 4) )
                if ilChannel.lastReading==value:
                    ilChannel.identicalCount += 1
                else:
                    ilChannel.identicalCount = 0 
                ilChannel.lastReading = value
            #freq_string = "{0:.4f}".format(self.channelResult[channel]) + " GHz"
        #read the wavemeter channel once per second
            if ilChannel.enable:
                QtCore.QTimer.singleShot(1000,functools.partial(self.getWavemeterData, channel))
        self.checkFreqsInRange()
        reply.finished.disconnect()  # necessary to make reply garbage collectable
        reply.error.disconnect()
        
    def checkFreqsInRange(self):
        """Check whether all laser frequencies being used by the interlock are in range.
        
            If they are not, loading is stopped/prevented, and the lock status bar turns
            from green to red. If the lock is not being used, the status bar is black."""
        enabledChannels = sum(1 if x.enable else 0 for x in self.settings.interlock.values() )
        outOfRangeChannels = sum(1 if x.enable and not x.inRange else 0 for x in self.settings.interlock.values() )
        maxIdenticalReading = max_iterable(x.identicalCount if x.enable else 0 for x in self.settings.interlock.values() ) 
        if enabledChannels==0:
            #if no channels are checked, set bar on GUI to black
            self.allFreqsInRange.setStyleSheet("QLabel {background-color: rgb(0, 0, 0)}")
            self.allFreqsInRange.setToolTip("No channels are selected")
            self.outOfRangeCount = 0
        elif outOfRangeChannels==0:
            if maxIdenticalReading is None or maxIdenticalReading<10:
                #if all channels are in range, set bar on GUI to green
                self.allFreqsInRange.setStyleSheet("QLabel {background-color: rgb(0, 198, 0)}")
                self.allFreqsInRange.setToolTip("All laser frequencies are in range")
                self.outOfRangeCount = 0
            else:
                self.allFreqsInRange.setStyleSheet("QLabel {background-color: rgb(198, 198, 0)}")
                self.allFreqsInRange.setToolTip("All laser frequencies seem in range but some readings are struck")
                self.outOfRangeCount += 1             
        else:
            #Because of the bug where the wavemeter reads incorrectly after calibration,
            #Loading is only inhibited after 10 consecutive bad measurements
            if self.outOfRangeCount < 20 and self.settings.useInterlock: #Count how many times the frequency measures out of range. Stop counting at 20. (why count forever?)
                self.outOfRangeCount += 1
#                 self.allFreqsInRange.setStyleSheet("QLabel {background-color: rgb(255, 255, 0)}")
#                 self.allFreqsInRange.setToolTip("There are laser frequencies temporarily of range")
            if (self.outOfRangeCount >= 10):
                #set bar on GUI to red
                self.allFreqsInRange.setStyleSheet("QLabel {background-color: rgb(255, 0, 0)}")
                self.allFreqsInRange.setToolTip("There are laser frequencies out of range")
                #This is the interlock: loading is inhibited if frequencies are out of range
                self.statemachine.processEvent( 'outOfLock' )
        
    def onValueChanged(self,attr,value):
        """Change the value of attr in settings to value"""
        setattr( self.settings, attr, value)
        
    def onArrayValueChanged(self, index, attr, value):
        """Change the value of attr[index] in settings to value"""
        a = getattr(self.settings, attr)
        a[index] = value
        
    def onStart(self):
        """Execute when start button is clicked. Begin loading if idle."""
        if self.statemachine.processEvent( 'startButton' ) == 'Preheat':
            self.numFailedAutoload = 0

    def onStop(self):
        """Execute when stop button is clicked. Stop loading."""
        self.statemachine.processEvent( 'stopButton' )

    def setIdle(self):
        """Execute when the loading process is set to idle. Disable timer, do not
           pay attention to the count rate, and turn off the ionization laser and oven."""
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        self.timer = None
        self.elapsedLabel.setStyleSheet("QLabel { color:black; }")
        self.statusLabel.setText("Idle")
        self.disconnectDataSignal()
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invertIf(False,self.settings.ovenChannelActiveLow) )
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invertIf(False,self.settings.shutterChannelActiveLow ))
    
    def exitIdle(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect( self.onTimer )
        self.timer.start(100)
        self.connectDataSignal()
        self.timerNullTime = datetime.now()
    
    def setPreheat(self):
        """Execute when the loading process begins. Turn on timer, turn on oven."""
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        self.elapsedLabel.setStyleSheet("QLabel { color:red; }")
        self.statusLabel.setText("Preheating")
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invertIf(True,self.settings.ovenChannelActiveLow) )
        self.timerNullTime = datetime.now()
    
    def setLoad(self):
        """Execute after preheating. Turn on ionization laser, and begin
           monitoring count rate."""
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        self.elapsedLabel.setStyleSheet("QLabel { color:purple; }")
        self.statusLabel.setText("Loading")
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invertIf(True,self.settings.shutterChannelActiveLow) )
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invertIf(True,self.settings.ovenChannelActiveLow) )
    
    def setCheck(self):
        """Execute when count rate goes over threshold."""
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        self.elapsedLabel.setStyleSheet("QLabel { color:blue; }")
        self.checkStarted = datetime.now()
        self.statusLabel.setText("Checking for ion")
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invertIf(False,self.settings.shutterChannelActiveLow) )
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invertIf(False,self.settings.ovenChannelActiveLow) )

    def setShuttleLoad(self):
        """Execute after preheating. Turn on ionization laser, and begin
           monitoring count rate."""
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        self.elapsedLabel.setStyleSheet("QLabel { color:purple; }")
        self.statusLabel.setText("Shuttle Loading")
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invertIf(True,self.settings.shutterChannelActiveLow) )
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invertIf(True,self.settings.ovenChannelActiveLow) )
        if self.voltageControl:
            self.voltageControl.onShuttleSequence()

    def exitShuttleLoad(self):
        if self.voltageControl:
            self.voltageControl.onShuttleSequence()
           
    def setShuttleCheck(self):
        """Execute when count rate goes over threshold."""
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        self.elapsedLabel.setStyleSheet("QLabel { color:blue; }")
        self.checkStarted = datetime.now()
        self.statusLabel.setText("Shuttle Checking for ion")
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invertIf(True,self.settings.shutterChannelActiveLow) )
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invertIf(True,self.settings.ovenChannelActiveLow) )
        
    def setPostSequenceWait(self):
        self.statusLabel.setText("Waiting after sequence finished.")
        
    def loadingToTrapped(self, check, trapped):
        logger = logging.getLogger(__name__)
        logger.info(  "Loading Trapped" )
        self.loadingTime = check.enterTime - self.timerNullTime
        self.historyTableModel.append( LoadingEvent(self.loadingTime,self.checkStarted) )
           
    def setTrapped(self):
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        self.elapsedLabel.setStyleSheet("QLabel { color:green; }")
        self.statusLabel.setText("Trapped :)")       
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invertIf(False,self.settings.ovenChannelActiveLow) )
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invertIf(False,self.settings.shutterChannelActiveLow) )
        self.numFailedAutoload = 0
        self.trappingTime = self.loadingHistory[-1].trappedAt
        self.timerNullTime = self.trappingTime
        self.ionReappeared.emit()        
    
    def exitTrapped(self):
        self.historyTableModel.updateLast('trappingTime',datetime.now()-self.trappingTime)
    
    def setFrozen(self):
        self.startButton.setEnabled( False )
        self.stopButton.setEnabled( False )       
        self.elapsedLabel.setStyleSheet("QLabel { color:grey; }")
        self.statusLabel.setText("Currently running pulse program")       
    
    def setDisappeared(self):
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        self.statusLabel.setText("Disappeared :(")

    def setWaitingForComeback(self):
        self.statusLabel.setText("Waiting to see if ion comes back")
        self.timerNullTime = datetime.now()
    
    def setCoolingOven(self):
        self.statusLabel.setText("Cooling Oven")
        self.timerNullTime = datetime.now()
        self.numFailedAutoload += 1
    
    def setAutoReloadFailed(self):
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        self.timer = None
        self.elapsedLabel.setStyleSheet("QLabel { color:black; }")
        self.statusLabel.setText("Auto reload failed")
        self.disconnectDataSignal()
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invertIf(False,self.settings.ovenChannelActiveLow) )
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invertIf(False,self.settings.shutterChannelActiveLow ))
        
    def onIonIsStillTrapped(self):
        self.statemachine.processEvent( 'ionStillTrapped' )
        
    def onTrappedIonNow(self):
        self.trappingTime = datetime.now()
        self.statemachine.processEvent('ionTrapped')           
    
    def onTimer(self):
        """Execute whenever the timer sends a timeout signal, which is every 100 ms.
           Trigger status changes based on elapsed time. This controls the flow
           of the loading process."""
        self.elapsed = datetime.now()-self.timerNullTime
        self.elapsedLabel.setText(formatDelta(self.elapsed) )
        self.statemachine.processEvent( 'timer' )
    
    def onData(self, data ):
        """Execute when count rate data is received. Change state based on count rate."""
        self.statemachine.processEvent( 'data', data )
    
    def onClose(self):
        self.statemachine.processEvent( 'stopButton' )
            
    def saveConfig(self):
        self.config['AutoLoad.Settings'] = self.settings
        self.config['AutoLoad.History'] = self.loadingHistory

    def setDisabled(self, disable):
        if disable:
            self.statemachine.processEvent( 'ppStarted' )
        else:
            self.statemachine.processEvent( 'ppStopped' )
            
    def connectDataSignal(self):
        self.dataSignal.connect( self.onData, QtCore.Qt.UniqueConnection )
        self.dataSignalConnected = True
    
    def disconnectDataSignal(self):
        if self.dataSignalConnected:
            self.dataSignal.disconnect( self.onData )
            self.dataSignalConnected = False
            
    def onLoadAlgorithmChanged(self, number):
        self.settings.loadAlgorithm = number
