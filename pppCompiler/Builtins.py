'''
Created on Feb 15, 2014

@author: pmaunz
'''
from pppCompiler import CompileException

def set_shutter( symboltable, arg=list(), kwarg=dict() ):
    if len(arg)!=2:
        raise CompileException( "expected exactly one argument in set_shutter" )
    symbol = symboltable.getVar( arg[1] )
    if symbol.type_ == "masked_shutter":
        code = ["  SHUTTERMASK {0}_mask".format(symbol.name),
                "  ASYNCSHUTTER {0}".format(symbol.name) ]
    elif symbol.type_ == "shutter":
        code = ["  SHUTTERMASK FFFFFFFF",
                "  ASYNCSHUTTER {0}".format(symbol.name) ]
    else:
        raise CompileException("cannot set shutter for variable type '{0}'".format(symbol.type_))
    return code

def set_inv_shutter( symboltable, arg=list(), kwarg=dict() ):
    if len(arg)!=2:
        raise CompileException( "expected exactly one argument in set_shutter" )
    symbol = symboltable.getVar( arg[1] )
    if symbol.type_ == "masked_shutter":
        code = ["  SHUTTERMASK {0}_mask".format(symbol.name),
                "  ASYNCINVSHUTTER {0}".format(symbol.name) ]
    elif symbol.type_ == "shutter":
        code = ["  SHUTTERMASK FFFFFFFF",
                "  ASYNCINVSHUTTER {0}".format(symbol.name) ]
    else:
        raise CompileException("cannot set shutter for variable type '{0}'".format(symbol.type_))
    return code

def set_counter( symboltable, arg=list(), kwarg=dict() ):
    if len(arg)!=2:
        raise CompileException( "expected exactly one argument in set_counter" )
    symbol = symboltable.getVar( arg[1], type_ = "counter" )
    return ["  COUNTERMASK {0}".format(symbol.name)]

def clear_counter( symboltable, arg=list(), kwarg=dict() ):
    if len(arg)!=1:
        raise CompileException( "expected no arguments in clear_counter" )
    return ["  COUNTERMASK NULL"]

def update( symboltable, arg=list(), kwarg=dict() ):
    code = ["  WAITDDSWRITEDONE"]
    if 'wait_dds' in kwarg:
        if not kwarg['wait_dds']:
            code = list()
    if len(arg)==2:
        symbol = symboltable.getVar( arg[1] )
        return code + ["  WAIT",
                "  UPDATE {0}".format(symbol.name) ]
    return code + ["  WAIT",
            "  UPDATE NULL"]

def load_count( symboltable, arg=list(), kwarg=dict()):
    if len(arg)!=2:
        raise CompileException( "expected exactly one argument in load_count" )
    symbol = symboltable.getConst( arg[1] )
    return ["  LDCOUNT {0}".format(symbol.name)]

def set_trigger( symboltable, arg=list(), kwarg=dict()):
    if len(arg)!=2:
        raise CompileException( "expected exactly one argument in set_trigger" )
    symbol = symboltable.getVar( arg[1], type_ = "trigger" )
    return ["  TRIGGER {0}".format(symbol.name)]

def set_dds( symboltable, arg=list(), kwarg=dict()):
    channel = symboltable.getConst( kwarg['channel'] )
    commandlist = list()
    if 'freq' in kwarg:
        freq = symboltable.getVar( kwarg['freq'] )
        commandlist.append( "  DDSFRQ {0}, {1}".format(channel.name, freq.name))
    if 'phase' in kwarg:
        freq = symboltable.getVar( kwarg['phase'] )
        commandlist.append( "  DDSPHS {0}, {1}".format(channel.name, freq.name))
    if 'amp' in kwarg:
        freq = symboltable.getVar( kwarg['amp'] )
        commandlist.append( "  DDSAMP {0}, {1}".format(channel.name, freq.name))
    if 'freqfine' in kwarg:
        freq = symboltable.getVar( kwarg['freqfine'] )
        commandlist.append( "  DDSFRQFINE {0}, {1}".format(channel.name, freq.name)) 
        commandlist.append( "  NOP" )       
    return commandlist
  
def read_pipe( symboltable, arg=list(), kwarg=dict()):
    return ["  READPIPE"]

def write_pipe( symboltable, arg=list(), kwarg=dict()):
    return ["  WRITEPIPE"]

def pipe_empty( symboltable, arg=list(), kwarg=dict()):
    #return ["  READPIPEEMPTY"]
    return {True: '  JMPPIPEEMPTY', False:'  JMPPIPEAVAIL'}

def ram_read_valid( symboltable, arg=list(), kwarg=dict()):
    return {True: ' JMPRAMVALID', False: '  JMPRAMINVALID'}

def exit_( symboltable, arg=list(), kwarg=dict()):
    if len(arg)!=2:
        raise CompileException( "expected exactly one argument in exit" )
    symbol = symboltable.getVar( arg[1], type_ = "exitcode" )
    return [ "  LDWR {0}".format(symbol.name),
             "  WAIT", "  WRITEPIPE", "  END"]

def set_ram_address( symboltable, arg=list(), kwarg=dict()):
    if len(arg)!=2:
        raise CompileException( "expected exactly one argument in set_ram_address" )
    symbol = symboltable.getVar( arg[1] )
    return [ "  SETRAMADDR {0}".format(symbol.name)]

def read_ram( symboltable, arg=list(), kwarg=dict()):
    return ["  RAMREAD"]

def wait_dds( symboltable, arg=list(), kwarg=dict()):
    return ["  WAITDDSWRITEDONE"]

def wait_trigger( symboltable, arg=list(), kwarg=dict()):
    if len(arg)!=2:
        raise CompileException( "expected exactly one argument in wait_trigger" )
    symbol = symboltable.getVar( arg[1] )
    return ["  WAITFORTRIGGER {0}".format(symbol.name)]

def apply_next_scan_point( symboltable, arg=list(), kwarg=dict()):
    if len(arg)!=1:
        raise CompileException( "apply_next_scan_point does not take arguments" )
    return [  "apply_next_scan_point:  READPIPEINDF",
              "  NOP",
              "  WRITEPIPEINDF",
              "  NOP",
              "  READPIPE",
              "  NOP",
              "  WRITEPIPE",
              "  NOP",
              "  STWI",
              "  JMPCMP apply_next_scan_point"  ]
    