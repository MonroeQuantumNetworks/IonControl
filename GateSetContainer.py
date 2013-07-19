# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 08:37:56 2013

@author: wolverine
"""
import xml.etree.ElementTree as etree
from collections import OrderedDict
import operator

class GateSetOrderedDict(OrderedDict):
    pass

class GateSetException(Exception):
    pass

class GateSetContainer(object):
    def __init__(self, gateDefinition ):
        self.gateDefinition = gateDefinition
        self.GateSetDict = GateSetOrderedDict()
        
    def __repr__(self):
        return self.GateSetDict.__repr__()
    
    def loadXml(self, filename):
        tree = etree.parse(filename)
        root = tree.getroot()
        
        # load pulse definition
        self.GateSetDict = GateSetOrderedDict()
        for gateset in root:
            self.GateSetDict.update( { gateset.attrib['name']: map(operator.methodcaller('strip'),gateset.text.split(','))} )
    
    """Validate the gates used in the gate sets against the defined gates"""            
    def validate(self):
        for name, gateset in self.GateSetDict.iteritems():
            for gate in gateset:
                if gate not in self.gateDefinition.Gates:
                    raise GateSetException( "'{0}' used in set '{1}' not defined".format(gate,name) )


if __name__=="__main__":
    from GateDefinition import GateDefinition
    gatedef = GateDefinition()
    gatedef.loadGateDefinition(r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\StandardGateDefinitions.xml")    

    container = GateSetContainer(gatedef)
    container.loadXml(r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\GateSetDefinition.xml")
    container.validate()
    
    print container
    
    