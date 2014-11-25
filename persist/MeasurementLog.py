'''
Created on Nov 21, 2014

@author: pmaunz
'''
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Interval, Float, Boolean
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy import create_engine
from modules.magnitude import mg, is_magnitude
from sqlalchemy.exc import OperationalError, InvalidRequestError, IntegrityError,\
    ProgrammingError
import logging
from sqlalchemy.sql.schema import ForeignKey
from modules.Observable import Observable
from sqlalchemy.orm.collections import attribute_mapped_collection
import weakref

Base = declarative_base()

class Study(Base):
    __tablename__ = "studies"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    startDate = Column(DateTime(timezone=True))
    endDate = Column(DateTime(timezone=True))

class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True)
    scanType = Column(String, nullable=False)
    scanName = Column(String, nullable=False)
    scanParameter = Column(String)
    evaluation = Column(String, nullable=False)
    startDate = Column(DateTime(timezone=True))
    duration = Column(Interval)
    filename = Column(String)
    comment = Column(String)
    longComment = Column(String)
    study_id = Column(Integer, ForeignKey('studies.id'))
    study = relationship( "Study", backref=backref('measurements', order_by=id))
    
    def __init__(self, *args, **kwargs):
        super(Measurement, self).__init__(*args, **kwargs)
        self._plottedTraceList = list()
        self.isPlotted = None
        
    def addResult(self, result):
        self.results.append( result )
        
    @property
    def plottedTraceList(self):
        self._plottedTraceList = [item for item in self._plottedTraceList if item() is not None] if hasattr(self,'_plottedTraceList') else list()
        return [item() for item in self._plottedTraceList]
    
    @plottedTraceList.setter
    def plottedTraceList(self, plottedTraceList):
        self._plottedTraceList = [weakref.ref(item) for item in plottedTraceList]
        
    def parameterByName(self, space, name):
        if not hasattr(self, '_parameterIndex') or len(self._parameterIndex) != len(self.parameters):
            self._parameterIndex = dict( ((param.space.name, param.name), index) for index, param in enumerate(self.parameters)  )
        return self.parameters[ self._parameterIndex[(space,name)] ] if (space,name) in self._parameterIndex else None
            
    def resultByName(self, name):
        if not hasattr(self, '_resultIndex') or len(self._resultIndex) != len(self.results):
            self._resultIndex = dict( (result.name, index) for index, result in enumerate(self.results)  )
        return self.results[ self._resultIndex[name] ] if name in self._resultIndex else None
            
        

class Space(Base):
    __tablename__ = 'space'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)    

class Result(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    _value = Column(Float)
    _bottom = Column(Float)
    _top = Column(Float) 
    unit = Column(String)
    manual = Column(Boolean, default=False)
    measurement_id = Column(Integer, ForeignKey('measurements.id'))
    measurement = relationship( "Measurement", backref=backref('results', order_by=id))
    
    def __init__(self, *args, **kwargs):
        updates = [(param, kwargs.pop(param)) for param in ['value', 'bottom', 'top'] if param in kwargs] 
        super( Result, self ).__init__(*args, **kwargs)
        for name, value in updates:
            setattr( self, name, value)

    @property
    def value(self):
        return mg( self._value, self.unit ) if self._value is not None else None
    
    @value.setter
    def value(self, magValue ):
        if self.unit is None:
            if is_magnitude(magValue):
                self._value, self.unit = magValue.toval( returnUnit=True )
            else:
                self._value = magValue
        else:
            self._value = magValue.toval(self.unit)
        
    @property
    def bottom(self):
        return mg( self._bottom, self.unit ) if self._bottom is not None else None
    
    @bottom.setter
    def bottom(self, magValue ):
        if self.unit is None:
            if is_magnitude(magValue):
                self._bottom, self.unit = magValue.toval( returnUnit=True )
            else:
                self._bottom = magValue
        else:
            self._bottom = magValue.toval(self.unit)
        
    @property
    def top(self):
        return mg( self._top, self.unit ) if self._top is not None else None
    
    @top.setter
    def top(self, magValue ):
        if self.unit is None:
            if is_magnitude(magValue):
                self._top, self.unit = magValue.toval( returnUnit=True )
            else:
                self._top = magValue
        else:
            self._top = magValue.toval(self.unit)
        
class Parameter(Base):
    __tablename__ = 'parameters'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    _value = Column(Float)
    unit = Column(String)
    definition = Column(String)
    manual = Column(Boolean, default=False)
    measurement_id = Column(Integer, ForeignKey('measurements.id'))
    measurement = relationship( "Measurement", backref=backref('parameters', order_by=id)) # , collection_class=attribute_mapped_collection('name')
    space_id = Column(Integer, ForeignKey('space.id'))
    space = relationship( "Space", backref=backref('parameters', order_by=id))
    
    def __init__(self, *args, **kwargs):
        if 'value' in kwargs:
            myvalue = kwargs['value']
            kwargs.pop('value')
            super( Parameter, self ).__init__(*args, **kwargs)
            self.value = myvalue
        else:
            super( Parameter, self ).__init__(*args, **kwargs)
            
    
    @property
    def value(self):
        return mg( self._value, self.unit )
    
    @value.setter
    def value(self, magValue ):
        if is_magnitude(magValue):
            self._value, self.unit = magValue.toval( returnUnit=True )
        else:
            self._value = magValue
        
class MeasurementContainer(object):
    def __init__(self,database_conn_str):
        self.database_conn_str = database_conn_str
        self.engine = create_engine(self.database_conn_str, echo=True)
        self.studies = list()
        self.measurements = list()
        self.spaces = list()
        self.isOpen = False
        self.beginInsertMeasurement = Observable()
        self.endInsertMeasurement = Observable()
        self.studiesObservable = Observable()
        self.measurementsUpdated = Observable()
        
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
            self.session.add( measurement )
            self.session.commit()
            self.beginInsertMeasurement.fire(first=len(self.measurements),last=len(self.measurements))
            self.measurements.append( measurement )
            self.endInsertMeasurement.firebare()
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
        
    def query(self, fromTime, toTime):
        self.measurements = self.session.query(Measurement).filter(Measurement.startDate>=fromTime).filter(Measurement.startDate<=toTime).order_by(Measurement.id).all()
        self.measurementsUpdated.fire(measurements=self.measurements)
    
    def refreshLookups(self):
        """Load the basic short tables into memory
        those are: Space"""
        try:
            self.spaces = dict(( (s.name,s) for s in self.session.query(Space).all() ))
        except (InvalidRequestError, IntegrityError, ProgrammingError) as e:
            logging.getLogger(__name__).error( str(e) )
            self.session.rollback()
            self.session = self.Session()
        
    def getSpace(self, name):
        if name not in self.spaces:
            self.refreshLookups()
        if name in self.spaces:
            return self.spaces[name]
        s = Space(name=name)
        self.spaces[name] = s
        return s
        
if __name__=='__main__':
    with MeasurementContainer("postgresql://python:yb171@localhost/ioncontrol") as d:
        d.addMeasurement( Measurement(scanName='test'))

        
    