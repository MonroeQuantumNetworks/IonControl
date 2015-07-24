'''
Created on Jul 24, 2015

@author: jmizrahi
'''

from PyQt4 import QtGui
import PyQt4.uic

from externalParameter.persistence import DBPersist #@UnusedImport
from modules.magnitude import is_magnitude, mg #@UnusedImport
from functools import partial #@UnusedImport
import time #@UnusedImport
from modules.Expression import Expression #@UnusedImport
from modules.GuiAppearance import restoreGuiState, saveGuiState 
import logging #@UnusedImport
from modules.Utility import unique #@UnusedImport

ScriptingForm, ScriptingBase = PyQt4.uic.loadUiType('ui/Scripting.ui')

class ScriptingUi(ScriptingForm, ScriptingBase):
    persistSpace = 'Scripting'
    def __init__(self, config, pulser, globalDict, parent=None):
        ScriptingForm.__init__(self)
        ScriptingBase.__init__(self,parent)
        self.config = config
        
    def setupUi(self,parent):
        ScriptingForm.setupUi(self,parent)
        logger = logging.getLogger(__name__)
        restoreGuiState( self, self.config.get('ScriptingUi.guiState') )
        
    def saveConfig(self):
        self.config['ScriptingUi.guiState'] = saveGuiState( self )