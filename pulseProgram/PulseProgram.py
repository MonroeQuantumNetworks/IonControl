#
# File: ppcomp_Jan2008.py
# based on ppcomp2.py
#
# read in menomic pulse program and translate into bytecode
# modified on 6/5/2012 by C. Spencer Nichols
# rewritten Peter Maunz
  
import collections
import logging
import math
import re, os
import struct
import copy

import modules.magnitude as magnitude


# add deg to magnitude
magnitude.new_mag( 'deg', magnitude.mg(math.pi/180,'rad') )
  
class ppexception(Exception):
    def __init__(self, message, filename, line, context):
        super(ppexception,self).__init__(message)
        self.file = filename
        self.line = line
        self.context = context
  
# Code definitions
OPS = {'NOP'    : 0x00,
       'DDSFRQ' : 0x01,
       'DDSAMP' : 0x02,
       'DDSPHS' : 0x03,
       'DDSCHN' : 0x04,
       'SHUTR'  : 0x05,
       'COUNT'  : 0x06,
       'DELAY'  : 0x07,
       'LDWR'   : 0x08,
       'LDWI'   : 0x09,
       'STWR'   : 0x0A,
       'STWI'   : 0x0B,
       'LDINDF' : 0x0C,
       'ANDW'   : 0x0D,
       'ADDW'   : 0x0E,
       'INC'    : 0x0F,
       'DEC'    : 0x10,
       'CLRW'   : 0x11,
       'CMP'    : 0x12,
       'JMP'    : 0x13,
       'JMPZ'   : 0x14,
       'JMPNZ'  : 0x15,
       'DAC'    : 0x17,
       'DACUP'  : 0x18,
       'COUNT1'	: 0x20,
       'COUNTBOTH' : 0x21,
       'LDWR1'	: 0x22,
       'STWR1'  : 0x23,
       'CMP1'   : 0x24,
       'JMPZ1'  : 0x25,
       'JMPNZ1'	: 0x26,
       'CLRW1'	: 0x27,
       'SHUTRVAR':0x28,
       'SHUTTERMASK' : 0x30,
       'ASYNCSHUTTER' : 0x31,
       'COUNTERMASK' : 0x32,
       'TRIGGER' : 0x33,
       'UPDATE' : 0x34,
       'WAIT' : 0x35,
       'DDSFRQFINE' : 0x36,
       'LDCOUNT' : 0x37,
       'WRITEPIPE' : 0x38,
       'READPIPE' : 0x39,
       'LDTDCCOUNT' : 0x3a,
       'CMPEQUAL' : 0x3b,
       'JMPCMP' : 0x3c,
       'JMPNCMP': 0x3d,
       'JMPPIPEAVAIL': 0x3e,
       'JMPPIPEEMPTY': 0x3f,
       'READPIPEINDF': 0x40,
       'WRITEPIPEINDF': 0x41,
       'SETRAMADDR': 0x42,
       'RAMREADINDF' : 0x43,
       'RAMREAD' : 0x44,
       'JMPRAMVALID' : 0x45,
       'JMPRAMINVALID' : 0x46,
       'CMPGE' : 0x47,
       'CMPLE' : 0x48, 
       'CMPGREATER' : 0x4a,
       'ORW' : 0x4b,
       'UPDATEINDF' : 0x4d,
       'WAITDDSWRITEDONE' : 0x4e,
       'CMPLESS' : 0x4f,
       'ASYNCINVSHUTTER' : 0x50,
       'CMPNOTEQUAL': 0x51,
       'SUBW' : 0x52,
       'WAITFORTRIGGER': 0x53,
       'END'    : 0xFF }

class Dimensions:
    time = (0, 1, 0, 0, 0, 0, 0, 0, 0)
    frequency = (0, -1, 0, 0, 0, 0, 0, 0, 0)
    voltage = (2, -3, 0, 1, -1, 0, 0, 0, 0)
    current = (0, 0, 0, 0, 1, 0, 0, 0, 0)
    dimensionless = (0, 0, 0, 0, 0, 0, 0, 0, 0)

class Variable:
    def __init__(self):
        self.enabled = True
        self.value = 0        
        
    def __setstate__(self, d):
        self.__dict__ = d
        
    def __repr__(self):
        return str(self.__dict__)
    
    def __deepcopy__(self, mode):
        new = Variable()
        new.__dict__ = copy.deepcopy( self.__dict__ )
        return new 

    def __eq__(self,other):
        return self.__dict__==other.__dict__

    def __ne__(self, other):
        return not self == other
    
    def outValue(self):
        return self.value if self.enabled else self.value * 0

