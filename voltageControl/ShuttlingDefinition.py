'''
Created on Jan 17, 2015

@author: pmaunz
'''

import struct 
from networkx import Graph, shortest_path, simple_cycles, dfs_postorder_nodes, dfs_preorder_nodes
from modules.pairs_iter import pairs_iter 
from modules.Observable import Observable
from modules.firstNotNone import firstNotNone


class ShuttleEdge(object):
    def __init__(self, startName="start", stopName="stop", startLine=0.0, stopLine=1.0, idleCount=0, direction=0, wait=0, soft_trigger=0 ):
        self.startLine = startLine
        self.stopLine = stopLine
        self.idleCount = idleCount
        self.direction = direction
        self.wait = wait
        self.startName = startName
        self.stopName = stopName
        self.steps = 0

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
        
    def initGraph(self):
        self.shuttlingGraph = Graph()
        for edge in self:
            self.shuttlingGraph.add_node( edge.startName )
            self.shuttlingGraph.add_node( edge.stopName )
            self.shuttlingGraph.add_edge( edge.startName, edge.stopName, edge=edge, weight=abs(edge.stopLine-edge.startLine) )
            self.nodeLookup[edge.startLine] = edge.startName
            self.nodeLookup[edge.stopLine] = edge.stopName
            
    def position(self, line):
        return self.nodeLookup.get(line)
    
    def setPosition(self, line):
        self.currentPosition = line
        self.currentPositionName = self.position(line)
        self.currentPositionObservable.fire( line=line, text=firstNotNone(self.currentPositionName, "") )
            
    def addEdge(self, edge):
        if not self.shuttlingGraph.has_edge( edge.startName, edge.stopName):
            self.append( edge )
            self.shuttlingGraph.add_edge( edge.startName, edge.stopName, edge=edge, weight=abs(edge.stopLine-edge.startLine) )
            self.nodeLookup[edge.startLine] = edge.startName
            self.nodeLookup[edge.stopLine] = edge.stopName
            self.graphChangedObservable.firebare()
            self.setPosition(self.currentPosition)
            
    def isValidEdge(self, edge):
        return (not self.shuttlingGraph.has_edge( edge.startName, edge.stopName)  
                and edge.startLine not in self.nodeLookup 
                and edge.stopLine not in self.nodeLookup )
    
    def removeEdge(self, edgeno):
        edge = self.pop(edgeno)
        self.shuttlingGraph.remove_edge( edge.startName, edge.stopName )
        if self.shuttlingGraph.degree( edge.startName )==0:
            self.shuttlingGraph.remove_node(edge.startName)
        if self.shuttlingGraph.degree( edge.stopName )==0:
            self.shuttlingGraph.remove_node(edge.stopName)
        self.graphChangedObservable.firebare()
        self.nodeLookup.pop(edge.startLine)
        self.nodeLookup.pop(edge.stopLine)
        self.setPosition(self.currentPosition)
    
    def setStartName(self, edgeno, startName):
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
        edge = self[edgeno]
        if startLine!=edge.startLine and startLine not in self.nodeLookup:
            self.nodeLookup.pop(edge.startLine)
            edge.startLine = startLine
            self.shuttlingGraph.edge[edge.startName][edge.stopName]['weight']=abs(edge.stopLine-edge.startLine)
            self.nodeLookup[edge.startLine] = edge.startName
            self.graphChangedObservable.firebare()
            self.setPosition(self.currentPosition)
            return True    
        return False  
    
    def setStopLine(self, edgeno, stopLine):
        edge = self[edgeno]
        if stopLine!=edge.stopLine and stopLine not in self.nodeLookup:
            self.nodeLookup.pop(edge.stopLine)
            edge.stopLine = stopLine
            self.shuttlingGraph.edge[edge.startName][edge.stopName]['weight']=abs(edge.stopLine-edge.startLine)
            self.nodeLookup[edge.stopLine] = edge.stopName
            self.graphChangedObservable.firebare()
            self.setPosition(self.currentPosition)
            return True  
        return False
    
    def setIdleCount(self, edgeno, idleCount):
        self[edgeno].idleCount = idleCount
        return True      

    def setSteps(self, edgeno, steps):
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
        
    #def storeTo