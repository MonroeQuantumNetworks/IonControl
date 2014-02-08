# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 09:22:24 2013

@author: wolverine
"""
import logging

from modules.Expression import Expression
import modules.magnitude as magnitude


class GateSequenceCompiler(object):
    def __init__(self, pulseProgram ):
        self.pulseProgram = pulseProgram
        self.compiledGates = dict()
        self.expression = Expression()
        
    """Compile all gate sets into binary representation
        returns tuple of start address list and bytearray data"""
    def gateSequencesCompile(self, gatesets ):
        logger = logging.getLogger(__name__)
        logger.info( "compiling {0} gateSequences.".format(len(gatesets.GateSequenceDict)) )
        self.gateCompile( gatesets.gateDefinition )
        addresses = list()
        data = list()
        index = 0
        for gateset in gatesets.GateSequenceDict.values():
            gatesetdata = self.gateSequenceCompile( gateset )
            addresses.append(index)
            data.append(gatesetdata)
            index += len(gatesetdata)*4
        return addresses, [item for sublist in data for item in sublist]
    
    """Compile one gateset into its binary representation"""
    def gateSequenceCompile(self, gateset ):
        data = list()
        for gate in gateset:
            data.append( self.compiledGates[gate] )
        return [len(gateset)] + [item for sublist in data for item in sublist]

    """Compile each gate definition into its binary representation"""
    def gateCompile(self, gateDefinition ):
        logger = logging.getLogger(__name__)
        variables = self.pulseProgram.variables()
        for name, gate in gateDefinition.Gates.iteritems():  # for all defined gates
            data = list()
            for pulsename, pulse in gateDefinition.PulseDefinition.iteritems():
                strvalue = gate.pulsedict[pulsename]
                result = self.expression.evaluate(strvalue, variables )      
                if isinstance(result, magnitude.Magnitude) and result.dimensionless():
                    result.output_prec(0)
                data.append( self.pulseProgram.convertParameter( result, pulse.encoding ) )
            self.compiledGates[name] = data
            logger.info( "compiled {0} to {1}".format(name,data) )
                
        
if __name__=="__main__":
    from pulseProgram.PulseProgram import PulseProgram
    from gateSequence.GateDefinition import GateDefinition
    from gateSequence.GateSequenceContainer import GateSequenceContainer
    
    pp = PulseProgram()
    pp.debug = False
    pp.loadSource(r"C:\Users\Public\Documents\experiments\QGA\config\PulsePrograms\YbGateSequenceTomography.pp")
    
    gatedef = GateDefinition()
    gatedef.loadGateDefinition(r"C:\Users\Public\Documents\experiments\QGA\config\GateSequences\StandardGateDefinitions.xml")    
    gatedef.printGates()
    
    container = GateSequenceContainer(gatedef)
    container.loadXml(r"C:\Users\Public\Documents\experiments\QGA\config\GateSequences\GateSequenceDefinition.xml")
    container.validate()  
    #print container
    
    compiler = GateSequenceCompiler(pp)
    compiler.gateCompile( container.gateDefinition )
    print compiler.gateSequenceCompile( container.GateSequenceDict['S11'])
    
    address, data = compiler.GateSequencesCompile( container )
    print address
    print data


    