encodings = { 'AD9912_FRQ': (1e9/2**48, 'Hz', Dimensions.frequency, 0xffffffffffff ),
              'AD9910_FRQ': (1e9/2**32, 'Hz', Dimensions.frequency, 0xffffffff ),
              'AD9912_PHASE': (360./2**14, '', Dimensions.dimensionless, 0x3fff),
              'AD9910_PHASE': (360./2**16, '', Dimensions.dimensionless, 0xffff),
              'CURRENT': (1, 'A', Dimensions.current, 0xffffffff ),
              'VOLTAGE': (1, 'V', Dimensions.voltage, 0xffffffff ),
              'TIME' : ( 20, 'ns', Dimensions.time, 0x1 ),
              None: (1, '', Dimensions.dimensionless, 0xffffffffffffffff ),
              'None': (1, '', Dimensions.dimensionless, 0xffffffffffffffff ) }


def variableValueDict( variabledict ):
    returndict = dict()
    for name, var in variabledict.iteritems():
        returndict[name] = var.value
    return returndict

class PulseProgram:    
    """ Encapsulates a PulseProgrammer Program
    loadSource( filename ) loads the contents of the file
    The code is compiled in the following steps
        parse()         generates self.code
        toBytecode()    generates self.bytecode
        toBinary()      generates self.binarycode
    the procedure updateVariables( dictionary )  updates variable values in the bytecode
    """    
    def __init__(self):
        self.variabledict = collections.OrderedDict()        # keeps information on all variables to easily change them later
        self.labeldict = dict()          # keep information on all labels
        self.source = collections.OrderedDict()             # dictionary of source code files (stored as strings)
        self.code = []                   # this is a list of lines
        self.bytecode = []               # list of op, argument tuples
        self.binarycode = bytearray()    # binarycode to be uploaded
        self._exitcodes = dict()          # generate a reverse dictionary of variables of type exitcode

        
        class Board:
            channelLimit = 1    
            halfClockLimit = 500000000
        self.adIndexList = [(x,0) for x in range(8) ]
        self.adBoards = [ Board() ]*8
        
        self.timestep = magnitude.mg(20.0,'ns')

    def setHardware(self, adIndexList, adBoards, timestep ):
        self.adIndexList = adIndexList
        self.adBoards = adBoards
        self.timestep = timestep
        assert self.timestep.has_dimension('s')
        
    def saveSource(self):
        for name, text in self.source.iteritems():
            with open(os.path.join(self.pp_dir,name),'w') as f:
                f.write(text)            
        
    def loadSource(self, pp_file, docompile=True):
        """ Load the source pp_file
        #include files are loaded recursively
        all code lines are added to self.sourcelines
        for each source file the contents are added to the dictionary self.source
        """
        self.source.clear()
        self.pp_dir, self.pp_filename = os.path.split(pp_file)
        self.sourcelines = []
        self.insertSource(self.pp_filename)
        if docompile:
            self.compileCode()

    def updateVariables(self, variables ):
        """ update the variable values in the bytecode
        """
        logger = logging.getLogger(__name__)
        for name, value in variables.iteritems():
            if name in self.variabledict:
                var = self.variabledict[name]
                address = var.address
                var.value = value
                logger.debug( "updateVariables {0} at address 0x{2:x} value {1}, 0x{3:x}".format(name,value,address,int(var.data)) )
                var.data = self.convertParameter(value, var.encoding )
                self.dataBytecode[address] =  var.data 
                self.variabledict[name] = var
            else:
                logger.error( "variable {0} not found in dictionary.".format(name) )
        return self.bytecode
        
    def variables(self):
        mydict = dict()
        for name, var in self.variabledict.iteritems():
            mydict.update( {name: var.value })
        return mydict
        
    def variable(self, variablename ):
        return self.variabledict.get(variablename).value

    def variableUpdateCode(self, variablename, value ):
        """returns the code to update the variable directly on the fpga
        consists of variablelocation and variablevalue
        """
        var = self.variabledict[variablename]
        data = self.convertParameter(value, var.encoding )
        return bytearray( struct.pack('II', (var.address, data)))
        
    def flattenList(self,l):
        return [item for sublist in l for item in sublist]
        
    def variableScanCode(self, variablename, values):
        var = self.variabledict[variablename]
        # [item for sublist in l for item in sublist] idiom for flattening of list
        return self.flattenList( [ (var.address,self.convertParameter(x,var.encoding)) for x in values ] )
                   
    def multiVariableUpdateCode(self, variablenames, values):
        varslist = [ self.variabledict[name] for name in  variablenames]
        codelist = list()
        for var, value in zip(varslist,values):
            codelist.extend( ( var.address | 0x8000, self.convertParameter(value,var.encoding)) )  # bit 15 set means there is more to come
        if len(codelist)>1:
            codelist[-2] &= 0x7fff 
        return codelist
                   
    def loadFromMemory(self, docompile=True):
        """Similar to loadSource
        only this routine loads from self.source
        """
        self.sourcelines = []
        self._exitcodes = dict()
        self.insertSource(self.pp_filename)
        if docompile:
            self.compileCode()

    def toBinary(self):
        """ convert bytecode to binary
        """
        logger = logging.getLogger(__name__)
        self.binarycode = bytearray()
        for wordno, (op, arg) in enumerate(self.bytecode):
            logger.debug( "{0} {1} {2} {3}".format( hex(wordno), hex(op), hex(arg), hex((op<<(32-8)) + arg)) ) 
            self.binarycode += struct.pack('I', (op<<(32-8)) + arg)
        self.dataBinarycode = bytearray()
        for wordno, arg in enumerate(self.dataBytecode):
            logger.debug( "{0} {1}".format( hex(wordno), hex(arg) )) 
            self.dataBinarycode += struct.pack('Q', long(arg))
            
        return self.binarycode, self.dataBinarycode
        
    def currentVariablesText(self):
        lines = list()
        for name, var in iter(sorted(self.variabledict.iteritems())):
            lines.append("{0} {1}".format(name,var.value))
        return '\n'.join(lines)
           

