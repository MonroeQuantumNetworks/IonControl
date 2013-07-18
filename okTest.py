# -*- coding: utf-8 -*-
"""
Encapsulation of the Pulse Programmer Hardware 
"""
import ok
import time

if __name__ == "__main__":
    xem = ok.FrontPanel()
    print xem.OpenBySerial('114400029T')
    print xem.ConfigureFPGA(r'C:\Users\Public\Documents\WmFiberSwitchFirmware\tutorial.bit')

    for i in range(100):
        for j in range(16):
            xem.SetWireInValue(8,j << 8 | 0x02)
            xem.UpdateWireIns()
            xem.UpdateWireOuts()
            switch = xem.GetWireOutValue(0x30)
            state = xem.GetWireOutValue(0x31)
            print switch, hex(state)
            time.sleep(0.1)
            
            
     