'''
Created on Jun 27, 2014

@author: pmaunz
'''


from modules.SequenceDict import SequenceDict

class Test(object):
    def __init__(self):
        self.__dict__ = SequenceDict()
        
a = Test()

a.a = 1
a.b = 2
a.__dict__['c'] = 3


print a.a
print a.b
print a.__dict__