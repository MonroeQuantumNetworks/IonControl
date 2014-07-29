'''
Created on Jun 21, 2014

@author: pmaunz
'''
from PyQt4 import QtCore
from pyqtgraph.parametertree import Parameter
import modules.magnitude as magnitude
import logging

def nextValue( current, target, stepsize, jump ):
    if current is None:
        return (target,True)
    temp = target-current
    return (target,True) if abs(temp)<=stepsize or jump else (current + stepsize.copysign(temp), False)  

class ExternalParameterBase(object):
    dimension = None
    def __init__(self,name,settings):
        self.name = name
        self.settings = settings
        self.displayValueCallback = None
        self.setDefaults()
        self._parameter = Parameter.create(name='params', type='group',children=self.paramDef())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        
    @property
    def parameter(self):
        # re-create the parameters each time to prevent a exception that says the signal is not connected
        self._parameter = Parameter.create(name='params', type='group',children=self.paramDef())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        return self._parameter        
        
    def setDefaults(self):
        self.settings.__dict__.setdefault('delay', magnitude.mg(100,'ms') )      # s delay between subsequent updates
        self.settings.__dict__.setdefault('jump' , False)       # if True go to the target value in one jump
        self.settings.__dict__.setdefault('value', None )      # the current value       
    
    def saveValue(self):
        """
        save current value
        """
        self.savedValue = self.value
    
    def restoreValue(self):
        """
        restore the value saved previously, this routine only goes stepsize towards this value
        if the stored value is reached returns True, otherwise False. Needs to be called repeatedly
        until it returns True in order to restore the saved value.
        """
        return self.setValue(self.savedValue)
    
    def setValue(self,value):
        """
        go stepsize towards the value. This function returns True if the value is reached. Otherwise
        it should return False. The user should call repeatedly until the intended value is reached
        and True is returned.
        """
        newvalue, arrived = nextValue(self.value, value, self.settings.stepsize, self.settings.jump)
        self._setValue( newvalue )
        if self.displayValueCallback:
            self.displayValueCallback( self.value )
        return arrived
    
    def _setValue(self, v):
        self.value = v
    
    def currentValue(self):
        """
        returns current value
        """
        return self.value
    
    def currentExternalValue(self):
        """
        if the value is determined externally, return the external value, otherwise return value
        """
        return self.value

    def paramDef(self):
        """
        return the parameter definition used by pyqtgraph parametertree to show the gui
        """
        return [{'name': 'delay', 'type': 'magnitude', 'value': self.settings.delay, 'tip': "between steps"},
                {'name': 'jump', 'type': 'bool', 'value': self.settings.jump}]
        
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
            elif change=='action':
                getattr( self, param.opt['field'] )()
            
    def close(self):
        pass
    
    def useExternalValue(self):
        return False
            
