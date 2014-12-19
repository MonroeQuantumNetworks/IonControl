'''
Created on Dec 18, 2014

@author: pmaunz
'''


class InputChannel(object):
    def __init__(self, device, name):
        self.device = device
        self.channelName = name
        
    @property
    def value(self):
        return self.device.getValue(self.channelName)