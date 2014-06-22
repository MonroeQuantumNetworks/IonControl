'''
Created on May 16, 2014

@author: wolverine
'''
from time import sleep
import random

class DummyReader:
    def __init__(self, port=0, timeout=1):
        self.timeout = timeout
        
    def open(self):
        pass
        
    def close(self):
        pass
                
    def value(self):
        sleep(self.timeout)
        return random.gauss(1,0.1)
    
    
    