'''
Created on Jul 24, 2015

@author: jmizrahi
'''

import os.path

from PyQt4 import QtCore, QtGui
import PyQt4.uic
import logging

from gui import ProjectSelection
from pulseProgram.PulseProgramSourceEdit import PulseProgramSourceEdit
from modules.PyqtUtility import BlockSignals
import copy

from PyQt4.Qsci import QsciLexerPython
from PyQt4.QtGui import QFont, QColor

ScriptingWidget, ScriptingBase = PyQt4.uic.loadUiType('ui/Scripting.ui')

class ScriptingLexer(QsciLexerPython):
    """Lexer used for scripts. Standard Python lexer, with additional keywords associated with scripting."""
    def __init__(self, parent=None, scriptingFunctions=dict()):
        """Initialize lexer with scriptingFunctions set."""
        super(ScriptingLexer,self).__init__(parent)
        self.scriptingFunctions = scriptingFunctions #ScriptingFunctions is a dictionary. The key is the function name, the value is the docstring
         
    def keywords(self, keyset):
        """Set scriptingFunctions to be keyset 2, so they will have unique highlighting."""
        if keyset == 2:
            return ' '.join([func for func in self.scriptingFunctions]) #This is a space separated list of all the scripting functions
        return QsciLexerPython.keywords(self, keyset)

class ScriptingSourceEdit(PulseProgramSourceEdit):
    """Editor used for scripts. Same as inherits PulseProgramSourceEdit, with different lexer."""
    def __init__(self, parent=None, scriptingFunctions=dict()):
        """Initialize editor with scripting functions set"""
        super(ScriptingSourceEdit,self).__init__(parent)
        self.scriptingFunctions = scriptingFunctions
        
    def setupUi(self, parent=None):
        """setup editor with custom scripting lexer"""
        super(ScriptingSourceEdit,self).setupUi(parent)
        lexer = ScriptingLexer(scriptingFunctions=self.scriptingFunctions) #Use a different lexer from that used for pulse program files
        lexer.setDefaultFont(self.textEdit.myfont)
        lexer.setColor( QColor('red'), lexer.SingleQuotedString )
        lexer.setFont( self.textEdit.myboldfont, lexer.Keyword)
        lexer.setFont( self.textEdit.myboldfont, lexer.HighlightedIdentifier )
        lexer.setColor( QColor('blue'), lexer.HighlightedIdentifier )
        self.textEdit.setLexer(lexer)

class ScriptingContext:
    def __init__(self, globaldict):
        self.scriptingFile = None
        
    def __setstate__(self, state):
        self.__dict__ = state
        
    stateFields = ['scriptingFile'] 
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))
    
class ConfiguredParams:
    def __init__(self):
        self.recentFiles = dict()
        self.lastContextName = None
        self.autoSaveContext = False
        
    def __setstate__(self,d):
        self.recentFiles = d['recentFiles']
        self.lastContextName = d.get('lastContextName', None )
        self.autoSaveContext = d.get('autoSaveContext', False)

