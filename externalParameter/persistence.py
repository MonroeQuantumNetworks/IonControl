'''
Created on Aug 30, 2014

@author: pmaunz
'''

from persist.ValueHistory import ValueHistoryStore
from datetime import datetime

class DBPersist:
    store = None
    name = "DB Persist"
    def __init__(self):
        if DBPersist.store is None:
            DBPersist.store = ValueHistoryStore("postgresql://python:yb171@localhost/ioncontrol")
            DBPersist.store.open()
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        if DBPersist.store is None:
            DBPersist.store = ValueHistoryStore("postgresql://python:yb171@localhost/ioncontrol")
            DBPersist.store.open()
        
    
    def persist(self, source, data):
        time, value, minval, maxval = data
        DBPersist.store.add( source, value, None, datetime.fromtimestamp(time), bottom=minval, top=maxval )
        
    def paramDef(self):
        return []


persistenceDict = { DBPersist.name: DBPersist }