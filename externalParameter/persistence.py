'''
Created on Aug 30, 2014

@author: pmaunz
'''

from persist.ValueHistory import ValueHistoryStore
from datetime import datetime
from ProjectConfig.Project import getProject
from modules.Observable import Observable

class DBPersist:
    store = None
    name = "DB Persist"
    newPersistData = Observable()
    def __init__(self):
        self.initialized = False

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.initialized = False
        
    def initDB(self):
        dbConnection = getProject().dbConnection
        if DBPersist.store is None:
            DBPersist.store = ValueHistoryStore(dbConnection)
            DBPersist.store.open_session()
        self.initialized = True
        
    def persist(self, space, source, time, value, minval=None, maxval=None, unit=None):
        if not self.initialized:
            self.initDB()
        if source:
            ts = datetime.fromtimestamp(time)
            DBPersist.store.add( space, source, value, unit, ts, bottom=minval, top=maxval )
            self.newPersistData.fire( space=space, parameter=source, value=value, unit=unit, timestamp=ts, bottom=minval, top=maxval )
        
    def paramDef(self):
        return []

    def sourceDict(self):
        if not self.initialized:
            self.initDB()
        return DBPersist.store.sourceDict

persistenceDict = { DBPersist.name: DBPersist }