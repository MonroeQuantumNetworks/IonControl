# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 07:28:56 2013

@author: wolverine
"""

import xml.etree.ElementTree as etree
from collections import OrderedDict

class Pulse(object):
    def __init__(self, name, pulsetype, encoding):
        self.name = name
        self.pulsetype = pulsetype
        self.encoding = encoding
        
    def __repr__(self):
        return "name: '{0}' pulsetype: '{1}' encoding: '{2}'".format(self.name,self.pulsetype,self.encoding)
        
class Gate(object):
    def __init__(self, name, pulsedict ):
        self.name = name
        self.pulsedict = pulsedict
        
    def __repr__(self):
        return "name: '{0}' pulsedict:{1}".format(self.name,self.pulsedict)


class GateDefinition(object):
    def __init__(self):
        self.PulseDefinition = OrderedDict()
        self.Gates = dict()
        
    def loadGateDefinition(self, filename):
        tree = etree.parse(filename)
        root = tree.getroot()
        
        # load pulse definition
        self.PulseDefinition = OrderedDict()
        PulseDefinitionElement = root.find("PulseDefinition")
        for pulse in PulseDefinitionElement:
            self.PulseDefinition.update( {pulse.attrib['name']: Pulse(pulse.attrib['name'],pulse.attrib['type'],pulse.text)} )
            
        print self.PulseDefinition 
        
        #load gate definitions
        self.Gates = dict()
        GateDefinitionElement = root.find("GateDefinition")
        for gate in GateDefinitionElement:
            self.addGate( gate )
                        
    def addGate(self, element):
        pulsedict = dict()
        for child in element:
            pulsedict.update( { child.attrib['name']: child.text })
        self.Gates.update( { element.attrib['name']: Gate(element.attrib['name'],pulsedict)} )

    def printGates(self):
        print "Gates defined:"
        for gate in self.Gates.values():
            print gate
        
if __name__=="__main__":
    gatedef = GateDefinition()
    gatedef.loadGateDefinition(r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\StandardGateDefinitions.xml")    
    gatedef.printGates()
    
