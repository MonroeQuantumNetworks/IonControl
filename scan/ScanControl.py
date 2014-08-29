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

import CountEvaluation
from EvaluationTableModel import EvaluationTableModel
import ScanList
from gateSequence import GateSequenceUi
from modules import MagnitudeUtilit
from modules.HashableDict import HashableDict
from modules.PyqtUtility import BlockSignals
from modules.PyqtUtility import updateComboBoxItems
from modules.Utility import unique
from modules.enum import enum
from modules.magnitude import mg, MagnitudeError
from uiModules.ComboBoxDelegate import ComboBoxDelegate
from modules.ScanDefinition import ScanSegmentDefinition
from ScanSegmentTableModel import ScanSegmentTableModel
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate 
import numpy
from modules.concatenate_iter import concatenate_iter
import random
from modules.concatenate_iter import interleave_iter

ScanControlForm, ScanControlBase = PyQt4.uic.loadUiType(r'ui\ScanControlUi.ui')


class EvaluationDefinition:
    def __init__(self):
        self.counter = None
        self.evaluation = None
        self.settings = HashableDict()
        self.name = None
        self.plotname = None
        self.settingsCache = HashableDict()
        self.showHistogram = False
        self.analysis = None
        
    def __setstate__(self, state):
        self.__dict__ = state
        if 'errorBars' in self.settings:   # remove errorBars property in old unpickled instances
            self.settings.pop('errorBars')
        self.__dict__.setdefault( 'analysis', None )
        
    stateFields = ['counter', 'evaluation', 'settings', 'settingsCache', 'name', 'plotname', 'showHistogram', 'analysis'] 
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        if not isinstance(self.settings,HashableDict):
            logging.getLogger(__name__).info("Replacing dict with hashable dict")
            self.settings = HashableDict(self.settings)
        return hash(tuple(getattr(self,field) for field in self.stateFields))
 

class Scan:
    ScanMode = enum('ParameterScan','StepInPlace','GateSequenceScan','CenterOut')
    ScanType = enum('LinearStartToStop','LinearStopToStart','Randomized')
    ScanRepeat = enum('SingleScan','RepeatedScan')
    def __init__(self):
        # Scan
        self.scanParameter = None
        self.externalScanParameter = None
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
        # Evaluation
        self.histogramBins = 50
        self.integrateHistogram = False
        self.counterChannel = 0
        self.evalList = list()
        # Timestamps
        self.enableTimestamps = False
        self.binwidth =  mg(1,'us')
        self.roiStart =  mg(0,'us')
        self.roiWidth =  mg(1,'ms')
        self.integrateTimestamps = 0
        self.timestampsChannel = 0
        self.saveRawData = False
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
        self.__dict__.setdefault('evalList',list())
        self.__dict__.setdefault('scanSegmentList',[ScanSegmentDefinition()])
        self.__dict__.setdefault('externalScanParameter', None)
        self.__dict__.setdefault('histogramFilename', "")
        self.__dict__.setdefault('histogramSave', False)
#         if self.histogramFilename is None:
#             self.histogramFilename = ""

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
        
    stateFields = ['scanParameter', 'externalScanParameter', 'scantype', 'scanMode', 'scanRepeat', 
                'filename', 'histogramFilename', 'autoSave', 'histogramSave', 'xUnit', 'xExpression', 'loadPP', 'loadPPName', 'histogramBins', 'integrateHistogram', 
                'enableTimestamps', 'binwidth', 'roiStart', 'roiWidth', 'integrateTimestamps', 'timestampsChannel', 'saveRawData', 'gateSequenceSettings',
                'evalList', 'scanSegmentList' ]

    documentationList = [ 'scanParameter', 'externalScanParameter', 'scantype', 'scanMode', 'scanRepeat', 
                'xUnit', 'xExpression', 'loadPP', 'loadPPName' ]
        
    def documentationString(self):
        r = "\r\n".join( [ "{0}\t{1}".format(field,getattr(self,field)) for field in self.documentationList] )
        r += self.gateSequenceSettings.documentationString()
        return r
    
    def description(self):
        desc = dict( ((field,getattr(self,field)) for field in self.documentationList) )
        return desc


class ScanControlParameters:
    def __init__(self):
        self.autoSave = False

