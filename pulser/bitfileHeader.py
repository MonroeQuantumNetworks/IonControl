'''
Created on Feb 8, 2014

@author: pmaunz
'''

import struct
import hashlib

class BitfileInfo(object):
    def __init__(self, filename):
        self.filename = filename
        with open(filename,"rb") as f:
            # Field 1, length 9, some sort of header
            (fieldlength, ) = struct.unpack(">H", f.read(2))
            f.read(fieldlength)
            
            # Field 2, length 1, letter 'a'
            (fieldlength, ) = struct.unpack(">H",f.read(2))
            _ = f.read(fieldlength)
            
            # Field 3, filename, commandstring
            (fieldlength, ) = struct.unpack(">H",f.read(2))
            self.commandString = f.read(fieldlength)
            
            # Field 4, 'b', length, targetdevice
            (_, fieldlength) = struct.unpack(">cH",f.read(3))
            self.targetDevice = f.read(fieldlength)

            # Field 5, 'c', datestring            
            (_, fieldlength) = struct.unpack(">cH",f.read(3))
            self.date = f.read(fieldlength)
        
            # Field 6, 'd', timestring
            (_, fieldlength) = struct.unpack(">cH",f.read(3))
            self.time = f.read(fieldlength)
        
            # Field 7, 'e', magicstring
            (_, fieldlength) = struct.unpack(">cH",f.read(3))
            _ = f.read(fieldlength)
            
            m = hashlib.md5()
            m.update(f.read())
            self.md5hex = m.hexdigest()
            self.md5 = m.digest()
            
    def __str__(self):
        if not hasattr(self, 'md5'):
            return "Bitfile data not available"
        return "Device: {0} Creation Date: {1} {2} Digest: {3}".format(self.targetDevice, self.date, self.time, self.md5hex)
    
if __name__=="__main__":
    bitfileinfo = BitfileInfo(r"C:\Users\pmaunz\Documents\Programming\aaAQC_FPGA\FPGA_Ions\fpgafirmware.bit")
    print str(bitfileinfo)
