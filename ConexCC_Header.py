#=========================================================================
# Newport Proprietary and Confidential    Newport Corporation 2012
#
# No part of this file in any format, with or without modification 
# shall be used, copied or distributed without the express written 
# consent of Newport Corporation.
# 
# Description: This is a Python Script to access CONEX-CC library
#==========================================================================
#Initialization Start
#The script within Initialization Start and Initialization End is needed for properly 
#initializing Command Interface DLL for Conex-CC instrument.
#The user should copy this code as is and specify correct paths here.
import sys
# Command Interface DLL can be found here.
#print "Adding location of Newport.CONEXCC.CommandInterface.dll to sys.path"
sys.path.append(r'C:\Program Files\Newport\MotionControl\CONEX-CC\Bin')
sys.path.append(r'C:\Program Files (x86)\Newport\MotionControl\CONEX-CC\Bin')
# The CLR module provide functions for interacting with the underlying 
# .NET runtime
import clr   #@UnresolvedImport
# Add reference to assembly and import names from namespace
assembly = "Newport.CONEXCC.CommandInterface"
available = clr.FindAssembly(assembly) #Check whether assembly is available
if available:
    clr.AddReference(assembly) #Only try and add it as a reference if it is available
else:
    raise ImportError('Unable to load {0} DLL'.format(assembly))
from CommandInterfaceConexCC import *

import System  #@UnresolvedImport @UnusedImport
#==========================================================================
