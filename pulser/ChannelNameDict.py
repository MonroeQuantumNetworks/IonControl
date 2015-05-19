'''
Created on May 16, 2015

@author: pmaunz
'''
from pandas.compat.chainmap_impl import ChainMap


class ChannelNameDict( ChainMap ):
    def __init__(self, CustomDict=None, DefaultDict=None ):
        super(ChannelNameDict, self).__init__( CustomDict if CustomDict is not None else dict(), DefaultDict if DefaultDict is not None else dict())
    
    @property
    def defaultDict(self):
        return self.maps[1]
    
    @defaultDict.setter
    def defaultDict(self, defaultDict ):
        self.maps[1] = defaultDict
    
    @property
    def customDict(self):
        return self.maps[0]