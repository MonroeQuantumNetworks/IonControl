'''
Created on Feb 27, 2015

@author: wolverine
'''
from enum import Enum

class StrEnum(str,Enum):
    __order__ = 'x time index'
    x = 'x'
    time = 'time'
    index = 'index'
    
    
class MyEnum(Enum):
    x = 1
    time = 2
    index = 3
    
    
a = StrEnum.x
print a
print a.name
b = StrEnum('x')
print b
print a==b
print [ e.name for e in StrEnum]

c = MyEnum.time
print c.name
