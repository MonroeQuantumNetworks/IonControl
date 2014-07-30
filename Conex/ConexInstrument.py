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
import time
sys.path.append(r'C:\Program Files\Newport\MotionControl\CONEX-CC\Python')
sys.path.append(r'C:\Program Files (x86)\Newport\MotionControl\CONEX-CC\Python')
from ConexCC_Header import ConexCC #@UnresolvedImport
#=========================================================================

class ConexInstrumentException(Exception):
	pass


def processResponse( name, response ):
	if len(response)<2:
		return response
	if response[0]!=0:
		raise ConexInstrumentException("{0}: {1}".format(name,response[-1]))
	return response[1:-1]


class ConexInstrument(object):
	def __init__(self, instrumentKey=None):
		self.instrumentKey = instrumentKey
		self.address = 1
		self.controllerId = None
		self._position = None
	
	def open(self, instrumentKey=None):
		self.instrumentKey = instrumentKey if instrumentKey is not None else self.instrumentKey
		self.CC = ConexCC()
		ret = self.CC.OpenInstrument(self.instrumentKey)
		if ret!=0:
			raise ConexInstrumentException("cannot open '{0}' returnvalue {1}".format(self.instrumentKey,ret))
		(self.controllerId,) = processResponse( 'ID_Get' , self.CC.ID_Get(self.address, None, None) )
		
	def close(self):
		self.CC.CloseInstrument()
		
	def controllerVersion(self):
		(version,) =  processResponse( 'controllerVersion' , self.CC.VE(self.address,None,None) )
		return version
	
	@property
	def position(self):
		number = 0.0
		(position, ) = processResponse( 'read position' , self.CC.TP(self.address, number, None) ) 
		self._position = float(position)
		return self._position

	@position.setter
	def position(self, position=0.0):
		if self.notHomed():
			raise ConexInstrumentException("Instrument {0} is not ready to move. Try a home search.".format(self.instrumentKey))
		processResponse( 'write position' , self.CC.PA_Set(self.address, position, None) ) 
		self._position = position
		return self._position
	
	@property
	def status(self):
		status = processResponse( 'status', self.CC.TS(self.address, None, None, None) )
		return status

	def homeSearch(self):
		processResponse( 'homeSearch', self.CC.OR(self.address, None) ) 
		
	def homeSearchRunning(self):
		(_, ControllerState) = self.status
		return ControllerState=='1E'
	
	def motionRunning(self):
		(_, ControllerState) = self.status
		return ControllerState=='28'
	
	def readyToMove(self):
		(_, ControllerState) = self.status
		return ControllerState in ['32','33','34']		
	
	def notHomed(self):
		(_, ControllerState) = self.status
		return ControllerState == '0A'		
		
		
	def waitEndOfHomeSearch(self):
		while self.homeSearchRunning():
			time.sleep(0.1)
			
	def waitEndOfMotion(self):
		while self.motionRunning():
			time.sleep(0.1)
			
			
#*************************************************
# Procedure to perform a motion cycle
#*************************************************	
def instrumentCycle(instr, address, nbLoops, displacement):

	instr.homeSearch()
	instr.waitEndOfHomeSearch()

	if instr.readyToMove():
		# Get current position
		responsePosition = instr.position
		print 'Current Position =>', responsePosition

		# Define absolute positions used in the motion cycle
		position1 = responsePosition
		position2 = (float)(position1) + (float)(displacement)
		
		# Motion cycle
		for i in range(nbLoops): 
			# First displacement
			print 'Moving from position ', responsePosition	,' to position ' , position2
			instr.position = position2
			
			# Wait the end of motion
			instr.waitEndOfMotion()
			
			# Get current position
			responsePosition = instr.position
			print 'Current Position =>', responsePosition
							
			# Second displacement
			print 'Moving from position ', responsePosition ,' to position ' , position1
			instr.position = position1
			
			# Wait the end of motion
			instr.waitEndOfMotion()
			
			# Get current position
			responsePosition = instr.position
			print 'Current Position =>', responsePosition
			
			# Increment and update cycle counter
			print i + 1 ,' Cycle(s) completed'				
	else:
		print 'Controller state is not in Ready state'
	print 'Cycles Complete'
	
	
	