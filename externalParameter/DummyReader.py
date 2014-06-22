'''
Created on May 16, 2014

@author: wolverine
'''
from time import sleep
import random
import logging

class DummyReader:
    def __init__(self, port=0, timeout=1):
        self.readTimeout = timeout
        logging.getLogger(__name__).info("Created class dummy")
        
    def open(self):
        pass
        
    def close(self):
        pass
                
    def value(self):
        sleep(self.readTimeout)
        value = random.gauss(1,0.1)
        logging.getLogger(__name__).info("dummy reading value {0}".format(value))
        return value
    
    
    