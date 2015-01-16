'''
Created on Dec 28, 2014

@author: pmaunz
'''


from sqlalchemy import Column, String, DateTime, Integer, Interval, Boolean
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import InvalidRequestError, IntegrityError, ProgrammingError
from sqlalchemy.exc import OperationalError
import logging
from modules.Observable import Observable
from modules.SequenceDict import SequenceDict

Base = declarative_base()

class LoadingEvent(Base):
    __tablename__ = 'loading_history'
    loadingProfile = Column(String)
    loadingDuration = Column(Interval)
    trappingDuration = Column(Interval)
    trappingTime = Column(DateTime(timezone=True), primary_key=True )
    ionCount = Column(Integer)
    valid = Column( Boolean, default=True )

    def __init__(self, *args, **kwargs):
        super(LoadingEvent, self).__init__(*args, **kwargs)


class LoadingHistory(object):
    def __init__(self,dbConnection):
        self.database_conn_str = dbConnection.connectionString
        self.engine = create_engine(self.database_conn_str, echo=dbConnection.echo)
        self.isOpen = False
        self.beginInsertRows = Observable()
        self.endInsertRows = Observable()
        self.beginResetModel = Observable()
        self.endResetModel = Observable()
        self._loadingEvents = SequenceDict()
        self._currentProfile = None
        self._profiles = set()
        
    def open(self):
        try:
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
            self.session = self.Session()
            self.isOpen = True
        except OperationalError as e:
            logging.getLogger(__name__).error("Cannot open database: {0}".format(str(e)))
            self.isOpen = False
        
    def close(self):
        self.session.commit()
        self.isOpen = False

    def __enter__(self):
        if not self.isOpen:
            self.open()
        return self
        
    def __exit__(self, exittype, value, tb):
        self.session.commit()

    def addLoadingEvent(self, loadingEvent):
        try:
            self.session.add( loadingEvent )
            self.session.commit()
            if self._currentProfile is None or loadingEvent.loadingProfile==self._currentProfile:
                self.beginInsertRows.fire(first=len(self._loadingEvents),last=len(self._loadingEvents))
                self._loadingEvents.append( loadingEvent )
                self.endInsertRows.firebare()
        except (InvalidRequestError, IntegrityError, ProgrammingError) as e:
            logging.getLogger(__name__).error( str(e) )
            self.session.rollback()
            self.session = self.Session()
        
    def commit(self):
        try:
            self.session.commit()
        except (InvalidRequestError, IntegrityError, ProgrammingError) as e:
            logging.getLogger(__name__).error( str(e) )
            self.session.rollback()
            self.session = self.Session()
        
    def query(self, fromTime, toTime, loadingProfiles=None):
        self.beginResetModel.firebare()
        if loadingProfiles is None:
            self._loadingEvents = self.session.query(LoadingEvent).filter(LoadingEvent.trappingTime>=fromTime).filter(LoadingEvent.trappingTime<=toTime).order_by(LoadingEvent.trappingTime).all()
        else:
            self._loadingEvents = self.session.query(LoadingEvent).filter(LoadingEvent.trappingTime>=fromTime).filter(LoadingEvent.trappingTime<=toTime).filter(LoadingEvent.loadingProfile.in_(loadingProfiles)).order_by(LoadingEvent.trappingTime).all()
        self.endResetModel.firebare()
    
    def getProfiles(self):
        return None
    
    @property
    def loadingEvents(self):
        return self._loadingEvents
    
    def lastEvent(self):
        return self._loadingEvents[-1]
    