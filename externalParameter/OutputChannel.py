'''
Created on Dec 18, 2014

@author: pmaunz
'''
from gui.ExpressionValue import ExpressionValue
from modules import magnitude
from decimation import StaticDecimation
from persistence import DBPersist
from modules.Observable import Observable
from pyqtgraph.parametertree import Parameter
from PyQt4 import QtCore
import time
from functools import partial
from modules.magnitude import is_magnitude

def nextValue( current, target, stepsize, jump ):
    if (current is None) or jump:
        return (target,True)
    else:
        temp = target-current
        return (target,True) if abs(temp)<=stepsize else (current + stepsize.copysign(temp), False)  


class OutputChannel(QtCore.QObject):
    persistSpace = 'externalOutput'
    valueChanged = QtCore.pyqtSignal(object)
    targetChanged = QtCore.pyqtSignal(object)

    def __init__(self, device, deviceName, channelName, globalDict, settings, outputUnit):
        super(OutputChannel, self).__init__()
        self.device = device
        self.deviceName = deviceName
        self.channelName = channelName
        self.globalDict = globalDict
        self.expressionValue = ExpressionValue(self.name, self.globalDict, None)
        self.settings = settings
        self.savedValue = None
        self.displayValueObservable = Observable()
        self.decimation = StaticDecimation()
        self.persistence = DBPersist()
        self.outputUnit = outputUnit
        self.setDefaults()
        self.expressionValue.string = self.settings.strValue
        self.expressionValue.value = self.settings.targetValue
        self.expressionValue.observable.subscribe(self.onExpressionUpdate)
        
    def setDefaults(self):
        self.settings.__dict__.setdefault('value', magnitude.mg(0, self.outputUnit))  # the current value
        self.settings.__dict__.setdefault('persistDelay', magnitude.mg(60, 's'))     # delay for persistency
        self.settings.__dict__.setdefault('strValue', None)                          # requested value as string (formula)
        self.settings.__dict__.setdefault('targetValue', magnitude.mg(0, self.outputUnit) )  # requested value as string (formula)

    def onExpressionUpdate(self, event):
        if event.origin == 'recalculate':
            self.setValue(event.value)
            self.targetChanged.emit(event.value)

    @property
    def name(self):
        return "{0}_{1}".format(self.deviceName, self.channelName) if self.deviceName else self.channelName
        
    @property
    def value(self):
        return self.settings.value
    
    def setValue(self, targetValue):
        """
        go stepsize towards the value. This function returns True if the value is reached. Otherwise
        it should return False. The user should call repeatedly until the intended value is reached
        and True is returned.
        """
        self.settings.targetValue = targetValue
        self.expressionValue.value = targetValue
        reportvalue = self.device.setValue(self.channelName, targetValue)
        self.settings.value = reportvalue
        self.valueChanged.emit(self.settings.value)
        return True
    
    def persist(self, channel, value):
        self.decimation.staticTime = self.settings.persistDelay
        decimationName = self.name if channel is None else self.name
        self.decimation.decimate(time.time(), value, partial(self.persistCallback, decimationName) )
        
    def persistCallback(self, source, data):
        time, value, minval, maxval = data
        if is_magnitude(value):
            value, unit = value.toval(returnUnit=True)
        else:
            value, unit = value, None
        self.persistence.persist(self.persistSpace, source, time, value, minval, maxval, unit)
           
    def saveValue(self):
        """
        save current value
        """
        self.savedValue = self.settings.value
        return self.savedValue

    def restoreValue(self):
        """
        restore the value saved previously, this routine only goes stepsize towards this value
        if the stored value is reached returns True, otherwise False. Needs to be called repeatedly
        until it returns True in order to restore the saved value.
        """
        return self.setValue(self.savedValue)
        
    @property
    def externalValue(self):
        return self.device.getExternalValue(self.channelName)
    
    @property
    def dimension(self):
        return self.outputUnit
    
    @property
    def useExternalValue(self):
        return self.device.useExternalValue(self.channelName)

    @property
    def hasDependency(self):
        return self.expressionValue.hasDependency
    
    @property
    def targetValue(self):
        return self.settings.targetValue

    @targetValue.setter
    def targetValue(self, requestval):
        self.setValue(requestval)

    @property
    def string(self):
        return self.expressionValue.string

    @string.setter
    def string(self, s):
        self.settings.strValue = s
        self.expressionValue.string = s
        
    @property
    def parameter(self):
        # re-create the parameters each time to prevent a exception that says the signal is not connected
        self._parameter = Parameter.create(name=self.name, type='group',children=self.paramDef())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        return self._parameter                
        
    def paramDef(self):
        """
        return the parameter definition used by pyqtgraph parametertree to show the gui
        """
        return [{'name': 'persistDelay', 'type': 'magnitude', 'value': self.settings.persistDelay }]

    def update(self, param, changes):
        """
        update the parameter, called by the signal of pyqtgraph parametertree
        """
        for param, change, data in changes:
            if change=='value':
                setattr( self.settings, param.name(), data)       
        
class SlowAdjustOutputChannel(OutputChannel):
    def __init__(self, device, deviceName, channelName, globalDict, settings, outputUnit):
        super(SlowAdjustOutputChannel, self).__init__(device, deviceName, channelName, globalDict, settings, outputUnit)
        
    def setDefaults(self):
        super(SlowAdjustOutputChannel, self).setDefaults()
        self.settings.__dict__.setdefault('delay', magnitude.mg(100,'ms') )      # s delay between subsequent updates
        self.settings.__dict__.setdefault('jump' , False)       # if True go to the target value in one jump
        self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1, self.outputUnit) )       # if True go to the target value in one jump
        
    def paramDef(self):
        param = super(SlowAdjustOutputChannel, self).paramDef()
        param.extend([{'name': 'delay', 'type': 'magnitude', 'value': self.settings.delay, 'tip': "between steps"},
                            {'name': 'jump', 'type': 'bool', 'value': self.settings.jump},
                            {'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize }])
        return param

    @staticmethod
    def encpasulate_value(arg, second=True):
        if not isinstance(arg, tuple):
            return arg, second
        elif len(arg) == 1:
            return arg[1], second
        return arg[1], arg[2] and second

    def setValue(self, targetValue):
        """
        go stepsize towards the value. This function returns True if the value is reached. Otherwise
        it should return False. The user should call repeatedly until the intended value is reached
        and True is returned.
        """
        self.settings.targetValue = targetValue
        newvalue, arrived = nextValue(self.settings.value, targetValue, self.settings.stepsize, self.settings.jump)
        reportvalue, arrived = self.encpasulate_value(self.device.setValue(self.channelName, newvalue), second=arrived)
        self.settings.value = reportvalue
        self.valueChanged.emit(self.settings.value)
        if arrived:
            self.persist(self.name, self.settings.value)
        return arrived

    def onExpressionUpdate(self, event):
        if event.origin == 'recalculate':
            self.expressionUpdateBottomHalf(event.value)
            self.targetChanged.emit(event.value)

    def expressionUpdateBottomHalf(self, target):
        if not self.setValue(target):
            QtCore.QTimer.singleShot(self.settings.delay.toval('ms'), partial(self.expressionUpdateBottomHalf, target))
