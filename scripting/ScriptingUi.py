'''
Created on Jul 24, 2015

@author: jmizrahi
'''

import os.path

from PyQt4 import QtCore, QtGui
import PyQt4.uic
import logging

from gui import ProjectSelection
from modules.PyqtUtility import BlockSignals
from Script import Script, scriptingFunctionNames

ScriptingWidget, ScriptingBase = PyQt4.uic.loadUiType('ui/Scripting.ui')

class ScriptingUi(ScriptingWidget,ScriptingBase):
    ScriptingContextDictChanged = QtCore.pyqtSignal(object)
    def __init__(self, config):
        ScriptingWidget.__init__(self)
        ScriptingBase.__init__(self)
        self.config = config
        self.textEdit = None
        self.recentFiles = dict() #dict of form {shortname: fullname}, where fullname has path and shortname doesn't 
        self.script = Script() #encapsulates the script
   
    def setupUi(self,parent):
        super(ScriptingUi,self).setupUi(parent)
        #logger = logging.getLogger(__name__)
        self.configname = 'Scripting'
        self.recentFiles = self.config.get( self.configname+'.recentFiles' , dict() )
        self.script = self.config.get( self.configname+'.script' , Script() )
        self.textEdit.setupUi(self.textEdit,extraKeywords1=[], extraKeywords2=scriptingFunctionNames)
        self.textEdit.setPlainText(self.script.code)
        #Add only the filename (without the full path) to the combo box
        self.filenameComboBox.addItems( [shortname for shortname, fullname in self.recentFiles.iteritems() if os.path.exists(fullname)] )

        self.actionOpen.triggered.connect( self.onLoad )
        self.actionSave.triggered.connect( self.onSave )
        self.actionReset.triggered.connect(self.onReset)
        self.actionStart.triggered.connect( self.onStart )
        self.actionStop.triggered.connect( self.onStop )
        self.actionStopImmediately.triggered.connect(self.onStopImmediately )
        self.loadButton.setDefaultAction( self.actionOpen )
        self.saveButton.setDefaultAction( self.actionSave )
        self.resetButton.setDefaultAction( self.actionReset )
                
        self.filenameComboBox.currentIndexChanged[str].connect( self.onFilenameChange )
        self.removeCurrent.clicked.connect( self.onRemoveCurrent )
        
        self.loadFile(self.script.fullname)
        
    def onStart(self):
        self.onSave()
        execfile(self.script.fullname)
    
    def onStop(self):
        pass
    
    def onStopImmediately(self):
        pass
    
    def onFilenameChange(self, shortname ):
        shortname = str(shortname)
        if shortname in self.recentFiles:
            fullname = self.recentFiles[shortname]
            if os.path.isfile(fullname) and fullname != self.script.fullname:
                self.loadFile(fullname)
                if str(self.filenameComboBox.currentText())!=fullname:
                    with BlockSignals(self.filenameComboBox) as w:
                        w.setCurrentIndex( self.filenameComboBox.findText( shortname ))
    
    def onLoad(self):
        fullname = str(QtGui.QFileDialog.getOpenFileName(self, 'Open Scripting file',ProjectSelection.configDir()+'\\Scripts','Python scripts (*.py *.pyw)'))
        if fullname!="":
            self.loadFile(fullname)
           
    def loadFile(self, fullname):
        logger = logging.getLogger(__name__)
        if fullname:
            self.script.fullname = fullname
            self.script.shortname = os.path.basename(fullname) 
            with open(fullname,"r") as f:
                self.script.code = f.read()
            self.textEdit.setPlainText(self.script.code)
            if self.script.shortname not in self.recentFiles:
                self.filenameComboBox.addItem(self.script.shortname)
            self.recentFiles[self.script.shortname] = fullname
            with BlockSignals(self.filenameComboBox) as w:
                w.setCurrentIndex( self.filenameComboBox.findText(self.script.shortname))
            logger.info('{0} loaded'.format(self.script.fullname))
            
    def onReset(self):
        if self.script.fullname:
            self.loadFile(self.script.fullname)

    def onRemoveCurrent(self):
        text = str(self.filenameComboBox.currentText())
        if text in self.recentFiles:
            self.recentFiles.pop(text)
        self.filenameComboBox.removeItem(self.filenameComboBox.currentIndex())

    def onSave(self):
        logger = logging.getLogger(__name__)
        self.script.code = str(self.textEdit.toPlainText())

        if self.script.code and self.script.fullname:
            with open(self.script.fullname, 'w') as f:
                f.write(self.script.code)
                logger.info('{0} saved'.format(self.script.fullname))
    
    def saveConfig(self):
        self.config[self.configname+'.recentFiles'] = self.recentFiles
        self.config[self.configname+'.script'] = self.script
       
    def show(self):
        pos = self.config.get(self.configname+'.ScriptingUi.pos')
        size = self.config.get(self.configname+'.ScriptingUi.size')
        if pos:
            self.move(pos)
        if size:
            self.resize(size)
        QtGui.QDialog.show(self)
        self.isShown = True

    def onClose(self):
        self.config[self.configname+'.ScriptingUi.pos'] = self.pos()
        self.config[self.configname+'.ScriptingUi.size'] = self.size()
        self.hide()

