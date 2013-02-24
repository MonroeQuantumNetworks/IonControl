# -*- coding: utf-8 -*-
"""
Created on Sun Dec 30 22:39:45 2012

@author: pmaunz
"""

import os
import shelve

class configshelve:
    def __init__(self,name):
        configdir = os.path.expanduser("~\\AppData\\Local\\python-control\\")
        if not os.path.exists(configdir):
            os.makedirs(configdir)
        self.configfile = os.path.join(configdir,name+".config")

    def __enter__(self):
        self.config = shelve.open(self.configfile)
        return self.config
        
    def __exit__(self, type, value, tb):
        self.config.close()
        
    def __iter__(self):
        return self.config.__iter__()
        
    def __setitem__(self, key, value):
        self.config.__setitem__(key, value)
        
    def __getitem__(self, key):
        return self.config.__getitem__(key)
        
    def next(self):
        return self.config.next()
        
    def open(self):
        print "configshelve open", self.configfile
        self.config = shelve.open(self.configfile)
        return self.config
        
    def close(self):
        print "configshelve close", self.configfile
        self.config.close()
        
if __name__ == "__main__":
    with configshelve("test") as d:
        if 'Peter' in d:
            print d['Peter']
        d['Peter'] = 'Maunz'
        
