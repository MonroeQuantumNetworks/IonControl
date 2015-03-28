# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import copy
import functools
import logging

from PyQt4 import QtCore, QtGui
import PyQt4.uic

import ScanList
from gateSequence import GateSequenceUi
from modules import MagnitudeUtilit, DataDirectory
from modules.PyqtUtility import BlockSignals
from modules.PyqtUtility import updateComboBoxItems
from modules.Utility import unique
from modules.enum import enum 
from modules.magnitude import MagnitudeError
from modules.ScanDefinition import ScanSegmentDefinition
from ScanSegmentTableModel import ScanSegmentTableModel
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate 
from modules.function_base import linspace
from modules.concatenate_iter import concatenate_iter
import random
from modules.concatenate_iter import interleave_iter
from gateSequence.GateSequenceContainer import GateSequenceException
from modules.firstNotNone import firstNotNone
import xml.etree.ElementTree as ElementTree
from modules.XmlUtilit import prettify, xmlEncodeAttributes, xmlParseAttributes

ScanControlForm, ScanControlBase = PyQt4.uic.loadUiType(r'ui\ScanControlUi.ui')


class Scan:
    ScanMode = enum('ParameterScan','StepInPlace','GateSequenceScan','Freerunning')
    ScanType = enum('LinearStartToStop','LinearStopToStart','Randomized','CenterOut')
    ScanRepeat = enum('SingleScan','RepeatedScan')
    def __init__(self):
        # Scan
        self.scanParameter = None
        self.scanTarget = None
        self.start = 0
        self.stop = 0
        self.center = 0
        self.span = 0
        self.steps = 0
        self.stepSize = 1
        self.stepsSelect = 0
        self.scantype = 0
        self.scanMode = 0
        self.scanRepeat = 0
        self.filename = ""
        self.histogramFilename = ""
        self.autoSave = False
        self.histogramSave = False
        self.xUnit = ""
        self.xExpression = ""
        self.loadPP = False
        self.loadPPName = ""
        self.saveRawData = False
        self.rawFilename = ""
        # GateSequence Settings
        self.gateSequenceSettings = GateSequenceUi.Settings()
        self.scanSegmentList = [ScanSegmentDefinition()]
        
    def __setstate__(self, state):
        """this function ensures that the given fields are present in the class object
        after unpickling. Only new class attributes need to be added here.
        """
        self.__dict__ = state
        self.__dict__.setdefault('xUnit', '')
        self.__dict__.setdefault('xExpression', '')
        self.__dict__.setdefault('scanRepeat', 0)
        self.__dict__.setdefault('loadPP', False)
        self.__dict__.setdefault('loadPPName', "")
        self.__dict__.setdefault('stepSize',1)
        self.__dict__.setdefault('center',0)
        self.__dict__.setdefault('span',0)
        self.__dict__.setdefault('gateSequenceSettings',GateSequenceUi.Settings())
        self.__dict__.setdefault('scanSegmentList',[ScanSegmentDefinition()])
        self.__dict__.setdefault('externalScanParameter', None)
        self.__dict__.setdefault('histogramFilename', "")
        self.__dict__.setdefault('histogramSave', False)
        self.__dict__.setdefault('scanTarget', None)
        self.__dict__.setdefault('saveRawData', False)
        self.__dict__.setdefault('rawFilename', "")

    def __eq__(self,other):
        try:
            equal = tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)
        except MagnitudeError:
            equal = False
        return equal

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))
        
    stateFields = ['scanParameter', 'scanTarget', 'scantype', 'scanMode', 'scanRepeat', 
                'filename', 'histogramFilename', 'autoSave', 'histogramSave', 'xUnit', 'xExpression', 'loadPP', 'loadPPName', 'gateSequenceSettings',
                'scanSegmentList', 'saveRawData', 'rawFilename' ]

    documentationList = [ 'scanParameter', 'scanTarget', 'scantype', 'scanMode', 'scanRepeat', 
                'xUnit', 'xExpression', 'loadPP', 'loadPPName' ]
        
    def exportXml(self, element, attrib=dict()):
        myElement = ElementTree.SubElement(element, "Scan", attrib=attrib )
        xmlEncodeAttributes(self.__dict__, myElement)
        self.gateSequenceSettings.exportXml(myElement)
        for segment in self.scanSegmentList:
            segment.exportXml(myElement)
        return myElement
    
    @staticmethod
    def fromXmlElement(element):
        s = Scan()
        s.__dict__.update( xmlParseAttributes(element) )
        s.gateSequenceSettings = GateSequenceUi.Settings.fromXmlElement( element )
        s.scanSegmentList = [ ScanSegmentDefinition.fromXmlElement(e) for e in element.findall(ScanSegmentDefinition.XMLTagName)]
        return s    

    def documentationString(self):
        r = "\r\n".join( [ "{0}\t{1}".format(field,getattr(self,field)) for field in self.documentationList] )
        r += self.gateSequenceSettings.documentationString()
        return r
    
    def description(self):
        desc = dict( ((field,getattr(self,field)) for field in self.documentationList) )
        return desc
    
    def evaluate(self, globalDictionary ):
        return any( [segment.evaluate(globalDictionary) for segment in self.scanSegmentList ] )            


