#=========================================================================
# Newport Proprietary and Confidential    Newport Corporation 2012
#
# No part of this file in any format, with or without modification 
# shall be used, copied or distributed without the express written 
# consent of Newport Corporation.
# 
# Description: This is a Python Script to access CONEX-LDS library
#==========================================================================
#Initialization Start
#The script within Initialization Start and Initialization End is needed for properly 
#initializing IOPortClientLib and Command Interface for Conex-CC instrument.
#The user should copy this code as is and specify correct paths here.
import sys
sys.path.append(r'C:\Program Files\Newport\MotionControl\CONEX-CC\Python')
sys.path.append(r'C:\Program Files (x86)\Newport\MotionControl\CONEX-CC\Python')
from ConexCC_Header import *
#=========================================================================

def controllerId(CC, address):
	print "Id:" , CC.ID_Get(address, None, None)
	
	
def getDevices(CC):
	print "Devices:", CC.GetDevices()

#*************************************************
# Procedure to initialize and connect instrument.
#*************************************************
def CONEXCC_Open (instrumentKey):	
	# CONEX-CC interface
	CC = ConexCC()   #@UndefinedVariable
	print 'Instrument Key=>', instrumentKey
	ret = CC.OpenInstrument(instrumentKey)
	print 'OpenInstrument => ', ret
	return CC
		
#*************************************************
# Procedure to disonnect instrument.
#*************************************************
def CONEXCC_Close (CC):	
	CC.CloseInstrument()
	
#*************************************************
# Procedure to get the controller version (VE)
#*************************************************
def CONEXCC_GetControllerVersion (CC, address, flag):
	result, version, errString = CC.VE(address,None,None)
	if flag == 1:
		if result == 0 :
			print 'CONEX-CC firmware version => ', version
		else:
			print 'VE Error => ',errString
	return result, version
	
#*************************************************
# Procedure to get the current position (TP Command)
#*************************************************
def CONEXCC_GetPosition (CC, address, flag):
	# Get current position Using TP Command
	number = 12.23
	result, position, errString = CC.TP(address, number, None) 
	if flag == 1:
		if result == 0 :
			print 'Position => ', position
	else:
			print 'TP Error => ',errString
	return result, position
	
#*************************************************
# Procedure to get the controller status (TS Command)
#*************************************************
def CONEXCC_GetControllerStatus (CC, address, flag):
	result, errorCode, statusCode, errString = CC.TS(address, None, None, None)
	if flag == 1:
		if result == 0 :
			print 'Error Code => ', errorCode
			print 'Status Code => ', statusCode
		else:
			print 'TS Error => ',errString
	return result, errorCode, statusCode

#*************************************************
# Procedure to perform a home search
#*************************************************
def CONEXCC_HomeSearch (CC, address, flag):
	# Get current position Using TP Command
	result, errString = CC.OR(address, None) 
	if flag == 1:
		if result != 0 :
			print 'OR Error => ',errString
	return result
	
#*************************************************
# Procedure to wait the end of current motion
#*************************************************
def CONEXCC_WaitEndOfHomeSearch (CC, address):
	print "WaitEndOfHomeSearch ..."
	
	# Get controller status
	result, errorCode, ControllerState, errString = CC.TS(address, None, None, None) 
	if result != 0 :
		print 'TS Error=>',errString
	else:		
		while ControllerState == "1E":
			# Get controller status
			result, errorCode, ControllerState, errString = CC.TS(address) 
			if result != 0 :
				print 'TS Error=>',errString
				
#*************************************************
# Procedure to wait the end of current motion
#*************************************************
def WaitEndOfMotion (CC, address):
	print "WaitEndOfMotion ..."

	# Get controller status
	result, errorCode, ControllerState, errString = CC.TS(address, None, None, None ) 
	if result != 0 :
		print 'TS Error=>',errString
		
	while ControllerState == "28":
		# Get controller status
		result, errorCode, ControllerState, errString = CC.TS(address, None, None, None ) 
		if result != 0 :
			print 'TS Error=>',errString
			
#*************************************************
# Procedure to perform a motion cycle
#*************************************************	
def CONEXCC_Cycle (CC, address, nbLoops):

	displacement = 1.00
	
	CONEXCC_HomeSearch(CC, address, 1)
	CONEXCC_WaitEndOfHomeSearch(CC, address)

	# Get controller state Using TS Command
	result, errorCode, controllerState, errString = CC.TS(address, None, None, None) 
	if result == 0 :
		print 'Current Controller State=>', controllerState
		
		# Check if the controller is ready to move
		if (controllerState == "32") | (controllerState == "33") | (controllerState == "34") :
		
			# Get current position
			number = 0.0
			resultPosition, responsePosition, errStringPosition = CC.TP(address, number, None)		
			if resultPosition == 0 :
				print 'Current Position =>', responsePosition

				# Define absolute positions used in the motion cycle
				position1 = responsePosition
				position2 = (float)(position1) + (float)(displacement)
				
				# Motion cycle
				for i in range(nbLoops): 
					 
					# First displacement
					print 'Moving from position ', responsePosition	,' to position ' , position2
					resultPosition, errStringMove = CC.PA_Set(address, position2, None)	
					
					# Wait the end of motion
					WaitEndOfMotion(CC, address)
					
					# Get current position
					resultPosition, responsePosition, errStringPosition = CC.TP(address, number, None)
					print 'Current Position =>', responsePosition
									
					# Second displacement
					print 'Moving from position ', responsePosition ,' to position ' , position1
					resultPosition, errStringMove = CC.PA_Set(address, position1, None)
					
					# Wait the end of motion
					WaitEndOfMotion(CC, address)
					
					# Get current position
					resultPosition, responsePosition, errStringPosition = CC.TP(address, number, None)
					print 'Current Position =>', responsePosition
					
					# Increment and update cycle counter
					print i + 1 ,' Cycle(s) completed'				
			else:
				print 'Error while getting position=>', errStringPosition
		else:
			print 'Controller state is not in Ready state'
	else:
		print 'Error while getting controller state=>',errString
	print 'Cycles Complete'
	
	
	