# -*- coding: utf-8 -*-
"""
Created on Fri May 24 14:46:16 2013

@author: wolverine
"""

from modules import DataDirectory
from array import array
import hashlib
import shutil

class RawData(object):
    def __init__(self):
        self.open = False
        self.hash = hashlib.sha256()
        self.datafile = None
        self.datafilename = None
        self.filenametemplate = None
    
    def _add(self,data,datatype):
        if not self.datafile:
            self.datafilename, _ = DataDirectory.DataDirectory().sequencefile( "RawData.bin" )
            self.datafile = open( self.datafilename, 'wb' )
        data_array = array(datatype, data)
        self.hash.update(data_array)
        data_array.tofile(self.datafile)
    
    def addFloat(self, data):
        self._add(data,'d')

    def addInt(self,data):
        self._add(data,'L')
    
    def save(self,name=None):
        if name and not self.filenametemplate:   # we are currently on a temp file
            self.datafile.close()
            newdatafilename, _ = DataDirectory.DataDirectory().sequencefile( name )
            shutil.move( self.datafilename, newdatafilename )
            self.datafilename = newdatafilename
            self.datafile = open( self.datafilename, 'wb+' )
            self.filenametemplate = name
        return self.datafilename, self.hash.hexdigest()
        
    def delete(self):
        pass
    
    def hexdigest(self):
        return self.hash.hexdigest()
    
    def close(self):
        if self.datafile:
            self.datafile.close()
        return self.hash.hexdigest()
    
    
if __name__=="__main__":
    DataDirectory.DefaultProject = "testproject"
    rd = RawData()
    rd.addFloat( range(200) )
    print rd.save("Peter.txt")
    print rd.close()
    
    filename, components = DataDirectory.DataDirectory().sequencefile( "TestTrace.txt" )    
    
    from trace import Trace
    tr = Trace.Trace()
    tr.x = range(200)
    tr.y = range(200)
    tr.rawdata = RawData()
    tr.rawdata.addInt( range(200) )
    tr.saveTrace(filename)
    
    