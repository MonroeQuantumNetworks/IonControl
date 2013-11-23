# -*- coding: utf-8 -*-
"""
Created on Sun Dec 23 19:27:39 2012

@author: pmaunz

This is the class in which the data associated with a single trace is stored.

"""

import numpy
from datetime import datetime
import os.path
import xml.etree.ElementTree as ElementTree
from modules.XmlUtilit import prettify
import xml.dom.minidom as dom
import io

try:
    import FitFunctions
    FitFunctionsAvailable = True
except:
    FitFunctionsAvailable = False

class Empty:
    pass

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
    def __init__(self, xColumn='x',yColumn='y',topColumn=None,bottomColumn=None,heightColumn=None,
                 rawColumn=None):
        self.xColumn = xColumn
        self.yColumn = yColumn
        self.topColumn = topColumn
        self.bottomColumn = bottomColumn
        self.heightColumn = heightColumn
        self.rawColumn = rawColumn
        self.fitFunction = None
        
    attrFields = ['xColumn','yColumn','topColumn', 'bottomColumn','heightColumn']

class TracePlottingList(list):        
    def toXmlElement(self, root):
        myElement = ElementTree.SubElement(root, 'TracePlottingList', {})
        for traceplotting in self:
            traceplottingElement = ElementTree.SubElement(myElement, 'TracePlotting', dict( (name,getattr(traceplotting,name)) for name in TracePlotting.attrFields))
            if traceplotting.fitFunction:
                traceplotting.fitFunction.toXmlElement(traceplottingElement)
        return myElement
    
    @staticmethod
    def fromXmlElement(element):
        l = TracePlottingList()
        for plottingelement in element.findall("TracePlotting"):
            plotting = TracePlotting()
            plotting.__dict__.update( plottingelement.attrib )
            if plottingelement.find("FitFunction") is not None:
                plotting.fitFunction = FitFunctions.fromXmlElement( plottingelement.find("FitFunction") )
            l.append(plotting)
        return l    

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
    vars --
        vars.comment -- comment to add to file
        vars.traceCreation -- the time the Trace object was created
    header --
    curvePen -- which style pen to use for displaying the trace
    _filename -- filename to save the trace as
    
    The data can be saved to and loaded
    from a file.
    """

    def __init__(self):
        """Construct a trace object."""
        self._x_ = numpy.array([]) #array of x values
        self._y_ = numpy.array([]) #array of y values
        self.name = "noname" #name to display in table of traces
        self.vars = Empty()
        self.vars.comment = ""
        self.vars.traceCreation = datetime.now()
        self.header = None
        self._filename = None
        self.filenameCallback = None   # function to result in filename for save
        self.dataChangedCallback = None # used to update the gui table
        self.rawdata = None
        self.columnNames = ['height', 'top', 'bottom','raw']
        self.vars.tracePlottingList = TracePlottingList()
        
    def varFromXmlElement(self, element):
        name = element.attrib['name']
        mytype = element.attrib['type']
        value = varFactory.get( mytype, str)( element.text )
        setattr( self.vars, name, value )
    
    @property
    def x(self):
        """Get x array"""
        return self._x_
        
    @x.setter
    def x(self, val):
        """Set x array"""
        self._x_ = val
        
    @property
    def y(self):
        """Get y array"""
        return self._y_
        
    @y.setter
    def y(self,val):
        """Set y array, and record the time it was set."""
        self._y_ = val
        self.vars.lastDataAquired = datetime.now()
         
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
        #print "Trace filename", self.filename, self.filepath, self.fileleaf
        if self.dataChangedCallback:
            self.dataChangedCallback()                            
        
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
        return str(self.vars.__dict__.get(name,""))
        
    def saveTraceHeader(self,outfile):
        """ save the header of the trace to outfile
        """
        self.vars.fileCreation = datetime.now()
        for var, value in sorted(self.vars.__dict__.iteritems()):
            print >>outfile, "# {0}\t{1}".format(var, value)
        if self.header is not None:
            print >>outfile, self.header
            
    def saveTraceHeaderXml(self,outfile):
        root = ElementTree.Element('DataFileHeader')
        varsElement = ElementTree.SubElement(root, 'Variables', {})
        for var, value in sorted(self.vars.__dict__.iteritems()):
            if hasattr(value,'toXmlElement'):
                value.toXmlElement(varsElement)
            else:
                e = ElementTree.SubElement(varsElement, 'Element', {'name': var, 'type': type(value).__name__})
                e.text = str(value)
        if self.header:
            e = ElementTree.SubElement(varsElement, 'Header', {})
            e.text = self.header        
        outfile.write(prettify(root,'# '))

    def saveTraceBare(self,filename):
        if self.rawdata:
            self.vars.rawdata = self.rawdata.save()
        if hasattr(self,'fitfunction'):
            #print 'fitfunction saved'
            self.vars.fitfunction = self.fitfunction
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
            self.vars.columnspec = ",".join(columnspec)
            self.saveTraceHeader(of)
            for l in zip(*columnlist):
                print >>of, "\t".join(map(repr,l))
            self.filename = filename
            of.close()

    def saveTrace(self,filename):
        if self.rawdata:
            self.vars.rawdata = self.rawdata.save()
        if hasattr(self,'fitfunction'):
            #print 'fitfunction saved'
            self.vars.fitfunction = self.fitfunction
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
            self.vars.columnspec = columnspec #",".join(columnspec)
            self.saveTraceHeaderXml(of)
            for l in zip(*columnlist):
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
            setattr( self, attr, numpy.array(d) )
        tpelement = root.find("./Variables/TracePlottingList")
        self.vars.tracePlottingList = TracePlottingList.fromXmlElement(tpelement) if tpelement is not None else None
        for element in root.findall("./Variables/Element"):
            self.varFromXmlElement(element)
        
    def loadTraceText(self, stream):    
        data = []
        self.vars.columnspec = "x,y"
        for line in stream:
            line = line.strip()
            if line[0]=='#':
                line = line.lstrip('# \t\r\n')
                if line.find('\t')<0:
                    a = line.split(None,1)
                else:
                    a = line.split('\t',1)
                if len(a)>1:
                    self.vars.__dict__[a[0]] = a[1]  
            else:
                data.append( map(float,line.split()) )
        columnspec =  self.vars.columnspec.split(',')
        for attr,d in zip( columnspec, zip(*data) ):
            setattr( self, attr, numpy.array(d) )
        if hasattr(self.vars,'fitfunction') and FitFunctionsAvailable:
            self.fitfunction = FitFunctions.fitFunctionFactory(self.vars.fitfunction)
            
    def addColumn(self, name):
        """ adds a column with the given name, the column is saved in the file in the order added
        """
        if hasattr( self, name):
            raise TraceException("cannot add column '{0}' trace already has attribute with this name.".format(name))
        self.columnNames.append(name)
        setattr( self, name, numpy.array([]))
            
    
    def setPlotfunction(self, callback):
        self.plotfunction = callback
        
    def addTracePlotting(self, traceplotting):
        self.vars.tracePlottingList.append(traceplotting)
        
    @property 
    def tracePlottingList(self):
        return self.vars.tracePlottingList
