'''
Created on Aug 27, 2014

@author: pmaunz
'''

from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Index
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from modules.magnitude import is_magnitude

Base = declarative_base()
    
    
class HistoryException(Exception):
    pass
    
class HistorySource(Base):
    __tablename__ = "history_source"
    id = Column(Integer, primary_key = True)
    space = Column(String, nullable=False, )
    name = Column(String, nullable=False, unique=True )
    __table_args__ = (Index('history_source_index', "space", "name", unique=True), )    
    
class ValueHistoryEntry(Base):
    __tablename__ = "history_value"
    source_id = Column(Integer, ForeignKey('history_source.id'), primary_key=True )
    source = relationship( HistorySource, backref=backref('history', uselist=True, cascade='delete,all'))
    value = Column(Float, nullable=False)
    bottom = Column(Float)
    top = Column(Float)
    unit = Column(String)
    upd_date = Column(DateTime, primary_key=True)
    
    def __init__(self,sourceObj,value,unit,upd_date):
        self.source = sourceObj
        self.value = value
        self.unit = unit
        self.upd_date = upd_date
        
    def __repr__(self):
        return "<'{0}.{1}' {2} {3} @ {4}>".format(self.source.space, self.source.name, self.value, self.unit, self.upd_date)
        
    
class ValueHistoryStore:
    def __init__(self,database_conn_str):
        self.database_conn_str = database_conn_str
        self.engine = create_engine(self.database_conn_str, echo=False)
        self.sourceDict = dict()
        
    def getSource(self, space, source):
        if space is None or source is None:
            raise HistoryException('Space or source cannot be None')
        if (space, source) in self.sourceDict:
            s = self.sourceDict[(space,source)]
            self.session.add(s)
            return s
        else:
            s = HistorySource( space=space, name=source )
            self.session.add(s)
            self.sourceDict[(space,source)] = s
            return s
        
    def refreshSourceDict(self):
        self.sourceDict = dict( [((s.space, s.name), s) for s in self.session.query(HistorySource).all()] )
        return self.sourceDict    
        
    def getHistory(self, space, source, fromTime, toTime ):
        return self.session.query(ValueHistoryEntry).filter(ValueHistoryEntry.source==self.getSource(space, source)).\
                                              filter(ValueHistoryEntry.upd_date>fromTime).\
                                              filter(ValueHistoryEntry.upd_date<toTime).order_by(ValueHistoryEntry.upd_date).all()
        
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
        self.refreshSourceDict()
        return self
        
    def __exit__(self, exittype, value, tb):
        self.session.commit()
        
    def add(self, space, source, value, unit, upd_date, bottom=None, top=None):
        if is_magnitude(value):
            value, unit = value.toval(returnUnit=True)
            if is_magnitude(bottom):
                bottom = bottom.toval(unit)
            if is_magnitude(top):
                top = top.toval(unit)           
        if space is not None and source is not None:
            paramObj = self.getSource(space, source)
            elem = ValueHistoryEntry(paramObj, value, unit, upd_date)
            self.session.add(elem)
            elem.value = value
            if bottom is not None:
                elem.bottom = bottom
            if top is not None:
                elem.top = top
            self.commit()
        
    def get(self, space, source ):
        return self.session.query(ValueHistoryEntry).filter(ValueHistoryEntry.source==self.getSource(space, source) )
                    
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
        d.add('test', 'Peter', 12, 'mm', datetime.datetime.now())
        d.add('test', 'Peter', 13, 'mm', datetime.datetime.now())
        d.add('test', 'Peter', 14, 'mm', datetime.datetime.now(), bottom=3, top=15 )
        

