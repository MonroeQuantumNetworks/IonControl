# -*- coding: utf-8 -*-
"""
Created on Thu Feb 07 22:55:28 2013

@author: pmaunz
"""
import os.path

from PyQt4 import QtCore, QtGui
import PyQt4.uic
import logging
from modules.file_data_cache import file_data_cache

from pulseProgram import CounterTableModel
from ProjectConfig.Project import getProject
from pulseProgram import TriggerTableModel
from pulseProgram import PulseProgram
from pulseProgram import ShutterTableModel
from pulseProgram.PulseProgramSourceEdit import PulseProgramSourceEdit
from pulseProgram.VariableDictionary import VariableDictionary
from pulseProgram.VariableTableModel import VariableTableModel
from uiModules.RotatedHeaderView import RotatedHeaderView
from modules.enum import enum
from pppCompiler.pppCompiler import pppCompiler
from pppCompiler.CompileException import CompileException
from pppCompiler.Symbol import SymbolTable
from modules.PyqtUtility import BlockSignals, restoreDockWidgetSizes, saveDockWidgetSizes
from pyparsing import ParseException
import copy
from ShutterDictionary import ShutterDictionary
from TriggerDictionary import TriggerDictionary
from CounterDictionary import CounterDictionary
from uiModules.KeyboardFilter import KeyListFilter
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
import xml.etree.ElementTree as ElementTree
from modules.XmlUtilit import prettify, xmlEncodeAttributes, xmlParseAttributes
from modules import DataDirectory
from PulseProgram import Variable, OPS
import modules.magnitude as magnitude
import functools
import yaml

uipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\PulseProgram.ui')
PulseProgramWidget, PulseProgramBase = PyQt4.uic.loadUiType(uipath)

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
    XMLTagName = "PulseProgramContext"
    def __init__(self, globaldict):
        self.parameters = VariableDictionary()
        self.parameters.setGlobaldict(globaldict)
        self.shutters = ShutterDictionary()
        self.triggers = TriggerDictionary()
        self.counters = CounterDictionary()
        self.pulseProgramFile = None
        self.pulseProgramMode = 'pp'
        self.ramFile = None
        self.writeRam = False

    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault('ramFile', '')
        self.__dict__.setdefault('writeRam', False)

    stateFields = ['parameters', 'shutters', 'triggers', 'counters', 'pulseProgramFile', 'pulseProgramMode', 'ramFile', 'writeRam']
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))
    
    def merge(self, variabledict, overwrite=False):
        self.parameters.merge(variabledict, overwrite=overwrite)
        self.shutters.merge(variabledict, overwrite)
        self.triggers.merge(variabledict, overwrite)
        self.counters.merge(variabledict, overwrite)
        
    def setGlobaldict(self, globaldict):
        self.parameters.setGlobaldict(globaldict)
        
    def exportXml(self, element, attrib=dict()):
        myElement = ElementTree.SubElement(element, self.XMLTagName, attrib=attrib )
        xmlEncodeAttributes(self.__dict__, myElement)
        for parameter in self.parameters.itervalues():
            parameter.exportXml(myElement, "PPVariable")
        for name, parameter in self.shutters.iteritems():
            shutterItemElement = ElementTree.SubElement(myElement, "Shutter", attrib={'name':name} )
            for item in parameter:
                if item is not None:
                    item.exportXml(shutterItemElement, "PPShutter")
        for parameter in self.counters.itervalues():
            parameter.exportXml(myElement, "PPCounter")
        for parameter in self.triggers.itervalues():
            parameter.exportXml(myElement, "PPTrigger")
        return myElement   
    
    @staticmethod
    def fromXmlElement( element, globaldict ):
        myElement = element if element.tag==PulseProgramContext.XMLTagName else element.find(PulseProgramContext.XMLTagName)
        c = PulseProgramContext(globaldict)
        c.__dict__.update( xmlParseAttributes(myElement))
        c.parameters = VariableDictionary( (Variable.fromXMLElement(e, returnTuple=True) for e in myElement.findall("PPVariable") ) )
        c.counters = CounterDictionary( (Variable.fromXMLElement(e, returnTuple=True) for e in myElement.findall("PPCounter") ) )
        c.triggers = TriggerDictionary( (Variable.fromXMLElement(e, returnTuple=True) for e in myElement.findall("PPTrigger") ) )
        c.shutters = ShutterDictionary()
        for e in myElement.findall("Shutter"):
            c.shutters[e.attrib['name']] = tuple((Variable.fromXMLElement(e) for e in myElement.findall("PPShutter") ))
        return (myElement.attrib['name'], c)


