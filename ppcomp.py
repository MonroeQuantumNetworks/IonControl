#
# File: ppcomp_Jan2008.py
# based on ppcomp2.py
#
# read in menomic pulse program and translate into bytecode

#modified on 6/5/2012 by C. Spencer Nichols
#

import os, sys, string, re, math
import magnitude

#TIMESTEP= 16e-9
TIMESTEP = 20.8333333333e-9  # in seconds
FREQSTEP = 1e9/2**48  # in Hz
CURRSTEP = 1                 # in A
VOLTSTEP = 10/2**16          # in V

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
       'DDSFREQFINE' : 0x36,
       'LDCOUNT' : 0x37,
       'END'    : 0xFF }

debug = False


class Dimensions:
    time = (0, 1, 0, 0, 0, 0, 0, 0, 0)
    frequency = (0, -1, 0, 0, 0, 0, 0, 0, 0)
    voltage = (2, -3, 0, 1, -1, 0, 0, 0, 0)
    current = (0, 0, 0, 0, 1, 0, 0, 0, 0)

class Variable:
    pass

# main compiler routine, called from outside
def pp2bytecode(pp_file, adIndexList, adBoards, parameters = dict()):
    globals().update(parameters)
    units = {'cycles2ns': 1e-9/TIMESTEP, 'cycles2us': 1e-6/TIMESTEP, 'cycles2ms': 1e-3/TIMESTEP}
    globals().update(units)

    try:
        pp_dir = pp_file.rsplit('/',1)[0]+'/'
        pp_filename = pp_file.rsplit('/',1)[1]
    except:
        pp_dir = ''
        pp_filename = pp_file

    # parse defs, ops, and make variable registers
    code, variabledict = parse_code(pp_filename, pp_dir,0, adIndexList, adBoards)

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

    bytecode = bc_gen(code, adIndexList, adBoards)
    return (bytecode,variabledict)



def parse_code(pp_filename, pp_dir, first_addr, adIndexList, adBoards):
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




def parse_defs(source, current_file):
    defs = {}

    for line in source:
        # is it a definition?
        m = re.match('#define\s+(\w+)\s+(\w+)[^#\n\r]*', line)     #csn

        if m:
            label = m.group(1) #change lab to label for readability CWC 08162012
            #print lab
            value = m.group(2)
            #print value
            if (defs.has_key(label)):
                print "Error parsing defs in file '%s': attempted to redefine'%s' to '%s' from '%s'" %(current_file,label, value, defs[label]) #correct float to value CWC 08162012
                #sys.exit(1)
                raise ppexception("Redefining variable")

            else:
                defs[label] = float(value)

            continue
    return defs



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


def convertTime( mag ):
    return int(round(mag.toval('s')/TIMESTEP)) 

def convertFrequency( mag ):
    return int(round(mag.toval('Hz')/FREQSTEP)) 

def convertCurrent( mag ):
    return int(round(mag.toval('A')/CURRSTEP)) 

def convertVoltage( mag ):
    return int(round(mag.toval('V')/VOLTSTEP)) 

def convertParameter( mag ):
    return { Dimensions.time: convertTime,
      Dimensions.frequency: convertFrequency,
      Dimensions.current: convertCurrent,
      Dimensions.voltage: convertVoltage }[tuple(mag.dimension())](mag)


def parse_vars(source,defs,first_var_addr,current_file):
    code = []
    variabledict = dict()
    for line in source:
        if (line[0:3] != 'var'):
                continue

        # is it a valid variable declaration?
        #m = re.match('var\s+(\w+)[ =]+(\w+)[^#\n\r]*', line)        #csn
        #m = re.match('var\s+(\w+)\s+([^#\n\r]*)', line) #
        m = re.match('var\s+(\w+)\s+(\w*)\s+([^#\n\r]*)', line) #
        if m:
            label = m.group(1)
            data = m.group(2).strip()
            print m.groups()

            try:
                data = str(eval(data,globals(),defs))
            except Exception, e:
                print "Evaluation error in file '%s' on line: '%s'" %(current_file, data)

            if (defs.has_key(label)):
                print "Error in file '%s': attempted to reassign '%s' to '%s' (from prev. value of '%s') in a var statement." %(current_file,label,data,defs[label])
                sys.exit(1)#exit the program after error CWC 08172012
            else:
                defs[label] = float(data) #add the variable to the dictionary of definitions CWC 08172012


            # determine units
            if ((label[:2] == "F_" or label[:2] == "f_") and label[-3:] != "INC"):
                data = float(data.strip())
            elif (label[:3] == "PH_" or label[:3] == "ph_" or label[:3] == "Ph"):
                data = int(round(float(data.strip())/360*(2**14)))
            elif (label[:3] == "NS_" or label[:3] == "ns_"):
                data = int(round(float(data.strip())*1e-9/TIMESTEP))
            elif (label[:3] == "US_" or label[:3] == "us_"):
                data = int(round(float(data.strip())*1e-6/TIMESTEP))
            elif (label[:3] == "MS_" or label[:3] == "ms_"):
                data = int(round(float(data.strip())*1e-3/TIMESTEP))
            elif (label[:4] == "INT_" or label[:4] == "int_" or label[:4] == "Int"):
                data = int(round(float(data.strip())))
            elif (label[:2] == "A_" or label[:2] == "a_"):
                data = int(round(float(data.strip())))
            elif (label[:2] == "V_" or label[:2] == "v_"): #added variables for DAC Vout CWC 08162012
                data = int(float(data.strip())/2.5*2**13)
            elif (label[-3:] == "INC" and (label[:2] == "F_" or label[:2] == "f_")):
                data = int(float(data.strip())/250*0x80000000)
            else:
                data = int(round(float(data.strip())))
                #print "No unit specified for variable",label,", assuming \"int\""
                
            address = len(code)+first_var_addr
            code.append((address, 'NOP', data, label, current_file))
            var = Variable()
            var.name = label
            var.address = address
            var.type = 0
            var.origin = current_file
            variabledict.update({ label: var})
        else:
            print "Error processing line '%s' in file '%s': Buffer overflow" %(line, current_file)
            #sys.exit(1) #exit the program after error CWC 08172012
            raise ppexception("Unidentified input")

    return (code, variabledict)



