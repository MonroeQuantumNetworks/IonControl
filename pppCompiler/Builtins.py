'''
Created on Feb 15, 2014

@author: pmaunz
'''
from CompileException import CompileException
from modules.stringutilit import stringToBool

def set_shutter( symboltable, arg=list(), kwarg=dict() ):
    """
    set_shutter( <shutter> )
    Set the shutter values to be applied with next update.
    """
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
    """
    set_inv_shutter( <shutter> )
    Set inverse shutter values to be applied with next update. All bits that are green become disabled, all bit red enabled, all white bits remain unaltered.
    """
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
    """
    set_counter( <counter> )
    Set the counterchannels to be enabled after the next update.
    """
    if len(arg)!=2:
        raise CompileException( "expected exactly one argument in set_counter" )
    symbol = symboltable.getVar( arg[1] )
    return ["  COUNTERMASK {0}".format(symbol.name)]

def clear_counter( symboltable, arg=list(), kwarg=dict() ):
    """
    clear_counter()
    Disable all counters after the next update.
    """
    if len(arg)!=1:
        raise CompileException( "expected no arguments in clear_counter" )
    return ["  COUNTERMASK NULL"]

def update( symboltable, arg=list(), kwarg=dict() ):
    """
    update( [time parameter], [wait_dds=True] )
    Update the shutter, trigger and counter gate outputs.
    If time parameter is given, start timer with this time.
    wait_dds=True (default): wait for all DDS and other hardware to be written.
    wait_dds=False : continue without waiting for hardware to be written.
    """
    code = ["  WAITDDSWRITEDONE"] if stringToBool(kwarg.get('wait_dds',True)) else list()
    pulseMode = stringToBool( kwarg.get('pulse_mode',False) )
    if len(arg)>=2:
        symbol = symboltable.getVar( arg[1] )
        return code + ["  WAIT",
                "  UPDATE {0}{1}".format('1, ' if pulseMode else '', symbol.name) ]
    return code + ["  WAIT",
            "  UPDATE NULL"]

def load_count( symboltable, arg=list(), kwarg=dict()):
    """
    load_count( <const> )
    load detected counts from counter channel given by the const paarameter.
    The new count value becomes available AFTER the gate is closed and is available
    until the next counter gate is closed for the same channel.
    """
    if len(arg)!=2:
        raise CompileException( "expected exactly one argument in load_count" )
    symbol = symboltable.getConst( arg[1] )
    return ["  LDCOUNT {0}".format(symbol.name)]

def set_trigger( symboltable, arg=list(), kwarg=dict()):
    """
    set_trigger( <trigger> )
    set trigger values to be applied after next update.
    trigger channels only put out one clock cycle pulses when enabled.
    """
    if len(arg)!=2:
        raise CompileException( "expected exactly one argument in set_trigger" )
    symbol = symboltable.getVar( arg[1], type_ = "trigger" )
    return ["  TRIGGER {0}".format(symbol.name)]

def set_dds( symboltable, arg=list(), kwarg=dict()):
    """
    set_dds( <const>, [freq=<parameter>], [phase=<parameter>], [amp=<parameter>] )
    set dds parameters of channel given by const parameter.
    Only given parameters are written. Frequency and Phase
    only take effect after the next io_update trigger.
    Amplitude takes effect immediately.
    """
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
    return commandlist

def set_dac( symboltable, arg=list(), kwarg=dict()):
    """
    set_dac( <const>, <parameter> )
    set dac channel given by const parameter to value given by second parameter.
    """
    if len(arg)!=3:
        raise CompileException( "expected exactly two arguments in serial_write" )
    channel = symboltable.getConst( arg[1] )
    value = symboltable.getVar( arg[2] )
    return [ "  DACOUT {0}, {1}".format(channel.name, value.name) ]

def serial_write( symboltable, arg=list(), kwarg=dict()):  # channel, variable
    """
    serial_write( <const channel>, <parameter value> )
    write value to serial interface channel.
    """
    if len(arg)!=3:
        raise CompileException( "expected exactly two arguments in serial_write" )
    channel = symboltable.getConst( arg[1] )
    value = symboltable.getVar( arg[2] )
    return [ "  SERIALWRITE {0}, {1}".format(channel.name, value.name) ]

