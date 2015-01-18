'''
Created on Jan 17, 2015

@author: pmaunz
'''

import struct 
from networkx import Graph, shortest_path, simple_cycles, dfs_postorder_nodes, dfs_preorder_nodes
from modules.pairs_iter import pairs_iter 
from modules.Observable import Observable


class ShuttleEdge(object):
    def __init__(self, startName, stopName, startLine, stopLine, idleCount=0, direction=0, wait=0, soft_trigger=0 ):
        self.startLine = startLine
        self.stopLine = stopLine
        self.idleCount = idleCount
        self.direction = direction
        self.wait = wait
        self.startName = startName
        self.stopName = stopName
        self.steps = 0
        
    def code(self, channelCount):
        struct.pack('=IIII', self.stopLine*2*channelCount, ( self.startLine*2*self.channelCount & 0x7fffffff ) | ((self.direction & 0x1) << 31 ),
                             self.idle_count, (self.wait & 0x1) | ((self.soft_trigger &0x1)<<1))


class ShuttlingGraphException(Exception):
    pass

class ShuttlingGraph(list):
    def __init__(self, shuttlingEdges=list() ):
        super(ShuttlingGraph, self).__init__(shuttlingEdges) 
        self.currentPosition = None
        self.currentPositionName = None
        self.nodeLookup = dict()
        self.currentPositionObservable = Observable()
        self.currentPositionNameObservable = Observable()
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
            
    def addEdge(self, edge):
        self.append( edge )
        self.shuttlingGraph.add_edge( edge.startName, edge.stopName, edge=edge, weight=abs(edge.stopLine-edge.startLine) )
        self.nodeLookup[edge.startLine] = edge.startName
        self.nodeLookup[edge.stopLine] = edge.stopName
        self.graphChangedObservable.firebare()
    
    def removeEdge(self, edgeno):
        edge = self.pop(edgeno)
        self.shuttlingGraph.remove_edge( edge.startName, edge.stopName )
        if self.shuttlingGraph.degree( edge.startName )==0:
            self.shuttlingGraph.remove_node(edge.startName)
        if self.shuttlingGraph.degree( edge.stopName )==0:
            self.shuttlingGraph.remove_node(edge.stopName)
        self.graphChangedObservable.firebare()
    
    def setStartName(self, edgeno, startName):
        startName = str(startName)
        edge = self[edgeno]
        if edge.startName!=startName:
            self.shuttlingGraph.remove_edge( edge.startName, edge.stopName )
            if self.shuttlingGraph.degree( edge.startName )==0:
                self.shuttlingGraph.remove_node(edge.startName)
            edge.startName = startName
            self.shuttlingGraph.add_edge( edge.startName, edge.stopName, edge=edge, weight=abs(edge.stopLine-edge.startLine) )     
        self.graphChangedObservable.firebare()
        return True      
    
    def setStopName(self, edgeno, stopName):
        stopName = str(stopName)
        edge = self[edgeno]
        if edge.stopName!=stopName:
            self.shuttlingGraph.remove_edge( edge.startName, edge.stopName )
            if self.shuttlingGraph.degree( edge.stopName )==0:
                self.shuttlingGraph.remove_node(edge.stopName)
            edge.stopName = stopName
            self.shuttlingGraph.add_edge( edge.startName, edge.stopName, edge=edge, weight=abs(edge.stopLine-edge.startLine) )           
        self.graphChangedObservable.firebare()
        return True      
    
    def setStartLine(self, edgeno, startLine):
        edge = self[edgeno]
        edge.startLine = startLine
        self.shuttlingGraph.edge[edge.startName][edge.stopName]['weight']=abs(edge.stopLine-edge.startLine)
        self.graphChangedObservable.firebare()
        return True      
    
    def setStopLine(self, edgeno, stopLine):
        edge = self[edgeno]
        edge.stopLine = stopLine
        self.shuttlingGraph.edge[edge.startName][edge.stopName]['weight']=abs(edge.stopLine-edge.startLine)
        self.graphChangedObservable.firebare()
        return True      
    
    def setIdleCount(self, edgeno, idleCount):
        self[edgeno].idleCount = idleCount
        return True      

    def setSteps(self, edgeno, steps):
        self[edgeno].steps = steps
        return True      
    
    def shuttlePath(self, fromName, toName ):
        sp = shortest_path(self.shuttlingGraph, fromName, toName)
        return [ self.shuttlingGraph.edge[a][b]['edge'] for a,b in pairs_iter(sp)]
    
    
        
        