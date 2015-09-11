__author__ = 'pmaunz'

import yaml
from modules.file_data_cache import file_data_cache

class Test:
    def __init__(self):
        pass

    @file_data_cache(maxsize=5)
    def load(self, filename):
        with open(filename,'r') as f:
            data = yaml.load(f)
            print "Loading data"
        return data

testdata = range(100)
with open('test.txt','w') as f:
    yaml.dump(testdata,f)

t = Test()
newdata = t.load(filename='test.txt')
newdata = t.load(filename='test.txt')
newdata = t.load(filename='test.txt')
newdata = t.load(filename='test.txt')

with open('test.txt','w') as f:
    yaml.dump(range(200),f)

newdata = t.load(filename='test.txt')

print testdata==newdata