class ConfiguredParams:
    def __init__(self):
        self.recentFiles = dict()
        self.recentRamFiles = dict()
        self.lastContextName = None
        self.autoSaveContext = True
        
    def __setstate__(self,d):
        self.recentFiles = d['recentFiles']
        self.recentRamFiles =getattr(self, 'recentRamFiles', dict())
        self.lastContextName = d.get('lastContextName', None )
        self.autoSaveContext = d.get('autoSaveContext', True)

class PulseProgramUi(PulseProgramWidget,PulseProgramBase):
    pulseProgramChanged = QtCore.pyqtSignal() 
    contextDictChanged = QtCore.pyqtSignal(object)
    definitionWords = ['counter', 'var', 'shutter', 'parameter', 'masked_shutter', 'trigger', 'address', 'exitcode', 'const']
    builtinWords = []
    for key, val in SymbolTable().iteritems(): #Extract the builtin words which should be highlighted
        if type(val).__name__ == 'Builtin':
            builtinWords.append(key)

    SourceMode = enum('pp','ppp') 
    def __init__(self, config, parameterdict, channelNameData):
        PulseProgramWidget.__init__(self)
        PulseProgramBase.__init__(self)
        self.pulseProgram = PulseProgram.PulseProgram()
        self.sourceCodeEdits = dict()
        self.pppCodeEdits = dict()
        self.config = config
        self.variableTableModel = None
        self.parameterChangedSignal = None
        self.channelNameData = channelNameData
        self.pppCompileException = None
        self.globaldict = parameterdict

    def setupUi(self,experimentname,parent):
        super(PulseProgramUi,self).setupUi(parent)
        self.setCentralWidget(None) #No central widget
        self.experimentname = experimentname
        self.configname = 'PulseProgramUi.'+self.experimentname
        self.contextDict = self.config.get( self.configname+'.contextdict', dict() )
        for context in self.contextDict.values():    # set the global dict as this field does not survive pickling
            context.setGlobaldict(self.globaldict)
        self.currentContext = self.config.get( self.configname+'.currentContext' , PulseProgramContext(self.globaldict) )
        self.currentContext.setGlobaldict(self.globaldict)
        self.configParams =  self.config.get(self.configname, ConfiguredParams())
        self.currentContextName = self.configParams.lastContextName
        
        self.filenameComboBox.addItems( [key for key, path in self.configParams.recentFiles.iteritems() if os.path.exists(path)] )
        self.contextComboBox.addItems( sorted(self.contextDict.keys()) )
        self.ramFilenameComboBox.addItems( [''] + [key for key, path in self.configParams.recentRamFiles.iteritems() if os.path.exists(path)] )
        self.writeRamCheckbox.setChecked(self.currentContext.writeRam)

        self.actionOpen.triggered.connect( self.onLoad )
        self.actionSave.triggered.connect( self.onSave )
        self.actionReset.triggered.connect(self.onReset)
        self.loadButton.setDefaultAction( self.actionOpen )
        self.saveButton.setDefaultAction( self.actionSave )
        self.resetButton.setDefaultAction( self.actionReset )
        self.loadButtonRam.clicked.connect( self.onLoadRamFile )
        self.writeRamCheckbox.clicked.connect( self.onWriteRamCheckbox )
        self.shutterTableView.setHorizontalHeader( RotatedHeaderView(QtCore.Qt.Horizontal, self.shutterTableView) )
        self.triggerTableView.setHorizontalHeader( RotatedHeaderView(QtCore.Qt.Horizontal,self.triggerTableView ) )
        self.counterTableView.setHorizontalHeader( RotatedHeaderView(QtCore.Qt.Horizontal,self.counterTableView ) )
        self.reloadContextButton.clicked.connect( self.onReloadContext )
        self.saveContextButton.clicked.connect( self.onSaveContext )
        self.deleteContextButton.clicked.connect( self.onDeleteContext )
        self.contextComboBox.currentIndexChanged[str].connect( self.onLoadContext )
        self.filenameComboBox.currentIndexChanged[str].connect( self.onFilenameChange )
        self.ramFilenameComboBox.currentIndexChanged[str].connect( self.onRamFilenameChange )
        self.removeCurrent.clicked.connect( self.onRemoveCurrent )
        self.removeCurrentRamFile.clicked.connect( self.onRemoveCurrentRamFile )

        self.variableTableModel = VariableTableModel( self.currentContext.parameters, self.config, self.currentContextName )
        if self.parameterChangedSignal:
            self.parameterChangedSignal.connect(self.variableTableModel.recalculateDependent )
        self.variableView.setModel(self.variableTableModel)
        self.variableView.resizeColumnToContents(0)
        self.filter = KeyListFilter( [], [QtCore.Qt.Key_B] )
        self.filter.controlKeyPressed.connect( self.onBold )
        self.variableView.installEventFilter(self.filter)
        self.shutterTableModel = ShutterTableModel.ShutterTableModel( self.currentContext.shutters, self.channelNameData[0:2], size=48 )
        self.shutterTableView.setModel(self.shutterTableModel)
        self.shutterTableView.resizeColumnsToContents()
        self.shutterTableView.clicked.connect(self.shutterTableModel.onClicked)
        self.triggerTableModel = TriggerTableModel.TriggerTableModel( self.currentContext.triggers, self.channelNameData[2:4] )
        self.triggerTableView.setModel(self.triggerTableModel)
        self.triggerTableView.resizeColumnsToContents()
        self.triggerTableView.clicked.connect(self.triggerTableModel.onClicked)
        self.counterTableModel = CounterTableModel.CounterTableModel( self.currentContext.counters, self.channelNameData[4] )
        self.counterTableView.setModel(self.counterTableModel)
        self.counterTableView.resizeColumnsToContents()
        self.counterTableView.clicked.connect(self.counterTableModel.onClicked)
        self.counterIdDelegate = MagnitudeSpinBoxDelegate()
        self.counterTableView.setItemDelegateForColumn(0, self.counterIdDelegate)
        try:
            self.loadContext(self.currentContext)
            if self.configParams.lastContextName:
                index = self.contextComboBox.findText(self.configParams.lastContextName)
                with BlockSignals(self.contextComboBox) as w:
                    w.setCurrentIndex(index)
        except:
            logging.getLogger(__name__).exception("Loading of previous context failed")
        #self.contextComboBox.editTextChanged.connect( self.updateSaveStatus )
        self.contextComboBox.lineEdit().editingFinished.connect( self.updateSaveStatus ) 
        self.variableTableModel.contentsChanged.connect( self.updateSaveStatus )
        self.counterTableModel.contentsChanged.connect( self.updateSaveStatus )
        self.shutterTableModel.contentsChanged.connect( self.updateSaveStatus )
        self.triggerTableModel.contentsChanged.connect( self.updateSaveStatus )
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.autoSaveAction = QtGui.QAction("Automatically save configuration", self)
        self.autoSaveAction.setCheckable(True)
        self.autoSaveAction.setChecked( self.configParams.autoSaveContext )
        self.autoSaveAction.triggered.connect( self.onAutoSave )
        self.addAction( self.autoSaveAction )
        self.exportXmlButton.clicked.connect( self.onExportXml )
        self.initMenu()
        self.restoreLayout()

    def restoreLayout(self):
        """Restore layout from config settings"""
        if self.configname+".state" in self.config:
            self.restoreState(self.config[self.configname+".state"])
        if self.configname+".splitter" in self.config:
            self.splitter.restoreState(self.config[self.configname+".splitter"])
        restoreDockWidgetSizes(self, self.config, self.configname)

    def initMenu(self):
        self.menuView.clear()
        dockList = self.findChildren(QtGui.QDockWidget)
        for dock in dockList:
            self.menuView.addAction(dock.toggleViewAction())

    def onExportXml(self, element=None, writeToFile=True):
        root = element if element is not None else ElementTree.Element('PulseProgramList')
        for name, context in self.contextDict.iteritems():
            context.exportXml(root,{'name':name})
        if writeToFile:
            filename = DataDirectory.DataDirectory().sequencefile("PulseProgramList.xml")[0]
            with open(filename,'w') as f:
                f.write(prettify(root))
            self.onImportXml(filename, mode="")
        return root

    def onImportXml(self, filename=None, mode="addMissing"):
        filename = filename if filename is not None else QtGui.QFileDialog.getOpenFileName(self, 'Import XML file', filter="*.xml" )
        tree = ElementTree.parse(filename)
        element = tree.getroot()
        self.importXml(element, mode=mode)
            
    def importXml(self, element, mode="addMissing"):   # modes: replace, update, addMissing
        newDict = dict( PulseProgramContext.fromXmlElement(e, self.globaldict) for e in element.findall(PulseProgramContext.XMLTagName) )
        if mode=="replace":
            self.contextDict = newDict
        elif mode=="update":
            self.contextDict.update( newDict )
        elif mode=="addMissing":
            newDict.update( self.contextDict )
            self.contextDict = newDict
       
    def onAutoSave(self, checked):
        self.configParams.autoSaveContext = checked
        if checked:
            self.onSaveContext()

    def loadContext(self, newContext ):
        previousContext = self.currentContext
        self.currentContext = copy.deepcopy(newContext)
        #changeMode = self.currentContext.pulseProgramMode != previousContext.pulseProgramMode
        if self.currentContext.pulseProgramFile != previousContext.pulseProgramFile or len(self.sourceCodeEdits)==0:
            self.adaptiveLoadFile(self.currentContext.pulseProgramFile)
        if self.currentContext.ramFile != previousContext.ramFile or (self.currentContext.ramFile):
            self.loadRamFile(self.currentContext.ramFile)
        self.currentContext.merge( self.pulseProgram.variabledict )
        self.updateDisplayContext()
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
            self.contextDictChanged.emit(self.contextDict.keys())
        self.updateSaveStatus(isSaved=True)
        self.currentContextName = name
    
    def onDeleteContext(self):
        name = str(self.contextComboBox.currentText())
        index = self.contextComboBox.findText(name)
        if index>=0:
            self.contextDict.pop(name)
            self.contextComboBox.removeItem( index )
            self.contextDictChanged.emit(self.contextDict.keys())
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
      
    def updatepppDisplay(self):
        for pppTab in self.pppCodeEdits.values():
            self.sourceTabs.removeTab( self.sourceTabs.indexOf(pppTab) )
        self.pppCodeEdits = dict()
        if self.currentContext.pulseProgramMode == 'ppp':
            for name, text in [(self.pppSourceFile,self.pppSource)]:
                textEdit = PulseProgramSourceEdit(mode='ppp')
                textEdit.setupUi(textEdit, extraKeywords1=self.definitionWords, extraKeywords2=self.builtinWords)
                textEdit.setPlainText(text)
                self.pppCodeEdits[name] = textEdit
                self.sourceTabs.addTab( textEdit, name )
                
    def updateppDisplay(self):
        for pppTab in self.sourceCodeEdits.values():
            self.sourceTabs.removeTab( self.sourceTabs.indexOf(pppTab) )
        self.sourceCodeEdits = dict()
        for name, text in self.pulseProgram.source.iteritems():
            textEdit = PulseProgramSourceEdit()
            textEdit.setupUi(textEdit, extraKeywords1=self.definitionWords, extraKeywords2=[key for key in OPS])
            textEdit.setPlainText(text)
            self.sourceCodeEdits[name] = textEdit
            self.sourceTabs.addTab( textEdit, name )
            textEdit.setReadOnly( self.currentContext.pulseProgramMode!='pp' )

    def updateDisplayContext(self):
        self.variableTableModel.setVariables( self.currentContext.parameters, self.currentContextName )
        self.variableView.resizeColumnsToContents()
        self.shutterTableModel.setShutterdict( self.currentContext.shutters )
        self.triggerTableModel.setTriggerdict(self.currentContext.triggers)
        self.counterTableModel.setCounterdict(self.currentContext.counters)
        self.writeRamCheckbox.setChecked(self.currentContext.writeRam)

    def documentationString(self):
        messages = [ "PulseProgram {0}".format( self.configParams.lastLoadFilename ) ]
        r = "\n".join(messages)
        return "\n".join( [r, self.pulseProgram.currentVariablesText()])      
    
    def description(self):
        desc = dict()
        desc["PulseProgram"] =  self.configParams.lastLoadFilename
        desc.update( self.pulseProgram.variables() )
        return desc
               
    def onFilenameChange(self, name ):
        name = str(name)
        if name in self.configParams.recentFiles and self.configParams.recentFiles[name]!=self.currentContext.pulseProgramFile:
            self.adaptiveLoadFile(self.configParams.recentFiles[name])
            if str(self.filenameComboBox.currentText())!=name:
                with BlockSignals(self.filenameComboBox) as w:
                    w.setCurrentIndex( self.filenameComboBox.findText( name ))
        self.updateSaveStatus()

    def onRamFilenameChange(self, name ):
        name = str(name)
        if name in self.configParams.recentRamFiles and self.configParams.recentRamFiles[name]!=self.currentContext.ramFile:
            self.loadRamFile(self.configParams.recentRamFiles[name])
            if str(self.ramFilenameComboBox.currentText())!=name:
                with BlockSignals(self.ramFilenameComboBox) as w:
                    w.setCurrentIndex( self.ramFilenameComboBox.findText( name ))
        self.updateSaveStatus()
        
    def onOk(self):
        pass
    
    def onLoadRamFile(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, 'Open RAM file', getProject().configDir, filter='*.yml'))
        if path:
            self.loadRamFile(path)

    @QtCore.pyqtProperty(list)
    def ramData(self):
        return self.loadRamData(filename=self.currentContext.ramFile)

    @QtCore.pyqtProperty(bool)
    def writeRam(self):
        return self.currentContext.writeRam

    @file_data_cache(maxsize=3)
    def loadRamData(self, filename=''):
        """load in the data from a RAM file"""
        with open(filename, 'r') as f:
            yamldata = yaml.load(f)
        return [self.pulseProgram.convertParameter(magnitude.mg(float(ramValue['value']), ramValue['unit']), ramValue['encoding']) for ramValue in yamldata]

    def loadRamFile(self, path):
        if path and os.path.exists(path):
            self.currentContext.ramFile = path
            filename = os.path.basename(path)
            if filename not in self.configParams.recentRamFiles:
                self.ramFilenameComboBox.addItem(filename)
            self.configParams.recentRamFiles[filename]=path
            with BlockSignals(self.ramFilenameComboBox) as w:
                w.setCurrentIndex( self.ramFilenameComboBox.findText(filename))
            self.updateSaveStatus()
        else:
            self.currentContext.ramFile = ''
            with BlockSignals(self.ramFilenameComboBox) as w:
                w.setCurrentIndex( self.ramFilenameComboBox.findText(''))

    def onWriteRamCheckbox(self):
        self.currentContext.writeRam = self.writeRamCheckbox.isChecked()
        self.updateSaveStatus()

    def onRemoveCurrentRamFile(self):
        text = str(self.ramFilenameComboBox.currentText())
        if text in self.configParams.recentRamFiles:
            self.configParams.recentRamFiles.pop(text)
        self.ramFilenameComboBox.removeItem(self.ramFilenameComboBox.currentIndex())
        self.currentContext.ramFile = ''
        self.updateSaveStatus()

    def onLoad(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self, 'Open Pulse Programmer file',getProject().configDir))
        if path!="":
            self.adaptiveLoadFile(path)
        self.updateSaveStatus()
        
    def adaptiveLoadFile(self, path):
        if path:
            _, ext = os.path.splitext(path)
            self.currentContext.pulseProgramFile = path
            if ext==".ppp":
                self.currentContext.pulseProgramMode = 'ppp'
                self.loadpppFile(path)
            else:
                self.currentContext.pulseProgramMode = 'pp'
                self.updatepppDisplay()
                self.loadppFile(path)            
            self.configParams.lastLoadFilename = path
            
    def onReset(self):
        if self.configParams.lastLoadFilename is not None:
            self.variabledict = VariableDictionary( self.pulseProgram.variabledict, self.parameterdict )
            self.adaptiveLoadFile(self.configParams.lastLoadFilename)
    
    def loadpppFile(self, path):
        self.pppSourcePath = path
        _, self.pppSourceFile = os.path.split(path)
        with open(path,"r") as f:
            self.pppSource = f.read()
        self.updatepppDisplay()
        ppFilename = getPpFileName(path)
        if self.compileppp(ppFilename):
            self.loadppFile(ppFilename, cache=False)
        filename = os.path.basename(path)
        if filename not in self.configParams.recentFiles:
            self.filenameComboBox.addItem(filename)
        self.configParams.recentFiles[filename]=path
        with BlockSignals(self.filenameComboBox) as w:
            w.setCurrentIndex( self.filenameComboBox.findText(filename))

    def saveppp(self, path):
        if self.pppSource and path:
            with open(path,'w') as f:
                f.write( self.pppSource )

    def compileppp(self, savefilename):
        self.pppSource = self.pppSource.expandtabs(4)
        success = False
        try:
            compiler = pppCompiler()
            ppCode = compiler.compileString( self.pppSource )
            self.pppReverseLineLookup = compiler.reverseLineLookup
            self.pppCompileException = None
            with open(savefilename,"w") as f:
                f.write(ppCode)
            success = True
            self.pppCodeEdits[self.pppSourceFile].clearHighlightError()
        except CompileException as e:
            self.pppCodeEdits[self.pppSourceFile].highlightError( e.message(), e.lineno(), col=e.col())
        except ParseException as e:
            e.__class__ = CompileException  # cast to CompileException. Is possible because CompileException does ONLY add behavior
            self.pppCodeEdits[self.pppSourceFile].highlightError( e.message(), e.lineno(), col=e.col())
        return success
    
    def loadppFile(self, path, cache=True):
        self.pulseProgram.loadSource(path, docompile=False)
        self.updateppDisplay()
        try:
            self.pulseProgram.compileCode()
        except PulseProgram.ppexception as compileexception:
            self.sourceCodeEdits[ compileexception.file ].highlightError(str(compileexception), compileexception.line, compileexception.context )
        if cache:
            filename = os.path.basename(path)
            if filename not in self.configParams.recentFiles:
                self.filenameComboBox.addItem(filename)
            self.configParams.recentFiles[filename]=path
            self.filenameComboBox.setCurrentIndex( self.filenameComboBox.findText(filename))
        self.currentContext.merge( self.pulseProgram.variabledict )
        self.updateDisplayContext()
        self.pulseProgramChanged.emit()

    def onRemoveCurrent(self):
        text = str(self.filenameComboBox.currentText())
        if text in self.configParams.recentFiles:
            self.configParams.recentFiles.pop(text)
        self.filenameComboBox.removeItem(self.filenameComboBox.currentIndex())

    def onSave(self):
        self.onApply()
        if self.currentContext.pulseProgramMode=='pp':
            self.pulseProgram.saveSource()
        else:
            self.saveppp(self.pppSourcePath)
    
    def onApply(self):
        if self.currentContext.pulseProgramMode=='pp':
            try:
                positionCache = dict()
                for name, textEdit in self.sourceCodeEdits.iteritems():
                    self.pulseProgram.source[name] = str(textEdit.toPlainText())
                    positionCache[name] = ( textEdit.textEdit.cursorPosition(),
                                            textEdit.textEdit.scrollPosition() )
                self.pulseProgram.loadFromMemory()
                self.updateppDisplay()
                for name, textEdit in self.sourceCodeEdits.iteritems():
                    textEdit.clearHighlightError()
                    if name in positionCache:
                        cursorpos, scrollpos = positionCache[name]
                        textEdit.textEdit.setCursorPosition( *cursorpos )
                        textEdit.textEdit.setScrollPosition( scrollpos )
            except PulseProgram.ppexception as ppex:
                textEdit = self.sourceCodeEdits[ ppex.file ].highlightError(str(ppex), ppex.line, ppex.context )
        else:
            positionCache = dict()
            for name, textEdit in self.pppCodeEdits.iteritems():
                self.pppSource = str(textEdit.toPlainText())
                positionCache[name] = ( textEdit.textEdit.cursorPosition(),
                                        textEdit.textEdit.scrollPosition() )
            ppFilename = getPpFileName( self.pppSourcePath )
            if self.compileppp(ppFilename):
                self.loadppFile(ppFilename, cache=False)
                for name, textEdit in self.pppCodeEdits.iteritems():
                    textEdit.clearHighlightError()
                    if name in positionCache:
                        cursorpos, scrollpos = positionCache[name]
                        textEdit.textEdit.setCursorPosition( *cursorpos )
                        textEdit.textEdit.setScrollPosition( scrollpos )
            
                    
    def onAccept(self):
        self.saveConfig()
    
    def onReject(self):
        pass
        
    def saveConfig(self):
        """Save the pulse program configuration state"""
        self.configParams.lastContextName = str(self.contextComboBox.currentText())
        self.config[self.configname+".state"] = self.saveState() #Arrangement of dock widgets
        self.config[self.configname+".splitter"] = self.splitter.saveState() #triggers/shutters/counters splitter position
        saveDockWidgetSizes(self, self.config, self.configname)
        self.config[self.configname] = self.configParams
        self.config[self.configname+'.contextdict'] = self.contextDict 
        self.config[self.configname+'.currentContext'] = self.currentContext
        self.variableTableModel.saveConfig()
       
    def getPulseProgramBinary(self,parameters=dict(),override=dict()):
        # need to update variables self.pulseProgram.updateVariables( self.)
        substitutes = dict( self.currentContext.parameters.valueView.iteritems() )
        for model in [self.shutterTableModel, self.triggerTableModel, self.counterTableModel]:
            substitutes.update( model.getVariables() )
        substitutes.update(override)
        self.pulseProgram.updateVariables(substitutes)
        return self.pulseProgram.toBinary()
    
    def exitcode(self, number):
        return self.pulseProgram.exitcode(number)
        
    def getVariableValue(self,name):
        return self.variableTableModel.getVariableValue(name)
    
    def variableScanCode(self, variablename, values, extendedReturn=False):
        tempparameters = copy.deepcopy( self.currentContext.parameters )
        updatecode = list()
        numVariablesPerUpdate = 0
        for currentval in values:
            upd_names, upd_values = tempparameters.setValue(variablename, currentval)
            numVariablesPerUpdate = len(upd_names)
            upd_names.append( variablename )
            upd_values.append( currentval )
            updatecode.extend( self.pulseProgram.multiVariableUpdateCode( upd_names, upd_values ) )
            logging.getLogger(__name__).info("{0}: {1}".format(upd_names, upd_values))
        if extendedReturn:
            return updatecode, numVariablesPerUpdate
        return updatecode

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
        
    def onBold(self, key):
        indexes = self.variableView.selectedIndexes()
        for index in indexes:
            self.variableTableModel.toggleBold( index )
    
    def lineOfInstruction(self, binaryelement ):
        ppline = self.pulseProgram.lineOfInstruction(binaryelement)
        pppline = self.pppReverseLineLookup.get(ppline,None) if hasattr(self, 'pppReverseLineLookup') else None
        return ppline, pppline

    def setTimingViolations(self, linelist):
        edit = self.pppCodeEdits.get(self.pppSourceFile)
        if edit:
            edit.highlightTimingViolation( [l[1]-1 for l in linelist] )

