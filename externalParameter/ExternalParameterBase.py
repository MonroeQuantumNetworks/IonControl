'''
Created on Jun 21, 2014

@author: pmaunz
'''
from PyQt4 import QtCore
from pyqtgraph.parametertree import Parameter
import logging
from externalParameter.OutputChannel import OutputChannel ,\
    SlowAdjustOutputChannel
from externalParameter.InputChannel import InputChannel
from InstrumentSettings import InstrumentSettings

InstrumentDict = dict()

class InstrumentException(Exception):
    pass

class InstrumentMeta(type):
    def __new__(self, name, bases, dct):
        instrclass = super(InstrumentMeta, self).__new__(self, name, bases, dct)
        if name!='ExternalParameterBase':
            if 'className' not in dct:
                raise InstrumentException("Instrument class needs to have class attribute 'className'")
            InstrumentDict[dct['className']] = instrclass
        return instrclass
    
class ExternalParameterBase(object):
    _outputChannels = { None: None }    # a single channel with key None designates a device only supporting a single channel
    _inputChannels = dict()
    __metaclass__ = InstrumentMeta
    def __init__(self, name, deviceSettings, globalDict):
        self.name = name
        self.settings = deviceSettings
        self.setDefaults()
        self._parameter = Parameter.create(name='params', type='group',children=self.paramDef())
        try:
            self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        except:
            pass
        self.globalDict = globalDict
        self.createOutputChannels()

    def createOutputChannels(self):
        """create all output channels"""
        self.outputChannels = dict( [(channel, SlowAdjustOutputChannel(self, self.name, channel, self.globalDict, self.settings.channelSettings.get(channel,dict()), unit)) 
                                    for channel, unit in self._outputChannels.iteritems()] )
        
    def lastOutputValue(self, channel):
        """return the last value written to channel""" 
        return self.outputChannels[channel].settings.value
        
    def initializeChannelsToExternals(self):
        """Initialize all channels to the values read from the instrument"""
        for cname in self._outputChannels.iterkeys():
            self.outputChannels[cname].settings.value = self.getValue(cname)

    def dimension(self, channel):
        """return the dimension eg 'Hz' or 'V' for channel""" 
        return self._outputChannels[channel] 
        
    @property
    def parameter(self):
        # re-create the parameters each time to prevent a exception that says the signal is not connected
        self._parameter = Parameter.create(name=self.name, type='group',children=self.paramDef())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        return self._parameter        
        
    def setDefaults(self, settings=None):
        if settings is None:
            self.settings.__dict__.setdefault('channelSettings', dict())
            for cname in self._outputChannels:
                self.settings.channelSettings.setdefault( cname, InstrumentSettings() )
        else:
            settings.__dict__.setdefault('channelSettings', dict())
            for cname in self._outputChannels:
                settings.channelSettings.setdefault( cname, InstrumentSettings() )
               
    def setValue(self, channel, v):
        """write the value to the instrument"""
        return None
    
    def getValue(self, channel=None):
        """returns current value as read from instrument (if the instruments supports reading)"""
        return self.lastOutputValue(channel)
    
    def getExternalValue(self, channel=None):
        """
        if the value is determined externally, return the external value, otherwise return value
        """
        return self.getValue(channel)

    def paramDef(self):
        """
        return the parameter definition used by pyqtgraph parametertree to show the gui
        """
        return []
        
    def update(self, param, changes):
        """
        update the parameter, called by the signal of pyqtgraph parametertree
        """
        logger = logging.getLogger(__name__)
        logger.debug( "ExternalParameterBase.update" )
        for param, change, data in changes:
            if change=='value':
                logger.debug( " ".join( [str(self), "update", param.name(), str(data)] ) )
                setattr( self.settings, param.name(), data)
            elif change=='activated':
                getattr( self, param.opts['field'] )()
            
    def close(self):
        pass
    
    def fullName(self, channel):
        return "{0}_{1}".format(self.name,channel) if channel is not None else self.name
    
    def useExternalValue(self, channel=None):
        return False
            
    def outputChannelList(self):
        return [(self.fullName(channelName), channel) for channelName, channel in self.outputChannels.iteritems()]
    
    def inputChannelList(self):
        return [(self.fullName(channel), InputChannel(self,self.name,channel)) for channel in self._inputChannels.iterkeys()]
        
    def getInputData(self, channel):
        return None