class ScriptingUi(ScriptingWidget,ScriptingBase):
    ScriptingChanged = QtCore.pyqtSignal() 
    ScriptingContextDictChanged = QtCore.pyqtSignal(object)
    def __init__(self, config, parameterdict, channelNameData):
        ScriptingWidget.__init__(self)
        ScriptingBase.__init__(self)
        self.scriptingCodeEdits = dict()
        self.config = config
        self.channelNameData = channelNameData
        self.scriptingException = None
        self.globaldict = parameterdict
   
    def setupUi(self,parent):
        super(ScriptingUi,self).setupUi(parent)
        logger = logging.getLogger(__name__)
        self.configname = 'Scripting'
        self.contextDict = self.config.get( self.configname+'.contextdict', dict() )
        self.currentContext = self.config.get( self.configname+'.currentContext' , ScriptingContext(self.globaldict) )
        self.configParams =  self.config.get(self.configname, ConfiguredParams())
        self.currentContextName = self.configParams.lastContextName
        
        self.filenameComboBox.addItems( [key for key, path in self.configParams.recentFiles.iteritems() if os.path.exists(path)] )
        self.contextComboBox.addItems( sorted(self.contextDict.keys()) )

        self.actionOpen.triggered.connect( self.onLoad )
        self.actionSave.triggered.connect( self.onSave )
        self.actionReset.triggered.connect(self.onReset)
        self.actionStart.triggered.connect( self.onStart )
        self.actionStop.triggered.connect( self.onStop )
        self.actionStopImmediately.triggered.connect(self.onStopImmediately )
        self.loadButton.setDefaultAction( self.actionOpen )
        self.saveButton.setDefaultAction( self.actionSave )
        self.resetButton.setDefaultAction( self.actionReset )
        self.reloadContextButton.clicked.connect( self.onReloadContext )
        self.saveContextButton.clicked.connect( self.onSaveContext )
        self.deleteContextButton.clicked.connect( self.onDeleteContext )
        self.contextComboBox.currentIndexChanged[str].connect( self.onLoadContext )
                
        self.filenameComboBox.currentIndexChanged[str].connect( self.onFilenameChange )
        self.removeCurrent.clicked.connect( self.onRemoveCurrent )
        
        try:
            self.loadContext(self.currentContext)
            if self.configParams.lastContextName:
                index = self.contextComboBox.findText(self.configParams.lastContextName)
                with BlockSignals(self.contextComboBox) as w:
                    w.setCurrentIndex(index)
        except:
            logger.exception("Loading of previous context failed")
        #self.contextComboBox.editTextChanged.connect( self.updateSaveStatus )
        self.contextComboBox.lineEdit().editingFinished.connect( self.updateSaveStatus ) 
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.autoSaveAction = QtGui.QAction("Automatically save configuration", self)
        self.autoSaveAction.setCheckable(True)
        self.autoSaveAction.setChecked( self.configParams.autoSaveContext )
        self.autoSaveAction.triggered.connect( self.onAutoSave )
        self.addAction( self.autoSaveAction )

    def onStart(self):
        self.onSave()
        exec(self.scriptingSource)
    
    def onStop(self):
        pass
    
    def onStopImmediately(self):
        pass
    
    def onAutoSave(self, checked):
        self.configParams.autoSaveContext = checked
        if checked:
            self.onSaveContext()

    def loadContext(self, newContext ):
        previousContext = self.currentContext
        self.currentContext = copy.deepcopy(newContext)
        #changeMode = self.currentContext.pulseProgramMode != previousContext.pulseProgramMode
        if self.currentContext.scriptingFile != previousContext.scriptingFile or len(self.scriptingCodeEdits)==0:
            self.loadFile(self.currentContext.scriptingFile)
        self.updateSaveStatus(isSaved=True)
        
    def onReloadContext(self):
        self.loadContext( self.contextDict[str(self.contextComboBox.currentText())] )
        self.updateSaveStatus()
    
    def onSaveContext(self):
        name = str(self.contextComboBox.currentText())
        isNewContext = not name in self.contextDict
        self.contextDict[ name ] = copy.deepcopy(self.currentContext)
        if self.contextComboBox.findText(name)<0:
            with BlockSignals(self.contextComboBox) as w:
                w.addItem(name)
        if isNewContext:
            self.ScriptingContextDictChanged.emit(self.contextDict.keys())
        self.updateSaveStatus(isSaved=True)
        self.currentContextName = name
    
    def onDeleteContext(self):
        name = str(self.contextComboBox.currentText())
        index = self.contextComboBox.findText(name)
        if index>=0:
            self.contextDict.pop(name)
            self.contextComboBox.removeItem( index )
            self.ScriptingContextDictChanged.emit(self.contextDict.keys())
            self.updateSaveStatus()
            self.currentContextName = None

    def onLoadContext(self):
        name = str(self.contextComboBox.currentText())
        self.currentContextName = name
        if name in self.contextDict:
            self.loadContext( self.contextDict[name] )
        else:
            self.onSaveContext()
            
    def loadContextByName(self, name):
        if name in self.contextDict:
            self.loadContext( self.contextDict[name] )
            with BlockSignals(self.contextComboBox) as w:
                w.setCurrentIndex( w.findText( name ))
      
    def updateScriptingDisplay(self):
        for scriptingTab in self.scriptingCodeEdits.values():
            self.sourceTabs.removeTab( self.sourceTabs.indexOf(scriptingTab) )
        self.scriptingCodeEdits = dict()
        for name, text in [(self.scriptingSourceFile,self.scriptingSource)]:
            textEdit = ScriptingSourceEdit(scriptingFunctions=dict())
            textEdit.setupUi(textEdit)
            textEdit.setPlainText(text)
            self.scriptingCodeEdits[name] = textEdit
            self.sourceTabs.addTab( textEdit, name )
                
    def documentationString(self):
        messages = [ "Scripting {0}".format( self.configParams.lastLoadFilename ) ]
        return "\n".join(messages)
    
    def description(self):
        desc = dict()
        desc["Scripting"] =  self.configParams.lastLoadFilename
        return desc
               
    def onFilenameChange(self, name ):
        name = str(name)
        if name in self.configParams.recentFiles:
            fullname = self.configParams.recentFiles[name]
            if os.path.isfile(fullname) and fullname != self.currentContext.scriptingFile:
                self.loadFile(fullname)
                if str(self.filenameComboBox.currentText())!=name:
                    with BlockSignals(self.filenameComboBox) as w:
                        w.setCurrentIndex( self.filenameComboBox.findText( name ))
                self.updateSaveStatus()
        
    def onOk(self):
        pass
    
    def onLoad(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, 'Open Scripting file',ProjectSelection.configDir()+'\\Scripts','Python scripts (*.py *.pyw)'))
        if path!="":
            self.loadFile(path)
        self.updateSaveStatus()
           
    def loadFile(self, path):
        logger = logging.getLogger(__name__)
        if path:
            self.currentContext.scriptingFile = path
            self.scriptingSourcePath = path
            _, self.scriptingSourceFile = os.path.split(path)
            with open(path,"r") as f:
                self.scriptingSource = f.read()
            self.updateScriptingDisplay()
            filename = os.path.basename(path)
            if filename not in self.configParams.recentFiles:
                self.filenameComboBox.addItem(filename)
            self.configParams.recentFiles[filename]=path
            with BlockSignals(self.filenameComboBox) as w:
                w.setCurrentIndex( self.filenameComboBox.findText(filename))
            self.configParams.lastLoadFilename = path
            logger.info('{0} loaded'.format(self.scriptingSourcePath))
            
    def onReset(self):
        if self.configParams.lastLoadFilename is not None:
            self.loadFile(self.configParams.lastLoadFilename)

    def onRemoveCurrent(self):
        text = str(self.filenameComboBox.currentText())
        if text in self.configParams.recentFiles:
            self.configParams.recentFiles.pop(text)
        self.filenameComboBox.removeItem(self.filenameComboBox.currentIndex())

    def onSave(self):
        positionCache = dict()
        logger = logging.getLogger(__name__)
        for name, textEdit in self.scriptingCodeEdits.iteritems():
            self.scriptingSource= str(textEdit.toPlainText())
            positionCache[name] = ( textEdit.textEdit.cursorPosition(),
                                    textEdit.textEdit.scrollPosition() )

        if self.scriptingSource and self.scriptingSourcePath:
            with open(self.scriptingSourcePath, 'w') as f:
                f.write( self.scriptingSource )
                logger.info('{0} saved'.format(self.scriptingSourcePath))
    
    def onAccept(self):
        pass
    
    def onReject(self):
        pass
        
    def saveConfig(self):
        self.configParams.lastContextName = str(self.contextComboBox.currentText())
        self.config[self.configname] = self.configParams
        self.config[self.configname+'.contextdict'] = self.contextDict 
        self.config[self.configname+'.currentContext'] = self.currentContext
       
    def updateSaveStatus(self, isSaved=None):
        try:
            if isSaved is None:
                currentText = str(self.contextComboBox.currentText())
                if not currentText:
                    self.contextSaveStatus = True
                elif currentText in self.contextDict:
                    self.contextSaveStatus = self.contextDict[currentText]==self.currentContext
                else:
                    self.contextSaveStatus = False
                if self.configParams.autoSaveContext and not self.contextSaveStatus:
                    self.onSaveContext()
                    self.contextSaveStatus = True
            else:
                self.contextSaveStatus = isSaved
            self.saveContextButton.setEnabled( not self.contextSaveStatus )
        except Exception:
            pass

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

