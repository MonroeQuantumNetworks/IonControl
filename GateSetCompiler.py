# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 09:22:24 2013

@author: wolverine
"""
from modules.Expression import Expression
import modules.magnitude as magnitude

class GateSetCompiler(object):
    def __init__(self, pulseProgram ):
        self.pulseProgram = pulseProgram
        self.compiledGates = dict()
        self.expression = Expression()
        
    """Compile all gate sets into binary representation
        returns tuple of start address list and bytearray data"""
    def gateSetsCompile(self, gatesets ):
        print "compiling {0} gateSets.".format(len(gatesets.GateSetDict))
        self.gateCompile( gatesets.gateDefinition )
        addresses = list()
        data = list()
        index = 0
        for name, gateset in gatesets.GateSetDict.iteritems():
            gatesetdata = self.gateSetCompile( gateset )
            addresses.append(index)
            data.append(gatesetdata)
            index += len(gatesetdata)*4
            #print name, index, len(data), len(addresses), len(gatesetdata)
        return addresses, [item for sublist in data for item in sublist]
    
    """Compile one gateset into its binary representation"""
    def gateSetCompile(self, gateset ):
        data = list()
        for gate in gateset:
            data.append( self.compiledGates[gate] )
        return [len(gateset)] + [item for sublist in data for item in sublist]

    """Compile each gate definition into its binary representation"""
    def gateCompile(self, gateDefinition ):
        variables = self.pulseProgram.variables()
        for name, gate in gateDefinition.Gates.iteritems():  # for all defined gates
            data = list()
            for pulsename, pulse in gateDefinition.PulseDefinition.iteritems():
                strvalue = gate.pulsedict[pulsename]
                result = self.expression.evaluate(strvalue, variables )      
                #print strvalue, result, variables[strvalue] if strvalue in variables else None
                if isinstance(result, magnitude.Magnitude) and result.dimensionless():
                    result.output_prec(0)
                data.append( self.pulseProgram.convertParameter( result, pulse.encoding ) )
            self.compiledGates[name] = data
            print "compiled {0} to {1}".format(name,data)
                
        
if __name__=="__main__":
    from PulseProgram import PulseProgram
    from GateDefinition import GateDefinition
    from GateSetContainer import GateSetContainer
    
    pp = PulseProgram()
    pp.debug = False
    pp.loadSource(r"C:\Users\Public\Documents\experiments\QGA\config\PulsePrograms\YbGateSetTomography.pp")
    
    gatedef = GateDefinition()
    gatedef.loadGateDefinition(r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\StandardGateDefinitions.xml")    
    gatedef.printGates()
    
    container = GateSetContainer(gatedef)
    container.loadXml(r"C:\Users\Public\Documents\experiments\QGA\config\GateSets\GateSetDefinition.xml")
    container.validate()  
    #print container
    
    compiler = GateSetCompiler(pp)
    compiler.gateCompile( container.gateDefinition )
    print compiler.gateSetCompile( container.GateSetDict['S11'])
    
    address, data = compiler.gateSetsCompile( container )
    print address
    print data


    