# -*- coding: utf-8 -*-
"""
Created on Fri May 24 14:46:16 2013

@author: wolverine
"""

from modules.DataDirectory import DataDirectory
from array import array

class RawData(object):
    def __init__(self):
        self.open = False
    
    def addFloat(self, data):
        if not self.open:
            self.tempfilename, components = DataDirectory().sequencefile( "RawData_temp.bin" )
            self.tempfile = open( self.tempfilename, 'wb' )
            float_array = array('d', data)
            float_array.tofile(self.tempfile)
    
    def save(self,name):
        return name
        
    def delete(self):
        pass
    
    