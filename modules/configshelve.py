# -*- coding: utf-8 -*-
"""
Created on Sun Dec 30 22:39:45 2012

Wrapper for python shelve module to be able to use it with the with expression.
It also includes default directory for storing of config files.

@author: pmaunz
"""

import os
import shelve
import shutil

class configshelve:
    def __init__(self,name,directory="~\\AppData\\Local\\python-control\\"):
        configdir = os.path.expanduser(directory)
        if not os.path.exists(configdir):
            os.makedirs(configdir)
        self.configfile = os.path.join(configdir,name+".config")
        #print "configshelve", self.configfile
        self.isOpen = False

    def __enter__(self):
        self.config = shelve.open(self.configfile)
        self.isOpen = True
        return self.config
        
    def __exit__(self, type, value, tb):
        self.config.close()
        self.isOpen = False
        
    def __iter__(self):
        return self.config.__iter__()
        
    def __setitem__(self, key, value):
        self.config.__setitem__(key, value)
        
    def __getitem__(self, key):
        return self.config.__getitem__(key)
        
    def get(self, key, default=None):
        return self.config.get(key,default)
        
    def next(self):
        return self.config.next()
        
    def open(self):
        #print "configshelve open", self.configfile
        self.config = shelve.open(self.configfile)
        self.isOpen = True
        return self.config
        
    def close(self):
        #print "configshelve close", self.configfile
        self.config.close()
        self.isOpen = False
        shutils.copy2( self.configfile, self.configfile+".bak" )
        
if __name__ == "__main__":
    with configshelve("test") as d:
        if 'Peter' in d:
            print d['Peter']
        mydict = { 'first':'Peter','last':'Maunz' }
        if 'dict' in d:
            print d['dict']
        d['Peter'] = 'Maunz'
        d['dict'] = mydict
        
