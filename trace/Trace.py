# -*- coding: utf-8 -*-
"""
Created on Sun Dec 23 19:27:39 2012

@author: pmaunz

This is the class in which the data associated with a single trace is stored.

"""

from datetime import datetime
import io
from itertools import izip_longest
import math
import os.path

import numpy

from modules.XmlUtilit import prettify
from modules.enum import enum
import xml.etree.ElementTree as ElementTree
import time
from modules.SequenceDictSignal import SequenceDictSignal as SequenceDict

try:
    from fit import FitFunctions
    FitFunctionsAvailable = True
except:
    FitFunctionsAvailable = False

class TraceException(Exception):
    pass

class ColumnSpec(list):
    def toXmlElement(self, root):
        myElement = ElementTree.SubElement(root, 'ColumnSpec', {})
        myElement.text = ", ".join( self )
        return myElement
    
    @staticmethod
    def fromXmlElement(element):
        return ColumnSpec( element.text.split(", ") )
    
class TracePlotting(object):
    Types = enum('default','steps')
    def __init__(self, xColumn='x',yColumn='y',topColumn=None,bottomColumn=None,heightColumn=None,
                 rawColumn=None,name="",type_ =None, xAxisUnit=None, xAxisLabel=None, windowName=None ):       
        self.xColumn = xColumn
        self.yColumn = yColumn
        self.topColumn = topColumn
        self.bottomColumn = bottomColumn
        self.heightColumn = heightColumn
        self.rawColumn = rawColumn
        self.fitFunction = None
        self.name = name
        self.xAxisUnit = xAxisUnit
        self.xAxisLabel = xAxisLabel
        self.type = TracePlotting.Types.default if type_ is None else type_
        self.windowName = windowName
        
    def __setstate__(self, d):
        self.__dict__ = d
        self.__dict__.setdefault( 'xAxisUnit', None )
        self.__dict__.setdefault( 'xAxisLabel', None )
        self.__dict__.setdefault( 'windowName', None)
        
    attrFields = ['xColumn','yColumn','topColumn', 'bottomColumn','heightColumn', 'name', 'type', 'xAxisUnit', 'xAxisLabel', 'windowName']

class TracePlottingList(list):        
    def toXmlElement(self, root):
        myElement = ElementTree.SubElement(root, 'TracePlottingList', {})
        for traceplotting in self:
            traceplottingElement = ElementTree.SubElement(myElement, 'TracePlotting', dict( (name,str(getattr(traceplotting,name))) for name in TracePlotting.attrFields))
            if traceplotting.fitFunction:
                traceplotting.fitFunction.toXmlElement(traceplottingElement)
        return myElement
    
    @staticmethod
    def fromXmlElement(element):
        l = TracePlottingList()
        for plottingelement in element.findall("TracePlotting"):
            plotting = TracePlotting()
            plotting.__dict__.update( plottingelement.attrib )
            plotting.type = int(plotting.type) if hasattr(plotting,'type') else 0
            if plottingelement.find("FitFunction") is not None:
                plotting.fitFunction = FitFunctions.fromXmlElement( plottingelement.find("FitFunction") )
            l.append(plotting)
        return l    
    
    def __str__(self):
        return "TracePlotting length {0}".format(len(self))        

varFactory = { 'str': str,
               'datetime': lambda s: datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f'),
               'float': float,
               'int': int }
    

