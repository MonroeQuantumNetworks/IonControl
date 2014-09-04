# -*- coding: utf-8 -*-
"""
Encapsulation of the Pulse Programmer Hardware 
"""


from PulserHardwareClient import PulserHardware
from PMTReaderServer import PMTReaderServer

class PMTReader(PulserHardware):
    serverClass = PMTReaderServer
    def __init__(self):
        super(PMTReader,self).__init__()
        
