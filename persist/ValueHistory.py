'''
Created on Aug 27, 2014

@author: pmaunz
'''


import logging

from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound


Base = declarative_base()
    
class ValueHistoryEntry(Base):
    __tablename__ = "value_history"
    parameter = Column(String, primary_key=True)
    value = Column(Float)
    unit = Column(String)
    upd_date = Column(DateTime, primary_key=True)
    
    def __init__(self,parameter,value,unit,upd_date):
        self.parameter = parameter
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
        
    def commit(self, copyTo=None ):
        self.session.commit()
        self.session = self.Session()

    def __enter__(self):
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        return self
        
    def __exit__(self, exittype, value, tb):
        self.session.commit()
        
    def add(self, parameter, value, unit, upd_date):
        elem = ValueHistoryEntry(parameter, value, unit, upd_date)
        self.session.add(elem)
        elem.value = value
        
    def get(self, parameter):
        return self.session.query(ValueHistoryEntry).filter(ValueHistoryEntry.parameter==parameter)
                    
    def open(self):
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.isOpen = True
        
    def close(self):
        self.session.commit()
        self.isOpen = False
        
if __name__ == "__main__":
    import datetime
    with ValueHistoryStore("postgresql://python:yb171@localhost/ioncontrol") as d:
        d.add('Peter', 12, 'mm', datetime.datetime.now())
        