class ScanControlParameters:
    def __init__(self):
        self.autoSave = False
        self.currentScanTarget = None
        self.scanTargetCache = dict()
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault( 'currentScanTarget', None )
        self.__dict__.setdefault( 'scanTargetCache', dict() )
        if self.scanTargetCache is None:
            self.scanTargetCache = dict()

class ScanControl(ScanControlForm, ScanControlBase ):
    ScanModes = enum('SingleScan','RepeatedScan','StepInPlace','GateSequenceScan')
    currentScanChanged = QtCore.pyqtSignal( object )
    integrationMode = enum('IntegrateAll','IntegrateRun','NoIntegration')
    scanConfigurationListChanged = QtCore.pyqtSignal( object )
    logger = logging.getLogger(__name__)
    def __init__(self, config, globalVariablesUi, parentname, plotnames=None, parent=None, analysisNames=None):
        logger = logging.getLogger(__name__)
        ScanControlForm.__init__(self)
        ScanControlBase.__init__(self,parent)
        self.config = config
        self.configname = 'ScanControl.'+parentname
        self.globalDict = globalVariablesUi.variables
        # History and Dictionary
        try:
            self.settingsDict = self.config.get(self.configname+'.dict',dict())
        except (TypeError, AttributeError):
            logger.info( "Unable to read scan control settings dictionary. Setting to empty dictionary." )
            self.settingsDict = dict()
        self.scanConfigurationListChanged.emit( self.settingsDict )
        self.settingsHistory = list()
        self.settingsHistoryPointer = None
        self.historyFinalState = None
        try:
            self.settings = self.config.get(self.configname,Scan())
        except (TypeError, AttributeError):
            logger.info( "Unable to read scan control settings. Setting to new scan." )
            self.settings = Scan()
        self.gateSequenceUi = None
        self.settingsName = self.config.get(self.configname+'.settingsName',None)
        self.pulseProgramUi = None
        self.parameters = self.config.get( self.configname+'.parameters', ScanControlParameters() )
        self.globalVariablesUi = globalVariablesUi
        self.scanTargetDict = dict()
        
    def setupUi(self, parent):
        ScanControlForm.setupUi(self,parent)
        # History and Dictionary
        self.saveButton.clicked.connect( self.onSave )
        self.removeButton.clicked.connect( self.onRemove )
        self.reloadButton.clicked.connect( self.onReload )

        self.tableModel = ScanSegmentTableModel(self.checkSettingsSavable, self.globalVariablesUi.variables )
        self.tableView.setModel( self.tableModel )
        self.addSegmentButton.clicked.connect( self.onAddScanSegment )
        self.removeSegmentButton.clicked.connect( self.onRemoveScanSegment )
        self.magnitudeDelegate = MagnitudeSpinBoxDelegate(self.globalVariablesUi.variables)
        self.tableView.setItemDelegate( self.magnitudeDelegate )
        self.tableView.resizeRowsToContents()
               
