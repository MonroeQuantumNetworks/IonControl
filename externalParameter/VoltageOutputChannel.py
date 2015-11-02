'''
Created on Dec 18, 2014

@author: pmaunz
'''
from externalParameter.OutputChannel import OutputChannel
from modules.magnitude import mg

class VoltageOutputChannel(OutputChannel):
    def __init__(self, device, deviceName, channelName, globalDict):
        super(VoltageOutputChannel, self).__init__(device, deviceName, channelName, globalDict)
                
    @property
    def externalValue(self):
        return self.device.currentValue(self.channelName)
    
    @property
    def strValue(self):
        return self.device.strValue(self.channelName)
    
    @strValue.setter
    def strValue(self, sval):
        self.device.setStrValue(self.channelName, sval)
        
    @property
    def dimension(self):
        return mg(1,'')
    
    @property
    def delay(self):
        return 0
    
    @property
    def observable(self):
        return self.device.displayValueObservable[self.channelName]
    
    @property
    def useExternalValue(self):
        return False
    