'''
Created on Nov 21, 2014

@author: pmaunz
'''
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Interval, Float
from sqlalchemy.orm import relationship, backref
from modules.magnitude import mg

Base = declarative_base()

class Study(Base):
    __tablename__ = "studies"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    startDate = Column(DateTime(timezone=True))
    endDate = Column(DateTime(timezone=True))
    measurements = relationship( "Measurement", order_by="Measurement.id", backref="study")

class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True)
    scanType = Column(String)
    scanName = Column(String)
    evaluation = Column(String)
    startDate = Column(DateTime(timezone=True))
    duration = Column(Interval)
    filename = Column(String)
    title = Column(String)
    comment = Column(String)
    study = relationship( "Study", backref=backref('studies', order_by=id))
    results = relationship( "Result", order_by="Result.id", backref='measurement')
    
class Result(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    _value = Column(Float)
    _bottom = Column(Float)
    _top = Column(Float) 
    unit = Column(String)
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
        


    