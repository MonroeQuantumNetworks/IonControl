'''
Created on Jan 17, 2015

@author: pmaunz
'''

import struct 
from networkx import Graph, shortest_path, simple_cycles, dfs_postorder_nodes, dfs_preorder_nodes
from modules.pairs_iter import pairs_iter 
from modules.Observable import Observable
from modules.firstNotNone import firstNotNone
import xml.etree.ElementTree as ElementTree
from modules.magnitude import mg
from uiModules.SoftStart import StartTypes


class ShuttleEdge(object):
    stateFields = ['startLine', 'stopLine', 'idleCount', 'direction', 'wait', 'startName', 'stopName', 'steps' ]
    def __init__(self, startName="start", stopName="stop", startLine=0.0, stopLine=1.0, idleCount=0, direction=0, wait=0, soft_trigger=0 ):
        self.startLine = startLine
        self.stopLine = stopLine
        self.interpolStartLine = startLine
        self.interpolStopLine = stopLine
        self.idleCount = idleCount
        self.direction = direction
        self.wait = wait
        self.startName = startName
        self.stopName = stopName
        self.steps = 0
        self._startType = ""
        self._stopType = ""
        self.startLength = 0
        self.stopLength = 0
        self.startGenerator = StartTypes[self._startType]() if self._startType else None
        self.stopGenerator = StartTypes[self._startType]() if self._stopType else None

    def toXmlElement(self, root):
        mydict = dict( ( (key, str(getattr(self,key))) for key in self.stateFields ))
        myElement = ElementTree.SubElement(root, 'ShuttleEdge', mydict )
        return myElement
    
    @staticmethod
    def fromXmlElement( element ):
        a = element.attrib
        edge = ShuttleEdge( startName=a.get('startName','start'),  stopName=a.get('stopName',"stop"), startLine=float(a.get('startLine','0.0')), 
                            stopLine=float(a.get('stopLine','1.0')), idleCount=float(a.get('idleCount','0.0')), direction=int(a.get('direction','0')), 
                            wait=int(a.get('wait','0')), soft_trigger=int(a.get('softTrigger','0')) )
        edge._startType = a.get('_startType','')
        edge._stopType = a.get('_stopType','')
        edge.startLength = int( a.get('startLength', 0) )
        edge.stopLength = int( a.get('stopLength', 0) )
        edge.steps = int(a.get('steps','0'))
        edge.startGenerator = StartTypes[edge._startType]() if edge._startType else None
        edge.stopGenerator = StartTypes[edge._startType]() if edge._stopType else None
        return edge
    
    @property
    def startType(self):
        return self._startType
    
    @startType.setter
    def startType(self, val):
        self._startType = val
        self.startGenerator = StartTypes[self._startType]() if self._startType else None
        
    @property
    def stopType(self):
        return self._stopType
    
    @stopType.setter
    def stopType(self, val):
        self._stopType = val
        self.stopGenerator = StartTypes[self._stopType]() if self._stopType else None
            
    @property
    def timePerSample(self):
        return mg(2.06,'us') + self.idleCount*mg(0.02,'us')

    @property 
    def sampleCount(self):
        return abs(self.stopLine - self.startLine)*max(self.steps,1) + 1
    
    @property 
    def totalSampleCount(self):
        return self.centralSteps + self.effectiveStartLength + self.effectiveStopLength
    
    @property
    def centralStartLine(self):
        return self.startLine + (self.startLength if self._startType else 0) /(self.sampleCount-1)*(self.stopLine - self.startLine) if self.startType else self.startLine

    @property
    def centralStopLine(self):
        return self.startLine + (self.sampleCount-1-(self.stopLength if self._stopType else 0))/(self.sampleCount-1)*(self.stopLine - self.startLine) if self.stopType else self.stopLine
    
    @property
    def centralSteps(self):
        return abs(self.centralStopLine - self.centralStartLine)*max(self.steps,1) + 1
    
    @property
    def totalTime(self):
        return self.totalSampleCount*self.timePerSample
    
    @property
    def effectiveStartLength(self):
        return self.startGenerator.effectiveLength(self.startLength) if self.startGenerator else 0

    @property
    def effectiveStopLength(self):
        return self.stopGenerator.effectiveLength(self.stopLength) if self.stopGenerator else 0 
    
    def start(self):
        return self.startGenerator.start( self ) if self.startGenerator else []
    
    def stop(self):
        return self.stopGenerator.stop( self ) if self.stopGenerator else []