class ScanControl(ScanControlForm, ScanControlBase ):
    ScanModes = enum('SingleScan','RepeatedScan','StepInPlace','GateSequenceScan')
    integrationMode = enum('IntegrateAll','IntegrateRun','NoIntegration')
    scanConfigurationListChanged = QtCore.pyqtSignal( object )
    logger = logging.getLogger(__name__)
    def __init__(self,config,parentname, plotnames=None, parent=None, analysisNames=None, internalParam=True, externalParam=False):
        logger = logging.getLogger(__name__)
        ScanControlForm.__init__(self)
        ScanControlBase.__init__(self,parent)
        self.config = config
        self.configname = 'ScanControl.'+parentname
        # History and Dictionary
        try:
            self.settingsDict = self.config.get(self.configname+'.dict',dict())
        except TypeError:
            logger.info( "Unable to read scan control settings dictionary. Setting to empty dictionary." )
            self.settingsDict = dict()
        self.scanConfigurationListChanged.emit( self.settingsDict )
        self.settingsHistory = list()
        self.settingsHistoryPointer = None
        self.historyFinalState = None
        try:
            self.settings = self.config.get(self.configname,Scan())
        except TypeError:
            logger.info( "Unable to read scan control settings. Setting to new scan." )
            self.settings = Scan()
        self.gateSequenceUi = None
        self.settingsName = self.config.get(self.configname+'.settingsName',None)
        self.evalAlgorithmList = list()
        self.plotnames = plotnames
        self.analysisNames = analysisNames
        self.pulseProgramUi = None
        self.parameters = self.config.get( self.configname+'.parameters', ScanControlParameters() )
        self.internalParam = internalParam
        self.externalParam = externalParam
        
    def setupUi(self, parent):
        logger = logging.getLogger(__name__)
        ScanControlForm.setupUi(self,parent)
        # History and Dictionary
        self.saveButton.clicked.connect( self.onSave )
        self.undoButton.clicked.connect( self.onUndo )
        self.redoButton.clicked.connect( self.onRedo )
        self.removeButton.clicked.connect( self.onRemove )
        self.reloadButton.clicked.connect( self.onReload )
        self.evalTableModel = EvaluationTableModel( self.updateSaveStatus, plotnames=self.plotnames, analysisNames=self.analysisNames )
        self.evalTableModel.dataChanged.connect( self.updateSaveStatus )
        self.evalTableModel.dataChanged.connect( self.onActiveEvalChanged )
        self.evalTableView.setModel( self.evalTableModel )
        self.evalTableView.clicked.connect( self.editEvaluationTable )
        self.delegate = ComboBoxDelegate()
        self.evalTableView.setItemDelegateForColumn(1, self.delegate )
        self.evalTableView.setItemDelegateForColumn(4, self.delegate )
        self.evalTableView.setItemDelegateForColumn(5, self.delegate )        
        self.addEvaluationButton.clicked.connect( self.onAddEvaluation )
        self.removeEvaluationButton.clicked.connect( self.onRemoveEvaluation )
        self.evalTableView.selectionModel().currentChanged.connect( self.onActiveEvalChanged )
        self.evalTableView.resizeColumnsToContents()

        self.tableModel = ScanSegmentTableModel(self.updateSaveStatus)
        self.tableView.setModel( self.tableModel )
        self.addSegmentButton.clicked.connect( self.onAddScanSegment )
        self.removeSegmentButton.clicked.connect( self.onRemoveScanSegment )
        self.magnitudeDelegate = MagnitudeSpinBoxDelegate()
        self.tableView.setItemDelegate( self.magnitudeDelegate )
        self.tableView.resizeRowsToContents()
        
        self.comboBoxParameter.setVisible( self.internalParam )
        self.comboBoxExternalParameter.setVisible( self.externalParam )
       
        try:
            self.setSettings( self.settings )
        except AttributeError as e:
            logger.error( "Ignoring exception" )
        self.comboBox.addItems( sorted(self.settingsDict.keys()))
        if self.settingsName and self.comboBox.findText(self.settingsName):
            self.comboBox.setCurrentIndex( self.comboBox.findText(self.settingsName) )
        self.comboBox.currentIndexChanged['QString'].connect( self.onLoad )
        #self.comboBox.editTextChanged.connect( lambda x: self.updateSaveStatus() )
        self.comboBox.lineEdit().editingFinished.connect( self.updateSaveStatus ) 
        # update connections
        self.comboBoxParameter.currentIndexChanged['QString'].connect( self.onCurrentTextChanged )
        self.comboBoxExternalParameter.currentIndexChanged['QString'].connect( self.onCurrentExternalTextChanged )
        self.scanTypeCombo.currentIndexChanged[int].connect( functools.partial(self.onCurrentIndexChanged,'scantype') )
        self.autoSaveCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'autoSave') )
        self.histogramSaveCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'histogramSave') )
        self.scanModeComboBox.currentIndexChanged[int].connect( self.onModeChanged )
        self.filenameEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.filenameEdit, 'filename') )
        self.histogramFilenameEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.histogramFilenameEdit, 'histogramFilename') )
        self.xUnitEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.xUnitEdit, 'xUnit') )
        self.xExprEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.xExprEdit, 'xExpression') )
        self.scanRepeatComboBox.currentIndexChanged[int].connect( functools.partial(self.onCurrentIndexChanged,'scanRepeat') )
        # Evaluation
        self.histogramBinsBox.valueChanged.connect(self.onHistogramBinsChanged)
        self.integrateHistogramCheckBox.stateChanged.connect( self.onIntegrateHistogramClicked )
                
        # Timestamps
        self.binwidthSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'binwidth') )
        self.roiStartSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'roiStart') )
        self.roiWidthSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'roiWidth') )
        self.enableCheckBox.stateChanged.connect( functools.partial(self.onStateChanged, 'enableTimestamps' ) )
        self.saveRawDataCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'saveRawData' ) )
        self.integrateCombo.currentIndexChanged[int].connect( self.onIntegrationChanged )
        self.channelSpinBox.valueChanged.connect( functools.partial(self.onBareValueChanged, 'timestampsChannel') )
        self.loadPPcheckBox.stateChanged.connect( functools.partial(self.onStateChanged, 'loadPP' ) )
        self.loadPPComboBox.currentIndexChanged['QString'].connect( self.onLoadPP )
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.autoSaveAction = QtGui.QAction( "auto save" , self)
        self.autoSaveAction.setCheckable(True)
        self.autoSaveAction.setChecked(self.parameters.autoSave )
        self.autoSaveAction.triggered.connect( self.onAutoSave )
        self.addAction( self.autoSaveAction )
        
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
        
    def setAnalysisNames(self, names):
        self.evalTableModel.setAnalysisNames(names)
        
    def setSettings(self, settings):
        self.settings = copy.deepcopy(settings)
        self.scanModeComboBox.setCurrentIndex( self.settings.scanMode )
        self.scanTypeCombo.setCurrentIndex(self.settings.scantype )
        self.autoSaveCheckBox.setChecked(self.settings.autoSave)
        self.histogramSaveCheckBox.setChecked(self.settings.histogramSave)
        if self.settings.scanParameter: 
            self.comboBoxParameter.setCurrentIndex( self.comboBoxParameter.findText(self.settings.scanParameter))
        elif self.comboBoxParameter.count()>0:  # if scanParameter is None set it to the current selection
            self.settings.scanParameter = self.comboBoxParameter.currentText()
        if self.settings.externalScanParameter: 
            self.comboBoxExternalParameter.setCurrentIndex( self.comboBoxExternalParameter.findText(self.settings.externalScanParameter))
        elif self.comboBoxExternalParameter.count()>0:  # if scanParameter is None set it to the current selection
            self.settings.externalScanParameter = self.comboBoxExternalParameter.currentText()
        self.filenameEdit.setText( getattr(self.settings,'filename','') )
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
        # Evaluation
        self.histogramBinsBox.setValue(self.settings.histogramBins)
        self.integrateHistogramCheckBox.setChecked( self.settings.integrateHistogram )
        # Timestamps
        self.enableCheckBox.setChecked(self.settings.enableTimestamps )
        self.saveRawDataCheckBox.setChecked(self.settings.saveRawData)
        self.binwidthSpinBox.setValue(self.settings.binwidth)
        self.roiStartSpinBox.setValue(self.settings.roiStart)
        self.roiWidthSpinBox.setValue(self.settings.roiWidth)
        self.integrateCombo.setCurrentIndex( self.settings.integrateTimestamps )
        self.channelSpinBox.setValue( self.settings.timestampsChannel )
        self.onModeChanged(self.settings.scanMode)
        if self.gateSequenceUi:
            self.gateSequenceUi.setSettings( self.settings.gateSequenceSettings )
        self.updateSaveStatus()
        self.evalAlgorithmList = []
        for evaluation in self.settings.evalList:
            self.addEvaluation(evaluation)
        assert len(self.settings.evalList)==len(self.evalAlgorithmList), "EvalList and EvalAlgoithmList length mismatch"
        self.evalTableModel.setEvalList( self.settings.evalList, self.evalAlgorithmList )
        self.evalTableView.resizeColumnsToContents()
        #self.evalTableView.horizontalHeader().setStretchLastSection(True)
        self.tableModel.setScanList(self.settings.scanSegmentList)

    def addEvaluation(self, evaluation):
        algo =  CountEvaluation.EvaluationAlgorithms[evaluation.evaluation]()
        algo.subscribe( self.updateSaveStatus )   # track changes of the algorithms settings so the save status is displayed correctly
        algo.setSettings( evaluation.settings, evaluation.name )
        self.evalAlgorithmList.append(algo)      

    def onAddEvaluation(self):
        evaluation = EvaluationDefinition()
        evaluation.counter = 0
        evaluation.plotname = "Scan Data" #Default to "Scan Data" plot
        evaluation.evaluation = CountEvaluation.EvaluationAlgorithms.keys()[0]
        self.settings.evalList.append( evaluation )
        self.addEvaluation( evaluation )
        assert len(self.settings.evalList)==len(self.evalAlgorithmList), "EvalList and EvalAlgoithmList length mismatch"
        self.evalTableModel.setEvalList( self.settings.evalList, self.evalAlgorithmList )
        self.evalTableView.resizeColumnsToContents()
        self.evalTableView.horizontalHeader().setStretchLastSection(True)
 
    def removeEvaluation(self, index):
        del self.evalAlgorithmList[index]

    def onRemoveEvaluation(self):
        for index in sorted(unique([ i.row() for i in self.evalTableView.selectedIndexes() ]),reverse=True):
            del self.settings.evalList[index]
            self.removeEvaluation(index)
        assert len(self.settings.evalList)==len(self.evalAlgorithmList), "EvalList and EvalAlgoithmList length mismatch"
        self.evalTableModel.setEvalList( self.settings.evalList, self.evalAlgorithmList )
        
    def onActiveEvalChanged(self, modelIndex, modelIndex2 ):
        self.evalParamTreeWidget.setParameters( self.evalAlgorithmList[modelIndex.row()].parameter)

    def updateSaveStatus(self):
        currentText = str(self.comboBox.currentText())
        try:
            if not currentText:
                self.saveStatus = True
            elif self.settingsName and self.settingsName in self.settingsDict:
                self.saveStatus = self.settingsDict[self.settingsName]==self.settings and currentText==self.settingsName
            else:
                self.saveStatus = False
            if self.parameters.autoSave and not self.saveStatus:
                self.onSave( updateSaveStatus=False )
                self.saveStatus = True
            self.saveButton.setEnabled( not self.saveStatus )
        except MagnitudeError:
            pass
            
    def onLoadPP(self, ppname):
        logger = logging.getLogger(__name__)
        self.settings.loadPPName = str(ppname)
        logger.debug( "ScanControl.onLoadPP {0} {1} {2}".format( self.settings.loadPP, bool(self.settings.loadPPName), self.settings.loadPPName ) )
        if self.settings.loadPP and self.settings.loadPPName and hasattr(self,"pulseProgramUi"):
            self.pulseProgramUi.loadContextByName( self.settings.loadPPName )
        self.updateSaveStatus()
            
    def onRecentPPFilesChanged(self, namelist):
        updateComboBoxItems( self.loadPPComboBox, sorted( namelist ) )
        self.updateSaveStatus()
        
    def setPulseProgramUi(self, pulseProgramUi ):
        logger = logging.getLogger(__name__)
        logger.debug( "ScanControl.setPulseProgramUi {0}".format(pulseProgramUi.configParams.recentFiles.keys()) )
        isStartup = self.pulseProgramUi is None
        self.pulseProgramUi = pulseProgramUi
        with BlockSignals(self.loadPPComboBox):
            self.loadPPComboBox.clear()
            self.loadPPComboBox.addItems(pulseProgramUi.contextDict.keys())
            if self.settings.loadPPName: 
                self.loadPPComboBox.setCurrentIndex( self.loadPPComboBox.findText(self.settings.loadPPName))
        self.pulseProgramUi.contextDictChanged.connect( self.onRecentPPFilesChanged, QtCore.Qt.UniqueConnection )

        if not self.gateSequenceUi:
            self.gateSequenceUi = GateSequenceUi.GateSequenceUi()
            self.gateSequenceUi.valueChanged.connect( self.updateSaveStatus )
            self.gateSequenceUi.postInit('test',self.config,self.pulseProgramUi.pulseProgram )
            self.gateSequenceUi.setupUi(self.gateSequenceUi)
            self.toolBox.addItem(self.gateSequenceUi,"Gate Sequences")
        if pulseProgramUi.currentContext.parameters:
            self.gateSequenceUi.setVariables( pulseProgramUi.currentContext.parameters )
        self.gateSequenceUi.setSettings( self.settings.gateSequenceSettings )
        if isStartup:
            self.onLoadPP(self.settings.loadPPName)

    def onEditingFinished(self,edit,attribute):
        self.beginChange()
        setattr( self.settings, attribute, str(edit.text())  )
        self.commitChange()
        self.updateSaveStatus()
                
    def beginChange(self):
        self.tempSettings = copy.deepcopy( self.settings )

    def commitChange(self): 
        pass
        #if self.tempSettings!=self.settings:
        #    self.comboBox.setEditText('')
        
    def onStateChanged(self, attribute, state):
        self.beginChange()
        setattr( self.settings, attribute, (state == QtCore.Qt.Checked)  )
        self.commitChange()
        self.updateSaveStatus()
        
    def onCurrentTextChanged(self, text):
        self.beginChange()
        self.settings.scanParameter = str(text)
        self.commitChange()
        self.updateSaveStatus()
    
    def onCurrentExternalTextChanged(self, text):
        self.beginChange()
        self.settings.externalScanParameter = str(text)
        self.commitChange()
        self.updateSaveStatus()
    
    def onCurrentIndexChanged(self, attribute, index):
        self.beginChange()
        setattr( self.settings, attribute, index )
        self.commitChange()
        self.updateSaveStatus()
        
    def onModeChanged(self, index):
        self.beginChange()
        self.settings.scanMode = index
        self.scanTypeCombo.setEnabled(index in [0,2])
        self.scanRepeatComboBox.setEnabled( index in [0,2] )
        self.xUnitEdit.setEnabled( index==0)
        self.xExprEdit.setEnabled( index==0)
        self.comboBoxParameter.setEnabled( index==0 )
        self.comboBoxExternalParameter.setEnabled( index==0 )
        self.commitChange()       
        self.updateSaveStatus()
    
    def onValueChanged(self, attribute, value):
        self.beginChange()
        setattr( self.settings, attribute, MagnitudeUtilit.mg(value) )
        self.commitChange()
        self.updateSaveStatus()

    def onBareValueChanged(self, attribute, value):
        self.beginChange()
        setattr( self.settings, attribute, value )
        self.commitChange()
        self.updateSaveStatus()
              
    def onIntValueChanged(self, attribute, value):
        self.beginChange()
        setattr( self.settings, attribute, value )
        self.commitChange()
        self.updateSaveStatus()
        
    def setVariables(self, variabledict):
        self.variabledict = variabledict