class Trace(object):
    
    """ Class to encapsulate one displayed trace. 
    
    instance variables:
    _x -- array of x values
    _y -- array of y values
    name -- name to display in table of traces
    description --
        description["comment"] -- comment to add to file
        description["traceCreation"] -- the time the Trace object was created
    header --
    curvePen -- which style pen to use for displaying the trace
    _filename -- filename to save the trace as
    
    The data can be saved to and loaded
    from a file.
    """

    def __init__(self, record_timestamps=False):
        """Construct a trace object."""
        self._x_ = numpy.array([]) #array of x values
        self._y_ = numpy.array([]) #array of y values
        self.name = "noname" #name to display in table of traces
        self.description = SequenceDict()
        self.description["comment"] = ""
        self.description["traceCreation"] = datetime.now()
        self.header = None
        self.headerDict = dict()
        self._filename = None
        self.filenameCallback = None   # function to result in filename for save
        self.dataChangedCallback = None # used to update the gui table
        self.rawdata = None
        self.columnNames = ['height', 'top', 'bottom','raw']
        self.description["tracePlottingList"] = TracePlottingList()
        self.record_timestamps = record_timestamps
        if record_timestamps:
            self.addColumn('timestamp')
        
    def varFromXmlElement(self, element, description):       
        name = element.attrib['name']
        mytype = element.attrib['type']
        if mytype=='dict':
            mydict = SequenceDict()
            for subelement in element:
                self.varFromXmlElement(subelement, mydict)
            description[name] = mydict
        else:
            value = varFactory.get( mytype, str)( element.text )
            description[name] = value
    
    @property
    def x(self):
        """Get x array"""
        return self._x_
        
    @x.setter
    def x(self, val):
        """Set x array"""
        self._x_ = val
        self.description["lastDataAquired"]  = datetime.now()
        if self.record_timestamps:
            self.timestamp = numpy.append( self.timestamp, time.time() )
        
    @property
    def y(self):
        """Get y array"""
        return self._y_
        
    @y.setter
    def y(self,val):
        """Set y array, and record the time it was set."""
        self._y_ = val
         
    def getFilename(self):
        """return the filename if no filename is available get a filename using the callback"""
        if not self._filename and self.filenameCallback:
            self.filename = self.filenameCallback()
            self.resave()
        return self._filename
          
    @property
    def filename(self):
        """Get the full pathname of the file."""
        return self._filename
        
    @filename.setter
    def filename(self, filename):
        """ setter for the full pathname of the file
        upon resave, the data gets saved into this file
        """
        self._filename = filename    
        if filename:
            self.filepath, self.fileleaf = os.path.split(filename)
        else:
            self.filepath, self.fileleaf = None, None
        if self.dataChangedCallback:
            self.dataChangedCallback()                            
        
    @property
    def xUnit(self):
        return self.description.get('xUnit')
    
    @xUnit.setter
    def xUnit(self, magnitude):
        self.description['xUnit'] = magnitude
        
    @property
    def yUnit(self):
        return self.description.get('yUnit')
    
    @yUnit.setter
    def yUnit(self, magnitude):
        self.description['yUnit'] = magnitude
        
        
        
    def resave(self, saveIfUnsaved=True):
        """ save the data to the filename set previously by writing to filename
        """
        if hasattr(self, 'filename' ) and self.filename and self.filename!='':
            self.saveTrace(self.filename)
        elif self.filenameCallback and saveIfUnsaved:
            self.saveTrace(self.filenameCallback())
        return self._filename
    
    def deleteFile(self):
        """ delete the file from disk
        """
        if hasattr(self, 'filename' ) and self.filename and self.filename!='':
            os.remove(self.filename)
    
    def plot(self,penindex):
        """ plot the data, penindex >= 0 gives requests the style with this number,
        penindex = -1 uses the first available style, penindex = -2 uses the previous style
        """
        if hasattr( self, 'plotfunction' ):
            (self.plotfunction)(self,penindex)
    
    def varstr(self,name):
        """return the variable value as a string"""
        return str(self.description.get(name,""))
        
    def saveTraceHeader(self,outfile):
        """ save the header of the trace to outfile
        """
        self.description["fileCreation"] = datetime.now()
        self.description.sort()
        for var, value in self.description.iteritems():
            print >>outfile, "# {0}\t{1}".format(var, value)
        if self.header is not None:
            print >>outfile, self.header
            
    def saveTraceHeaderXml(self,outfile):
        root = ElementTree.Element('DataFileHeader')
        varsElement = ElementTree.SubElement(root, 'Variables', {})
        self.description.sort()
        for name, value in self.description.iteritems():
            self.saveDescriptionElement(name, value, varsElement)
        if self.header:
            e = ElementTree.SubElement(varsElement, 'Header', {})
            e.text = self.header        
        outfile.write(prettify(root,'# '))
        
    def saveDescriptionElement(self, name, value, element):
        if hasattr(value,'toXmlElement'):
            value.toXmlElement(element)
        elif isinstance(value, dict):
            subElement = ElementTree.SubElement(element, 'Element', {'name': name, 'type': 'dict'})
            for subname, subvalue in value.iteritems():
                self.saveDescriptionElement(subname, subvalue, subElement)           
        else:
            e = ElementTree.SubElement(element, 'Element', {'name': name, 'type': type(value).__name__})
            e.text = str(value)

    def saveTraceBare(self,filename):
        if self.rawdata:
            self.description["rawdata"] = self.rawdata.save()
        if hasattr(self,'fitfunction'):
            self.description['fitfunction'] = self.fitfunction
        if filename!='':
            of = open(filename,'w')
            columnlist = [self._x_]
            columnspec = ['x']
            if len(self._y_)>0:
                columnlist += [self._y_]
                columnspec += ['y']
            for column in self.columnNames:
                if hasattr(self, column):
                    columnlist.append( getattr(self,column) )
                    columnspec.append( column )
            self.description["columnspec"] = ",".join(columnspec)
            self.saveTraceHeader(of)
            for l in zip(*columnlist):
                print >>of, "\t".join(map(repr,l))
            self.filename = filename
            of.close()

    def saveTrace(self,filename):
        # move the timestamp column to the end
        if self.record_timestamps and 'timestamp' in self.columnNames:
            self.columnNames.append( self.columnNames.pop(self.columnNames.index('timestamp')))
        if self.rawdata:
            self.description["rawdata"] = self.rawdata.save()
        if hasattr(self,'fitfunction'):
            self.description["fitfunction"] = self.fitfunction
        if filename!='':
            of = open(filename,'w')
            columnlist = [self._x_]
            columnspec = ColumnSpec(['x'])
            if len(self._y_)>0:
                columnlist += [self._y_]
                columnspec += ['y']
            for column in self.columnNames:
                if hasattr(self, column):
                    columnlist.append( getattr(self,column) )
                    columnspec.append( column )
            self.description["columnspec"] = columnspec #",".join(columnspec)
            self.saveTraceHeaderXml(of)
            for l in izip_longest(*columnlist, fillvalue=float('NaN')):
                print >>of, "\t".join(map(repr,l))
            self.filename = filename
            of.close()
    
    def loadTrace(self,filename):
        with io.open(filename,'r') as instream:
            position = instream.tell()
            firstline = instream.readline()
            instream.seek(position)
            if firstline.find("<?xml version")>0:
                self.loadTraceXml(instream)
            else:
                self.loadTraceText(instream)
                self.description["tracePlottingList"].append(TracePlotting())
        self.filename = filename

        
    def loadTraceXml(self, stream):
        xmlstringlist = []
        data = []
        for line in stream:
            if line[0]=="#":
                xmlstringlist.append(line.lstrip("# "))
            else:
                data.append( map(float,line.split()) )
        root = ElementTree.fromstringlist(xmlstringlist)
        columnspec = ColumnSpec.fromXmlElement(root.find("./Variables/ColumnSpec"))
        for attr,d in zip( columnspec, zip(*data) ):
            if math.isnan(d[-1]):
                a = numpy.array( d[0:-1])
            else:
                a = numpy.array(d)
            setattr( self, attr, a )
        tpelement = root.find("./Variables/TracePlottingList")
        self.description["tracePlottingList"] = TracePlottingList.fromXmlElement(tpelement) if tpelement is not None else None
        for element in root.findall("./Variables/Element"):
            self.varFromXmlElement(element, self.description)
        for header in root.findall("./Variables/Header"):
            for line in header.text.splitlines():
                try:
                    key, value = line.split(None,1)
                    self.headerDict[key] = value
                except ValueError:
                    pass
                    
        
    def loadTraceText(self, stream):    
        data = []
        self.description["columnspec"] = "x,y"
        for line in stream:
            line = line.strip()
            if line[0]=='#':
                line = line.lstrip('# \t\r\n')
                if line.find('\t')<0:
                    a = line.split(None,1)
                else:
                    a = line.split('\t',1)
                if len(a)>1:
                    self.description[a[0]] = a[1]  
            else:
                data.append( map(float,line.split()) )
        columnspec =  self.description["columnspec"].split(',')
        for attr,d in zip( columnspec, zip(*data) ):
            setattr( self, attr, numpy.array(d) )
        if 'fitfunction' in self.description and FitFunctionsAvailable:
            self.fitfunction = FitFunctions.fitFunctionFactory(self.description["fitfunction"])
        self.description["tracePlottingList"] = [TracePlotting(xColumn='x',yColumn='y',topColumn=None,bottomColumn=None,heightColumn=None, rawColumn=None,name="")]
            
    def addColumn(self, name, ignoreExisting=False):
        """ adds a column with the given name, the column is saved in the file in the order added
        """
        if hasattr( self, name):
            if not ignoreExisting:
                raise TraceException("cannot add column '{0}' trace already has attribute with this name.".format(name))
        else:
            self.columnNames.append(name)
            setattr( self, name, numpy.array([]))
            
    
    def setPlotfunction(self, callback):
        self.plotfunction = callback
        
    def addTracePlotting(self, traceplotting):
        self.description["tracePlottingList"].append(traceplotting)
        
    @property 
    def tracePlottingList(self):
        return self.description["tracePlottingList"]
    
#     def __del__(self):
#         print "Deleting Trace"
#         
        
if __name__=="__main__":
    import sys
    import gc
    t = Trace()
    print sys.getrefcount(t)
    del t
    gc.collect()
