# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 08:37:56 2013

@author: wolverine
"""
from collections import OrderedDict
import operator

import xml.etree.ElementTree as etree


class GateSequenceOrderedDict(OrderedDict):
    pass

class GateSequenceException(Exception):
    pass

class GateSequenceContainer(object):
    def __init__(self, gateDefinition ):
        self.gateDefinition = gateDefinition
        self.GateSequenceDict = GateSequenceOrderedDict()
        self.GateSequenceAttributes = OrderedDict()
        
    def __repr__(self):
        return self.GateSequenceDict.__repr__()
    
    def loadXml(self, filename):
        self.GateSequenceDict = GateSequenceOrderedDict()
        if filename is not None:
            tree = etree.parse(filename)
            root = tree.getroot()
            
            # load pulse definition
            for gateset in root:
                if gateset.text:
                    self.GateSequenceDict.update( { gateset.attrib['name']: map(operator.methodcaller('strip'),gateset.text.split(','))} )
                else:  # we have the length 0 gate string
                    self.GateSequenceDict.update( { gateset.attrib['name']: [] } )
                self.GateSequenceAttributes.update( { gateset.attrib['name']: gateset.attrib })
            self.validate()
    
    """Validate the gates used in the gate sets against the defined gates"""            
    def validate(self):
        for name, gatesequence in self.GateSequenceDict.iteritems():
            self.validateGateSequence( name, gatesequence )

    def validateGateSequence(self, name, gatesequence):
        for gate in gatesequence:
            self.validateGate(name, gate)
        return gatesequence

    def validateGate(self, name, gate):
        if gate not in self.gateDefinition.Gates:
            raise GateSequenceException( "Gate '{0}' used in GateSequence '{1}' is not defined".format(gate,name) )
        

if __name__=="__main__":
    from gateSequence.GateDefinition import GateDefinition
    gatedef = GateDefinition()
    gatedef.loadGateDefinition(r"C:\Users\Public\Documents\experiments\QGA\config\GateSequences\StandardGateDefinitions.xml")    

    container = GateSequenceContainer(gatedef)
    container.loadXml(r"C:\Users\Public\Documents\experiments\QGA\config\GateSequences\GateSequenceLongGSTwithInversion.xml")
    
    print container
    
    