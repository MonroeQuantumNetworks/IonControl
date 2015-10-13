'''
Created on Feb 27, 2015

@author: wolverine
'''

import PyQt4.uic

from dedicatedCounters.StatusTableModel import StatusTableModel
from modules.GuiAppearance import restoreGuiState, saveGuiState

import os
uipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\TableViewWidget.ui')
Form, Base = PyQt4.uic.loadUiType(uipath)


class Settings:
    def __init__(self):
        self.average = False
        

DigitalStatusChannels = [ ("PI 0 underflow", 0, 1),
                          ("PI 0 overflow", 1, 1),
                          ("PI 1 underflow", 2, 1),
                          ("PI 1 overflow", 3, 1),
                          ("PI 2 underflow", 4, 1),
                          ("PI 2 overflow", 5, 1),
                          ("PI 3 underflow", 6, 1),
                          ("PI 3 overflow", 7, 1) ]        

class StatusDisplay(Form,Base ):
    def __init__(self,config,parent=None):
        Form.__init__(self)
        Base.__init__(self,parent)
        self.config = config
        self.digitalStatus = 0

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        self.model = StatusTableModel(DigitalStatusChannels)
        self.tableView.setModel( self.model )
        restoreGuiState( self, self.config.get("StatusDisplay") )
            
    def setData(self, data):
        if data.externalStatus is not None and self.digitalStatus !=data.externalStatus:
            self.digitalStatus = data.externalStatus
            self.model.setData( data.externalStatus ) 

    def saveConfig(self):
        self.config["StatusDisplay"] = saveGuiState(self)