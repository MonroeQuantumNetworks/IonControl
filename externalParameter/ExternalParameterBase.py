'''
Created on Jun 21, 2014

@author: pmaunz
'''
from PyQt4 import QtCore
from pyqtgraph.parametertree import Parameter
import modules.magnitude as magnitude
import logging
from decimation import StaticDecimation
from persistence import DBPersist
import time
from functools import partial
from modules.magnitude import is_magnitude
from modules.AttributeRedirector import AttributeRedirector
from externalParameter.OutputChannel import OutputChannel

def nextValue( current, target, stepsize, jump ):
    if current is None:
        return (target,True)
    temp = target-current
    return (target,True) if abs(temp)<=stepsize or jump else (current + stepsize.copysign(temp), False)  

class ExternalParameterBase(object):
    persistSpace = 'externalOutput'
    strValue = AttributeRedirector('settings', 'strValue', None)
    _outputChannels = { None: None }    # a single channel with key None designates a device only supporting a single channel
    _inputChannels = dict()
    def __init__(self,name,settings):
        self.name = name
        self.settings = settings
        self.displayValueCallback = None
        self.setDefaults()
        self._parameter = Parameter.create(name='params', type='group',children=self.paramDef())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        self.savedValue = dict()
        self.decimation = StaticDecimation()
        self.persistence = DBPersist()

    def dimension(self, channel):
        return self._outputChannels[channel]
        
    @property
    def parameter(self):
        # re-create the parameters each time to prevent a exception that says the signal is not connected
        self._parameter = Parameter.create(name=self.name, type='group',children=self.paramDef())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        return self._parameter        
        
    def setDefaults(self):
        self.settings.__dict__.setdefault('delay', magnitude.mg(100,'ms') )      # s delay between subsequent updates
        self.settings.__dict__.setdefault('jump' , False)       # if True go to the target value in one jump
        self.settings.__dict__.setdefault('value', dict() )      # the current value       
        self.settings.__dict__.setdefault('persistDelay', magnitude.mg(60,'s' ) )     # delay for persistency  
        self.settings.__dict__.setdefault('strValue', dict() )
        if not isinstance( self.settings.value, dict):
            self.settings.value = dict()
        if not isinstance( self.settings.strValue, dict ):
            self.settings.strValue = dict()
    
    def saveValue(self, channel=None, overwrite=True):
        """
        save current value
        """
        if not channel in self.savedValue or overwrite:
            self.savedValue[channel] = self.settings.value[channel]
            
    def restoreValue(self, channel=None):
        """
        restore the value saved previously, this routine only goes stepsize towards this value
        if the stored value is reached returns True, otherwise False. Needs to be called repeatedly
        until it returns True in order to restore the saved value.
        """
        return self.setValue(self.savedValue[channel])
    
    def setValue(self, channel, value):
        """
        go stepsize towards the value. This function returns True if the value is reached. Otherwise
        it should return False. The user should call repeatedly until the intended value is reached
        and True is returned.
        """
        newvalue, arrived = nextValue(self.settings.value[channel], value, self.settings.stepsize, self.settings.jump)
        self._setValue( channel, newvalue )
        if self.displayValueCallback:
            self.displayValueCallback( self.settings.value[channel] )
        if arrived:
            self.persist(channel, self.settings.value)
        return arrived
    
    def persist(self, channel, value):
        self.decimation.staticTime = self.settings.persistDelay
        decimationName = self.channelName if channel is None else self.fullName(channel)
        self.decimation.decimate(time.time(), value, partial(self.persistCallback, decimationName) )
        
    def persistCallback(self, source, data):
        time, value, minval, maxval = data
        if is_magnitude(value):
            value, unit = value.toval(returnUnit=True)
        self.persistence.persist(self.persistSpace, source, time, value, minval, maxval, unit)
    
    def _setValue(self, channel, v):
        self.settings.value[channel] = v
    
    def currentValue(self, channel=None):
        """
        returns current value
        """
        return self.settings.value[channel]
    
    def currentExternalValue(self, channel=None):
        """
        if the value is determined externally, return the external value, otherwise return value
        """
        return self.settings.value[channel]

    def paramDef(self):
        """
        return the parameter definition used by pyqtgraph parametertree to show the gui
        """
        return [{'name': 'delay', 'type': 'magnitude', 'value': self.settings.delay, 'tip': "between steps"},
                {'name': 'jump', 'type': 'bool', 'value': self.settings.jump},
                {'name': 'persistDelay', 'type': 'magnitude', 'value': self.settings.persistDelay }]
        
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
        return "{0}_{1}".format(self.channelName,channel)
    
    def useExternalValue(self, channel=None):
        return False
            
    def outputChannels(self):
        return [(self.fullName(channel), OutputChannel(self,channel)) for channel in self._outputChannels.iterkeys()]
    
    def inputChannels(self):
        return [(self.fullName(channel), OutputChannel(self,channel)) for channel in self._inputChannels.iterkeys()]
        