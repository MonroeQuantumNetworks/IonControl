'''
Created on Dec 18, 2014

@author: pmaunz
'''

class OutputChannel(object):
    def __init__(self, device, deviceName, channelName):
        self.device = device
        self.deviceName = deviceName
        self.channelName = channelName
        
    @property
    def name(self):
        return "{0}_{1}".format(self.deviceName, self.channelName)
        
    @property
    def value(self):
        return self.device.currentValue(self.channelName)
    
    @value.setter
    def value(self, newval):
        self.device.setValue(self.channelName, newval)
    
    def setValue(self, newval):
        return self.device.setValue(self.channelName, newval)
        
    def saveValue(self, overwrite=True):
        self.device.saveValue(self.channelName)
        
    def restoreValue(self):
        self.device.restoreValue(self.channelName)
        
    @property 
    def savedValue(self):
        return self.device.savedValue[self.channelName]
    
    @savedValue.setter
    def savedValue(self, value):
        self.device.savedValue[self.channelName] = value
        
    @property
    def externalValue(self):
        return self.device.currentExternalValue(self.channelName)
    
    @property
    def strValue(self):
        return self.device.settings.strValue.get(self.channelName)
    
    @strValue.setter
    def strValue(self, sval):
        self.device.settings.strValue[self.channelName] = sval
        
    @property
    def dimension(self):
        return self.device.dimension(self.channelName)
    
    @property
    def delay(self):
        return self.device.settings.delay
    
    @property
    def observable(self):
        return self.device.displayValueObservable[self.channelName]
    
    @property
    def useExternalValue(self):
        return self.device.useExternalValue(self.channelName)
    