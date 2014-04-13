# -*- coding: utf-8 -*-
"""
Created on Thu Feb 07 22:55:28 2013

@author: pmaunz
"""
import logging
import os.path

from PyQt4 import QtCore, QtGui
import PyQt4.uic

from pulseProgram import CounterTableModel
from gui import ProjectSelection
from pulseProgram import TriggerTableModel
from modules import dictutil
from pulseProgram import PulseProgram
from pulseProgram import ShutterTableModel
from pulseProgram.PulseProgramSourceEdit import PulseProgramSourceEdit
from pulseProgram.VariableDictionary import VariableDictionary
from pulseProgram.VariableTableModel import VariableTableModel
from uiModules.RotatedHeaderView import RotatedHeaderView
from modules.enum import enum
from pppCompiler.pppCompiler import pppCompiler
from pppCompiler.CompileException import CompileException
from modules.PyqtUtility import BlockSignals
from pyparsing import ParseException
import copy
from ShutterDictionary import ShutterDictionary
from TriggerDictionary import TriggerDictionary
from CounterDictionary import CounterDictionary

PulseProgramWidget, PulseProgramBase = PyQt4.uic.loadUiType('ui/PulseProgram.ui')

def getPpFileName( filename ):
    if filename is None:
        return filename
    _, ext = os.path.splitext(filename)
    if ext != '.ppp':
        return filename
    path, leafname = os.path.split( filename )
    _, tail = os.path.split(path)
    pp_path = os.path.join(path,"generated_pp") if tail != "generated_pp" else path    
    if not os.path.exists(pp_path):
        os.makedirs(pp_path)
    base, _ = os.path.splitext(leafname)
    return os.path.join(pp_path, base+".ppc")


class PulseProgramContext:
    def __init__(self):
        self.parameters = VariableDictionary()
        self.shutters = ShutterDictionary()
        self.triggers = TriggerDictionary()
        self.counters = CounterDictionary()
        self.pulseProgram = None
        
    def __setstate__(self, state):
        self.__dict__ = state
        
    stateFields = ['parameters', 'shutters', 'triggers', 'counters', 'pulseProgram'] 
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))
    
    def mergeFromPP(self, pulseProgram):
        self.parameters.mergeFromVariabledict( pulseProgram.variabledict )
        for name,var in pulseProgram.variabledict.iteritems():
            if var.type in ['parameter','address']:
                super(VariableDictionary,self).__setitem__(name, copy.deepcopy(var) )
    
    def setFromPP(self, pulseProgram):
        self.parameters.setFromVariabledict( pulseProgram.variabledict )
        
class ConfiguredParams:
    def __init__(self):
        self.recentFiles = dict()
        
    def __setstate__(self,d):
        self.recentFiles = d['recentFiles']

