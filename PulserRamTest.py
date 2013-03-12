# -*- coding: utf-8 -*-
"""
Created on Sun Mar 10 11:04:52 2013

@author: pmaunz
"""

from PulserHardware import PulserHardware
import time

if __name__ == "__main__":
    import fpgaUtilit
    
    printdata = True
    
    fpga = fpgaUtilit.FPGAUtilit()
    fpga.xem = fpga.openBySerial('12320003V5')
    print fpga.xem.ConfigureFPGA(r'FPGA_Ions\fpgafirmware_ram.bit')
    fpga.xem.ActivateTriggerIn( 0x41, 4 )
    fpga.xem.ActivateTriggerIn( 0x41, 5 )
        
    data = bytearray("0123456789abcdef"*80)
    blankdata =  bytearray([0]* max(2*len(data),256) )   
    print fpga.xem.WriteToPipeIn( 0x82, blankdata )
    fpga.xem.ActivateTriggerIn( 0x41, 4 )    
    fpga.xem.ActivateTriggerIn( 0x41, 5 )    
    print fpga.xem.WriteToPipeIn( 0x82, data )
    fpga.xem.ActivateTriggerIn( 0x41, 5 )
    fpga.xem.ActivateTriggerIn( 0x41, 4 )    
    backdata = bytearray( ['x']*len(data) )
    print fpga.xem.ReadFromPipeOut( 0xa3, backdata )
    print "'{0}'".format(backdata)
    