class PulseProgramSetUi(QtGui.QDialog):
    class Parameters:
        pass
    
    def __init__(self,config, channelNameData):
        super(PulseProgramSetUi,self).__init__()
        self.config = config
        self.configname = 'PulseProgramSetUi'
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
        self.config[self.configname+'.pos'] = self.pos()
        self.config[self.configname+'.size'] = self.size()
        self.hide()
        self.recipient.onSettingsApply()  
        for page in self.pulseProgramSet.values():
            page.onAccept()
        
    def reject(self):
        self.config[self.configname+'.pos'] = self.pos()
        self.config[self.configname+'.size'] = self.size()
        self.hide()
        for page in self.pulseProgramSet.values():
            page.onAccept()
        
    def show(self):
        if self.configname+'.pos' in self.config:
            self.move(self.config[self.configname+'.pos'])
        if self.configname+'.size' in self.config:
            self.resize(self.config[self.configname+'.size'])
        for page in self.pulseProgramSet.values():
            page.restoreLayout()
        QtGui.QDialog.show(self)
        self.isShown = True
        
    def saveConfig(self):
        self.config[self.configname+'.pos'] = self.pos()
        self.config[self.configname+'.size'] = self.size()
        self.config[self.configname+'.isVisible'] = self.isVisible()
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
