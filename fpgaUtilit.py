#C. Spencer Nichols
#3-31-2012
#This code initializes the connection with the FPGA

import ok, sys


ModelStrings = {
		0: 'Unknown',
		1: 'XEM3001v1',
		2: 'XEM3001v2',
		3: 'XEM3010',
		4: 'XEM3005',
		5: 'XEM3001CL',
		6: 'XEM3020',
		7: 'XEM3050',
		8: 'XEM9002',
		9: 'XEM3001RB',
		10: 'XEM5010',
		11: 'XEM6110LX45',
		15: 'XEM6110LX150',
		12: 'XEM6001',
		13: 'XEM6010LX45',
		14: 'XEM6010LX150',
		16: 'XEM6006LX9',
		17: 'XEM6006LX16',
		18: 'XEM6006LX25',
		19: 'XEM5010LX110',
		20: 'ZEM4310',
		21: 'XEM6310LX45',
		22: 'XEM6310LX150',
		23: 'XEM6110v2LX45',
		24: 'XEM6110v2LX150'
}

ErrorMessages = {
	 0: 'NoError',
	-1: 'Failed',
	-2: 'Timeout',
	-3: 'DoneNotHigh',
	-4: 'TransferError',
	-5: 'CommunicationError',
	-6: 'InvalidBitstream',
	-7: 'FileError',
	-8: 'DeviceNotOpen',
	-9: 'InvalidEndpoint',
	-10: 'InvalidBlockSize',
	-11: 'I2CRestrictedAddress',
	-12: 'I2CBitError',
	-13: 'I2CNack',
	-14: 'I2CUnknownStatus',
	-15: 'UnsupportedFeature',
	-16: 'FIFOUnderflow',
	-17: 'FIFOOverflow',
	-18: 'DataAlignmentError',
	-19: 'InvalidResetProfile',
	-20: 'InvalidParameter'
}


class DeviceDescription:
    pass

class FPGAException(Exception):
    pass
        
def check(number, command):
    if number not in [0,None]:
        print 
        raise FPGAException("OpalKelly exception '{0}' in command {1}".format(ErrorMessages.get(number,number),command))


class FPGAUtilit:
    def __init__(self):
        self.modules = dict()
        self.openModule = None
        self.xem = None

    def listBoards(self):
        xem = ok.FrontPanel()
        self.moduleCount = xem.GetDeviceCount()
        self.modules = dict()
        for i in range(self.moduleCount):
            serial = xem.GetDeviceListSerial(i)
            tmp = ok.FrontPanel()
            check( tmp.OpenBySerial( serial ), "OpenBySerial" )
            desc = self.getDeviceDescription(tmp)
            tmp = None
            self.modules[desc.identifier] = desc
        del(xem)
        if self.openModule is not None:
            self.modules[self.openModule.identifier] = self.openModule
        return self.modules
        
    def getDeviceDescription(self,xem):
        """Get informaion from an open device
        """
        desc = DeviceDescription()
        desc.serial = xem.GetSerialNumber()
        desc.identifier = xem.GetDeviceID()
        desc.major = xem.GetDeviceMajorVersion()
        desc.minor = xem.GetDeviceMinorVersion()
        desc.model = xem.GetBoardModel()
        desc.modelName = ModelStrings.get(desc.model,'Unknown')
        return desc
        
    def renameBoard(self,serial,newname):
        tmp = ok.FrontPanel()
        tmp.OpenBySerial(serial)
        oldname = tmp.GetDeviceID()
        tmp.SetDeviceId( newname )
        tmp.OpenBySerial(serial)
        newname = tmp.GetDeviceID()
        if newname!=oldname:
            self.modules[newname] = self.modules.pop(oldname)
        
    def uploadBitfile(self,bitfile):
        if self.xem is not None and self.xem.IsOpen():
            check( self.xem.ConfigureFPGA(bitfile), "Configure bitfile {0}".format(bitfile))
        
    def openByName(self,name):
        self.xem = ok.FrontPanel()
        check( self.xem.OpenBySerial( self.modules[name].serial ), "OpenByName {0}".format(name) )
        return self.xem

    def openBySerial(self,serial):
        print "Open Serial",serial
        if self.xem is None or not self.xem.IsOpen() or self.xem.GetSerialNumber()!=serial:
            self.xem = ok.FrontPanel()
            check( self.xem.OpenBySerial( serial ), "OpenBySerial {0}".format(serial) )
            self.openModule = self.getDeviceDescription(self.xem)
        return self.xem
    
if __name__ == "__main__":
    fpga = FPGAUtilit()
    boards = fpga.listBoards()
    print "Modules:", fpga.moduleCount

    for name, board in boards.iteritems():
        print board.__dict__
    
    
