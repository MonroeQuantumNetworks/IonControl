# -*- coding: utf-8 -*-
"""
Created on Wed Dec 19 11:21:41 2012

@author: plmaunz
"""
import datetime
import os.path
import re

class DataDirectoryException(Exception):
    pass

class DataDirectory:
    def __init__(self,project):
        self.project = project
    
    def setProject(self,project):
        self.project = project
    
    def path(self, current=datetime.date.today()):
        basedir = os.path.join(os.path.expanduser("~\\Documents\\"),self.project)
        yeardir = os.path.join(basedir,str(current.year))
        monthdir = os.path.join(yeardir,"{0}_{1:02d}".format(current.year,current.month))
        daydir = os.path.join(monthdir,"{0}_{1:02d}_{2:02d}".format(current.year,current.month,current.day))
        if not os.path.exists(basedir):
            raise DataDirectoryException("Project directory does not exist")
        if not os.path.exists(daydir):
            os.makedirs(daydir)
        return daydir;
        
    def sequencefile(self,name,  current=datetime.date.today()):
        directory = self.path(current)
        fileName, fileExtension = os.path.splitext(name)
        pattern = re.compile(re.escape(fileName)+"_(?P<num>\\d+)"+re.escape(fileExtension))
        maxNumber = 0
        for name in os.listdir(directory):
            m = pattern.match(name)
            if m!=None:
                maxNumber = max(int(m.group('num')),maxNumber)
        return os.path.join(directory,"{0}_{1:03d}{2}".format(fileName,maxNumber+1,fileExtension)), ( directory, "{0}_{1:03d}".format(fileName,maxNumber+1), fileExtension )
         
        
if __name__ == "__main__":
    d = DataDirectory("QGA")    
    print d.path()
    print d.sequencefile("test.txt")