# routines below here should not be needed by the user   

    insertPattern = re.compile('insert\s+([\w.-_]+)',re.IGNORECASE)
    codelinePattern = re.compile('(\s*[^#\s]+)',re.IGNORECASE)
    def insertSource(self, pp_file):
        """ read a source file pp_file
        calls itself recursively to for #insert
        adds the contents of this file to the dictionary self.source
        """
        logger = logging.getLogger(__name__)
        if pp_file not in self.source:
            with open(os.path.join(self.pp_dir,pp_file)) as f:
                self.source[pp_file] = ''.join(f.readlines())
        sourcecode = self.source[pp_file]
        for line, text in enumerate(sourcecode.splitlines()):
            m = self.insertPattern.match(text)
            if m:
                filename = m.group(1)
                logger.info( "inserting code from {0}".format(filename) )
                self.insertSource(filename)
            else:
                if self.codelinePattern.match(text):
                    self.sourcelines.append((text, line+1, pp_file))

    definePattern = re.compile('const\s+(\w+)\s+(\w+)[^#\n\r]*')     #csn
    def addDefine(self, m, lineno, sourcename):
        """ add the define to the self.defines dictionary
        """
        logger = logging.getLogger(__name__)
        label, value = m.groups() #change lab to label for readability CWC 08162012
        if label in self.defines:
            logger.error( "Error parsing defs in file '{0}': attempted to redefine'{1}' to '{2}' from '{3}'".format(sourcename, label, value, self.defines[label]) )#correct float to value CWC 08162012
            raise ppexception("Redefining variable", sourcename, lineno, label)    
        else:
            self.defines[label] = float(value)

    labelPattern = re.compile('(\w+):\s+([^#\n\r]*)')
    opPattern = re.compile('\s*(\w+)(?:\s+([^#\n\r]*)){0,1}',re.IGNORECASE)
    varPattern = re.compile('var\s+(\w+)\s+([^#,\n\r]+)(?:,([^#,\n\r]+)){0,1}(?:,([^#,\n\r]+)){0,1}(?:,([^#,\n\r]+)){0,1}(?:#([^\n\r]+)){0,1}') #
    def parse(self):
        """ parse the code
        """
        logger = logging.getLogger(__name__)
        self.code = []
        self.variabledict = collections.OrderedDict() 
        self.defines = dict()
        addr_offset = 0
    
        for text, lineno, sourcename in self.sourcelines:    
            m = self.varPattern.match(text)
            if m:
                self.addVariable(m,lineno,sourcename)
            else:
                m = self.definePattern.match(text)
                if m:
                    self.addDefine(m,lineno,sourcename)
                else:
                    # extract any JMP label, if present
                    m = self.labelPattern.match(text)
                    if m:
                        label, text = m.groups() #so the operation after ":" still gets parsed CWC 08162012
                    else:
                        label = None #The label for non-jump label line is NONE CWC 08172012
            
                    # search OPS list for a match to the current line
                    m = self.opPattern.match(text)
                    if m:
                        op, args = m.groups()
                        op = op.upper()
                        # split and remove whitespace 
                        arglist = [0] if args is None else [ 0 if x is None else x.strip() for x in args.split(',')]
                        #substitute the defined variable directly with the corresponding value CWC 08172012
                        arglist = [ self.defines[x] if x in self.defines else x for x in arglist ] 
                        #check for dds commands so CHAN commands can be inserted
                        if (op[:3] == 'DDS'):
                            try:
                                board = self.adIndexList[int(arglist[0])][0]
                            except ValueError:
                                raise ppexception("DDS argument does not resolve to integer", sourcename, lineno, arglist[0])
                            chan = self.adIndexList[int(arglist[0])][1]
                            if (self.adBoards[board].channelLimit != 1):
                                #boards with more than one channel require an extra channel selection command
                                chanData = self.adBoards[board].addCMD(chan)
                                chanData = (int(board) << 16) + chanData
                                self.code.append((len(self.code)+addr_offset, 'DDSCHN', chanData, label, sourcename, lineno))
                        data = arglist if len(arglist)>1 else arglist[0]

                        self.addLabel( label, len(self.code), sourcename, lineno)
                        self.code.append((len(self.code)+addr_offset, op, data, label, sourcename, lineno))
                    else:
                        logger.error( "Error processing line {2}: '{0}' in file '{1}' (unknown opcode?)".format(text, sourcename, lineno) )
                        raise ppexception("Error processing line {2}: '{0}' in file '{1}' (unknown opcode?)".format(text, sourcename, lineno),
                                          sourcename, lineno, text)
        self.dataCode = self.appendVariableCode()
        return self.code, self.dataCode

    def addLabel(self,label,address, sourcename, lineno):
        if label is not None:
            if label in self.defines:
                raise ppexception("Redefining label: {0}".format(label), sourcename, lineno, label)
            else:
                self.defines[label] = address
                self.labeldict[label] = address
                
    def appendVariableCode(self):
        """ append all variables to the instruction part of the code
        """
        self.dataCode = []
        for var in self.variabledict.values():
            address = len(self.dataCode)
            self.dataCode.append((address, 'NOP', var.data if var.enabled else 0, None, var.origin, 0 ))
            var.address = address    
        return self.dataCode    

    def addVariable(self, m, lineno, sourcename):
        """ add a variable to the self.variablesdict
        """
        logger = logging.getLogger(__name__)
        logger.debug( "Variable {0} {1} {2}".format( m.groups(), lineno, sourcename ) )
        var = Variable()
        label, data, var.type, unit, var.encoding, var.comment = [ x if x is None else x.strip() for x in m.groups()]
        var.name = label
        var.origin = sourcename
        var.lineno = lineno
        var.enabled = True

        if var.encoding not in encodings:
            raise ppexception("unknown encoding {0} in file '{1}':{2}".format(var.encoding,sourcename,lineno), sourcename, lineno, var.encoding)

        try:
            data = str(eval(data,globals(),self.defines))
        except Exception:
            logger.exception( "Evaluation error in file '{0}' on line: '{1}'".format(sourcename, data) )

        if unit is not None:
            var.value = magnitude.mg( float(data), unit )
            data = self.convertParameter( var.value, var.encoding )
        else:
            var.value = magnitude.mg( float(data), '' )
            var.value.output_prec(0)   # without dimension the parameter has to be int. Thus, we do not want decimal places :)
            data = int(round(float(data)))

        if label in self.defines:
            logger.error( "Error in file '%s': attempted to reassign '%s' to '%s' (from prev. value of '%s') in a var statement." %(sourcename,label,data,self.defines[label]) )
            raise ppexception("variable redifinition", sourcename, lineno, label)
        else:
            self.defines[label] = label # add the variable to the dictionary of definitions to prevent identifiers and variables from having the same name
                                        # however, we do not want it replaced with a number but keep the name for the last stage of compilation
            pass
        var.data = data
        var.strvalue = str(var.value)
        self.variabledict.update({ label: var})
        if var.type == "exitcode":
            self._exitcodes[data & 0x0000ffff] = var

    # code is (address, operation, data, label or variablename, currentfile)
    def toBytecode(self):
        """ generate bytecode from code
        """
        logger = logging.getLogger(__name__)
        logger.debug( "\nCode ---> ByteCode:" )
        self.bytecode = []
        self.dataBytecode = []
        for line in self.code:
            logger.debug( "{0}: {1}".format(hex(line[0]),  line[1:] )) 
            bytedata = 0
            if line[1] not in OPS:
                raise ppexception("Unknown command {0}".format(line[1]), line[4], line[5], line[1]) 
            byteop = OPS[line[1]]
            try:
                data = line[2]
                #attempt to locate commands with constant data
                if (data == ''):
                    #found empty data
                    bytedata = 0
                elif isinstance(data,(int,long)):
                    bytedata = data
                elif isinstance(data,float):
                    bytedata = int(data)
                elif isinstance(data,basestring): # now we are dealing with a variable and need its address
                    bytedata = self.variabledict[line[2]].address if line[2] in self.variabledict else self.labeldict[line[2]]
                elif isinstance(data,list): # list is what we have for DDS, will have 8bit channel and 16bit address
                    channel, data = line[2]
                    if isinstance(data,basestring):
                        data = self.variabledict[data].address
                    bytedata = ((int(channel) & 0xf) << (64-16)) | (int(data) & 0x0fff)
            except KeyError:
                logger.error( "Error assembling bytecode from file '{0}': Unknown variable: '{1}'. \n".format(line[4],data) )
                raise ppexception("{0}: Unknown variable {1}".format(line[4],data), line[4], line[5], data)
            self.bytecode.append((byteop, bytedata))
            logger.debug( "---> {0} {1}".format(hex(byteop), hex(bytedata)) )
    
        for line in self.dataCode:
            logger.debug( "{0}: {1}".format(hex(line[0]),  line[1:] )) 
            bytedata = 0
            if line[1] not in OPS:
                raise ppexception("Unknown command {0}".format(line[1]), line[4], line[5], line[1]) 
            byteop = OPS[line[1]]
            try:
                data = line[2]
                #attempt to locate commands with constant data
                if (data == ''):
                    #found empty data
                    bytedata = 0
                elif isinstance(data,(int,long)):
                    bytedata = data
                elif isinstance(data,float):
                    bytedata = int(data)
                elif isinstance(data,basestring): # now we are dealing with a variable and need its address
                    bytedata = self.variabledict[line[2]].address if line[2] in self.variabledict else self.labeldict[line[2]]
                elif isinstance(data,list): # list is what we have for DDS, will have 8bit channel and 16bit address
                    channel, data = line[2]
                    if isinstance(data,basestring):
                        data = self.variabledict[data].address
                    bytedata = ((int(channel) & 0xf) << (64-16)) | (int(data) & 0x0fff)
            except KeyError:
                logger.error( "Error assembling bytecode from file '{0}': Unknown variable: '{1}'. \n".format(line[4],data) )
                raise ppexception("{0}: Unknown variable {1}".format(line[4],data), line[4], line[5], data)
            self.dataBytecode.append( bytedata )
            logger.debug( "---> {0} {1}".format(hex(byteop), hex(bytedata)) )

        return self.bytecode, self.dataBytecode


    def convertParameter(self, mag, encoding=None ):
        """ convert a dimensioned parameter to the binary value
        expected by the hardware. The conversion is determined by the variable encoding
        """
        if isinstance(mag, magnitude.Magnitude):
            if tuple(mag.dimension())==Dimensions.time:
                result = int((mag/self.timestep).round()) 
            else:
                step, unit, _, mask = encodings[encoding]
                result = int(math.floor(mag.toval(unit)/step)) & mask
        else:
            if encoding:
                step, unit, _, mask = encodings[encoding]
                result = int(math.floor(mag/step)) & mask
            else:
                result = mag
        return result

    def compileCode(self):
        self.parse()
        self.toBytecode()
        
    def exitcode(self, code):
        if code in self._exitcodes:
            var = self._exitcodes[code]
            if var.comment:
                return var.comment
            else:
                return var.name
        else:
            return "Exitcode {0} Not found".format(code)

if __name__ == "__main__":
    pp = PulseProgram()
    pp.debug = True
    pp.loadSource(r"prog\Ions\Bluetest.pp")
    #pp.loadSource(r"prog\single_pulse_exp_adiabatic.pp")
    
        
    pp.toBytecode()
    print "updateVariables"
    pp.updateVariables({'coolingFreq': magnitude.mg(125,'MHz')})
    
    for op, val in pp.bytecode:
        print hex(op), hex(val)
        
    pp.toBinary()
        
#    for var in pp.variabledict.iteritems():
#        print var
    
