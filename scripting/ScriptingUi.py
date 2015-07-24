'''
Created on Jul 24, 2015

@author: jmizrahi
'''

from PyQt4 import QtGui
import PyQt4.uic

import os.path
from externalParameter.persistence import DBPersist #@UnusedImport
from modules.magnitude import is_magnitude, mg #@UnusedImport
from functools import partial
from gui import ProjectSelection
import time #@UnusedImport
from modules.Expression import Expression #@UnusedImport
from modules.GuiAppearance import restoreGuiState, saveGuiState 
import logging #@UnusedImport
from modules.Utility import unique #@UnusedImport

ScriptingForm, ScriptingBase = PyQt4.uic.loadUiType('ui/Scripting.ui')

class ScriptingUi(ScriptingForm, ScriptingBase):
    def __init__(self, config, pulser, globalDict, parent=None):
        ScriptingForm.__init__(self)
        ScriptingBase.__init__(self,parent)
        self.config = config
        
    def setupUi(self,parent):
        ScriptingForm.setupUi(self,parent)
        logger = logging.getLogger(__name__)
        self.configname = 'ScriptingUi'
        self.recentFiles = self.config.get(self.configname+'.recentFiles', [])
        self.currentFile = self.config.get(self.configname+'.currentFile', None)
        self.recentFilesComboBox.addItems( [filename for filename in self.recentFiles] )
        
        self.actionStart.triggered.connect( self.onStart )
        self.actionStop.triggered.connect( self.onStop )
        self.actionSave.triggered.connect( self.onSave )
        self.actionOpen.triggered.connect( self.onOpen )
        self.removeCurrent.clicked.connect( self.onRemoveCurrent )
        self.recentFilesComboBox.currentIndexChanged.connect( partial(self.loadFile, self.recentFilesComboBox.currentText()) )

    def onStart(self):
        pass
    
    def onStop(self):
        pass
    
    def onSave(self):
        pass
    
    def onOpen(self):
        filename = str(QtGui.QFileDialog.getOpenFileName(self, 'Open Python Script',ProjectSelection.configDir(),"Python scripts (*.py *.pyw)"))
        if (filename!="") and filename:
            self.currentFile = filename
            self.recentFiles.append[filename]
            self.recentFilesComboBox.addItem(filename)
            self.loadFile(filename)

    def onRemoveCurrent(self):
        pass
    
    def loadFile(self, filename):
        pass
    
    def show(self):
        if 'ScriptingUi.pos' in self.config:
            self.move(self.config['ScriptingUi.pos'])
        if 'ScriptingUi.size' in self.config:
            self.resize(self.config['ScriptingUi.size'])
        QtGui.QDialog.show(self)
        self.isShown = True
    
    def saveConfig(self):
        self.config[self.configname+'.pos'] = self.pos()
        self.config[self.configname+'ScriptingUi.size'] = self.size()
        self.config[self.configname+'ScriptingUi.guiState'] = saveGuiState( self )
        self.config[self.configname+'.recentFiles'] = self.recentFiles
        self.config[self.configname+'.currentFile'] = self.currentFile

        
    def onClose(self):
        self.config[self.configname+'ScriptingUi.pos'] = self.pos()
        self.config[self.configname+'ScriptingUi.size'] = self.size()
        self.config[self.configname+'ScriptingUi.guiState'] = saveGuiState( self )
        self.config[self.configname+'.recentFiles'] = self.recentFiles
        self.config[self.configname+'.currentFile'] = self.currentFile
        self.hide()
