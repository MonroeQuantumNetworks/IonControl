#C. Spencer Nichols
#3-31-2012
#This code initializes the connection with the FPGA

import ok, sys

def fpgaInit(name, pllFreqs, bitFile):
    xem = ok.FrontPanel()
    module_count = xem.GetDeviceCount()

    print "Found %d modules"%(module_count)
    if (module_count == 0): 
        print "No XEMs found!"
        sys.exit(1)
    id = ''

    for i in range(module_count):
        serial = xem.GetDeviceListSerial(i)
        tmp = ok.FrontPanel()
        tmp.OpenBySerial(serial)
        id = tmp.GetDeviceID()
        print id
        tmp = None
        if (id == name):
            break
    if (id  != name):
        print "Didn't find " + name + " in module list!"
        sys.exit(1)

    xem.OpenBySerial(serial)
    print "Found device called %s"%(xem.GetDeviceID())

    print "Loading PLL config"
    pll = ok.PLL22393()
    xem.GetEepromPLL22393Configuration(pll)
    pll.SetPLLParameters(0, 240, 48, True)
    pll.SetPLLParameters(1, 240, 48, False)
    pll.SetPLLParameters(2, 240, 48, False)  #change 200 to 240 CWC 05212012
    for i in range(5):
        pll.SetOutputSource(i, pll.ClkSrc_PLL0_0)
        pll.SetOutputDivider(i, 2)
        pll.SetOutputEnable(i, (i == 0))

    print "Ref is at %gMHz, PLL is at %gMHz"%(pll.GetReference(), pll.GetPLLFrequency(0))
    for i in range(5):
        if (pll.IsOutputEnabled(i)):
            print "Clock %d at %gMHz"%(i, pll.GetOutputFrequency(i))

    print "Programming PLL"
    # xem.SetEepromPLL22393Configuration(pll)
    xem.SetPLL22393Configuration(pll)

    print "Programming FPGA"
    xem.ConfigureFPGA('./FPGA/' + bitFile)
    return xem
    
    
    
    