def set_parameter( symboltable, arg=list(), kwarg=dict()):  # index, variable):
    """
    set_parameter( <const index>, <parameter value> )
    set pulser parameter channel index to value.
    """
    if len(arg)!=3:
        raise CompileException( "expected exactly two arguments in set_parameter" )
    channel = symboltable.getConst( arg[1] )
    value = symboltable.getVar( arg[2] )
    return [ "  SETPARAMETER {0}, {1}".format(channel.name, value.name) ]
  
def read_pipe( symboltable, arg=list(), kwarg=dict()):
    """
    <parameter> = read_pipe()
    Read one word from the incoming pipe and place in parameter.
    """
    return ["  READPIPE"]

def write_pipe( symboltable, arg=list(), kwarg=dict()):
    """
    write_pipe( <parameter> )
    Write parameter to pipe to computer.
    """
    code = list()
    if len(arg)>1:
        value = symboltable.getVar( arg[1] )
        code.append("  LDWR {0}".format(value.name))
    code.append("  WRITEPIPE")
    return code

def write_result( symboltable, arg=list(), kwarg=dict()):  # channel, variable
    """
    write_result( <const channel>, <parameter value> )
    Write value as a result of the given channel.
    Values can be plotted by selecting "Result" and channel
    number in the Evaluation configuration.
    """
    if len(arg)!=3:
        raise CompileException( "expected exactly two arguments in write_result" )
    channel = symboltable.getConst( arg[1] )
    value = symboltable.getVar( arg[2] )
    return [ "  WRITERESULTTOPIPE {0}, {1}".format(channel.name, value.name) ]

def pipe_empty( symboltable, arg=list(), kwarg=dict()):
    """
    pipe_empty()
    return true if pipe from computer is empty.
    """
    #return ["  READPIPEEMPTY"]
    return {True: '  JMPPIPEEMPTY', False:'  JMPPIPEAVAIL'}

def ram_read_valid( symboltable, arg=list(), kwarg=dict()):
    """
    ram_read_valid()
    true if the next word read from RAM is available and valid.
    """
    return {True: ' JMPRAMVALID', False: '  JMPRAMINVALID'}

def exit_( symboltable, arg=list(), kwarg=dict()):
    """
    exit( <exitcode> )
    Stop propgram execution with the given exitcode.
    """
    if len(arg)!=2:
        raise CompileException( "expected exactly one argument in exit" )
    symbol = symboltable.getVar( arg[1], type_ = "exitcode" )
    return [ "  LDWR {0}".format(symbol.name),
             "  WAIT", "  WRITEPIPE", "  END"]

def set_ram_address( symboltable, arg=list(), kwarg=dict()):
    """
    set_ram_address( <parameter> )
    Set the address of the RAM read pointer.
    Invalidates the FIFO and starts reading at the given address.
    """
    if len(arg)!=2:
        raise CompileException( "expected exactly one argument in set_ram_address" )
    symbol = symboltable.getVar( arg[1] )
    return [ "  SETRAMADDR {0}".format(symbol.name)]

def read_ram( symboltable, arg=list(), kwarg=dict()):
    """
    parameter = read_ram()
    Read one word from the RAM pipe.
    Only valif if ram_valid() return true.
    """
    return ["  RAMREAD"]

def wait_dds( symboltable, arg=list(), kwarg=dict()):
    """
    wait_dds()
    wait until all external hardware has been written.
    """
    return ["  WAITDDSWRITEDONE"]

def wait_trigger( symboltable, arg=list(), kwarg=dict()):
    """
    wait_trigger( <parameter> )
    wait for external trigger. Parameter is a bitmask where
    [7:0]: edge trigger, continue if |(parameter[7:0] & trigger_in[7:0])
    [31:24]: level trigger, we care about bits set here.
    [23:16]: and we need those bits to have the value given here.
    """
    if len(arg)!=2:
        raise CompileException( "expected exactly one argument in wait_trigger" )
    symbol = symboltable.getVar( arg[1] )
    return ["  WAITFORTRIGGER {0}".format(symbol.name)]

def apply_next_scan_point( symboltable, arg=list(), kwarg=dict()):
    """
    apply_next_scan_point()
    To be called to proceed to the next scan point.
    It will update all necessary parameters for the enxt scan point.
    """
    if len(arg)!=1:
        raise CompileException( "apply_next_scan_point does not take arguments" )
    return [  "apply_next_scan_point:  READPIPEINDF",
              "  WRITEPIPEINDF",
              "  READPIPE",
              "  WRITEPIPE",
              "  STWI",
              "  JMPCMP apply_next_scan_point"  ]
    