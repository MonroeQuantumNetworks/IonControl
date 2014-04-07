'''
Created on Apr 4, 2014

@author: pmaunz
'''

from collections import defaultdict
from datetime import datetime
import logging
from modules.magnitude import mg 

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
    def __init__(self, fromstate, tostate, condition=None, transitionfunc=None):
        self.fromstate = fromstate
        self.tostate = tostate
        self.condition = condition if condition is not None else lambda *args: True
        self.transitionfunc = transitionfunc
        
    def transitionState(self, fromObj, toObj ):
        if self.transitionfunc is not None:
            self.transitionfunc( fromObj, toObj )

class Statemachine:
    def __init__(self):
        self.states = dict()
        self.transitions = defaultdict( list )
        self.currentState = None
        
    def initialize(self, state, enter=True):
        if enter:
            self.states[state].enterState()
        self.currentState = state
                
    def addState(self, name, enterfunc=None, exitfunc=None):
        self.states[name] = State( name, enterfunc, exitfunc )
        
    def addStateObj(self, state ):
        self.states[state.name] = state
        
    def addTransition(self, eventType, fromstate, tostate, condition=None, transitionfunc=None):
        self.addTransitionObj(eventType, Transition(fromstate, tostate, condition, transitionfunc))
        
    def addTransitionList(self, eventType, fromstates, tostate, condition=None):
        for state in fromstates:
            self.addTransitionObj(eventType, Transition(state, tostate, condition))            
        
    def addTransitionObj(self, eventType, transition):
        if transition.fromstate not in self.states:
            raise StatemachineException("cannot add transition because origin state '{0}' is not defined.".format(transition.fromstate))
        if transition.tostate not in self.states:
            raise StatemachineException("cannot add transition because target state '{0}' is not defined.".format(transition.tostate))
        self.transitions[(eventType,transition.fromstate)].append( transition )
        
    def makeTransition(self, transition):
        if self.currentState!=transition.fromstate:
            raise StatemachineException("Cannot make transition {0} -> {1} because current state is {2}".format(transition.fromstate, transition.tostate, self.currentState))
        fromStateObj = self.states[transition.fromstate]
        toStateObj = self.states[transition.tostate]
        fromStateObj.exitState()
        transition.transitionState( fromStateObj, toStateObj )
        toStateObj.enterState()
        self.currentState = transition.tostate
        
    def processEvent(self, eventType, *args, **kwargs ):
        for thistransition in self.transitions[(eventType,self.currentState)]:
            if thistransition.condition( self.states[self.currentState], *args, **kwargs ):
                self.makeTransition( thistransition )
        return self.currentState
                
                
if __name__=="__main__":
    sm = Statemachine()
    sm.addState( 'idle', lambda: 1, lambda: 2 )
    sm.addState( 'running', lambda: 3, lambda: 4)
    sm.addTransition('runButton', 'idle', 'running')
    sm.addTransition('stopButton', 'running', 'idle')
    
    sm.initialize('idle')
    sm.processEvent( 'runButton')
    sm.processEvent( 'stopButton' )