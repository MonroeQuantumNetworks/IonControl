'''
Created on Apr 18, 2015

@author: pmaunz
'''
import math

class SinSqStart(object):
    name = "Sine square"
    
    def start(self, edge ):
        N = edge.startLength * 2
        return [ edge.startLine + (edge.centralStartLine-edge.startLine)*2*(n/(2*float(N))-math.sin(math.pi*n/float(N))/(2*math.pi)) for n in range(N) ]
    
    def stop(self, edge ):
        N = edge.stopLength * 2
        return [ edge.centralStopLine + (edge.stopLine-edge.centralStopLine)*2*(n/(2*float(N))+math.sin(math.pi*n/float(N))/(2*math.pi)) for n in range(1,N+1) ]
    
    def effectiveLength(self, length):
        return 2*length

class LinearStart(object):
    name = "Linear"
    
    def start(self, edge ):
        N = edge.startLength * 2
        return [ edge.startLine + (edge.centralStartLine-edge.startLine)*(n**2/float(N)**2) for n in range(N) ]
    
    def stop(self, edge ):
        N = edge.stopLength * 2
        return [ edge.centralStopLine + (edge.stopLine-edge.centralStopLine)*(2*n/float(N)-n**2/float(N)**2) for n in range(1,N+1) ]
    
    def effectiveLength(self, length):
        return 2*length

StartTypes = { "": None, SinSqStart.name: SinSqStart, LinearStart.name: LinearStart }
