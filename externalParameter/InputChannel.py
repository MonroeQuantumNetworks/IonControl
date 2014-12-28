'''
Created on Dec 18, 2014

@author: pmaunz
'''

class InputChannel(object):
    def __init__(self, device, deviceName, channelName):
        self.device = device
        self.deviceName = deviceName
        self.channelName = channelName

    @property
    def observable(self):
        return self.device.inputObservable[self.channelName]
        
    @property
    def value(self):
        return self.device.getValue(self.channelName)
    
    @property
    def inputData(self):
        return self.device.getInputData(self.channelName)