# code is (address, operation, data, label or variablename, currentfile)
def bc_gen(code, adIndexList, adBoards):
    if debug:
        print "\nCode ---> ByteCode:"
    bytecode = []
    translatedVars = {}
    index = 0
    for line in code:
        bytedata = 0
        byteop = OPS[line[1]]
        try:
            #attempt to locate commands with constant data
            if (line[2] == ''):
                #found empty data
                bytedata = 0
            else:
                #found data
                bytedata = int(float(line[2])) #if this line fails, found a variable name, so go to exception
                if (line[3] in translatedVars.keys()):
                    #print 'translating ' + str(line[3]) + ' from ' + str(line[2]) + ' to proper frequency:'
                    bytedata = int(float(line[2])/translatedVars[line[3]] * 0x80000000)
                    #print hex(bytedata)
                if (bytedata < 0):
                    bytedata = (1<<32) + bytedata
        except:
            #incurred when line[2] is a phrase CWC 08172012
            #inserting variable data - so run through the code again to locate
            #variable location
            for addr, op, data, label, scope in code:
                if ((line[1][:3] == 'DDS') and (label == line[2][1]) and (scope == line[4] or scope == 'globalparam')):
                    #found a DDS command and the associated variable to use 'label'
                    #print 'found dds cmd'
                    board = adIndexList[int(line[2][0])][0]
                    bytedata = (int(board) << 16) + addr

                    #need to translate all variables used with adBoard frequency commands
                    if (str(line[1]) == 'DDSFRQ'):
                        translatedVars[line[2][1]] = adBoards[board].halfClockLimit
                        #print 'translatedVars[%s]=%i'%(line[2][1],adBoards[board].halfClockLimit)
                    break
                if ((line[1][:3] == 'DAC') and ((str(label) == str(line[2][1])) and (str(scope) == str(line[4]) or str(scope) == 'globalparam'))):
                    bytedata = (int(line[2][0])<<16)+addr;
                    break
                if ((str(label) == str(line[2])) and (str(scope) == str(line[4]) or str(scope) == 'globalparam')):
                    #found another place to put in the associated variable 'label'
                    bytedata = addr;
                    break
            else:
                print "Error assembling bytecode from file '%s': Unknown variable: '%s'. \n"%(line[4],line[2]) # raise
                #sys.exit(1) #exit the program after error CWC 08172012
                raise ppexception("Unknown variable")
        bytecode.append((byteop, bytedata))
        if debug:
        #print hex(index), (hex(byteop), hex(bytedata))
            print line[0],  ": ", line[1:], "--->", (hex(byteop), hex(bytedata))
        #print index, (hex(byteop), hex(bytedata))
        index = index + 1

    return bytecode

def codeToBinary( code ):
    databuf = ''
    for op, arg in code:
        memword = '%c%c'%((arg&0xFF), (arg>>8)&0xFF) + '%c%c'%((arg>>16)&0xFF, op + (arg>>24))
        #print '%x, %x, %x, %x' %(ord(memword[0]), ord(memword[1]), ord(memword[2]), ord(memword[3]))
        databuf = databuf + memword
    return databuf



#parameters2 = {'THREE': 3, 'FIVE': 5, 'F_BlueHi': 1, 'A_BlueHi': 1, 'F_IRon': 2, 'us_MeasTime': 3, 'us_RedTime': 5, 'ms_ReadoutDly': 8, 'F_RedOn': 13, 'A_RedOn': 21, 'F_BlueOn': 34, 'A_BlueOn': 55, 'SCloops': 89, 'F_RedPL': 144, 'A_RedPL': 233, 'F_Sec': 377, 'A_SCool': 610, 'F_RedCenter': 42, 'us_RamseyDly': 42, 'Ph_Ramsey':3, 'us_PiTime':42}
#pp2bytecode(sys.argv[1], parameters2)

if __name__ == "__main__":
    debug = True
    code, variabledict = pp2bytecode(r"C:\Users\plmaunz\Documents\prog\Bluetest-Peter.pp", [], [])
    print code
    for name, var in variabledict.iteritems():
        print name, var.__dict__
    code = codeToBinary( code )
    with open('bytecode','wb') as of:
        of.write( code )
    
    print convertParameter( magnitude.mg(250,'MHz') )
