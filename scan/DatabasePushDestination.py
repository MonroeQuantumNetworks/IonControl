'''
Created on Dec 19, 2014

@author: pmaunz
'''
from externalParameter.persistence import DBPersist
import time
from modules.magnitude import is_magnitude

class DatabasePushDestination:
    def __init__(self, space):
        self.persist = DBPersist()
        self.space = space
    
    def update(self, pushlist, upd_time=None ):
        upd_time = time.time() if upd_time is None else upd_time
        for _, variable, value in pushlist:
            if is_magnitude(value):
                value, unit = value.toval(returnUnit=True)
            else:
                unit = None
            self.persist.persist(self.space, variable, upd_time, value, unit)
    
    def keys(self):
        return (source for (space,source) in self.persist.sourceDict().keys() if space == self.space) 

