'''
Created on Aug 27, 2014

@author: pmaunz
'''


import logging

from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.orm.exc import NoResultFound


Base = declarative_base()
    
class HistorySource(Base):
    __tablename__ = "history_source"
    id = Column(Integer, primary_key = True)
    name = Column(String, nullable=False, unique=True )
    
    
class ValueHistoryEntry(Base):
    __tablename__ = "value_history"
    source_id = Column(Integer, ForeignKey('history_source.id'), primary_key=True )
    source = relationship( HistorySource, backref=backref('history', uselist=True, cascade='delete,all'))
    value = Column(Float, nullable=False)
    bottom = Column(Float)
    top = Column(Float)
    unit = Column(String)
    upd_date = Column(DateTime, primary_key=True)
    
    def __init__(self,source,value,unit,upd_date):
        self.source = source
        self.value = value
        self.unit = unit
        self.upd_date = upd_date
        
    def __repr__(self):
        return "<'{0}.{1}' {2} {3} @ {4}>".format(self.category, self.parameter, self.value, self.unit, self.upd_date)
        
    
class ValueHistoryElement:
    def __init__(self, name, update_strategy):
        self.name = name
        self.value = None
        self.update_strategy = update_strategy
        
    def update(self, value):
        pass
   
   
class ValueHistoryStore:
    def __init__(self,database_conn_str):
        self.database_conn_str = database_conn_str
        self.engine = create_engine(self.database_conn_str, echo=False)
        self.sourceDict = dict()
        
    def getSource(self, source):
        if source in self.sourceDict:
            s = self.sourceDict[source]
            self.session.add(s)
            return s
        else:
            s = HistorySource( name=source )
            self.session.add(s)
            self.sourceDict[source] = s
            return s
        
    def commit(self, copyTo=None ):
        self.session.commit()
#        self.session = self.Session()

    def open_session(self):
        self.__enter__()
        
    def close_session(self):
        self.session.commit()        

    def __enter__(self):
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.sourceDict.update( [(s.name, s) for s in self.session.query(HistorySource).all()] )
        return self
        
    def __exit__(self, exittype, value, tb):
        self.session.commit()
        
    def add(self, parameter, value, unit, upd_date, bottom=None, top=None):
        paramObj = self.getSource(parameter)
        elem = ValueHistoryEntry(paramObj, value, unit, upd_date)
        self.session.add(elem)
        elem.value = value
        if bottom is not None:
            elem.bottom = bottom
        if top is not None:
            elem.top = top
        self.commit()
        
    def get(self, parameter):
        return self.session.query(ValueHistoryEntry).filter(ValueHistoryEntry.parameter==parameter)
                    
    def open(self):
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.session = self.Session()
        self.isOpen = True
        
    def close(self):
        self.session.commit()
        self.isOpen = False
        
if __name__ == "__main__":
    import datetime
    with ValueHistoryStore("postgresql://python:yb171@localhost/ioncontrol") as d:
        d.add('Peter', 12, 'mm', datetime.datetime.now())
        d.add('Peter', 13, 'mm', datetime.datetime.now())
        d.add('Peter', 14, 'mm', datetime.datetime.now(), bottom=3, top=15 )
        

