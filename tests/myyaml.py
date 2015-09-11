__author__ = 'pmaunz'

import yaml

class Test:
    def __init__(self):
        self.peter = 42
        self.s = "Dies ist ein string"

t = Test()
t2 = [t,t]
print yaml.dump({t:t}, default_flow_style=False)