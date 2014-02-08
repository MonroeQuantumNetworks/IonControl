# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 08:37:56 2013

@author: wolverine
"""
from collections import OrderedDict
import logging
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
        
    def __repr__(self):
        return self.GateSequenceDict.__repr__()
    
    def loadXml(self, filename):
        tree = etree.parse(filename)
        root = tree.getroot()
        
        # load pulse definition
        self.GateSequenceDict = GateSequenceOrderedDict()
        for gateset in root:
            if gateset.text:
                self.GateSequenceDict.update( { gateset.attrib['name']: map(operator.methodcaller('strip'),gateset.text.split(','))} )
            else:  # we have the length 0 gate string
                self.GateSequenceDict.update( { gateset.attrib['name']: [] } )
            
        self.validate()
    
    """Validate the gates used in the gate sets against the defined gates"""            
    def validate(self):
        for name, gateset in self.GateSequenceDict.iteritems():
            self.validateGateSequence( name, gateset )

    def validateGateSequence(self, name, gateset):
        for index, gate in enumerate(gateset):
            replacement = self.validateGate(name, gate)
            if replacement:
                gateset[index:index+1] = replacement
        return gateset

    def validateGate(self, name, gate):
        logger = logging.getLogger(__name__)
        if gate not in self.gateDefinition.Gates:
            if gate in self.GateSequenceDict:
                logger.info( "{0} {1}".format(gate, self.GateSequenceDict[gate] ) )
                return self.validateGateSequence( gate, self.GateSequenceDict[gate] )
            else:
                raise GateSequenceException( "Gate '{0}' used in GateSequence '{1}' is not defined".format(gate,name) )
        else:
            return None                
        

if __name__=="__main__":
    from gateSequence.GateDefinition import GateDefinition
    gatedef = GateDefinition()
    gatedef.loadGateDefinition(r"C:\Users\Public\Documents\experiments\QGA\config\GateSequences\StandardGateDefinitions.xml")    

    container = GateSequenceContainer(gatedef)
    container.loadXml(r"C:\Users\Public\Documents\experiments\QGA\config\GateSequences\GateSequenceLongGSTwithInversion.xml")
    
    print container
    
    