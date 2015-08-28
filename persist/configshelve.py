# -*- coding: utf-8 -*-
"""
Created on Sun Dec 30 22:39:45 2012

Wrapper for python shelve module to be able to use it with the with expression.
It also includes default directory for storing of config files.

@author: pmaunz
"""

import logging
import cPickle as pickle
#import pickle
from shutil import copyfile

from sqlalchemy import Column, String, Binary
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound


Base = declarative_base()
defaultcategory = 'main'
    
class ShelveEntry(Base):
    __tablename__ = "shelve"
    category = Column(String, primary_key=True )
    key = Column(String, primary_key=True)
    pvalue = Column(Binary)
    
    def __init__(self,key,value,category=defaultcategory):
        self.category = category
        self.key = key
        self.pvalue = pickle.dumps(value,2)
        
    def __repr__(self):
        return "<'{0}.{1}' '{2}'>".format(self.category, self.key, self.value)
       
    @property
    def value(self):
        return pickle.loads(self.pvalue)
        
    @value.setter
    def value(self,value):
        self.pvalue = pickle.dumps(value,2)

class configshelve:
    def __init__(self,filename):
        self.configfile = filename
        self.engine = create_engine('sqlite:///'+self.configfile, echo=False)
        
    def saveConfig(self, copyTo=None ):
        self.session.commit()
        if copyTo:
            copyfile( self.configfile, copyTo )
        self.session = self.Session()

    def __enter__(self):
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        return self
        
    def __exit__(self, exittype, value, tb):
        self.session.commit()
        
    def __setitem__(self, key, value):
        if isinstance(key,tuple):
            category, key = key
        else:
            category, key = defaultcategory, key
        try:
            elem = self.session.query(ShelveEntry).filter(ShelveEntry.key==key, ShelveEntry.category==category).one()
        except NoResultFound:
            elem = ShelveEntry(key,value,category)
            self.session.add(elem)
        elem.value = value
        
    def __getitem__(self, key):
        if isinstance(key,tuple):
            category, key = key
        else:
            category, key = defaultcategory, key
        return self.session.query(ShelveEntry).filter(ShelveEntry.key==key, ShelveEntry.category==category).one().value
            
    def __contains__(self, key):
        if isinstance(key,tuple):
            category, key = key
        else:
            category, key = defaultcategory, key
        return self.session.query(ShelveEntry).filter(ShelveEntry.key==key, ShelveEntry.category==category).count()>0
        
    def get(self, key, default=None):
        if isinstance(key,tuple):
            category, key = key
        else:
            category, key = defaultcategory, key
        try:
            return self.session.query(ShelveEntry).filter(ShelveEntry.key==key, ShelveEntry.category==category).one().value
        except (NoResultFound, AttributeError):
            return default
        
    def next(self):
        logging.getLogger(__name__).error("__next__ not implemented")
        
    def open(self):
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.isOpen = True
        
    def close(self):
        self.session.commit()
        self.isOpen = False
        
if __name__ == "__main__":
    with configshelve("new-test.db") as d:
        d['Peter'] = 'Maunz'
        print 'Peter'in d
        print ('Peter', 'main') in d
        print ('main','Peter') in d
        
