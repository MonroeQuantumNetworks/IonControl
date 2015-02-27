'''
Created on Feb 27, 2015

@author: wolverine
'''
from enum import Enum


columnLookup = { 'time': 'timestamp', 'x': 'x', 'index': 'indexColumn'}

class AbszisseType(str, Enum):
    x = 'x'
    time = 'time'
    index = 'index'
        
    @property
    def columnName(self):
        return columnLookup.get( self.value )
    
    
if __name__=="__main__":
    print AbszisseType.time.columnName
    a = AbszisseType.time
    print a.name
    print a.columnName