class ShuttlingGraphException(Exception):
    pass

class ShuttlingGraph(list):
    def __init__(self, shuttlingEdges=list() ):
        super(ShuttlingGraph, self).__init__(shuttlingEdges) 
        self.currentPosition = None
        self.currentPositionName = None
        self.nodeLookup = dict()
        self.currentPositionObservable = Observable()
        self.graphChangedObservable = Observable()
        self.initGraph()
        self._hasChanged = True
        
    def initGraph(self):
        self.shuttlingGraph = Graph()
        for edge in self:
            self.shuttlingGraph.add_node( edge.startName )
            self.shuttlingGraph.add_node( edge.stopName )
            self.shuttlingGraph.add_edge( edge.startName, edge.stopName, edge=edge, weight=abs(edge.stopLine-edge.startLine) )
            self.nodeLookup[edge.startLine] = edge.startName
            self.nodeLookup[edge.stopLine] = edge.stopName
        
    @property 
    def hasChanged(self):
        return self._hasChanged
    
    @hasChanged.setter
    def hasChanged(self, value):
        self._hasChanged = value
            
    def position(self, line):
        return self.nodeLookup.get(line)
    
    def setPosition(self, line):
        self.currentPosition = line
        self.currentPositionName = self.position(line)
        self.currentPositionObservable.fire( line=line, text=firstNotNone(self.currentPositionName, "") )
            
    def addEdge(self, edge):
        if not self.shuttlingGraph.has_edge( edge.startName, edge.stopName):
            self._hasChanged = True
            self.append( edge )
            self.shuttlingGraph.add_edge( edge.startName, edge.stopName, edge=edge, weight=abs(edge.stopLine-edge.startLine) )
            self.nodeLookup[edge.startLine] = edge.startName
            self.nodeLookup[edge.stopLine] = edge.stopName
            self.graphChangedObservable.firebare()
            self.setPosition(self.currentPosition)
            
    def isValidEdge(self, edge):
        return (not self.shuttlingGraph.has_edge( edge.startName, edge.stopName)  
                and (edge.startLine not in self.nodeLookup or self.nodeLookup[edge.startLine]==edge.startName) 
                and (edge.stopLine not in self.nodeLookup or self.nodeLookup[edge.stopLine]==edge.stopName ) )
        
    def getValidEdge(self):
        index = 0
        while self.shuttlingGraph.has_node("Start_{0}".format(index)):
            index += 1
        startName = "Start_{0}".format(index)
        index = 0
        while self.shuttlingGraph.has_node("Stop_{0}".format(index)):
            index += 1
        stopName = "Stop_{0}".format(index)
        index = 0
        startLine = (max( self.nodeLookup.keys() )+1) if self.nodeLookup else 1
        stopLine = startLine + 1
        return ShuttleEdge(startName, stopName, startLine, stopLine, 0, 0, 0, 0)
    
    def removeEdge(self, edgeno):
        self._hasChanged = True
        edge = self.pop(edgeno)
        self.shuttlingGraph.remove_edge( edge.startName, edge.stopName )
        if self.shuttlingGraph.degree( edge.startName )==0:
            self.shuttlingGraph.remove_node(edge.startName)
        if self.shuttlingGraph.degree( edge.stopName )==0:
            self.shuttlingGraph.remove_node(edge.stopName)
        self.graphChangedObservable.firebare()
        #self.nodeLookup.pop(edge.startLine)
        #self.nodeLookup.pop(edge.stopLine)
        self.setPosition(self.currentPosition)
    
    def setStartName(self, edgeno, startName):
        self._hasChanged = True
        startName = str(startName)
        edge = self[edgeno]
        if edge.startName!=startName:
            if not self.shuttlingGraph.has_edge( startName, edge.stopName):
                self.shuttlingGraph.remove_edge( edge.startName, edge.stopName )
                if self.shuttlingGraph.degree( edge.startName )==0:
                    self.shuttlingGraph.remove_node(edge.startName)
                edge.startName = startName
                self.shuttlingGraph.add_edge( edge.startName, edge.stopName, edge=edge, weight=abs(edge.stopLine-edge.startLine) )     
                self.graphChangedObservable.firebare()
                self.nodeLookup[edge.startLine] = edge.startName
                self.setPosition(self.currentPosition)
                return True
            else:
                return False
        return True
    
    def setStopName(self, edgeno, stopName):
        self._hasChanged = True
        stopName = str(stopName)
        edge = self[edgeno]
        if edge.stopName!=stopName:
            if not self.shuttlingGraph.has_edge( edge.startName, stopName):
                self.shuttlingGraph.remove_edge( edge.startName, edge.stopName )
                if self.shuttlingGraph.degree( edge.stopName )==0:
                    self.shuttlingGraph.remove_node(edge.stopName)
                edge.stopName = stopName
                self.shuttlingGraph.add_edge( edge.startName, edge.stopName, edge=edge, weight=abs(edge.stopLine-edge.startLine) )           
                self.graphChangedObservable.firebare()
                self.nodeLookup[edge.stopLine] = edge.stopName
                self.setPosition(self.currentPosition)
                return True
            else:
                return False
        return True    
    
    def setStartLine(self, edgeno, startLine):
        self._hasChanged = True
        edge = self[edgeno]
        if startLine!=edge.startLine and (startLine not in self.nodeLookup or self.nodeLookup[startLine]==edge.startName):
            self.nodeLookup.pop(edge.startLine)
            edge.startLine = startLine
            self.shuttlingGraph.edge[edge.startName][edge.stopName]['weight']=abs(edge.stopLine-edge.startLine)
            self.nodeLookup[edge.startLine] = edge.startName
            self.graphChangedObservable.firebare()
            self.setPosition(self.currentPosition)
            return True    
        return False  
    
    def setStopLine(self, edgeno, stopLine):
        self._hasChanged = True
        edge = self[edgeno]
        if stopLine!=edge.stopLine and (stopLine not in self.nodeLookup or self.nodeLookup[stopLine]==edge.stopName):
            self.nodeLookup.pop(edge.stopLine)
            edge.stopLine = stopLine
            self.shuttlingGraph.edge[edge.startName][edge.stopName]['weight']=abs(edge.stopLine-edge.startLine)
            self.nodeLookup[edge.stopLine] = edge.stopName
            self.graphChangedObservable.firebare()
            self.setPosition(self.currentPosition)
            return True  
        return False
    
    def setIdleCount(self, edgeno, idleCount):
        self._hasChanged = True
        self[edgeno].idleCount = idleCount
        return True      

    def setSteps(self, edgeno, steps):
        self._hasChanged = True
        self[edgeno].steps = steps
        return True      
    
    def shuttlePath(self, fromName, toName ):
        fromName = firstNotNone(fromName, self.currentPositionName)
        sp = shortest_path(self.shuttlingGraph, fromName, toName)
        path = list()
        for a,b in pairs_iter(sp):
            edge = self.shuttlingGraph.edge[a][b]['edge']
            path.append( (a,b,edge,self.index(edge) ))
        return path
    
    def nodes(self):
        return self.shuttlingGraph.nodes()
    
    def toXmlElement(self, root):
        mydict = dict( ( (key, str(getattr(self,key))) for key in ('currentPosition','currentPositionName') if getattr(self,key) is not None  ) ) 
        myElement = ElementTree.SubElement(root, "ShuttlingGraph", attrib=mydict )
        for edge in self:
            edge.toXmlElement( myElement )
        return myElement
    
    def setStartType(self, edgeno, Type):
        self._hasChanged = True
        self[edgeno].startType = str(Type)
        return True
    
    def setStopType(self, edgeno, Type):
        self._hasChanged = True
        self[edgeno].stopType = str(Type)
        return True
    
    def setStartLength(self, edgeno, length):
        edge = self[edgeno]
        if length!=edge.startLength:
            if edge.startLength+edge.stopLength<edge.sampleCount:
                self._hasChanged = True
                edge.startLength = int(length)
            else:
                return False
        return True
    
    def setStopLength(self, edgeno, length):
        edge = self[edgeno]
        if length!=edge.stopLength:
            if edge.startLength+edge.stopLength<edge.sampleCount:
                self._hasChanged = True
                edge.stopLength = int(length)
            else:
                return False
        return True
    
    @staticmethod
    def fromXmlElement( element ):
        edgeElementList = element.findall("ShuttleEdge")
        edgeList = [ ShuttleEdge.fromXmlElement(e) for e in edgeElementList ]
        return ShuttlingGraph(edgeList)

