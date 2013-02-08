#
# File: ppcomp_Jan2008.py
# based on ppcomp2.py
#
# read in menomic pulse program and translate into bytecode

#modified on 6/5/2012 by C. Spencer Nichols
#

import sys, re, os
import magnitude
import struct

#TIMESTEP= 16e-9
TIMESTEP = 20.8333333333e-9  # in seconds

class ppexception(Exception):
    pass

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
       'END'    : 0xFF }

class Dimensions:
    time = (0, 1, 0, 0, 0, 0, 0, 0, 0)
    frequency = (0, -1, 0, 0, 0, 0, 0, 0, 0)
    voltage = (2, -3, 0, 1, -1, 0, 0, 0, 0)
    current = (0, 0, 0, 0, 1, 0, 0, 0, 0)
    dimensionless = (0, 0, 0, 0, 0, 0, 0, 0, 0)

class Variable:
    pass

encodings = { 'AD9912_FRQ': (5e8/2**32, 'Hz', Dimensions.frequency, 0xffffffff ),
              'AD9912_FRQFINE': (5e8/2**48, 'Hz', Dimensions.frequency, 0xffff ),
              'AD9912_PHASE': (360/2**14, '', Dimensions.dimensionless, 0xfff),
              'CURRENT': (1, 'A', Dimensions.current, 0xffffffff ),
              'VOLTAGE': (1, 'V', Dimensions.voltage, 0xffffffff ) }


debug = False


