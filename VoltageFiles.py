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
        self.lastDir = "."

    def setupUi(self, parent):
        VoltageFilesForm.setupUi(self,parent)
        self.mappingCombo.addItems( self.files.mappingHistory.keys() )
        self.loadMappingButton.clicked.connect( self.onLoadMapping )
        self.loadDefinitionButton.clicked.connect( self.onLoadDefinition )
        self.loadGlobalButton.clicked.connect( self.onLoadGlobal )
        self.loadLocalButton.clicked.connect( self.onLoadLocal )
        if self.files.mappingFile is not None:
            filedir, filename = os.path.split(self.files.mappingFile)
            self.mappingCombo.setCurrentIndex( self.mappingCombo.findText(filename))
        self.definitionCombo.addItems( self.files.definitionHistory.keys() )
        if self.files.definitionFile is not None:
            filedir, filename = os.path.split(self.files.definitionFile)
            self.definitionCombo.setCurrentIndex( self.definitionCombo.findText(filename))
        self.globalCombo.addItems( self.files.globalHistory.keys() )
        if self.files.globalFile is not None:
            filedir, filename = os.path.split(self.files.globalFile)
            self.globalCombo.setCurrentIndex( self.globalCombo.findText(filename))
        self.localCombo.addItems( self.files.localHistory.keys() )
        if self.files.localFile is not None:
            filedir, filename = os.path.split(self.files.localFile)
            self.localCombo.setCurrentIndex( self.localCombo.findText(filename))
        self.mappingCombo.currentIndexChanged['QString'].connect( self.onMappingChanged )
        self.definitionCombo.currentIndexChanged['QString'].connect( self.onDefinitionChanged )
        self.globalCombo.currentIndexChanged['QString'].connect( self.onGlobalChanged )
        self.localCombo.currentIndexChanged['QString'].connect( self.onLocalChanged )
        
    def reloadAll(self):
        if self.files.mappingFile:
            self.loadMapping.emit(self.files.mappingFile)
        if self.files.definitionFile:
            self.loadDefinition.emit(self.files.definitionFile)
        if self.files.globalFile:
            self.loadGlobalAdjust.emit(self.files.globalFile)
        if self.files.localFile:
            self.loadLocalAdjust.emit(self.files.localFile)
            
        
    def onMappingChanged(self,value):
        self.files.mappingFile = self.files.mappingHistory[str(value)]
        self.loadMapping.emit(self.files.mappingFile)
        print "onMappingChanged",self.files.mappingFile
        
    def onDefinitionChanged(self,value):
        self.files.definitionFile = self.files.definitionHistory[str(value)]
        self.loadDefinition.emit(self.files.definitionFile)
        print "onDefinitionChanged",self.files.definitionFile
        
    def onGlobalChanged(self,value):
        self.files.globalFile = self.files.globalHistory[str(value)]
        self.loadGlobalAdjust.emit(self.files.globalFile)
        print "onGlobalChanged",self.files.globalFile
        
    def onLocalChanged(self,value):
        pass

    def onLoadMapping(self):
        print "onLoadMapping"
        path = str(QtGui.QFileDialog.getOpenFileName(self, "Open mapping file:", self.lastDir ))
        if path!="":
            filedir, filename = os.path.split(path)
            self.lastDir = filedir
            if filename not in self.files.mappingHistory:
                self.mappingCombo.addItem(filename)
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
                self.definitionCombo.addItem(filename)
            self.files.definitionHistory[filename] = path
            self.definitionCombo.setCurrentIndex( self.definitionCombo.findText(filename))
            self.files.definitionFile = path
            self.loadDefinition.emit(path)

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
    
    def onClose(self):
        self.config[self.configname] = self.files
        