class PulseProgramUi(PulseProgramWidget,PulseProgramBase):
    pulseProgramChanged = QtCore.pyqtSignal() 
    recentFilesChanged = QtCore.pyqtSignal(str)
    SourceMode = enum('pp','ppp') 
    def __init__(self,config,parameterdict, channelNameData):
        PulseProgramWidget.__init__(self)
        PulseProgramBase.__init__(self)
        self.pulseProgram = PulseProgram.PulseProgram()
        self.sourceCodeEdits = dict()
        self.pppCodeEdits = dict()
        self.config = config
        self.variableTableModel = None
        self.parameterChangedSignal = None
        self.channelNameData = channelNameData
        self.sourceMode = self.SourceMode.pp
        self.pppCompileException = None
   
    def setupUi(self,experimentname,parent):
        super(PulseProgramUi,self).setupUi(parent)
        self.experimentname = experimentname
        self.configname = 'PulseProgramUi.'+self.experimentname
        self.contextDict = self.config.get( self.configname+'context', dict() )
        self.currentContext = self.config.get( self.configname+'currentContext' , PulseProgramContext() )
        self.configParams =  self.config.get(self.configname, ConfiguredParams())
        
        self.filenameComboBox.addItems( [key for key, path in self.configParams.recentFiles.iteritems() if os.path.exists(path)] )
        self.contextComboBox.addItems( self.contextDict.keys() )

        self.actionOpen.triggered.connect( self.onLoad )
        self.actionSave.triggered.connect( self.onSave )
        self.actionReset.triggered.connect(self.onReset)
        self.loadButton.setDefaultAction( self.actionOpen )
        self.saveButton.setDefaultAction( self.actionSave )
        self.resetButton.setDefaultAction( self.actionReset )
        self.shutterTableView.setHorizontalHeader( RotatedHeaderView(QtCore.Qt.Horizontal, self.shutterTableView) )
        self.triggerTableView.setHorizontalHeader( RotatedHeaderView(QtCore.Qt.Horizontal,self.triggerTableView ) )
        self.reloadContextButton.clicked.connect( self.onReloadContext )
        self.saveContextButton.clicked.connect( self.onSaveContext )
        self.deleteContextButton.clicked.connect( self.onDeleteContext )
        self.contextComboBox.currentIndexChanged[str].connect( self.onLoadContext )
                
        if hasattr(self.configParams,'splitterHorizontal'):
            self.splitterHorizontal.restoreState(self.configParams.splitterHorizontal)
        if hasattr(self.configParams,'splitterVertical'):
            self.splitterVertical.restoreState(self.configParams.splitterVertical)
        self.filenameComboBox.currentIndexChanged[str].connect( self.onFilenameChange )
        self.removeCurrent.clicked.connect( self.onRemoveCurrent )
        
        self.variableTableModel = VariableTableModel( self.currentConext.parameters )
        if self.parameterChangedSignal:
            self.parameterChangedSignal.connect(self.variableTableModel.recalculateDependent )
        self.variableView.setModel(self.variableTableModel)
        self.variableView.resizeColumnToContents(0)
        self.shutterTableModel = ShutterTableModel.ShutterTableModel( self.currentContext.shutters, self.channelNameData[0:2] )
        self.shutterTableView.setModel(self.shutterTableModel)
        self.shutterTableView.resizeColumnsToContents()
        self.shutterTableView.clicked.connect(self.shutterTableModel.onClicked)
        self.triggerTableModel = TriggerTableModel.TriggerTableModel( self.currentContext.triggers, self.channelNameData[2:4] )
        self.triggerTableView.setModel(self.triggerTableModel)
        self.triggerTableView.resizeColumnsToContents()
        self.triggerTableView.clicked.connect(self.triggerTableModel.onClicked)
        self.counterTableModel = CounterTableModel.CounterTableModel( self.currentContext.counters )
        self.counterTableView.setModel(self.counterTableModel)
        self.counterTableView.resizeColumnsToContents()
        self.counterTableView.clicked.connect(self.counterTableModel.onClicked)

    def loadContext(self, newContext ):
        pass
        
    def updateDisplay(self, compileexception=None, pppCompileException=None):   # why does this not update the display?
        self.sourceTabs.clear()
        self.sourceCodeEdits = dict()
        self.pppCodeEdits = dict()
        if self.sourceMode==self.SourceMode.ppp:
            for name, text in [(self.pppSourceFile,self.pppSource)]:
                textEdit = PulseProgramSourceEdit(mode='ppp')
                textEdit.setupUi(textEdit)
                textEdit.setPlainText(text)
                self.pppCodeEdits[name] = textEdit
                self.sourceTabs.addTab( textEdit, name )
        for name, text in self.pulseProgram.source.iteritems():
            textEdit = PulseProgramSourceEdit()
            textEdit.setupUi(textEdit)
            textEdit.setPlainText(text)
            self.sourceCodeEdits[name] = textEdit
            self.sourceTabs.addTab( textEdit, name )
            textEdit.setReadOnly( self.sourceMode!=self.SourceMode.pp )
        if self.combinedDict is not None:
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
        if pppCompileException and self.sourceMode==self.SourceMode.ppp:
            textEdit = self.pppCodeEdits[self.pppSourceFile].highlightError( pppCompileException.message(), pppCompileException.lineno(), col=pppCompileException.col())

    def documentationString(self):
        messages = [ "PulseProgram {0}".format( self.configParams.lastLoadFilename ) ]
        r = "\n".join(messages)
        return "\n".join( [r, self.pulseProgram.currentVariablesText()])        
               
    def onFilenameChange(self, name ):
        name = str(name)
        if name in self.configParams.recentFiles and self.configParams.recentFiles[name]!=self.configParams.lastLoadFilename:
            self.adaptiveLoadFile(self.configParams.recentFiles[name])
            if str(self.filenameComboBox.currentText())!=name:
                self.filenameComboBox.setCurrentIndex( self.filenameComboBox.findText( name ))
        
    def onOk(self):
        pass
    
    def onLoad(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, 'Open Pulse Programmer file',ProjectSelection.configDir()))
        if path!="":
            self.adaptiveLoadFile(path)
            
    def adaptiveLoadFile(self, path):
        _, ext = os.path.splitext(path)
        if ext==".ppp":
            self.sourceMode = self.SourceMode.ppp
            self.loadpppFile(path)
        else:
            self.sourceMode = self.SourceMode.pp
            self.loadFile(path)            
        self.configParams.lastLoadFilename = path
            
    def onReset(self):
        if self.configParams.lastLoadFilename is not None:
            self.variabledict = VariableDictionary( self.pulseProgram.variabledict, self.parameterdict )
            self.adaptiveLoadFile(self.configParams.lastLoadFilename)
    
    def loadpppFile(self, path):
        if self.combinedDict is not None and self.configParams.lastppFilename is not None:
            self.config[(self.configname,getPpFileName(self.configParams.lastppFilename))] = self.combinedDict
        self.pppSourcePath = path
        _, self.pppSourceFile = os.path.split(path)
        with open(path,"r") as f:
            self.pppSource = f.read()
        self
        ppFilename = getPpFileName(path)
        self.compileppp(ppFilename)
        if self.pppCompileException is None:
            self.loadFile(ppFilename, cache=False)
        else:
            self.updateDisplay(pppCompileException=self.pppCompileException)
        filename = os.path.basename(path)
        if filename not in self.configParams.recentFiles:
            self.filenameComboBox.addItem(filename)
            self.recentFilesChanged.emit(filename)
        self.configParams.recentFiles[filename]=path
        with BlockSignals(self.filenameComboBox) as w:
            w.setCurrentIndex( self.filenameComboBox.findText(filename))

    def saveppp(self, path):
        if self.pppSource and path:
            with open(path,'w') as f:
                f.write( self.pppSource )

    def compileppp(self, savefilename):
        self.pppSource = self.pppSource.expandtabs(4)
        try:
            compiler = pppCompiler()
            ppCode = compiler.compileString( self.pppSource )
            self.pppCompileException = None
            with open(savefilename,"w") as f:
                f.write("# autogenerated from '{0}' \n# DO NOT EDIT DIRECTLY\n# The file will be overwritten by the compiler\n#\n".format(self.pppSourcePath))
                f.write(ppCode)
        except CompileException as e:
            self.pppCompileException = e
        except ParseException as e:
            e.__class__ = CompileException  # cast to CompileException. Is possible because CompileException does ONLY add behavior
            self.pppCompileException = e
    
    def loadFile(self, path, cache=True):
        logger = logging.getLogger(__name__)
        logger.debug( "loadFile {0}".format( path ) )
        if self.combinedDict is not None and self.configParams.lastppFilename is not None:
            self.config[(self.configname,getPpFileName(self.configParams.lastppFilename))] = self.combinedDict
        self.configParams.lastppFilename = getPpFileName(path)
        key = self.configParams.lastppFilename
        compileexception = None
        try:
            self.pulseProgram.loadSource(path)
        except PulseProgram.ppexception as compileexception:
            # compilation failed, we save the exception and pass to to updateDisplay
            pass
        self.combinedDict = self.pulseProgram.variabledict.copy()
        if (self.configname,key) in self.config:
            self.combinedDict.update( dictutil.subdict(self.config[(self.configname,key)], self.combinedDict.keys() ) )
        self.updateDisplay(compileexception, self.pppCompileException)
        if cache:
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
        if self.sourceMode==self.SourceMode.pp:
            self.pulseProgram.saveSource()
        else:
            self.saveppp(self.pppSourcePath)
    
    def onApply(self):
        if self.sourceMode==self.SourceMode.pp:
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
                self.updateDisplay(pppCompileException=self.pppCompileException)
                for name, textEdit in self.sourceCodeEdits.iteritems():
                    textEdit.clearHighlightError()
                    cursor = textEdit.textEdit.textCursor()
                    cursorpos, scrollpos = positionCache[name]
                    cursor.setPosition( cursorpos )
                    textEdit.textEdit.verticalScrollBar().setValue( scrollpos )
                    textEdit.textEdit.setTextCursor( cursor )
            except PulseProgram.ppexception as ppex:
                textEdit = self.sourceCodeEdits[ ppex.file ].highlightError(str(ppex), ppex.line, ppex.context )
        else:
            positionCache = dict()
            for name, textEdit in self.pppCodeEdits.iteritems():
                self.pppSource = str(textEdit.toPlainText())
                positionCache[name] = ( textEdit.textEdit.textCursor().position(),
                                        textEdit.textEdit.verticalScrollBar().value() )
            self.oldcombinedDict = self.combinedDict
            ppFilename = getPpFileName( self.pppSourcePath )
            self.compileppp(ppFilename)
            if self.pppCompileException is None:
                self.loadFile(ppFilename, cache=False)
                self.combinedDict = self.pulseProgram.variabledict.copy()
                self.combinedDict.update( dictutil.subdict(self.oldcombinedDict, self.combinedDict.keys() ) )
            self.updateDisplay(pppCompileException=self.pppCompileException)
            if self.pppCompileException is None:
                for name, textEdit in self.pppCodeEdits.iteritems():
                    textEdit.clearHighlightError()
                    cursor = textEdit.textEdit.textCursor()
                    cursorpos, scrollpos = positionCache[name]
                    cursor.setPosition( cursorpos )
                    textEdit.textEdit.verticalScrollBar().setValue( scrollpos )
                    textEdit.textEdit.setTextCursor( cursor )
    
            
                    
    def onAccept(self):
        pass
    
    def onReject(self):
        pass
        
    def saveConfig(self):
        logger = logging.getLogger(__name__)
        self.configParams.splitterHorizontal = self.splitterHorizontal.saveState()
        self.configParams.splitterVertical = self.splitterVertical.saveState()
        self.config[self.configname] = self.configParams
        if self.configParams.lastppFilename:
            self.config[(self.configname,getPpFileName(self.configParams.lastppFilename))] = self.combinedDict
        logger.debug("Save config for file '{1}' in tab {0}".format(self.configname,getPpFileName(self.configParams.lastppFilename)))
       
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
    
    def variableScanCode(self, variablename, values):
        tempvariabledict = copy.deepcopy( self.variabledict )
        updatecode = list()
        for currentval in values:
            upd_names, upd_values = tempvariabledict.setValue(variablename, currentval)
            upd_names.append( variablename )
            upd_values.append( currentval )
            updatecode.extend( self.pulseProgram.multiVariableUpdateCode( upd_names, upd_values ) )
        return updatecode

             
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
