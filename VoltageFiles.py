# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtGui, QtCore
import os.path
       
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
    loadDefinition = QtCore.pyqtSignal(str)
    loadGlobalAdjust = QtCore.pyqtSignal(str)
    loadLocalAdjust = QtCore.pyqtSignal(str)
    
    def __init__(self,config,parent=0):
        VoltageFilesForm.__init__(self,parent)
        VoltageFilesBase.__init__(self)
        self.config = config
        self.configname = 'VoltageFiles.Files'
        self.files = self.config.get(self.configname,Files())

    def setupUi(self, parent):
        VoltageFilesForm.setupUi(self,parent)
        self.mappingCombo.addItems( self.files.mappingHistory.keys() )
        if self.files.mappingFile is not None:
            self.mappingCombo.setCurrentIndex( self.mappingCombo.findText(self.files.mappingFile))
        self.definitionCombo.addItems( self.files.definitionHistory.keys() )
        if self.files.definitionFile is not None:
            self.definitionCombo.setCurrentIndex( self.definitionCombo.findText(self.files.definitionFile))
        self.globalCombo.addItems( self.files.globalHistory.keys() )
        if self.files.globalFile is not None:
            self.globalCombo.setCurrentIndex( self.globalCombo.findText(self.files.globalFile))
        self.localCombo.addItems( self.files.localHistory.keys() )
        if self.files.localFile is not None:
            self.localCombo.setCurrentIndex( self.localCombo.findText(self.files.localFile))
        self.loadMappingButton.clicked.connect( self.onLoadMapping )
        self.loadDefinitionButton.clicked.connect( self.onLoadDefinition )
        self.loadGlobalButton.clicked.connect( self.onLoadGlobal )
        self.loadLocalButton.clicked.connect( self.onLoadLocal )

    def onLoadMapping(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open mapping file:"))
        if path!="":
            filedir, filename = os.path.split(path)
            if filename not in self.files.mappingHistory:
                self.mappingCombo.addItem(filename)
            self.files.mappingHistory[filename] = path
            self.mappingCombo.setCurrentIndex( self.mappingCombo.findText(filename))
            self.files.mappingFile = path
            self.loadMapping.emit(path)
            
    def onLoadDefinition(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open definition file:"))
        if path!="":
            filedir, filename = os.path.split(path)
            if filename not in self.files.definitionHistory:
                self.definitionCombo.addItem(filename)
            self.files.definitionHistory[filename] = path
            self.definitionCombo.setCurrentIndex( self.definitionCombo.findText(filename))
            self.files.definitionFile = path
            self.loadDefinition.emit(path)

    def onLoadGlobal(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open global adjust file:"))
        if path!="":
            filedir, filename = os.path.split(path)
            if filename not in self.files.globalHistory:
                self.globalCombo.addItem(filename)
            self.files.globalHistory[filename] = path
            self.globalCombo.setCurrentIndex( self.globalCombo.findText(filename))
            self.files.globalFile = path
            self.loadGlobalAdjust.emit(path)

    def onLoadLocal(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open local adjust file:"))
        if path!="":
            filedir, filename = os.path.split(path)
            if filename not in self.files.localHistory:
                self.localCombo.addItem(filename)
            self.files.localHistory[filename] = path
            self.localCombo.setCurrentIndex( self.localCombo.find(filename))
            self.files.localFile = path
            self.loadLocalAdjust.emit(path)
    
    def onClose(self):
        self.config[self.configname] = self.files
        