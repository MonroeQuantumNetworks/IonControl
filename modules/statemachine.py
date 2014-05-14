'''
Created on Apr 4, 2014

@author: pmaunz
'''

from collections import defaultdict
from datetime import datetime
import logging
from modules.magnitude import mg 
import networkx as nx
from networkx.drawing.nx_agraph import to_agraph

class StatemachineException(Exception):
    pass

class State:
    def __init__(self, name, enterfunc=None, exitfunc=None ):
        self.name = name
        self.enterfunc = enterfunc
        self.exitfunc = exitfunc
        self.enterTime = None
        self.exitTime = None
        
    def enterState(self):
        logging.getLogger(__name__).log(25,"Entering state {0}".format(self.name))
        self.enterTime = datetime.now()
        if self.enterfunc is not None:
            self.enterfunc()
        
    def exitState(self):
        self.exitTime = datetime.now()
        if self.exitfunc is not None:
            self.exitfunc()
            
    def timeInState(self):
        return mg( (datetime.now()-self.enterTime).total_seconds(), 's' )
        
class Transition:
    def __init__(self, fromstate, tostate, condition=None, transitionfunc=None, description=None):
        self.fromstate = fromstate
        self.tostate = tostate
        self.condition = condition if condition is not None else lambda *args: True
        self.transitionfunc = transitionfunc
        self.description = description
        
    def transitionState(self, fromObj, toObj ):
        if self.transitionfunc is not None:
            self.transitionfunc( fromObj, toObj )

class Statemachine:
    def __init__(self, name="Statemachine"):
        self.states = dict()
        self.transitions = defaultdict( list )
        self.currentState = None
        self.graph = nx.MultiDiGraph()
        self.name=name
        
    def initialize(self, state, enter=True):
        if enter:
            self.states[state].enterState()
        self.currentState = state
        self.generateDiagram()
                
    def addState(self, name, enterfunc=None, exitfunc=None):
        self.states[name] = State( name, enterfunc, exitfunc )
        self.graph.add_node(name)
        
    def addStateObj(self, state ):
        self.states[state.name] = state
        
    def addTransition(self, eventType, fromstate, tostate, condition=None, transitionfunc=None, description=None):
        self.addTransitionObj(eventType, Transition(fromstate, tostate, condition, transitionfunc, description=description))
        
    def addTransitionList(self, eventType, fromstates, tostate, condition=None, description=None):
        for state in fromstates:
            self.addTransitionObj(eventType, Transition(state, tostate, condition, description=description))            
        
    def addTransitionObj(self, eventType, transition):
        if transition.fromstate not in self.states:
            raise StatemachineException("cannot add transition because origin state '{0}' is not defined.".format(transition.fromstate))
        if transition.tostate not in self.states:
            raise StatemachineException("cannot add transition because target state '{0}' is not defined.".format(transition.tostate))
        self.transitions[(eventType,transition.fromstate)].append( transition )
        self.graph.add_edge(transition.fromstate, transition.tostate, label=transition.description )
        
    def makeTransition(self, transition):
        if self.currentState!=transition.fromstate:
            raise StatemachineException("Cannot make transition {0} -> {1} because current state is {2}".format(transition.fromstate, transition.tostate, self.currentState))
        fromStateObj = self.states[transition.fromstate]
        toStateObj = self.states[transition.tostate]
        fromStateObj.exitState()
        transition.transitionState( fromStateObj, toStateObj )
        self.currentState = transition.tostate
        toStateObj.enterState()
        logging.getLogger(__name__).debug("Now in state {0}".format(self.currentState))
        
    def processEvent(self, eventType, *args, **kwargs ):
        for thistransition in self.transitions[(eventType,self.currentState)]:
            if thistransition.condition( self.states[self.currentState], *args, **kwargs ):
                logging.getLogger(__name__).debug("Transition initiated by {0} in {1} from {2} to {3}".format(eventType, self.currentState, thistransition.fromstate, thistransition.tostate))
                self.makeTransition( thistransition )
        return self.currentState
                
    def generateDiagram(self):
        # convert from networkx -> pydot
        pydot_graph = to_agraph(self.graph)
        
        # render pydot by calling dot, no file saved to disk
        pydot_graph.graph_attr['overlap']='scale'
        pydot_graph.edge_attr.update(fontsize='12',decorate=True)
        pydot_graph.layout()
        pydot_graph.draw(self.name+".png")
        pydot_graph.write(self.name+'.dot')

                
if __name__=="__main__":
    sm = Statemachine("Example")
    sm.addState( 'idle', lambda: 1, lambda: 2 )
    sm.addState( 'running', lambda: 3, lambda: 4)
    sm.initialize('idle', True)
    sm.addTransition('runButton', 'idle', 'running', description="runButton")
    sm.addTransition('stopButton', 'running', 'idle', description="stopButton")
    
    sm.initialize('idle')
    sm.processEvent( 'runButton')
    sm.processEvent( 'stopButton' )