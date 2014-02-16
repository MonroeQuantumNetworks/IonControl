from collections import OrderedDict
import Builtins
from CompileError import CompileError

class Symbol(object):
    def __init__(self, name):
        self.name = name

class ConstSymbol(Symbol):
    def __init__(self, name, value):
        super(ConstSymbol, self).__init__(name)
        self.value = value

class VarSymbol(Symbol):
    def __init__(self, type_=None, encoding=None, name=None, value=None, unit=None):
        super(VarSymbol, self).__init__(name)
        self.type_ = type_
        self.encoding = encoding
        self.value = value
        self.unit = unit

class FunctionSymbol(Symbol):
    def __init__(self, name, block=None):
        super(FunctionSymbol, self).__init__(name)
        self.block = block
        
    def codegen(self, symboltable, arg=list(), kwarg=dict()):
        if len(arg)>1:
            raise CompileError( "defined functions cannot have arguments" )
        return self.block

class Builtin(Symbol):
    def __init__(self, name, codegen):
        super(Builtin, self).__init__(name)
        self.codegen = codegen
        
    
class SymbolTable(OrderedDict):
    
    def __init__(self):
        super(SymbolTable, self).__init__()
        self.addBuiltins()
        self.inlineParameterValues = dict() 
        self.inlineParameterValues[0] = 'NULL'
        self.inlineParameterValues[0xffffffff] = 'FFFFFFFF'
        self.labelNumber = 0 
        
    def addBuiltins(self):
        self['set_shutter'] = Builtin('set_shutter',Builtins.set_shutter)
        self['set_inv_shutter'] = Builtin('set_inv_shutter',Builtins.set_inv_shutter)
        self['set_counter'] = Builtin('set_counter',Builtins.set_counter)
        self['update'] = Builtin('update', Builtins.update)
        self['load_count'] = Builtin('load_count', Builtins.load_count)
        self['set_trigger'] = Builtin( 'set_trigger', Builtins.set_trigger )
        self['set_dds'] = Builtin( 'set_dds', Builtins.set_dds)
        self['read_pipe'] = Builtin( 'read_pipe', Builtins.read_pipe )
        self['write_pipe'] = Builtin( 'write_pipe', Builtins.write_pipe )
        self['exit'] = Builtin( 'exit', Builtins.exit_ )
        self['pipe_empty'] = Builtin( 'pipe_empty', Builtins.pipe_empty )
        self['apply_next_scan_point'] = Builtin( 'apply_next_scan_point', Builtins.apply_next_scan_point )
        
    def getInlineParameter(self, prefix, value):
        if value not in self.inlineParameterValues:
            self.inlineParameterValues[value] = "{0}_{1}".format(prefix,len(self.inlineParameterValues))
        return self.inlineParameterValues[value]
    
    def getLabelNumber(self):
        self.labelNumber += 1
        return self.labelNumber
        
    def getConst(self, name):
        """get a const symbol"""
        return self[name]

    def getVar(self, name, type_=None):
        """check for the availability and type of a vaiabledefinition"""
        return self[name]
        
    def getProcedure(self, name):
        return self[name]

    def checkAvailable(self, name):
        if name in self:
            raise CompileError("symbol {0} already exists.".format(name))
        
    def getAllConst(self):
        return [value for value in self.values() if isinstance(value,ConstSymbol)]

    def getAllVar(self):
        return [value for value in self.values() if isinstance(value,VarSymbol)]
        
        
    