#        try:
        self.setSettings( self.settings )
#         except AttributeError:
#             logger.error( "Ignoring exception" )
        self.comboBox.addItems( sorted(self.settingsDict.keys()))
        if self.settingsName and self.comboBox.findText(self.settingsName):
            self.comboBox.setCurrentIndex( self.comboBox.findText(self.settingsName) )
        self.comboBox.currentIndexChanged[QtCore.QString].connect( self.onLoad )
        self.comboBox.lineEdit().editingFinished.connect( self.checkSettingsSavable ) 
        # update connections
        self.comboBoxParameter.currentIndexChanged[QtCore.QString].connect( self.onCurrentTextChanged )
        self.scanTypeCombo.currentIndexChanged[int].connect( functools.partial(self.onCurrentIndexChanged,'scantype') )
        self.autoSaveCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'autoSave') )
        self.saveRawCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'saveRawData') )
        self.histogramSaveCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'histogramSave') )
        self.scanModeComboBox.currentIndexChanged[int].connect( self.onModeChanged )
        self.filenameEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.filenameEdit, 'filename') )
        self.rawFilenameEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.rawFilenameEdit, 'rawFilename') )
        self.histogramFilenameEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.histogramFilenameEdit, 'histogramFilename') )
        self.xUnitEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.xUnitEdit, 'xUnit') )
        self.xExprEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.xExprEdit, 'xExpression') )
        self.scanRepeatComboBox.currentIndexChanged[int].connect( functools.partial(self.onCurrentIndexChanged,'scanRepeat') )
        self.loadPPcheckBox.stateChanged.connect( functools.partial(self.onStateChanged, 'loadPP' ) )
        self.loadPPComboBox.currentIndexChanged[QtCore.QString].connect( self.onLoadPP )
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.autoSaveAction = QtGui.QAction( "auto save" , self)
        self.autoSaveAction.setCheckable(True)
        self.autoSaveAction.setChecked(self.parameters.autoSave )
        self.autoSaveAction.triggered.connect( self.onAutoSave )
        self.addAction( self.autoSaveAction )
        self.settings.evaluate(self.globalVariablesUi.variables)
        self.globalVariablesUi.valueChanged.connect( self.evaluate )
        self.comboBoxScanTarget.currentIndexChanged[QtCore.QString].connect( self.onChangeScanTarget )
        self.currentScanChanged.emit( self.settingsName )
        self.exportXmlButton.clicked.connect( self.onExportXml )

    def onExportXml(self):
        root = ElementTree.Element('ScanList')
        for name, setting in self.settingsDict.iteritems():
            setting.exportXml(root,{'name':name})
        with open(DataDirectory.DataDirectory().sequencefile("ScanList.xml")[0],'w') as f:
            f.write(prettify(root))
       
    def evaluate(self, name):
        if self.settings.evaluate( self.globalDict ):
            self.tableModel.update()
            self.tableView.viewport().repaint()
        
    def onAutoSave(self, checked):
        self.parameters.autoSave = checked
        if self.parameters.autoSave:
            self.onSave()     
        
    def onAddScanSegment(self):
        self.settings.scanSegmentList.append( ScanSegmentDefinition() )
        self.tableModel.setScanList(self.settings.scanSegmentList)
        
    def onRemoveScanSegment(self):
        for index in sorted(unique([ i.column() for i in self.tableView.selectedIndexes() ]),reverse=True):
            del self.settings.scanSegmentList[index]
            self.tableModel.setScanList(self.settings.scanSegmentList)
        
    def setSettings(self, settings):
        self.settings = copy.deepcopy(settings)
        if self.globalDict:
            self.settings.evaluate(self.globalDict)
        self.scanModeComboBox.setCurrentIndex( self.settings.scanMode )
        self.scanTypeCombo.setCurrentIndex(self.settings.scantype )
        self.autoSaveCheckBox.setChecked(self.settings.autoSave)
        self.saveRawCheckBox.setChecked(self.settings.saveRawData)
        self.histogramSaveCheckBox.setChecked(self.settings.histogramSave)
        if self.settings.scanTarget:
            self.settings.scanParameter = self.doChangeScanTarget(self.settings.scanTarget, self.settings.scanParameter)
        elif self.comboBoxScanTarget.count()>0:
            self.settings.scanTarget = self.comboBoxScanTarget.currentText()
            self.settings.scanParameter = self.doChangeScanTarget(self.settings.scanTarget, None)
        self.filenameEdit.setText( getattr(self.settings,'filename','') )
        self.rawFilenameEdit.setText( getattr(self.settings,'rawFilename','') )
        self.histogramFilenameEdit.setText( getattr(self.settings,'histogramFilename','') )
        self.scanTypeCombo.setEnabled(self.settings.scanMode in [0,1])
        self.xUnitEdit.setText( self.settings.xUnit )
        self.xExprEdit.setText( self.settings.xExpression )
        self.scanRepeatComboBox.setCurrentIndex( self.settings.scanRepeat )
        self.loadPPcheckBox.setChecked( self.settings.loadPP )
        if self.settings.loadPPName: 
            index = self.loadPPComboBox.findText(self.settings.loadPPName)
            if index>=0:
                self.loadPPComboBox.setCurrentIndex( index )
                self.onLoadPP(self.settings.loadPPName)
        self.onModeChanged(self.settings.scanMode)
        if self.gateSequenceUi:
            self.gateSequenceUi.setSettings( self.settings.gateSequenceSettings )
        self.checkSettingsSavable()
        self.tableModel.setScanList(self.settings.scanSegmentList)

    def checkSettingsSavable(self, savable=None):
        if not isinstance(savable, bool):
            currentText = str(self.comboBox.currentText())
            try:
                if currentText is None or currentText=="":
                    savable = False
                elif self.settingsName and self.settingsName in self.settingsDict:
                    savable = self.settingsDict[self.settingsName]!=self.settings or currentText!=self.settingsName
                else:
                    savable = True
                if self.parameters.autoSave and savable:
                    self.onSave()
                    savable = False
            except MagnitudeError:
                pass
        self.saveButton.setEnabled( savable )
            
    def onLoadPP(self, ppname):
        logger = logging.getLogger(__name__)
        self.settings.loadPPName = str(ppname)
        logger.debug( "ScanControl.onLoadPP {0} {1} {2}".format( self.settings.loadPP, bool(self.settings.loadPPName), self.settings.loadPPName ) )
        if self.settings.loadPP and self.settings.loadPPName and hasattr(self,"pulseProgramUi"):
            self.pulseProgramUi.loadContextByName( self.settings.loadPPName )
        self.checkSettingsSavable()
            
    def onRecentPPFilesChanged(self, namelist):
        updateComboBoxItems( self.loadPPComboBox, sorted( namelist ) )
        self.checkSettingsSavable()
        
    def setPulseProgramUi(self, pulseProgramUi ):
        logger = logging.getLogger(__name__)
        logger.debug( "ScanControl.setPulseProgramUi {0}".format(pulseProgramUi.configParams.recentFiles.keys()) )
        isStartup = self.pulseProgramUi is None
        self.pulseProgramUi = pulseProgramUi
        updateComboBoxItems(self.loadPPComboBox, sorted(pulseProgramUi.contextDict.keys()), self.settings.loadPPName)
        try:
            self.pulseProgramUi.contextDictChanged.connect( self.onRecentPPFilesChanged, QtCore.Qt.UniqueConnection )
        except TypeError:
            pass  # is raised if the connection already existed
            

        if not self.gateSequenceUi:
            self.gateSequenceUi = GateSequenceUi.GateSequenceUi()
            self.gateSequenceUi.valueChanged.connect( self.checkSettingsSavable )
            self.gateSequenceUi.postInit('test',self.config,self.pulseProgramUi.pulseProgram )
            self.gateSequenceUi.setupUi(self.gateSequenceUi)
            self.toolBox.addItem(self.gateSequenceUi,"Gate Sequences")
        if pulseProgramUi.currentContext.parameters:
            self.gateSequenceUi.setVariables( pulseProgramUi.currentContext.parameters )
        try:
            self.gateSequenceUi.setSettings( self.settings.gateSequenceSettings )
        except GateSequenceException as e:
            logger.exception(e)
        if isStartup:
            self.onLoadPP(self.settings.loadPPName)

    def onEditingFinished(self,edit,attribute):        
        setattr( self.settings, attribute, str(edit.text())  )        
        self.checkSettingsSavable()
                
    def onStateChanged(self, attribute, state):        
        setattr( self.settings, attribute, (state == QtCore.Qt.Checked)  )        
        self.checkSettingsSavable()
        
    def onCurrentTextChanged(self, text):        
        self.settings.scanParameter = str(text)        
        self.checkSettingsSavable()
    
    def onCurrentIndexChanged(self, attribute, index):        
        setattr( self.settings, attribute, index )        
        self.checkSettingsSavable()
        
    def onModeChanged(self, index):       
        self.settings.scanMode = index
        self.scanTypeCombo.setEnabled(index in [0,2])
        self.scanRepeatComboBox.setEnabled( index in [0,2] )
        self.xUnitEdit.setEnabled( index in [0,3] )
        self.xExprEdit.setEnabled( index in [0,3] )
        self.comboBoxParameter.setEnabled( index==0 )
        self.comboBoxScanTarget.setEnabled( index==0 )    
        self.tableView.setEnabled( index==0 )           
        self.checkSettingsSavable()
    
    def onValueChanged(self, attribute, value):        
        setattr( self.settings, attribute, MagnitudeUtilit.mg(value) )        
        self.checkSettingsSavable()

    def onBareValueChanged(self, attribute, value):        
        setattr( self.settings, attribute, value )        
        self.checkSettingsSavable()
              
    def onIntValueChanged(self, attribute, value):       
        setattr( self.settings, attribute, value )        
        self.checkSettingsSavable()
        
    def setVariables(self, variabledict):
        self.updateScanTarget('Internal', [var.name for var in sorted(variabledict.values()) if var.type=='parameter'])
        self.variabledict = variabledict
        if self.settings.scanParameter:
            self.comboBoxParameter.setCurrentIndex(self.comboBoxParameter.findText(self.settings.scanParameter) )
        elif self.comboBoxParameter.count()>0:  # if scanParameter is None set it to the current selection
            self.settings.scanParameter = str(self.comboBoxParameter.currentText())
        if self.gateSequenceUi:
            self.gateSequenceUi.setVariables(variabledict)
        self.checkSettingsSavable()
            
    def updateScanTarget(self, target, scannames):
        self.scanTargetDict[target] = scannames
        updateComboBoxItems( self.comboBoxScanTarget, self.scanTargetDict.keys(), self.parameters.currentScanTarget )
        self.parameters.currentScanTarget = firstNotNone(self.parameters.currentScanTarget, target)
        if target==self.parameters.currentScanTarget:
            self.settings.scanParameter = str(updateComboBoxItems( self.comboBoxParameter, sorted(scannames), self.settings.scanParameter ))

    def onChangeScanTarget(self, name):
        """ called on currentIndexChanged[QString] signal of ComboBox"""
        name = str(name)
        if name!=self.parameters.currentScanTarget:
            self.parameters.scanTargetCache[self.parameters.currentScanTarget] = self.settings.scanParameter
            cachedParam = self.parameters.scanTargetCache.get(name)
            cachedParam = updateComboBoxItems( self.comboBoxParameter, sorted(self.scanTargetDict[name]), cachedParam )
            self.settings.scanParameter = cachedParam
            self.settings.scanTarget = name
            self.parameters.currentScanTarget = name
        self.checkSettingsSavable()

    def doChangeScanTarget(self, name, scanParameter):
        """ Change the scan target as part of loading a parameter set,
        we know the ScanParameter to select and want it either selected or added as red item """
        name = str(name)
        if name!=self.parameters.currentScanTarget:
            with BlockSignals(self.comboBoxScanTarget):
                self.comboBoxScanTarget.setCurrentIndex( self.comboBoxScanTarget.findText(name) )
            scanParameter = updateComboBoxItems( self.comboBoxParameter, sorted(self.scanTargetDict[name]), scanParameter )
            self.settings.scanTarget = name
            self.parameters.currentScanTarget = name
        else:
            self.comboBoxParameter.setCurrentIndex( self.comboBoxParameter.findText(scanParameter) )
        self.checkSettingsSavable()
        return scanParameter
                
    def getScan(self):
        scan = copy.deepcopy(self.settings)
        if scan.scanMode!=0:
            scan.scanTarget = 'Internal'
        scan.scanTarget = str(scan.scanTarget)
        scan.type = [ ScanList.ScanType.LinearUp, ScanList.ScanType.LinearDown, ScanList.ScanType.Randomized, ScanList.ScanType.CenterOut][self.settings.scantype]
        
        if scan.scanMode==Scan.ScanMode.Freerunning:
            scan.list = None
        else:
            scan.list = list( concatenate_iter( *[ linspace(segment.start, segment.stop, segment.steps) for segment in scan.scanSegmentList ] ) )
            if scan.type==0:
                scan.list = sorted( scan.list )
                scan.start = scan.list[0]
                scan.stop = scan.list[-1]
            elif scan.type==1:
                scan.list = sorted( scan.list, reverse=True )
                scan.start = scan.list[-1]
                scan.stop = scan.list[0]
            elif scan.type==2:
                scan.list = sorted( scan.list )
                scan.start = scan.list[0]
                scan.stop = scan.list[-1]
                random.shuffle( scan.list )
            elif scan.type==3:        
                scan.list = sorted( scan.list )
                center = len(scan.list)/2
                scan.list = list( interleave_iter(scan.list[center:],reversed(scan.list[:center])) )
            
        scan.gateSequenceUi = self.gateSequenceUi
        scan.settingsName = self.settingsName
        return scan
        
    def saveConfig(self):
        self.config[self.configname] = self.settings
        self.config[self.configname+'.dict'] = self.settingsDict
        self.config[self.configname+'.settingsName'] = self.settingsName
        self.config[self.configname+'.parameters'] = self.parameters

    def onSave(self):
        self.settingsName = str(self.comboBox.currentText())
        if self.settingsName != '':
            if self.settingsName not in self.settingsDict:
                if self.comboBox.findText(self.settingsName)==-1:
                    self.comboBox.addItem(self.settingsName)
            self.settingsDict[self.settingsName] = copy.deepcopy(self.settings)
            self.scanConfigurationListChanged.emit( self.settingsDict )
        self.checkSettingsSavable(savable=False)
        self.currentScanChanged.emit( self.settingsName )

    def onRemove(self):
        name = str(self.comboBox.currentText())
        if name != '':
            if name in self.settingsDict:
                self.settingsDict.pop(name)
            idx = self.comboBox.findText(name)
            if idx>=0:
                self.comboBox.removeItem(idx)
            self.scanConfigurationListChanged.emit( self.settingsDict )
       
    def onLoad(self,name):
        self.settingsName = str(name)
        if self.settingsName !='' and self.settingsName in self.settingsDict:
            self.setSettings(self.settingsDict[self.settingsName])
        self.checkSettingsSavable()
        self.currentScanChanged.emit( self.settingsName )

    def loadSetting(self, name):
        if name and self.comboBox.findText(name)>=0:
            self.comboBox.setCurrentIndex( self.comboBox.findText(name) )  
            self.onLoad(name)      

    def onReload(self):
        self.onLoad( self.comboBox.currentText() )
   
    def documentationString(self):
        return self.settings.documentationString()
    
    def editEvaluationTable(self, index):
        if index.column() in [0,1,2,4]:
            self.evalTableView.edit(index)
            

if __name__=="__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = ScanControl(config,"parent")
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
        