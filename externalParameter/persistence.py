'''
Created on Aug 30, 2014

@author: pmaunz
'''

from persist.ValueHistory import ValueHistoryStore
from datetime import datetime
from gui.ProjectSelection import getDatabaseConnection

class DBPersist:
    store = None
    name = "DB Persist"
    def __init__(self):
        self.initDB()
        
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.initDB()
        
    def initDB(self):
        if DBPersist.store is None:
            DBPersist.store = ValueHistoryStore(getDatabaseConnection())
            DBPersist.store.open_session()        
        
    def persist(self, space, source, time, value, minval=None, maxval=None, unit=None):
        if source:
            DBPersist.store.add( space, source, value, unit, datetime.fromtimestamp(time), bottom=minval, top=maxval )
        
    def paramDef(self):
        return []

    def sourceDict(self):
        return DBPersist.store.sourceDict

persistenceDict = { DBPersist.name: DBPersist }