#         oldParameterName = self.settings.scanParameter
        with BlockSignals(self.comboBoxParameter):
            self.comboBoxParameter.clear()
            for _, var in iter(sorted(variabledict.iteritems())):
                if var.type == "parameter":
                    self.comboBoxParameter.addItem(var.name)
        if self.settings.scanParameter:
            self.comboBoxParameter.setCurrentIndex(self.comboBoxParameter.findText(self.settings.scanParameter) )
        elif self.comboBoxParameter.count()>0:  # if scanParameter is None set it to the current selection
            self.settings.scanParameter = self.comboBoxParameter.currentText()
        if self.gateSequenceUi:
            self.gateSequenceUi.setVariables(variabledict)
        self.updateSaveStatus()
            
    def setScanNames(self, scannames):
        updateComboBoxItems( self.comboBoxExternalParameter, scannames ) 
        if self.settings.externalScanParameter:
            self.comboBoxExternalParameter.setCurrentIndex( self.comboBoxExternalParameter.findText(self.settings.externalScanParameter))
        self.updateSaveStatus()
                
    def getScan(self):
        scan = copy.deepcopy(self.settings)
        scan.type = [ ScanList.ScanType.LinearUp, ScanList.ScanType.LinearDown, ScanList.ScanType.Randomized, ScanList.ScanType.CenterOut][self.settings.scantype]
        
        scan.list = list( concatenate_iter( *( numpy.linspace(segment.start, segment.stop, segment.steps) for segment in scan.scanSegmentList ) ) )
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
            
        scan.evalAlgorithmList = copy.deepcopy( self.evalAlgorithmList )
        scan.gateSequenceUi = self.gateSequenceUi
        scan.settingsName = self.settingsName
