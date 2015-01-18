'''
Created on Dec 28, 2014

@author: pmaunz
'''

class InputData:
    def __init__(self, raw=None, calibrated=None, decimated=None, persisted=None):
        self.raw = raw
        self.calibrated = calibrated
        self.decimated = decimated
        self.persisted = persisted
        
    def update(self, other):
        if other.raw is not None:
            self.raw = other.raw
        if other.calibrated is not None:
            self.calibrated = other.calibrated
        if other.decimated is not None:
            self.decimated = other.decimated
        if other.persisted is not None:
            self.persisted = other.persisted

