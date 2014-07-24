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
from ConexInstrument import ConexInstrument, instrumentCycle
#=========================================================================

#*************************************************
# Procedure to start example
#*************************************************
def Start():	
	# Initialization
	#instrumentKey="CONEX-CC (A6U1PBW3)"
	instrumentKey="COM9"
	instr = ConexInstrument()
	instr.open(instrumentKey)
	print instr.controllerId
	
	NB_LOOPS = 2

	# Get controller revision information
	print "Version:" , instr.controllerVersion()
		
	# Get controller status 
	print  "Status:", instr.status
		
	# Get current position
	print instr.position
	
	# Motion cycle
	instrumentCycle(instr, 1, NB_LOOPS, 100) 
	# Close communication
	instr.close()
	print 'End of script'
	
#*************************************************
#*************************************************
#***************  Main program  ******************
#*************************************************
#*************************************************
Start()