#         try:
#             scan.xUnit = ensureCorrectUnit(scan.xUnit, scan.start)
#         except AttributeError:
#             pass  # scan.start is not a magnitude, don't change xunit
        self.onCommit()
        return scan
        
    def saveConfig(self):
        self.config[self.configname] = self.settings
        self.config[self.configname+'.dict'] = self.settingsDict
        self.config[self.configname+'.settingsName'] = self.settingsName
        self.config[self.configname+'.parameters'] = self.parameters
    # History stuff
    
    def onRedo(self):
        if self.settingsHistoryPointer<len(self.settingsHistory):
            self.settingsHistoryPointer += 1
            if self.settingsHistoryPointer<len(self.settingsHistory):
                self.setSettings( self.settingsHistory[self.settingsHistoryPointer])
            elif self.historyFinalState:
                self.setSettings( self.historyFinalState )
                self.historyFinalState = None
     
    def onUndo(self):
        if self.settingsHistoryPointer>0:
            if self.settingsHistoryPointer==len(self.settingsHistory):
                self.historyFinalState = copy.deepcopy( self.settings )
            self.settingsHistoryPointer -= 1
            self.setSettings( self.settingsHistory[self.settingsHistoryPointer] )
    
    def onSave(self, updateSaveStatus=True):
        self.settingsName = str(self.comboBox.currentText())
        if self.settingsName != '':
            if self.settingsName not in self.settingsDict:
                if self.comboBox.findText(self.settingsName)==-1:
                    self.comboBox.addItem(self.settingsName)
            self.settingsDict[self.settingsName] = copy.deepcopy(self.settings)
            self.scanConfigurationListChanged.emit( self.settingsDict )
        if updateSaveStatus:
            self.updateSaveStatus()

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
        self.updateSaveStatus()

    def loadSetting(self, name):
        if name and self.comboBox.findText(name)>=0:
            self.comboBox.setCurrentIndex( self.comboBox.findText(name) )  
            self.onLoad(name)      

    def onReload(self):
        self.onLoad( self.comboBox.currentText() )
   
    def onCommit(self):
        if len(self.settingsHistory)==0 or self.settings!=self.settingsHistory[-1]:
            self.settingsHistory.append(copy.deepcopy(self.settings))
            self.settingsHistoryPointer = len(self.settingsHistory)
                
    def onIntegrationChanged(self, value):
        self.beginChange()
        self.settings.integrateTimestamps = value
        self.commitChange()
        self.updateSaveStatus()
        
    def onAlgorithmValueChanged(self, algo, name, value):
        self.beginChange()
#        self.algorithms[algo].setParameter(name, value)
        self.commitChange()
        self.updateSaveStatus()

    def onIntegrateHistogramClicked(self, state):
        self.beginChange()
        self.settings.integrateHistogram = self.integrateHistogramCheckBox.isChecked()
        self.commitChange()
        self.updateSaveStatus()
 
    def onHistogramBinsChanged(self, bins):
        self.beginChange()
        self.settings.histogramBins = bins
        self.commitChange()
        self.updateSaveStatus()
        
    def onAlgorithmNameChanged(self, name):
        self.beginChange()
        self.commitChange()
        self.updateSaveStatus()
        
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
        