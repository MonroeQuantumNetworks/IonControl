# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import logging
import os.path

from PyQt4 import QtGui, QtCore
import PyQt4.uic

#from gui import ProjectSelection
from ProjectConfig.Project import getProject
from modules.firstNotNone import firstNotNone


VoltageFilesForm, VoltageFilesBase = PyQt4.uic.loadUiType(r'ui\VoltageFiles.ui')


class Scan:
    pass

class Files:
    def __init__(self):
        self.mappingFile = None
        self.definitionFile = None
        self.globalFile = None
        self.localFile = None
        self.mappingHistory = dict()
        self.definitionHistory = dict()
        self.globalHistory = dict()
        self.localHistory = dict()

class VoltageFiles(VoltageFilesForm, VoltageFilesBase ):
    loadMapping = QtCore.pyqtSignal(str)
    loadDefinition = QtCore.pyqtSignal(str,str)
    loadGlobalAdjust = QtCore.pyqtSignal(str)
    loadLocalAdjust = QtCore.pyqtSignal(str)
    
    def __init__(self,config,parent=None):
        VoltageFilesForm.__init__(self)
        VoltageFilesBase.__init__(self,parent)
        self.config = config
        self.configname = 'VoltageFiles.Files'
        self.files = self.config.get(self.configname,Files())
        self.lastDir = getProject().configDir

    def setupUi(self, parent):
        VoltageFilesForm.setupUi(self,parent)
        self.mappingCombo.addItems( self.files.mappingHistory.keys() )
        self.loadMappingButton.clicked.connect( self.onLoadMapping )
        self.loadDefinitionButton.clicked.connect( self.onLoadDefinition )
        self.loadGlobalButton.clicked.connect( self.onLoadGlobal )
        if self.files.mappingFile is not None:
            _, filename = os.path.split(self.files.mappingFile)
            self.mappingCombo.setCurrentIndex( self.mappingCombo.findText(filename))
        self.definitionCombo.addItems( self.files.definitionHistory.keys() )
        if self.files.definitionFile is not None:
            _, filename = os.path.split(self.files.definitionFile)
            self.definitionCombo.setCurrentIndex( self.definitionCombo.findText(filename))
        self.globalCombo.addItems( self.files.globalHistory.keys() )
        if self.files.globalFile is not None:
            _, filename = os.path.split(self.files.globalFile)
            self.globalCombo.setCurrentIndex( self.globalCombo.findText(filename))
        self.mappingCombo.currentIndexChanged['QString'].connect( self.onMappingChanged )
        self.definitionCombo.currentIndexChanged['QString'].connect( self.onDefinitionChanged )
        self.globalCombo.currentIndexChanged['QString'].connect( self.onGlobalChanged )
        
    def reloadAll(self):
        if self.files.mappingFile:
            self.loadMapping.emit(self.files.mappingFile)
        if self.files.definitionFile:
            self.loadDefinition.emit(self.files.definitionFile, self.shuttlingDefinitionPath() )
        if self.files.globalFile:
            self.loadGlobalAdjust.emit(self.files.globalFile)
        if self.files.localFile:
            self.loadLocalAdjust.emit(self.files.localFile)
            
        
    def onMappingChanged(self,value):
        logger = logging.getLogger(__name__)
        self.files.mappingFile = self.files.mappingHistory[str(value)]
        self.loadMapping.emit(self.files.mappingFile)
        logger.info( "onMappingChanged {0}".format(self.files.mappingFile) )
        
    def onDefinitionChanged(self,value):
        logger = logging.getLogger(__name__)
        self.files.definitionFile = self.files.definitionHistory[str(value)]
        self.loadDefinition.emit(self.files.definitionFile, self.shuttlingDefinitionPath())
        logger.info( "onDefinitionChanged {0}".format(self.files.definitionFile) )
        
    def onGlobalChanged(self,value):
        if value is not None:
            logger = logging.getLogger(__name__)
            value = str(value)
            if  value in self.files.globalHistory:
                self.files.globalFile = self.files.globalHistory[value]
            self.loadGlobalAdjust.emit(self.files.globalFile)
            logger.info( "onGlobalChanged {0}".format(self.files.globalFile) )
        
    def onLocalChanged(self,value):
        pass

    def onLoadMapping(self):
        logger = logging.getLogger(__name__)
        logger.debug( "onLoadMapping" )
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open mapping file:", self.lastDir ))
        if path!="":
            filedir, filename = os.path.split(path)
            self.lastDir = filedir
            if filename not in self.files.mappingHistory:
                self.files.mappingHistory[filename] = path
                self.mappingCombo.addItem(filename)
            else:
                self.files.mappingHistory[filename] = path
            self.mappingCombo.setCurrentIndex( self.mappingCombo.findText(filename))
            self.files.mappingFile = path
            self.loadMapping.emit(path)
            
    def onLoadDefinition(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open definition file:", self.lastDir))
        if path!="":
            filedir, filename = os.path.split(path)
            self.lastDir = filedir
            if filename not in self.files.definitionHistory:
                self.files.definitionHistory[filename] = path
                self.definitionCombo.addItem(filename)
            else:
                self.files.definitionHistory[filename] = path
            self.definitionCombo.setCurrentIndex( self.definitionCombo.findText(filename))
            self.files.definitionFile = path
            self.loadDefinition.emit(path, self.shuttlingDefinitionPath(path) )
            
    def shuttlingDefinitionPath(self, definitionpath=None ):
        path = firstNotNone( definitionpath, self.files.definitionFile )
        filedir, filename = os.path.split(path)
        basename, _ = os.path.splitext(filename)
        return os.path.join( filedir, basename+"_shuttling.xml" )


    def onLoadGlobal(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open global adjust file:", self.lastDir))
        if path!="":
            filedir, filename = os.path.split(path)
            self.lastDir = filedir
            if filename not in self.files.globalHistory:
                self.globalCombo.addItem(filename)
            self.files.globalHistory[filename] = path
            self.globalCombo.setCurrentIndex( self.globalCombo.findText(filename))
            self.files.globalFile = path
            self.loadGlobalAdjust.emit(path)

    def onLoadLocal(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open local adjust file:", self.lastDir))
        if path!="":
            filedir, filename = os.path.split(path)
            self.lastDir = filedir
            if filename not in self.files.localHistory:
                self.localCombo.addItem(filename)
            self.files.localHistory[filename] = path
            self.localCombo.setCurrentIndex( self.localCombo.find(filename))
            self.files.localFile = path
            self.loadLocalAdjust.emit(path)
    
    def saveConfig(self):
        self.config[self.configname] = self.files
        