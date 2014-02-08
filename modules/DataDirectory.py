# -*- coding: utf-8 -*-
"""
Created on Wed Dec 19 11:21:41 2012

Open the default data directory
<DataDirectoryBase>\<project>\2013\01\37
missing directories below the project directory are created.
It is also used to generate file serials. For serial determination, the directory is read every time.

@author: plmaunz
"""
import datetime
import functools
import os.path
import re


class DataDirectoryException(Exception):
    pass

DataDirectoryBase = os.path.expanduser("~public\\Documents\\experiments")
DefaultProject = None

class DataDirectory:
    def __init__(self,project=None,basedirectory=None):
        self.project = project if project else DefaultProject
        global DataDirectoryBase
        if basedirectory:
            DataDirectoryBase = basedirectory
            
    
    def setProject(self,project):
        self.project = project
    
    def path(self, current=None):
        if not current:
            current = datetime.date.today()
        #basedir = os.path.join(os.path.expanduser("~\\Documents\\"),self.project)
        basedir = os.path.join(DataDirectoryBase,self.project)
        yeardir = os.path.join(basedir,str(current.year))
        monthdir = os.path.join(yeardir,"{0}_{1:02d}".format(current.year,current.month))
        daydir = os.path.join(monthdir,"{0}_{1:02d}_{2:02d}".format(current.year,current.month,current.day))
        if not os.path.exists(basedir):
            raise DataDirectoryException("Data directory '{0}' does not exist.".format(basedir))
        if not os.path.exists(daydir):
            os.makedirs(daydir)
        return daydir;
        
    def sequencefile(self,name,  current=None):
        """
        return the sequenced filename in the current data directory.
        _000 serial is inserted before the file extension or at the end of the name if the filename has no extension.
        The directory is reread every time.
        """
        if not current:
            current = datetime.date.today()
        """
        return the sequenced filename in the current data directory.
        _000 serial is inserted before the file extension or at the end of the name if the filename has no extension.
        The directory is reread every time.
        """
        directory = self.path(current)
        fileName, fileExtension = os.path.splitext(name)
        pattern = re.compile(re.escape(fileName)+"_(?P<num>\\d+)"+re.escape(fileExtension))
        maxNumber = 0
        for name in os.listdir(directory):
            m = pattern.match(name)
            if m!=None:
                maxNumber = max(int(m.group('num')),maxNumber)
        return os.path.join(directory,"{0}_{1:03d}{2}".format(fileName,maxNumber+1,fileExtension)), ( directory, "{0}_{1:03d}".format(fileName,maxNumber+1), fileExtension )
        
    def datafilelist(self,name,date):
        """ return a list of files in the results directory of date "date" order by serial number """
        directory = self.path(date)
        fileName, fileExtension = os.path.splitext(name)
        pattern = re.compile(re.escape(fileName)+"_(?P<num>\\d+)"+re.escape(fileExtension))
        fileList = list()
        numberList = list()
        for name in os.listdir(directory):
            m = pattern.match(name)
            if m!=None:
                fileList.append(name)
                numberList.append(int(m.group('num')))
        return map( functools.partial( os.path.join, directory), fileList ), numberList
         
        
if __name__ == "__main__":
    d = DataDirectory("HOA")    
    print d.path()
    print d.sequencefile("test.txt")