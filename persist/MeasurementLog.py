'''
Created on Nov 21, 2014

@author: pmaunz
'''
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Interval, Float
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy import create_engine
from modules.magnitude import mg
from sqlalchemy.exc import OperationalError, InvalidRequestError, IntegrityError
import logging
from sqlalchemy.sql.schema import ForeignKey

Base = declarative_base()

class Study(Base):
    __tablename__ = "studies"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    startDate = Column(DateTime(timezone=True))
    endDate = Column(DateTime(timezone=True))

class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True)
    scanType = Column(String, nullable=False)
    scanName = Column(String, nullable=False)
    evaluation = Column(String, nullable=False)
    startDate = Column(DateTime(timezone=True))
    duration = Column(Interval)
    filename = Column(String)
    title = Column(String)
    comment = Column(String)
    study_id = Column(Integer, ForeignKey('studies.id'))
    study = relationship( "Study", backref=backref('measurements', order_by=id))
    
    def addResult(self, result):
        self.results.append( result )

class Space(Base):
    __tablename__ = 'space'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)    

class Result(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    _value = Column(Float, nullable=False)
    _bottom = Column(Float)
    _top = Column(Float) 
    unit = Column(String)
    measurement_id = Column(Integer, ForeignKey('measurements.id'))
    measurement = relationship( "Measurement", backref=backref('results', order_by=id))
    
    @property
    def value(self):
        return mg( self._value, self._unit )
    
    @value.setter
    def value(self, magValue ):
        if self.unit is None:
            self._value, self._unit = magValue.toval( returnUnit=True )
        else:
            self._value = magValue.toval(self.unit)
        
    @property
    def bottom(self):
        return mg( self._bottom, self._unit )
    
    @bottom.setter
    def bottom(self, magValue ):
        if self.unit is None:
            self._bottom, self._unit = magValue.toval( returnUnit=True )
        else:
            self._bottom = magValue.toval(self.unit)
        
    @property
    def top(self):
        return mg( self._top, self._unit )
    
    @top.setter
    def top(self, magValue ):
        if self.unit is None:
            self._top, self._unit = magValue.toval( returnUnit=True )
        else:
            self._top = magValue.toval(self.unit)
        
class Parameter(Base):
    __tablename__ = 'parameters'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    _value = Column(Float, nullable=False)
    unit = Column(String)
    definition = Column(String)
    measurement_id = Column(Integer, ForeignKey('measurements.id'))
    measurement = relationship( "Measurement", backref=backref('parameters', order_by=id))
    space_id = Column(Integer, ForeignKey('space.id'))
    measurement = relationship( "Space", backref=backref('parameters', order_by=id))
    
    @property
    def value(self):
        return mg( self._value, self._unit )
    
    @value.setter
    def value(self, magValue ):
        self._value, self._unit = magValue.toval( returnUnit=True )
        
class MeasurementContainer(object):
    def __init__(self,database_conn_str):
        self.database_conn_str = database_conn_str
        self.engine = create_engine(self.database_conn_str, echo=False)
        self.studies = list()
        self.measurements = list()
        self.isOpen = False
        
    def open(self):
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.session = self.Session()
        self.isOpen = True
        
    def close(self):
        self.session.commit()
        self.isOpen = False

    def __enter__(self):
        if not self.isOpen:
            self.open()
        return self
        
    def __exit__(self, exittype, value, tb):
        self.session.commit()

    def addMeasurement(self, measurement):
        try:
            self.measurements.append( measurement )
            self.session.add( measurement )
            self.session.commit()
        except (InvalidRequestError, IntegrityError) as e:
            logging.getLogger(__name__).error( str(e) )
            self.session.rollback()
            self.session = self.Session()
        
    def query(self, fromTime, toTime):
        pass
        
if __name__=='__main__':
    with MeasurementContainer("postgresql://python:yb171@localhost/ioncontrol") as d:
        d.addMeasurement( Measurement(scanName='test'))

        
    