class PulseProgram:    
    def __init__(self):
        self.variabledict = dict()       # keeps information on all variables to easily change them later
        self.labeldict = dict()          # keep information on all labels
        self.source = ''                 # this is the source code
        self.code = []                   # this is a list of lines
        self.bytecode = []               # list of op, argument tuples
        self.binarycode = bytearray()    # binarycode to be uploaded
        
    def loadSource(self, pp_file):
        self.pp_dir, self.pp_filename = os.path.split(pp_file)
        self.sourcelines = []
        self.insertSource(self.pp_filename)
        self.source = '\n'.join(self.sourcelines)

    insertPattern = re.compile('#insert\s+([\w.-_]+)',re.IGNORECASE)   
    def insertSource(self, pp_file):
        with open(os.path.join(self.pp_dir,pp_file)) as f:
            for line in f:
                m = self.insertPattern.match(line)
                if m:
                    filename = m.group(1)
                    print "inserting code from ",filename,"..."
                    self.insertSource(filename)
                else:
                    self.sourcelines.append(line)
                
        
        

    # main compiler routine, called from outside
    def pp2bytecode(self, adIndexList, adBoards, parameters = dict()):
        globals().update(parameters)
        units = {'cycles2ns': 1e-9/TIMESTEP, 'cycles2us': 1e-6/TIMESTEP, 'cycles2ms': 1e-3/TIMESTEP}
        globals().update(units)
    
        # initialize the datastructures
        self.variabledict = dict()
        self.labeldict = dict()
        self.bytecode = []
        self.binarycode = bytearray()
        self.defines = dict()
        
        # parse defs, ops, and make variable registers
        code = parse_code(self.pp_filename, self.pp_dir, 0, adIndexList, adBoards)
    
        # then make global registers for parameters so that ops can use them.
        # parameters that start with "F_" are assumed to be frequency, those
        # that start with "PH_" are phase, and the rest are int.
        if debug:
            print "\nGlobal parameters:"
        for key,value in parameters.iteritems():
            if ((key[:2] == "F_" or key[:2] == "f_") and key[-3:] != "INC"):
                data = float(value)#int(round(float(value))) changed to allow sub-MHz resolution for the frequency CWC 08162012
            elif (key[:3] == "PH_" or key[:3] == "Ph_" or key[:3] == "ph_"):
                data = int(round(float(value)/360*(2**14)))
            elif (key[:3] == "NS_" or key[:3] == "ns_"):
                data = int(round(float(value)*1e-9/TIMESTEP))
            elif (key[:3] == "US_" or key[:3] == "us_"):
                data = int(round(float(value)*1e-6/TIMESTEP))
            elif (key[:3] == "MS_" or key[:3] == "ms_"):
                data = int(round(float(value)*1e-3/TIMESTEP))
            elif (key[:4] == "INT_" or key[:4] == "int_" or key[:4] == "Int_"):
                data = int(round(float(value)))
            elif (key[:2] == "A_" or key[:2] == "a_"):
                data = int(round(float(value)))
            elif (key[:2] == "V_" or key[:2] == "v_"): #added variables for DAC Vout CWC 08162012
                data = int(float(value)/2.5*2**13)
            elif (key[-3:] == "INC" and (key[:2] == "F_" or key[:2] == "f_")):
                    data = int(float(value)/250*0x80000000)
            else:
                data = float(value)
                #print "No unit specified for parameter", key ,", assuming \"int\""
            address = len(code)
            code.append((address, 'NOP', data, key, 'globalparam'))
            var = Variable()
            var.name = key
            var.address = address
            var.type = 0
            var.origin = 'globalparam'
            variabledict.update({ key: var})
            if debug:
                print key, ":", value, "-->", data
    
        for line in code:
            print line
        bytecode = bc_gen(code, adIndexList, adBoards)
        return bytecode



    def parse_code(self, pp_filename, pp_dir, first_addr, adIndexList, adBoards):
        f = open(pp_dir+pp_filename)
        source = f.readlines()
        f.close()
    
        # first, parse defenitions
        defs = parse_defs(source, pp_filename)
        #print defs
    
        # then, parse ops and take care of #insert instructions by recursively
        # calling parse_code from inside parse_ops(...)
        code = parse_ops(source,defs,pp_dir,first_addr,pp_filename, adIndexList, adBoards)
        if (code != []):
            first_var_addr = code[len(code)-1][0]+1
        else:
            first_var_addr = 0
    
        # next, make variable registers
        code_varsonly, variabledict = parse_vars(source,defs,first_var_addr,pp_filename)
        code.extend(code_varsonly)
    
        return (code, variabledict)



    definePattern = re.compile('#define\s+(\w+)\s+(\w+)[^#\n\r]*')     #csn
    def parse_defs(self,source, current_file):
        self.defines = {}
    
        for line in self.source:
            # is it a definition?
            m = self.definePattern.match(line)     #csn   
            if m:
                label, value = m.groups() #change lab to label for readability CWC 08162012
                if (self.defines.has_key(label)):
                    #print "Error parsing defs in file '%s': attempted to redefine'%s' to '%s' from '%s'" %(current_file,label, value, defs[label]) #correct float to value CWC 08162012
                    #sys.exit(1)
                    raise ppexception("Redefining variable")    
                else:
                    self.defines[label] = float(value)
        return self.defines



    def parse_ops(source, defs, pp_dir,first_addr,current_file, adIndexList, adBoards):
        code = []
        addr_offset = first_addr
    
        for line in source:
            # process #insert instruction, if present
            m = re.match('#insert\s+([\w.-_]+)',line)
            if not m:
                 m = re.match('#INSERT\s+([\w.-_]+)',line)
            if m:
                print "inserting code from ",m.group(1),"..."
                insert_this_code = parse_code(m.group(1), pp_dir, len(code)+addr_offset, adIndexList, adBoards)
                if (insert_this_code != None):
                    code.extend(insert_this_code)
                continue
    
            # filter out irrelevant or commented lines (or variable declarations CWC 08162012)
            if (line[0]=='#') or (len(line.strip())<2 or (line[0:3] == 'var')):
                continue
    
            # extract any JMP label, if present
            m = re.match('(\w+):\s+(.*)',line)
            if m:
                label = m.group(1)
                line = "%s " % m.group(2) #so the operation after ":" still gets parsed CWC 08162012
            else:
                label = None #The label for non-jump label line is NONE CWC 08172012
    
            # search OPS list for a match to the current line
            data = ''
            for op in OPS.keys():
                m = re.match('\s*%s\s+([^#\n\r]*)' % op, line)
                if not m:
                    m = re.match('\s*%s\s+([^#\n\r]*)' % op.lower(), line)
                if m:
                    args = m.group(1)
                    arglist = map(lambda x: x.strip(), args.split(','))
                    for i in range(len(arglist)):
                        if defs.has_key(arglist[i]):
                            arglist[i] = defs[arglist[i]] #substitute the defined variable directly with the corresponding value CWC 08172012
                        # Delay parsing until all code is known
                    #check for dds commands so CHAN commands can be inserted
                    if (op[:3] == 'DDS'):
                        board = adIndexList[int(arglist[0])][0]
                        chan = adIndexList[int(arglist[0])][1]
                        if (adBoards[board].channelLimit != 1):
                            #boards with more than one channel require an extra channel selection command
                            chanData = adBoards[board].addCMD(chan)
                            chanData = (int(board) << 16) + chanData
                            code.append((len(code)+addr_offset, 'DDSCHN', chanData, label, current_file))
                    if (len(arglist) == 1):
                        data = arglist[0]
                    else:
                        data = arglist
                    break
            else:
                print "Error processing line '%s' in file '%s' (unknown opcode?)" %(line, current_file)
                    #sys.exit(1)#exit the program after error CWC 08172012
                raise ppexception("Error parsing ops.")
    
            code.append((len(code)+addr_offset, op, data, label, current_file))
    
        return code

    varPattern = re.compile('var\s+(\w+)\s+([^#,\n\r]+)(?:,([^#,\n\r]+)){0,1}(?:,([^#,\n\r]+)){0,1}(?:,([^#,\n\r]+)){0,1}(?:#([^\n\r]+)){0,1}') #
    def parse_vars(self,first_var_addr,current_file):
        code = []
        variabledict = dict()
        for line in source:
            #syntax is var name value [, type, encoding, unit]
            m = self.varPattern.match(line) #
            if m:
                var = Variable()
                label, data, var.type, unit, var.encoding, var.comment = [ x if x is None else x.strip() for x in m.groups()]
                var.name = label
                var.origin = current_file
    
                try:
                    data = str(eval(data,globals(),defs))
                except Exception, e:
                    print "Evaluation error in file '%s' on line: '%s'" %(current_file, data)
    
                if unit is not None:
                    data = convertParameter( magnitude.mg( float(data), unit ), var )
                    print data, hex(data)
                else:
                    data = int(round(float(data)))
                    print data, hex(data)
    
                if label in self.defines:
                    print "Error in file '%s': attempted to reassign '%s' to '%s' (from prev. value of '%s') in a var statement." %(current_file,label,data,defs[label])
                    raise ppexception("variable redifinition")
                else:
                    defs[label] = data #add the variable to the dictionary of definitions CWC 08172012
    
                address = len(code)+first_var_addr
                code.append((address, 'NOP', data, label, current_file))
                var.address = address
                var.index = len(variabledict)
                variabledict.update({ label: var})
            else:
                print "Error processing line '%s' in file '%s': Buffer overflow" %(line, current_file)
                #sys.exit(1) #exit the program after error CWC 08172012
                raise ppexception("Unidentified input")
    
        return (code, variabledict)



    # code is (address, operation, data, label or variablename, currentfile)
    def bc_gen(self):
        if debug:
            print "\nCode ---> ByteCode:"
        self.bytecode = []
        for index, line in enumerate(self.code):
            if debug:
                print line[0],  ": ", line[1:]
            bytedata = 0
            byteop = OPS[line[1]]
            try:
                data = line[2]
                #attempt to locate commands with constant data
                if (data == ''):
                    #found empty data
                    bytedata = 0
                elif isinstance(data,basestring): # now we are dealing with a variable and need its address
                    bytedata = self.variabledict[line[2]].address
                elif isinstance(data,list): # list is what we have for DDS, will have 8bit channel and 16bit address
                    channel, data = line[2]
                    if isinstance(data,basestring):
                        data = self.variabledict[data].address
                    bytedata = (int(channel) << 16) + int(data) & 0xffff
            except KeyError:
                print "Error assembling bytecode from file '{0}': Unknown variable: '{1}'. \n".format(line[4],data) # raise
                #sys.exit(1) #exit the program after error CWC 08172012
                raise ppexception("Unknown variable")
            bytecode.append((byteop, bytedata))
            if debug:
                print line[0],  ": ", line[1:], "--->", (hex(byteop), hex(bytedata))
    
        return bytecode


    def codeToBinary(self):
        self.binarycode = bytearray()
        for op, arg in self.code:
            if debug:
                print hex(op), hex(arg), hex(int((op<<24) + arg))
            self.binarycode += struct.pack('I', int((op<<24) + arg))
        return self.binarycode

    def convertDimension(self, mag, variable ):
        step, unit, dimension, mask = encodings[variable.encoding]
        return int(round(mag.toval(unit)/step)) & mask

    def convertParameter(self, mag, variable=None ):
        if isinstance(mag, magnitude.Magnitude):
            if tuple(mag.dimension())==Dimensions.time:
                return int(round(mag.toval('s')/TIMESTEP)) 
            else:
                step, unit, dimension, mask = encodings[variable.encoding]
                return int(round(mag.toval(unit)/step)) & mask
        else:
            return mag

    def updateVariables(self, variables ):
        for name, value in variables.iteritems():
            if name in self.variabledict:
                address = self.variabledict[name].address
                self.code[address] = (code[address][0], convertParameter(value, variabledict[name]))
            else:
                print "variable", name, "not found in dictionary."
        return code



if __name__ == "__main__":
    class Board:
        channelLimit = 1    
        halfClockLimit = 500000000
        
    print "Start"
    debug = True
    adIndex = [(x,0) for x in range(6) ]
    adBoards = [ Board() ]*6
    code, variabledict = pp2bytecode(r"prog\Ions\Bluetest.pp", adIndex, adBoards)
    print code
    for name, var in variabledict.iteritems():
        print name, var.__dict__
    binarycode = codeToBinary( code )
    with open('bytecode','wb') as of:
        of.write( binarycode )
    
    print hex( convertParameter( magnitude.mg(250,'MHz'), variabledict['coolingFreq'] ) )
    code = updateVariables( code, variabledict, {'coolingTime':magnitude.mg(10,'ms')} )
    
    for line, (cmd, val) in enumerate(code):
        print hex(line), hex(cmd), hex(val)
