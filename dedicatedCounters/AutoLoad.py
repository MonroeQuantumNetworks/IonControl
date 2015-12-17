# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 23:45:54 2013

@author: pmaunz

This is the GUI for the autoload program. Includes start/stop button for loading,
a record of all loads, and an interlock to the laser frequencies returned by
the wavemeter.
"""

from datetime import datetime, timedelta
import functools
import logging

from PyQt4 import QtCore, QtNetwork, QtGui
import PyQt4.uic

from dedicatedCounters.LoadingHistoryModel import LoadingHistoryModel
from dedicatedCounters.WavemeterInterlockTableModel import WavemeterInterlockTableModel
from modules.SequenceDict import SequenceDict
from modules.Utility import unique
from modules.formatDelta import formatDelta
from modules.magnitude import mg
from uiModules.KeyboardFilter import KeyFilter
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.mymath import max_iterable
from modules.statemachine import Statemachine, timedeltaToMagnitude
from gui.TodoListSettingsTableModel import TodoListSettingsTableModel
from uiModules.ComboBoxDelegate import ComboBoxDelegate
from pyqtgraph.parametertree.Parameter import Parameter
from modules.GuiAppearance import restoreGuiState, saveGuiState #@UnresolvedImport
import copy
from modules.PyqtUtility import updateComboBoxItems
from persist.LoadingEvent import LoadingEvent, LoadingHistory
from modules.firstNotNone import firstNotNone

import os
uipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\AutoLoad.ui')
UiForm, UiBase = PyQt4.uic.loadUiType(uipath)

import pytz
def now():
    return datetime.now(pytz.utc)


class AutoLoadSettings(object):
    def __init__(self):
        self.globalDict = None
        self.counterChannel = 0
        self.shutterChannel = 0
        self.shutterChannel2 = 0
        self.ovenChannel = 0
        self.laserDelay = mg(5,'s')
        self.maxTime = mg(60,'s')
        self.thresholdBare = mg(10,'kHz')
        self.thresholdOven = mg(0,'kHz')
        self.checkTime = mg(10, 's')
        self.useInterlock = False
        self.interlock = SequenceDict()
        self.wavemeterAddress = ""
        self.ovenChannelActiveLow = False
        self.shutterChannelActiveLow = False
        self.shutterChannelActiveLow2 = False
        self.autoReload = False
        self.waitForComebackTime =  mg( 60, 's' )
        self.minLaserScatter = mg( 0.1, 'kHz' )
        self.maxFailedAutoload = 0
        self.postSequenceWaitTime = mg( 5, 's' )
        self.loadAlgorithm = 0
        self.shuttleLoadTime = mg( 500, 'ms')
        self.shuttleCheckTime = mg( 1, 's')
        self.ovenCoolingTime = mg( 80, 's' )
        self.thresholdRunning = mg(5, 'kHz')
        self.globalsAdjustList = SequenceDict()
        self.historyLength = mg(7, 'day')
        self.loadingVoltageNode = ""
        self.shuttlingNodes = list()
        self.instantToLoading = False
        self.beyondThresholdLimit = mg( 100, 'kHz')
        self.beyondThresholdTime = mg(3, 's')
        self.resetField = None
        self.resetValue = mg(0)

    def paramDef(self):
        """
        return the parameter definition used by pyqtgraph parametertree to show the gui
        """
        return [{'name': 'Oven background', 'type': 'magnitude', 'value': self.thresholdOven, 'tip': "background counts added by oven (frequency)", 'field': 'thresholdOven', 'dimension': 'Hz' },
                {'name': 'Threshold during loading', 'type': 'magnitude', 'value': self.thresholdBare, 'tip': "presence threshold during loading (frequency)", 'field': 'thresholdBare' , 'dimension': 'Hz'},
                {'name': 'Threshold while running', 'type': 'magnitude', 'value': self.thresholdRunning, 'tip': "presence threshold during normal operation (frequency)", 'field': 'thresholdRunning', 'dimension': 'Hz'},
                {'name': 'Beyond threshold limit', 'type':'magnitude', 'value': self.beyondThresholdLimit, 'tip': 'Beyond this rate we loaded more ions than intended', 'field':'beyondThresholdLimit' },
                {'name': 'Check time', 'type': 'magnitude', 'value': self.checkTime, 'tip': "Time ions need to be present before switching to trapped", 'field': 'checkTime', 'dimension': 's'},
                {'name': 'Beyond threshold time', 'type': 'magnitude', 'value': self.beyondThresholdTime, 'tip': "Time in the state BeyondThreshold to reset (kick out) the ions", 'field': 'beyondThresholdTime', 'dimension': 's'},
                {'name': 'Max time', 'type': 'magnitude', 'value': self.maxTime, 'tip': "Maximum time oven is on during one attempt", 'field': 'maxTime', 'dimension': 's'},
                {'name': 'Laser delay', 'type': 'magnitude', 'value': self.laserDelay, 'tip': "delay after which ionization laser is switched on", 'field': 'laserDelay', 'dimension': 's'},
                {'name': 'Wait for comeback', 'type': 'magnitude', 'value': self.waitForComebackTime, 'tip': "time to wait for re-appearance of an ion after it is lost", 'field': 'waitForComebackTime', 'dimension': 's'},
                {'name': 'Post sequence wait', 'type': 'magnitude', 'value': self.postSequenceWaitTime, 'tip': "wait time after running sequence is finished", 'field': 'postSequenceWaitTime', 'dimension': 's'},
                {'name': 'Oven cooling time', 'type': 'magnitude', 'value': self.ovenCoolingTime, 'tip': "time between load attemps in autoloading", 'field': 'ovenCoolingTime', 'dimension': 's'},
                {'name': 'Max failed autoload', 'type': 'magnitude', 'value': self.maxFailedAutoload, 'tip': "maximum number of consecutive failed loading attempts", 'field': 'maxFailedAutoload'},
                {'name': 'Oven shutter', 'type': 'int', 'value': self.ovenChannel, 'tip': "Shutter channel controlling the oven", 'field': 'ovenChannel'},
                {'name': 'Oven active low', 'type': 'bool', 'value': self.ovenChannelActiveLow, 'tip': "True means oven channel is active low", 'field': 'ovenChannelActiveLow'},
                {'name': 'Ionization shutter', 'type': 'int', 'value': self.shutterChannel, 'tip': "Shutter channel controlling the ionization laser", 'field': 'shutterChannel'},
                {'name': 'Ionization active low', 'type': 'bool', 'value': self.shutterChannelActiveLow, 'tip': "Ionization shutter is active low", 'field': 'shutterChannelActiveLow'},
                {'name': 'Ionization shutter 2', 'type': 'int', 'value': self.shutterChannel2, 'tip': "Shutter channel controlling the second ionization laser", 'field': 'shutterChannel2'},
                {'name': 'Ionization active low 2', 'type': 'bool', 'value': self.shutterChannelActiveLow2, 'tip': "Ionization 2 shutter is active low", 'field': 'shutterChannelActiveLow2'},
                {'name': 'Counter channel', 'type': 'int', 'value': self.counterChannel, 'tip': "Counter channel", 'field': 'counterChannel'},
                {'name': 'Reset global name', 'type':'list', 'values': sorted(self.globalDict.keys()), 'value': self.resetField, 'tip': 'Beyond threshold sets this global to the value Reset global value', 'field':'resetField' },
                {'name': 'Reset global value', 'type':'magnitude', 'value': self.resetValue, 'tip': 'Beyond threshold sets the global "Reset global name" to this value during reset', 'field':'resetValue' },
                {'name': 'Wavemeter address', 'type': 'str', 'value': self.wavemeterAddress, 'tip': "Address of wavemeter interface (http://)", 'field': 'wavemeterAddress'},
                {'name': 'History timespan', 'type': 'magnitude', 'value': self.historyLength, 'tip': "Time range to display loading history", 'field': 'historyLength'},
                {'name': 'Loading shuttle instantly', 'type':'bool', 'value': self.instantToLoading, 'tip': 'When shuttling to loading, move there instantly instead of shuttling properly', 'field':'instantToLoading' },
                {'name': 'Loading Voltage node', 'type':'list', 'values': self.shuttlingNodes, 'value': self.loadingVoltageNode, 'tip': 'Shuttle to this node for loading', 'field':'loadingVoltageNode' }]
        
    def update(self, param, changes):
        """
        update the parameter, called by the signal of pyqtgraph parametertree
        """
        logger = logging.getLogger(__name__)
        logger.debug( "ExternalParameterBase.update" )
        for param, change, data in changes:
            if change=='value':
                logger.debug( " ".join( [str(self), "update", param.name(), str(data)] ) )
                setattr( self, param.opts['field'], data)
            elif change=='activated':
                getattr( self, param.opts['field'] )()

    def __setstate__(self, state):
        """this function ensures that the given fields are present in the class object
        after unpickling. Only new class attributes need to be added here.
        """
        self.__dict__ = state
        self.globalDict = None
        self.__dict__.setdefault( 'ovenChannelActiveLow', False)
        self.__dict__.setdefault( 'shutterChannelActiveLow', False )
        self.__dict__.setdefault( 'shutterChannel2', False )
        self.__dict__.setdefault( 'shutterChannelActiveLow2', False )
        self.__dict__.setdefault( 'autoReload', False )
        self.__dict__.setdefault( 'waitForComebackTime', mg( 60, 's' ) )
        self.__dict__.setdefault( 'minLaserScatter', mg( 0.1, 'kHz' ) )
        self.__dict__.setdefault( 'maxFailedAutoload', 0 )
        self.__dict__.setdefault( 'postSequenceWaitTime', mg( 5, 's' ) )
        self.__dict__.setdefault( 'loadAlgorithm', 0 )
        self.__dict__.setdefault( 'shuttleLoadTime', mg( 500, 'ms') )
        self.__dict__.setdefault( 'shuttleCheckTime', mg( 1, 's') )
        self.__dict__.setdefault( 'ovenCoolingTime', mg( 80, 's') )
        self.__dict__.setdefault( 'thresholdRunning', mg(5, 'kHz'))
        self.__dict__.setdefault( 'globalsAdjustList', SequenceDict() )
        self.__dict__.setdefault( 'historyLength', mg(7,'day') )
        self.__dict__.setdefault( 'loadingVoltageNode', "" )
        self.__dict__.setdefault( 'shuttlingNodes', list())
        self.__dict__.setdefault( 'instantToLoading', False )
        self.__dict__.setdefault( 'beyondThresholdLimit', mg(100, 'kHz'))
        self.__dict__.setdefault( 'beyondThresholdTime', mg(10, 's'))
        self.__dict__.setdefault( 'resetField', None)
        self.__dict__.setdefault( 'resetValue', mg(0))

    stateFields = ['counterChannel', 'shutterChannel', 'shutterChannel2', 'ovenChannel', 'laserDelay', 'maxTime', 'thresholdBare', 'thresholdOven',
                   'checkTime', 'useInterlock', 'interlock', 'wavemeterAddress', 'ovenChannelActiveLow', 'shutterChannelActiveLow', 'shutterChannelActiveLow2',
                   'autoReload', 'waitForComebackTime', 'minLaserScatter', 'maxFailedAutoload', 'postSequenceWaitTime', 'loadAlgorithm',
                   'shuttleLoadTime', 'shuttleCheckTime', 'ovenCoolingTime', 'thresholdRunning', 'globalsAdjustList', 'historyLength', 'loadingVoltageNode', 'shuttlingNodes',
                   'instantToLoading', 'beyondThresholdLimit',
                   'beyondThresholdTime', 'resetField', 'resetValue']
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))

    def __getstate__(self):
        dictcopy = dict(self.__dict__)
        dictcopy.pop('globalDict')
        return dictcopy


def invertIf( logic, invert ):
    """ returns logic for positive channel number, inverted for negative channel number """
    return (not logic if invert else logic)


class Parameters(object):
    def __init__(self):
        self.autoSave = False
        
    def __setstate__(self, state):
        self.__dict__ = state

class AutoLoad(UiForm,UiBase):
    ionReappeared = QtCore.pyqtSignal()
    def __init__(self, config, dbConnection, pulser, dataAvailableSignal, globalVariablesUi, externalInstrumentObservable, parent=None):
        UiBase.__init__(self,parent)
        UiForm.__init__(self)
        self.globalVariablesUi = globalVariablesUi
        self.config = config
        self.parameters = self.config.get('AutoLoad.Parameters', Parameters() )
        self.settings = self.config.get('AutoLoad.Settings',AutoLoadSettings())
        self.settings.globalDict = self.globalVariablesUi.globalDict
        self.settingsDict = self.config.get('AutoLoad.Settings.dict', dict())
        self.currentSettingsName = self.config.get('AutoLoad.SettingsName','')
        self.loadingHistory = LoadingHistory(dbConnection)
        self.loadingHistory.open()
        self.loadingHistory.query( now()-timedelta(seconds=self.settings.historyLength.toval('s')), now()+timedelta(hours=2), self.currentSettingsName )
        self.timer = None
        self.pulser = pulser
        self.dataSignalConnected = False
        self.outOfRangeCount=0
        self.dataSignal = dataAvailableSignal
        self.numFailedAutoload = 0
        self.constructStatemachine()
        self.timerNullTime = now()
        self.trappingTime = None
        self.voltageControl = None
        self.preheatStartTime = now()
        self.globalAdjustRevertList = list()
        self.voltageNodeBeforeLoading = ""
        self.externalInstrumentObservable = externalInstrumentObservable
        
    def constructStatemachine(self):
        self.statemachine = Statemachine('AutoLoad', now=now )
        self.statemachine.addState( 'Idle' , self.setIdle, self.exitIdle )
        self.statemachine.addState( 'AdjustToLoading')
        self.statemachine.addState( 'Preheat', self.setPreheat )
        self.statemachine.addState( 'Load', self.setLoad )
        self.statemachine.addState( 'Check', self.setCheck )
        self.statemachine.addState( 'BeyondThreshold', self.setBeyondThreshold, self.exitBeyondThreshold )
        self.statemachine.addState( 'AdjustFromLoading' )
        self.statemachine.addState( 'Trapped', self.setTrapped, self.exitTrapped )
        self.statemachine.addState( 'Disappeared', self.setDisappeared )
        self.statemachine.addState( 'Frozen', self.setFrozen )
        self.statemachine.addState( 'WaitingForComeback', self.setWaitingForComeback )
        self.statemachine.addState( 'AutoReloadFailed', self.setAutoReloadFailed )
        self.statemachine.addState( 'CoolingOven', self.setCoolingOven )
        self.statemachine.addState( 'PostSequenceWait', self.setPostSequenceWait )
        self.statemachine.addState( 'ShuttleLoad', self.setShuttleLoad, self.exitShuttleLoad )
        self.statemachine.addState( 'ShuttleCheck' , self.setShuttleCheck )
        self.statemachine.addStateGroup('LoadingConfiguration', ['AdjustToLoading','Preheat','Load','Check'], self.adjustToLoading, self.adjustFromLoading)

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
        self.statemachine.addTransition( 'timer', 'Check', 'AdjustFromLoading',
                                         lambda state: state.timeInState() > self.settings.checkTime,
                                         self.loadingToTrapped,
                                         description="checkTime" )
        self.statemachine.addTransition( 'timer', 'Load', 'AutoReloadFailed', 
                                         lambda state: self.ovenLimitReached() and 
                                                       self.settings.autoReload and 
                                                       self.numFailedAutoload>=self.settings.maxFailedAutoload,
                                         description="maxTime" ) 
        self.statemachine.addTransition( 'timer', 'Load', 'CoolingOven',
                                         lambda state: self.ovenLimitReached() and
                                                       self.settings.autoReload and
                                                       self.numFailedAutoload<self.settings.maxFailedAutoload,
                                         description="maxTime"  )                                         
        self.statemachine.addTransition( 'timer', 'Load', 'Idle',
                                         lambda state: self.ovenLimitReached() and 
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
                                        lambda state: state.timeInState() > self.settings.ovenCoolingTime and
                                                      self.settings.autoReload,
                                         description="waitForComebackTime" )
        self.statemachine.addTransition( 'timer', 'BeyondThreshold', 'Load',
                                        lambda state: state.timeInState() > self.settings.beyondThresholdTime,
                                         description="end beyond threshold" )
        self.statemachine.addTransition( 'data', 'PostSequenceWait', 'Trapped',
                                         lambda state, data: state.timeInState() > self.settings.postSequenceWaitTime and
                                                             data.data[self.settings.counterChannel]/data.integrationTime >= self.settings.thresholdRunning,
                                         description="postSequenceWaitTime" )
        self.statemachine.addTransition( 'data', 'PostSequenceWait', 'Disappeared', 
                                         lambda state, data: state.timeInState() > self.settings.postSequenceWaitTime and
                                                             data.data[self.settings.counterChannel]/data.integrationTime < self.settings.thresholdRunning,
                                         description="postSequenceWaitTime" )
        self.statemachine.addTransition( 'data', 'Load', 'Check', lambda state, data: data.data[self.settings.counterChannel]/data.integrationTime > self.settings.thresholdOven+self.settings.thresholdBare,
                                         description="thresholdOven"  )
        self.statemachine.addTransition( 'data', 'Check', 'BeyondThreshold', lambda state, data: state.timeInState() > self.settings.checkTime/2 and
                                                                                                 data.data[self.settings.counterChannel]/data.integrationTime > self.settings.beyondThresholdLimit,
                                         description="too many ions"  )
        self.statemachine.addTransition( 'data', 'Check', 'Load', lambda state, data: data.data[self.settings.counterChannel]/data.integrationTime < self.settings.thresholdOven+self.settings.thresholdBare,
                                         description="thresholdRunning"  )
        self.statemachine.addTransition( 'data', 'Trapped', 'Disappeared', lambda state, data: data.data[self.settings.counterChannel]/data.integrationTime < self.settings.thresholdRunning,
                                         description="thresholdRunning" )
        self.statemachine.addTransition( 'data', 'Disappeared', 'Trapped', lambda state, data: data.data[self.settings.counterChannel]/data.integrationTime > self.settings.thresholdRunning,
                                         description="thresholdRunning" )
        self.statemachine.addTransition( 'data', 'WaitingForComeback', 'Trapped', lambda state, data: data.data[self.settings.counterChannel]/data.integrationTime > self.settings.thresholdRunning,
                                         description="thresholdRunning" )
        self.statemachine.addTransition( 'data', 'ShuttleCheck', 'Trapped', lambda state, data: data.data[self.settings.counterChannel]/data.integrationTime > self.settings.thresholdOven+self.settings.thresholdBare,
                                         self.loadingToTrapped,
                                         description="thresholdOven" )
        self.statemachine.addTransitionList( 'stopButton', ['Preheat','AdjustToLoading','Load','Check','AdjustFromLoading','Trapped','Disappeared', 'Frozen', 'WaitingForComeback', 'AutoReloadFailed', 'CoolingOven', 'ShuttleCheck', 'ShuttleLoad'], 'Idle',
                                         description="stopButton" )
        self.statemachine.addTransitionList( 'startButton', ['Idle', 'AutoReloadFailed'], 'AdjustToLoading',
                                         description="startButton" )
        self.statemachine.addTransitionList( 'ppStarted', ['Trapped','PostSequenceWait','WaitingForComeback','Disappeared','Check'], 'Frozen',
                                         description="ppStarted"  )
        self.statemachine.addTransition( 'ppStopped', 'Frozen', 'PostSequenceWait' ,
                                         description="ppStopped" )
        self.statemachine.addTransition( 'doneAdjusting', 'AdjustToLoading', 'Preheat')
        self.statemachine.addTransition( 'doneAdjusting', 'AdjustFromLoading', 'Trapped')
        self.statemachine.addTransitionList( 'outOfLock', ['Preheat', 'Load', 'ShuttleLoad', 'ShuttleCheck'], 'Idle',
                                         description="outOfLock"  )
        self.statemachine.addTransition( 'ionStillTrapped', 'Idle', 'Trapped', lambda state: len(self.historyTableModel.history)>0 and not self.pulser.ppActive ,
                                         description="ionStillTrapped" )
        self.statemachine.addTransition( 'ionStillTrapped', 'Idle', 'Frozen', lambda state: len(self.historyTableModel.history)>0 and self.pulser.ppActive ,
                                         description="ionStillTrapped" )
        self.statemachine.addTransition( 'ionTrapped', 'Idle', 'Trapped',
                                         transitionfunc = self.idleToTrapped,
                                         description="ionTrapped"  )
        
    def parameter(self):
        # re-create the parameters each time to prevent a exception that says the signal is not connected
        self._parameter = Parameter.create(name='Settings', type='group',children=self.settings.paramDef())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        return self._parameter        
    
    def update(self, *args, **kwargs):
        self.settings.update(*args, **kwargs)
        self.autoSave()
    
    def ovenLimitReached(self):
        return timedeltaToMagnitude(now() - self.preheatStartTime) > self.settings.maxTime
        
        
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
              
        self.startButton.clicked.connect( self.onStart )
        self.stopButton.clicked.connect( self.onStop )
        self.saveProfileButton.clicked.connect( self.onSaveProfile )
        self.removeProfileButton.clicked.connect( self.onRemoveProfile )
        self.initCheckBox(self.autoReloadBox, 'autoReload')
        
        self.historyTableModel = LoadingHistoryModel(self.loadingHistory.loadingEvents )
        self.loadingHistory.beginResetModel.subscribe( self.historyTableModel.beginResetModel )
        self.loadingHistory.endResetModel.subscribe( self.historyTableModel.endResetModel )
        self.loadingHistory.beginInsertRows.subscribe( self.historyTableModel.beginInsertRows )
        self.loadingHistory.endInsertRows.subscribe( self.historyTableModel.endInsertRows )
        self.historyTableView.setModel(self.historyTableModel)
        self.keyFilter = KeyFilter(QtCore.Qt.Key_Delete)
        self.keyFilter.keyPressed.connect( self.deleteFromHistory )
        self.historyTableView.installEventFilter( self.keyFilter )                
                
        #Wavemeter interlock setup        
        self.am = QtNetwork.QNetworkAccessManager()
        self.useInterlockGui.setChecked(self.settings.useInterlock)
        self.useInterlockGui.stateChanged.connect(self.onUseInterlockClicked)
        self.tableModel = WavemeterInterlockTableModel( self.settings.interlock )
        self.tableModel.edited.connect( self.autoSave )
        self.delegate = MagnitudeSpinBoxDelegate()
        self.interlockTableView.setItemDelegateForColumn(3, self.delegate ) 
        self.interlockTableView.setItemDelegateForColumn(4, self.delegate ) 
        self.tableModel.getWavemeterData.connect( self.getWavemeterData )
        self.tableModel.getWavemeterData.connect( self.checkFreqsInRange )
        self.interlockTableView.setModel( self.tableModel )
        self.interlockTableView.resizeColumnsToContents()
        self.interlockTableView.setSortingEnabled(True)
        self.checkFreqsInRange() #Begins the loop which continually checks if frequencies are in range
        for ilChannel in self.settings.interlock.values():
            self.getWavemeterData(ilChannel.channel)
        #end wavemeter interlock setup      
        self.pulser.ppActiveChanged.connect( self.setDisabled )
        self.statemachine.initialize( 'Idle' )
        
        # Settings
        self.globalsAdjustTableModel = TodoListSettingsTableModel( self.settings.globalsAdjustList, self.globalVariablesUi.globalDict )
        self.globalsAdjustTableModel.edited.connect( self.autoSave )
        self.globalsAdjustTableView.setModel( self.globalsAdjustTableModel )
        self.comboBoxDelegate = ComboBoxDelegate()
        self.magnitudeSpinBoxDelegate = MagnitudeSpinBoxDelegate()
        self.globalsAdjustTableView.setItemDelegateForColumn( 0, self.comboBoxDelegate )
        self.globalsAdjustTableView.setItemDelegateForColumn( 1, self.magnitudeSpinBoxDelegate )

        # Actions
        self.createAction("Last ion is still trapped", self.onIonIsStillTrapped )
        self.createAction("Trapped an ion now", self.onTrappedIonNow )
        self.createAction("Add global adjustment", self.globalsAdjustTableModel.addSetting )
        self.createAction("Remove selected global adjustments", self.onRemoveSetting)
        self.createAction("Add wavemeter channel", self.tableModel.addChannel)
        self.createAction("Remove selected wavemeter channels", self.onRemoveChannel)
        self.createAction("auto save profile", self.onAutoSave, checkable=True, checked=self.parameters.autoSave )
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        restoreGuiState( self, self.config.get('AutoLoad.guiState') )
        
        self.profileComboBox.addItems( self.settingsDict.keys() )
        if self.currentSettingsName in self.settingsDict:
            self.profileComboBox.setCurrentIndex( self.profileComboBox.findText(self.currentSettingsName))
        else:
            self.currentSettingsName = str( self.profileComboBox.currentText() )
        self.profileComboBox.currentIndexChanged[QtCore.QString].connect( self.onLoadProfile )
        self.profileComboBox.lineEdit().editingFinished.connect( self.autoSave ) 
        
        self.setProfile( self.currentSettingsName, self.settings )
        self.autoSave()

    def setProfile(self, name, profile):
        self.settings = profile
        self.currentSettingsName = name
        self.parameterWidget.setParameters( self.parameter() )
        self.useInterlockGui.setChecked(self.settings.useInterlock)
        self.autoReloadBox.setChecked(self.settings.autoReload)
        self.loadingHistory.query( now()-timedelta(seconds=self.settings.historyLength.toval('s')), now()+timedelta(hours=2), self.currentSettingsName )
        self.globalsAdjustTableModel.setSettings(self.settings.globalsAdjustList)
        self.tableModel.setChannelDict( self.settings.interlock )

    def onLoadProfile(self, name):
        name = str(name)
        if name in self.settingsDict and name!=self.currentSettingsName:
            self.setProfile( name, copy.deepcopy( self.settingsDict[name] ) )
        
    def onSaveProfile(self):
        name = str(self.profileComboBox.currentText())
        isNew = name not in self.settingsDict
        self.settingsDict[name] = copy.deepcopy( self.settings )
        if isNew:
            updateComboBoxItems( self.profileComboBox, sorted(self.settingsDict.keys()), name)
        self.saveProfileButton.setEnabled( False )
        
    def onRemoveProfile(self):
        name = str(self.profileComboBox.currentText())
        if name in self.settingsDict:
            self.settingsDict.pop(name)
        
    def onAutoSave(self, enable):
        self.parameters.autoSave = enable
    
    def autoSave(self):
        if self.parameters.autoSave:
            self.onSaveProfile()
            self.saveProfileButton.setEnabled( False )
        else:
            self.saveProfileButton.setEnabled( self.saveable() )
    
    def saveable(self):
        name = str(self.profileComboBox.currentText())
        return name != '' and ( name not in self.settingsDict or not (self.settingsDict[name] == self.settings))                    
        
    def onRemoveSetting(self):
        for index in sorted(unique([ i.row() for i in self.globalsAdjustTableView.selectedIndexes() ]),reverse=True):
            self.globalsAdjustTableModel.dropSetting(index)
        self.autoSave()

    def setVoltageControl(self, voltageControl ):
        if voltageControl:
            self.voltageControl = voltageControl
            self.voltageControl.shuttlingNodesObservable().subscribe( self.onShuttlingNodesChanged )
            self.onShuttlingNodesChanged()

    def onShuttlingNodesChanged(self):
        self.settings.shuttlingNodes = [""] + self.voltageControl.shuttlingNodes()
        self.parameterWidget.setParameters( self.parameter() )        
        
    def createAction(self, text, slot, target=None, checkable=False, checked=False ):
        action = QtGui.QAction( text, self )
        action.triggered.connect( slot )
        action.setCheckable(checkable)
        action.setChecked(checked)
        if target is not None:
            target.addAction( action )
        else:
            self.addAction( action )
        
    def deleteFromHistory(self):
        for row in sorted(unique([ i.row() for i in self.historyTableView.selectedIndexes() ]),reverse=False):
            self.historyTableModel.removeRow(row)
        
    def onRemoveChannel(self):
        for index in sorted(unique([ i.row() for i in self.interlockTableView.selectedIndexes() ]),reverse=True):
            self.tableModel.removeChannel(index)
        self.autoSave()
            
    def onStateChanged(self, name, state):
        setattr( self.settings, name, state==QtCore.Qt.Checked )
        self.autoSave()
        
    def onUseInterlockClicked(self):
        """Run if useInterlock button is clicked. Change settings to match."""
        self.settings.useInterlock = self.useInterlockGui.isChecked()
        self.autoSave()

    def onWavemeterError(self, channel, reply, error):
        """Print out received error"""
        logging.getLogger(__name__).warning( "Error {0} accessing wavemeter at '{1}'".format(error, self.settings.wavemeterAddress) )
        reply.finished.disconnect()  # necessary to make reply garbage collectable
        reply.error.disconnect()
        reply.deleteLater()
        del reply

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
        reply.deleteLater()
        del reply
        
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
            if self.outOfRangeCount < 20 : #Count how many times the frequency measures out of range. Stop counting at 20. (why count forever?)
                self.outOfRangeCount += 1
#                 self.allFreqsInRange.setStyleSheet("QLabel {background-color: rgb(255, 255, 0)}")
#                 self.allFreqsInRange.setToolTip("There are laser frequencies temporarily of range")
            if (self.outOfRangeCount >= 10):
                #set bar on GUI to red
                self.allFreqsInRange.setStyleSheet("QLabel {background-color: rgb(255, 0, 0)}")
                self.allFreqsInRange.setToolTip("There are laser frequencies out of range")
                #This is the interlock: loading is inhibited if frequencies are out of range
                if self.settings.useInterlock:
                    self.statemachine.processEvent( 'outOfLock' )
        
    def onValueChanged(self,attr,value):
        """Change the value of attr in settings to value"""
        setattr( self.settings, attr, value)
        self.autoSave()
        
    def onArrayValueChanged(self, index, attr, value):
        """Change the value of attr[index] in settings to value"""
        a = getattr(self.settings, attr)
        a[index] = value
        self.autoSave()
        
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
        if self.settings.shutterChannel2 >= 0:
            self.pulser.setShutterBit( abs(self.settings.shutterChannel2), invertIf(False,self.settings.shutterChannelActiveLow2 ))
    
    def exitIdle(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect( self.onTimer )
        self.timer.start(100)
        self.connectDataSignal()
        self.timerNullTime = now()
    
    def setPreheat(self):
        """Execute when the loading process begins. Turn on timer, turn on oven."""
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        self.elapsedLabel.setStyleSheet("QLabel { color:red; }")
        self.statusLabel.setText("Preheating")
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invertIf(True,self.settings.ovenChannelActiveLow) )
        self.timerNullTime = now()
        self.preheatStartTime = now()
    
    def setLoad(self):
        """Execute after preheating. Turn on ionization laser, and begin
           monitoring count rate."""
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        self.elapsedLabel.setStyleSheet("QLabel { color:purple; }")
        self.statusLabel.setText("Loading")
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invertIf(True,self.settings.shutterChannelActiveLow) )
        if self.settings.shutterChannel2 >= 0:
            self.pulser.setShutterBit( abs(self.settings.shutterChannel2), invertIf(True,self.settings.shutterChannelActiveLow2) )
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invertIf(True,self.settings.ovenChannelActiveLow) )
   
    def adjustFromLoading(self):
        self.globalVariablesUi.update( self.globalAdjustRevertList )
        self.externalInstrumentObservable( lambda: self.statemachine.processEvent('doneAdjusting') )
        if self.voltageNodeBeforeLoading:
            self.voltageControl.shuttleTo( self.voltageNodeBeforeLoading )
        
    def adjustToLoading(self):
        self.globalAdjustRevertList = [('Global', key, self.globalVariablesUi.globalDict[key]) for key in self.settings.globalsAdjustList]
        self.globalVariablesUi.update( ( ('Global', k, v) for k,v in self.settings.globalsAdjustList.iteritems() ))   
        self.externalInstrumentObservable( lambda: self.statemachine.processEvent('doneAdjusting') )
        if self.settings.loadingVoltageNode:
            self.voltageNodeBeforeLoading = self.voltageControl.currentShuttlingPosition()
            if not self.voltageControl.shuttleTo( self.settings.loadingVoltageNode, onestep=self.settings.instantToLoading):
                self.voltageNodeBeforeLoading = None
            #if not self.voltageControl.onUpdate( self.settings.shuttlingNodes(self.settings.loadingVoltageNode) ):
            #    self.voltageNodeBeforeLoading = None
        else:
            self.voltageNodeBeforeLoading = None 
        
    
    def setCheck(self):
        """Execute when count rate goes over threshold."""
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        self.elapsedLabel.setStyleSheet("QLabel { color:blue; }")
        self.checkStarted = now()
        self.statusLabel.setText("Checking for ion")
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invertIf(False,self.settings.shutterChannelActiveLow) )
        if self.settings.shutterChannel2 >= 0:
            self.pulser.setShutterBit( abs(self.settings.shutterChannel2), invertIf(False,self.settings.shutterChannelActiveLow2) )
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invertIf(False,self.settings.ovenChannelActiveLow) )

    def setShuttleLoad(self):
        """Execute after preheating. Turn on ionization laser, and begin
           monitoring count rate."""
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        self.elapsedLabel.setStyleSheet("QLabel { color:purple; }")
        self.statusLabel.setText("Shuttle Loading")
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invertIf(True,self.settings.shutterChannelActiveLow) )
        if self.settings.shutterChannel2 >= 0:
            self.pulser.setShutterBit( abs(self.settings.shutterChannel2), invertIf(True,self.settings.shutterChannelActiveLow2) )
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
        self.checkStarted = now()
        self.statusLabel.setText("Shuttle Checking for ion")
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invertIf(True,self.settings.shutterChannelActiveLow) )
        if self.settings.shutterChannel2 >= 0:
            self.pulser.setShutterBit( abs(self.settings.shutterChannel2), invertIf(True,self.settings.shutterChannelActiveLow2) )
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invertIf(True,self.settings.ovenChannelActiveLow) )
        
    def setPostSequenceWait(self):
        self.statusLabel.setText("Waiting after sequence finished.")
        
    def loadingToTrapped(self, check, trapped):
        logger = logging.getLogger(__name__)
        logger.info(  "Loading Trapped" )
        self.loadingTime = check.enterTime - self.timerNullTime
        self.loadingHistory.addLoadingEvent( LoadingEvent( loadingDuration=self.loadingTime, trappingTime=self.checkStarted, loadingProfile=self.currentSettingsName) )
           
    def idleToTrapped(self, check, trapped):
        logger = logging.getLogger(__name__)
        logger.info(  "Idle Trapped" )
        self.loadingTime = timedelta(0)
        self.loadingHistory.addLoadingEvent( LoadingEvent( loadingDuration=self.loadingTime, trappingTime=now(), loadingProfile=self.currentSettingsName) )
           
    def setTrapped(self):
        self.startButton.setEnabled( True )
        self.stopButton.setEnabled( True )       
        self.elapsedLabel.setStyleSheet("QLabel { color:green; }")
        self.statusLabel.setText("Trapped :)")       
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invertIf(False,self.settings.ovenChannelActiveLow) )
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invertIf(False,self.settings.shutterChannelActiveLow) )
        if self.settings.shutterChannel2 >= 0:
            self.pulser.setShutterBit( abs(self.settings.shutterChannel2), invertIf(False,self.settings.shutterChannelActiveLow2) )
        self.numFailedAutoload = 0
        self.trappingTime = firstNotNone(self.loadingHistory.lastEvent().trappingTime, now())
        self.timerNullTime = self.trappingTime
        self.ionReappeared.emit()        
    
    def exitTrapped(self):
        self.updateTrappingTime()

    def updateTrappingTime(self):
        duration = now()-self.trappingTime
        self.loadingHistory.setTrappingDuration(duration)
        self.historyTableModel.updateLast()

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
        self.timerNullTime = now()
    
    def setCoolingOven(self):
        self.pulser.setShutterBit( abs(self.settings.ovenChannel), invertIf(False,self.settings.ovenChannelActiveLow) )
        self.pulser.setShutterBit( abs(self.settings.shutterChannel), invertIf(False,self.settings.shutterChannelActiveLow ))
        if self.settings.shutterChannel2 >= 0:
            self.pulser.setShutterBit( abs(self.settings.shutterChannel2), invertIf(False,self.settings.shutterChannelActiveLow2 ))
        self.statusLabel.setText("Cooling Oven")
        self.timerNullTime = now()
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
        if self.settings.shutterChannel2 >= 0:
            self.pulser.setShutterBit( abs(self.settings.shutterChannel2), invertIf(False,self.settings.shutterChannelActiveLow2 ))
        
    def onIonIsStillTrapped(self):
        self.statemachine.processEvent( 'ionStillTrapped' )
        
    def onTrappedIonNow(self):
        current = now()
        self.timerNullTime = current
        self.trappingTime = current
        self.checkStarted = current
        self.statemachine.processEvent('ionTrapped')           
    
    def onTimer(self):
        """Execute whenever the timer sends a timeout signal, which is every 100 ms.
           Trigger status changes based on elapsed time. This controls the flow
           of the loading process."""
        self.elapsed = now()-self.timerNullTime
        self.elapsedLabel.setText(formatDelta(self.elapsed) )
        self.statemachine.processEvent( 'timer' )
    
    def onData(self, data ):
        """Execute when count rate data is received. Change state based on count rate."""
        self.statemachine.processEvent( 'data', data )
    
    def onClose(self):
        self.statemachine.processEvent( 'stopButton' )
            
    def saveConfig(self):
        self.config['AutoLoad.Settings'] = self.settings
        self.config['AutoLoad.guiState'] = saveGuiState( self )
        self.config['AutoLoad.Settings.dict'] = self.settingsDict
        self.config['AutoLoad.SettingsName'] = self.currentSettingsName
        self.config['AutoLoad.Parameters'] = self.parameters
        if self.statemachine.currentState == 'Trapped':
            self.loadingHistory.setTrappingDuration( now()-self.trappingTime )

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

    def setBeyondThreshold(self):
        self.originalResetValue = self.globalVariablesUi.globalDict[self.settings.resetField]
        self.globalVariablesUi.globalDict[self.settings.resetField] = self.settings.resetValue
        self.statusLabel.setText("Too many ions, dumping them :(")

    def exitBeyondThreshold(self):
        self.globalVariablesUi.globalDict[self.settings.resetField] = self.originalResetValue
