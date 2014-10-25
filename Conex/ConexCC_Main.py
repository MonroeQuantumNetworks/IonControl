#=========================================================================
# Newport Proprietary and Confidential    Newport Corporation 2012
#
# No part of this file in any format, with or without modification 
# shall be used, copied or distributed without the express written 
# consent of Newport Corporation.
# 
# Description: This is a sample Python Script to illustrate how to execute  
# Conex-CC commands
#==========================================================================
import sys
sys.path.append(r'C:\Program Files\Newport\MotionControl\CONEX-CC\Python')
sys.path.append(r'C:\Program Files (x86)\Newport\MotionControl\CONEX-CC\Python')
from ConexCC_Functions import CONEXCC_Open, CONEXCC_GetControllerVersion, CONEXCC_GetControllerStatus, CONEXCC_GetPosition
from ConexCC_Functions import CONEXCC_Cycle, CONEXCC_Close
#=========================================================================

#*************************************************
# Procedure to start example
#*************************************************
def Start():	
	# Initialization
	#instrumentKey="CONEX-CC (A6U1PBW3)"
	instrumentKey="COM8"
	displayFlag = 1
	address = 1
	NB_LOOPS = 3

	# Create CONEX-CC interface and open communication.
	CC = CONEXCC_Open(instrumentKey)

	# Get controller revision information
	result, version = CONEXCC_GetControllerVersion(CC, address, displayFlag) 
	print result, version
		
	# Get controller status 
	result, errorCode, statusCode = CONEXCC_GetControllerStatus(CC, address, displayFlag)
	print  result, errorCode, statusCode
		
	# Get current position
	returnValue, position = CONEXCC_GetPosition(CC, address, displayFlag) 
	print returnValue, position
	
	# Motion cycle
	CONEXCC_Cycle (CC, address, NB_LOOPS)

	# Close communication
	CONEXCC_Close(CC)
	
	print 'End of script'
	
#*************************************************
#*************************************************
#***************  Main program  ******************
#*************************************************
#*************************************************
Start()



