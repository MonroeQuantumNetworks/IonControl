# -*- coding: utf-8 -*-
"""
Created on Thu Feb 07 22:55:28 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtCore, QtGui
from pulseProgram import PulseProgram
from pulseProgram.VariableDictionary import VariableDictionary
from pulseProgram.VariableTableModel import VariableTableModel
from pulseProgram import ShutterTableModel
import TriggerTableModel
import CounterTableModel
import os.path
from modules import dictutil
from pulseProgram.PulseProgramSourceEdit import PulseProgramSourceEdit
import ProjectSelection
import logging
from uiModules.RotatedHeaderView import RotatedHeaderView

PulseProgramWidget, PulseProgramBase = PyQt4.uic.loadUiType('ui/PulseProgram.ui')

class ConfiguredParams:
    def __init__(self):
        self.lastFilename = None
        self.recentFiles = dict()
        
    def __setstate__(self,d):
        self.__dict__ = d
        self.__dict__.setdefault('lastFilename',None)
        self.__dict__.setdefault('recentFiles',dict())

class PulseProgramUi(PulseProgramWidget,PulseProgramBase):
    pulseProgramChanged = QtCore.pyqtSignal() 
    recentFilesChanged = QtCore.pyqtSignal(str)
    
    def __init__(self,config,parameterdict, channelNameData):
        PulseProgramWidget.__init__(self)
        PulseProgramBase.__init__(self)
        self.pulseProgram = PulseProgram.PulseProgram()
        self.sourceCodeEdits = dict()
        self.config = config
        self.parameterdict = parameterdict     # dictionary of globals
        self.combinedDict = None               # dictionary containing all PP variables
        self.variabledict = None               # dictionary containing only the 'parameters'
        self.variableTableModel = None
        self.parameterChangedSignal = None
        self.channelNameData = channelNameData
   
    def setupUi(self,experimentname,parent):
        super(PulseProgramUi,self).setupUi(parent)
        self.experimentname = experimentname
        self.configname = 'PulseProgramUi.'+self.experimentname
        self.actionOpen.triggered.connect( self.onLoad )
        self.actionSave.triggered.connect( self.onSave )
        self.actionReset.triggered.connect(self.onReset)
        self.loadButton.setDefaultAction( self.actionOpen )
        self.saveButton.setDefaultAction( self.actionSave )
        self.resetButton.setDefaultAction( self.actionReset )
        self.configParams =  self.config.get(self.configname, ConfiguredParams())
        self.shutterTableView.setHorizontalHeader( RotatedHeaderView(QtCore.Qt.Horizontal, self.shutterTableView) )
        self.triggerTableView.setHorizontalHeader( RotatedHeaderView(QtCore.Qt.Horizontal,self.triggerTableView ) )
        
        if hasattr(self.configParams,'recentFiles'):
            for key, path in self.configParams.recentFiles.iteritems():
                if os.path.exists(path):
                    self.filenameComboBox.addItem(key)
        if self.configParams.lastFilename is not None:
#             try:
            self.loadFile( self.configParams.lastFilename )
#             except Exception as e:
#                 logger.error( "Ignoring exception {0}, pulse programming file '{1}' cannot be loaded.".format(str(e),self.configParams.lastFilename) )
        if hasattr(self.configParams,'splitterHorizontal'):
            self.splitterHorizontal.restoreState(self.configParams.splitterHorizontal)
        if hasattr(self.configParams,'splitterVertical'):
            self.splitterVertical.restoreState(self.configParams.splitterVertical)
        self.filenameComboBox.currentIndexChanged[str].connect( self.onFilenameChange )
        self.removeCurrent.clicked.connect( self.onRemoveCurrent )
        
    def documentationString(self):
        messages = [ "PulseProgram {0}".format( self.configParams.lastFilename ) ]
        r = "\n".join(messages)
        return "\n".join( [r, self.pulseProgram.currentVariablesText()])        
               
    def onFilenameChange(self, name ):
        name = str(name)
        if name in self.configParams.recentFiles and self.configParams.recentFiles[name]!=self.configParams.lastFilename:
            self.loadFile(self.configParams.recentFiles[name])
            if str(self.filenameComboBox.currentText())!=name:
                self.filenameComboBox.setCurrentIndex( self.filenameComboBox.findText( name ))
        
    def onOk(self):
        pass
    
    def onLoad(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, 'Open Pulse Programmer file',ProjectSelection.configDir()))
        if path!="":
            self.loadFile(path)
            
    def onReset(self):
        if self.configParams.lastFilename is not None:
            self.variabledict = VariableDictionary( self.pulseProgram.variabledict, self.parameterdict )
            self.loadFile(self.configParams.lastFilename)
    
    def loadFile(self, path):
        logger = logging.getLogger(__name__)
        logger.debug( "loadFile {0}".format( path ) )
        if self.combinedDict is not None and self.configParams.lastFilename is not None:
            self.config[(self.configname,self.configParams.lastFilename)] = self.combinedDict
        self.configParams.lastFilename = path
        key = self.configParams.lastFilename
        compileexception = None
        try:
            self.pulseProgram.loadSource(path)
        except PulseProgram.ppexception as compileexception:
            # compilation failed, we save the exception and pass to to updateDisplay
            pass
        self.combinedDict = self.pulseProgram.variabledict.copy()
        if (self.configname,key) in self.config:
            self.combinedDict.update( dictutil.subdict(self.config[(self.configname,key)], self.combinedDict.keys() ) )
        self.updateDisplay(compileexception)
        filename = os.path.basename(path)
        if filename not in self.configParams.recentFiles:
            self.filenameComboBox.addItem(filename)
            logger.debug( "self.recentFilesChanged.emit({0})".format(filename) )
            self.recentFilesChanged.emit(filename)
        self.configParams.recentFiles[filename]=path
        self.filenameComboBox.setCurrentIndex( self.filenameComboBox.findText(filename))

    def onRemoveCurrent(self):
        text = str(self.filenameComboBox.currentText())
        if text in self.configParams.recentFiles:
            self.configParams.recentFiles.pop(text)
        self.filenameComboBox.removeItem(self.filenameComboBox.currentIndex())

    def onSave(self):
        self.onApply()
        self.pulseProgram.saveSource()
    
    def onApply(self):
        try:
            positionCache = dict()
            for name, textEdit in self.sourceCodeEdits.iteritems():
                self.pulseProgram.source[name] = str(textEdit.toPlainText())
                positionCache[name] = ( textEdit.textEdit.textCursor().position(),
                                        textEdit.textEdit.verticalScrollBar().value() )
            self.pulseProgram.loadFromMemory()
            self.oldcombinedDict = self.combinedDict
            self.combinedDict = self.pulseProgram.variabledict.copy()
            self.combinedDict.update( dictutil.subdict(self.oldcombinedDict, self.combinedDict.keys() ) )
            self.updateDisplay()
            for name, textEdit in self.sourceCodeEdits.iteritems():
                textEdit.clearHighlightError()
                cursor = textEdit.textEdit.textCursor()
                cursorpos, scrollpos = positionCache[name]
                cursor.setPosition( cursorpos )
                textEdit.textEdit.verticalScrollBar().setValue( scrollpos )
                textEdit.textEdit.setTextCursor( cursor )
        except PulseProgram.ppexception as ppex:
            textEdit = self.sourceCodeEdits[ ppex.file ].highlightError(str(ppex), ppex.line, ppex.context )
    
    def updateDisplay(self, compileexception=None):   # why does this not update the display?
        self.sourceTabs.clear()
        self.sourceCodeEdits = dict()
        for name, text in self.pulseProgram.source.iteritems():
            textEdit = PulseProgramSourceEdit()
            textEdit.setupUi(textEdit)
            textEdit.setPlainText(text)
            self.sourceCodeEdits[name] = textEdit
            self.sourceTabs.addTab( textEdit, name )
        self.variabledict = VariableDictionary( self.combinedDict, self.parameterdict )
        self.variableTableModel = VariableTableModel( self.variabledict )
        if self.parameterChangedSignal:
            self.parameterChangedSignal.connect(self.variableTableModel.recalculateDependent )
        self.variableView.setModel(self.variableTableModel)
        self.variableView.resizeColumnToContents(0)
        self.shutterTableModel = ShutterTableModel.ShutterTableModel( self.combinedDict, self.channelNameData[0:2] )
        self.shutterTableView.setModel(self.shutterTableModel)
        self.shutterTableView.resizeColumnsToContents()
        self.shutterTableView.clicked.connect(self.shutterTableModel.onClicked)
        self.triggerTableModel = TriggerTableModel.TriggerTableModel( self.combinedDict, self.channelNameData[2:4] )
        self.triggerTableView.setModel(self.triggerTableModel)
        self.triggerTableView.resizeColumnsToContents()
        self.triggerTableView.clicked.connect(self.triggerTableModel.onClicked)
        self.counterTableModel = CounterTableModel.CounterTableModel( self.combinedDict )
        self.counterTableView.setModel(self.counterTableModel)
        self.counterTableView.resizeColumnsToContents()
        self.counterTableView.clicked.connect(self.counterTableModel.onClicked)
        self.pulseProgramChanged.emit()
        if compileexception:
            textEdit = self.sourceCodeEdits[ compileexception.file ].highlightError(str(compileexception), compileexception.line, compileexception.context )
            
                    
    def onAccept(self):
        pass
    
    def onReject(self):
        pass
        
    def saveConfig(self):
        logger = logging.getLogger(__name__)
        self.configParams.splitterHorizontal = self.splitterHorizontal.saveState()
        self.configParams.splitterVertical = self.splitterVertical.saveState()
        self.config[self.configname] = self.configParams
        if self.configParams.lastFilename:
            self.config[(self.configname,self.configParams.lastFilename)] = self.combinedDict
        logger.debug("Save config for file '{1}' in tab {0}".format(self.configname,self.configParams.lastFilename))
       
    def getPulseProgramBinary(self,parameters=dict()):
        # need to update variables self.pulseProgram.updateVariables( self.)
        substitutes = dict( self.variabledict.valueView.iteritems() )
        for model in [self.shutterTableModel, self.triggerTableModel, self.counterTableModel]:
            substitutes.update( model.getVariables() )
        self.pulseProgram.updateVariables(substitutes)
        return self.pulseProgram.toBinary()
    
    def exitcode(self, number):
        return self.pulseProgram.exitcode(number)
        
    def getVariableValue(self,name):
        return self.variableTableModel.getVariableValue(name)
             
class PulseProgramSetUi(QtGui.QDialog):
    class Parameters:
        pass
    
    def __init__(self,config, channelNameData):
        super(PulseProgramSetUi,self).__init__()
        self.config = config
        self.pulseProgramSet = dict()        # ExperimentName -> PulseProgramUi
        self.lastExperimentFile = dict()     # ExperimentName -> last pp file used for this experiment
        self.isShown = False
        self.channelNameData = channelNameData
    
    def setupUi(self,parent):
        self.horizontalLayout = QtGui.QHBoxLayout(parent)
        self.tabWidget = QtGui.QTabWidget(parent)
        self.horizontalLayout.addWidget(self.tabWidget)
        self.setWindowTitle('Pulse Program')
        self.setWindowFlags(QtCore.Qt.WindowMinMaxButtonsHint)
        self.setWindowIcon(QtGui.QIcon(":/petersIcons/icons/pulser1.png"))

    def addExperiment(self, experiment, parameterdict=dict(), parameterChangedSignal=None):
        if not experiment in self.pulseProgramSet:
            programUi = PulseProgramUi(self.config, parameterdict, self.channelNameData )
            programUi.parameterChangedSignal = parameterChangedSignal
            programUi.setupUi(experiment,programUi)
            programUi.myindex = self.tabWidget.addTab(programUi,experiment)
            self.pulseProgramSet[experiment] = programUi
        return self.pulseProgramSet[experiment]
            
    def setCurrentTab(self, name):
        if name in self.pulseProgramSet:
            self.tabWidget.setCurrentWidget( self.pulseProgramSet[name] )        
            
    def getPulseProgram(self, experiment):
        return self.pulseProgramSet[experiment]
        
    def accept(self):
        self.config['PulseProgramSetUi.pos'] = self.pos()
        self.config['PulseProgramSetUi.size'] = self.size()
        self.hide()
        self.recipient.onSettingsApply()  
        for page in self.pulseProgramSet.values():
            page.onAccept()
        
    def reject(self):
        self.config['PulseProgramSetUi.pos'] = self.pos()
        self.config['PulseProgramSetUi.size'] = self.size()
        self.hide()
        for page in self.pulseProgramSet.values():
            page.onAccept()
        
    def show(self):
        if 'PulseProgramSetUi.pos' in self.config:
            self.move(self.config['PulseProgramSetUi.pos'])
        if 'PulseProgramSetUi.size' in self.config:
            self.resize(self.config['PulseProgramSetUi.size'])
        QtGui.QDialog.show(self)
        self.isShown = True
        
    def saveConfig(self):
        self.config['PulseProgramSetUi.pos'] = self.pos()
        self.config['PulseProgramSetUi.size'] = self.size()
        if self.isShown:
            for page in self.pulseProgramSet.values():
                page.saveConfig()
                
    def onClose(self):
        self.reject()

#    def resizeEvent(self, event):
#        self.config['PulseProgramSetUi.size'] = event.size()
#        super(PulseProgramSetUi,self).resizeEvent(event)
#    
#    def moveEvent(self,event):
#        super(PulseProgramSetUi,self).moveEvent(event)
#        self.config['PulseProgramSetUi.pos'] = self.pos()
        
        
    
if __name__ == "__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = PulseProgramSetUi(config)
    ui.setupUi(ui)
    ui.addExperiment("Sequence")
    ui.addExperiment("Doppler Recooling")
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
    print config
