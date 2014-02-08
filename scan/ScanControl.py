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
from modules.MagnitudeUtilit import valueAs
from modules.PyqtUtility import BlockSignals
from modules.PyqtUtility import updateComboBoxItems
from modules.Utility import unique
from modules.enum import enum
from modules.magnitude import mg, MagnitudeError
from uiModules.ComboBoxDelegate import ComboBoxDelegate


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
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault('plotname', None)        
        self.__dict__.setdefault('settings', HashableDict())        
        self.__dict__.setdefault('settingsCache', HashableDict())
        self.__dict__.setdefault('showHistogram', False)   
        
    stateFields = ['counter', 'evaluation', 'settings', 'settingsCache', 'name', 'plotname', 'showHistogram'] 
        
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
    ScanMode = enum('ParameterScan','StepInPlace','GateSequenceScan')
    ScanType = enum('LinearStartToStop','LinearStopToStart','Randomized')
    ScanRepeat = enum('SingleScan','RepeatedScan')
    def __init__(self):
        # Scan
        self.scanParameter = None
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
        self.autoSave = False
        self.xUnit = ""
        self.loadPP = False
        self.loadPPName = ""
        self.startCenter = 0    # 0: start, stop;  1:center, span
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
        
    def __setstate__(self, state):
        """this function ensures that the given fields are present in the class object
        after unpickling. Only new class attributes need to be added here.
        """
        self.__dict__ = state
        self.__dict__.setdefault('xUnit', '')
        self.__dict__.setdefault('scanRepeat', 0)
        self.__dict__.setdefault('loadPP', False)
        self.__dict__.setdefault('loadPPName', "")
        self.__dict__.setdefault('stepSize',1)
        self.__dict__.setdefault('center',0)
        self.__dict__.setdefault('span',0)
        self.__dict__.setdefault('startCenter',0)        
        self.__dict__.setdefault('gateSequenceSettings',GateSequenceUi.Settings())
        self.__dict__.setdefault('evalList',list())

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
        
    stateFields = ['scanParameter', 'start', 'stop', 'steps', 'stepSize', 'stepsSelect', 'scantype', 'scanMode', 'scanRepeat', 
                'filename', 'autoSave', 'xUnit', 'loadPP', 'loadPPName', 'histogramBins', 'integrateHistogram', 
                'enableTimestamps', 'binwidth', 'roiStart', 'roiWidth', 'integrateTimestamps', 'timestampsChannel', 'saveRawData', 'gateSequenceSettings',
                'center', 'span', 'startCenter', 'evalList']

    documentationList = [ 'scanParameter', 'start', 'stop', 'steps', 'stepSize', 'scantype', 'scanMode', 'scanRepeat', 
                'xUnit', 'loadPP', 'loadPPName' ]
        
    def documentationString(self):
        r = "\r\n".join( [ "{0}\t{1}".format(field,getattr(self,field)) for field in self.documentationList] )
        r += self.gateSequenceSettings.documentationString()
        return r


class ScanControl(ScanControlForm, ScanControlBase ):
    ScanModes = enum('SingleScan','RepeatedScan','StepInPlace','GateSequenceScan')
    integrationMode = enum('IntegrateAll','IntegrateRun','NoIntegration')
    logger = logging.getLogger(__name__)
    def __init__(self,config,parentname, plotnames=None, parent=None):
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

    def setupUi(self, parent):
        logger = logging.getLogger(__name__)
        ScanControlForm.setupUi(self,parent)
        # History and Dictionary
        self.saveButton.clicked.connect( self.onSave )
        self.undoButton.clicked.connect( self.onUndo )
        self.redoButton.clicked.connect( self.onRedo )
        self.removeButton.clicked.connect( self.onRemove )
        self.reloadButton.clicked.connect( self.onReload )
        self.evalTableModel = EvaluationTableModel( self.updateSaveStatus, plotnames=self.plotnames )
        self.evalTableModel.dataChanged.connect( self.updateSaveStatus )
        self.evalTableModel.dataChanged.connect( self.onActiveEvalChanged )
        self.evalTableView.setModel( self.evalTableModel )
        self.evalTableView.clicked.connect( self.editEvaluationTable )
        delegate = ComboBoxDelegate()
        self.evalTableView.setItemDelegateForColumn(1, delegate  )
        self.evalTableView.setItemDelegateForColumn(4, delegate )
        self.addEvaluationButton.clicked.connect( self.onAddEvaluation )
        self.removeEvaluationButton.clicked.connect( self.onRemoveEvaluation )
        self.evalTableView.selectionModel().currentChanged.connect( self.onActiveEvalChanged )
        self.evalTableView.resizeColumnsToContents()
        
        try:
            self.setSettings( self.settings )
        except AttributeError:
            logger.error( "Ignoring exception" )
        for name in self.settingsDict:
            self.comboBox.addItem(name)
        if self.settingsName and self.comboBox.findText(self.settingsName):
            self.comboBox.setCurrentIndex( self.comboBox.findText(self.settingsName) )
        self.comboBox.currentIndexChanged['QString'].connect( self.onLoad )
        self.comboBox.editTextChanged.connect( lambda x: self.updateSaveStatus() ) 
        # update connections
        self.comboBoxParameter.currentIndexChanged['QString'].connect( self.onCurrentTextChanged )
        self.startBox.valueChanged.connect( self.onStartChanged )
        self.stopBox.valueChanged.connect( self.onStopChanged )
        self.stepsBox.valueChanged.connect( self.onStepsValueChanged )
        self.stepsCombo.currentIndexChanged[int].connect( self.onStepsSelectChanged )
        self.scanTypeCombo.currentIndexChanged[int].connect( functools.partial(self.onCurrentIndexChanged,'scantype') )
        self.autoSaveCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'autoSave') )
        self.scanModeComboBox.currentIndexChanged[int].connect( self.onModeChanged )
        self.filenameEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.filenameEdit, 'filename') )
        self.xUnitEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.xUnitEdit, 'xUnit') )
        self.scanRepeatComboBox.currentIndexChanged[int].connect( functools.partial(self.onCurrentIndexChanged,'scanRepeat') )
        self.startCenterCombo.currentIndexChanged[int].connect( self.onStartCenterChanged )
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
        self.channelSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'timestampsChannel') )
        self.loadPPcheckBox.stateChanged.connect( functools.partial(self.onStateChanged, 'loadPP' ) )
        self.loadPPComboBox.currentIndexChanged['QString'].connect( self.onLoadPP )
        
    def setSettings(self, settings):
        self.settings = copy.deepcopy(settings)
        self.scanModeComboBox.setCurrentIndex( self.settings.scanMode )
        self.setStartCenter()
        self.calculateSteps( self.settings )
        self.setSteps( self.settings, True )
        self.stepsCombo.setCurrentIndex(self.settings.stepsSelect)
        self.scanTypeCombo.setCurrentIndex(self.settings.scantype )
        self.autoSaveCheckBox.setChecked(self.settings.autoSave)
        if self.settings.scanParameter: 
            self.comboBoxParameter.setCurrentIndex( self.comboBoxParameter.findText(self.settings.scanParameter))
        elif self.comboBoxParameter.count()>0:  # if scanParameter is None set it to the current selection
            self.settings.scanParameter = self.comboBoxParameter.currentText()
        self.filenameEdit.setText( getattr(self.settings,'filename','') )
        self.startBox.setEnabled(self.settings.scanMode in [0,1])
        self.stopBox.setEnabled(self.settings.scanMode in [0,1])
        self.scanTypeCombo.setEnabled(self.settings.scanMode in [0,1])
        self.xUnitEdit.setText( self.settings.xUnit )
        self.scanRepeatComboBox.setCurrentIndex( self.settings.scanRepeat )
        self.loadPPcheckBox.setChecked( self.settings.loadPP )
        if self.settings.loadPPName: 
            self.loadPPComboBox.setCurrentIndex( self.loadPPComboBox.findText(self.settings.loadPPName))
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
        self.evalTableView.horizontalHeader().setStretchLastSection(True)

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
            self.saveButton.setEnabled( not self.saveStatus )
        except MagnitudeError:
            pass
            
    def onStartCenterChanged(self, value):   
        self.settings.startCenter = value 
        self.calculateBoundaries()
        self.setStartCenter()
        self.updateSaveStatus()
 
    def setStartCenter(self):
        self.beginChange()
        if self.settings.startCenter == 0:
            self.startBox.setValue(self.settings.start)
            self.stopBox.setValue(self.settings.stop)
            self.startCenterCombo.setCurrentIndex(0)
            self.stopLabel.setText("Stop")
        elif self.settings.startCenter == 1:
            self.startBox.setValue(self.settings.center)
            self.stopBox.setValue(self.settings.span)
            self.startCenterCombo.setCurrentIndex(1)
            self.stopLabel.setText("Span")        
        self.commitChange()
        
    def onStartChanged(self, value):
        self.beginChange()
        if self.settings.startCenter == 0:
            self.settings.start = MagnitudeUtilit.mg(value)
        elif self.settings.startCenter == 1:
            self.settings.center = MagnitudeUtilit.mg(value)
        self.calculateBoundaries()
        self.commitChange()
        self.updateSaveStatus()

    def onStopChanged(self, value):
        self.beginChange()
        if self.settings.startCenter == 0:
            self.settings.stop = MagnitudeUtilit.mg(value)
        elif self.settings.startCenter == 1:
            self.settings.span = MagnitudeUtilit.mg(value)
        self.calculateBoundaries()
        self.commitChange()
        self.updateSaveStatus()
            
    def calculateBoundaries(self):
        try:
            if self.settings.startCenter == 0:
                self.settings.center = (self.settings.start + self.settings.stop)/2
                self.settings.span = abs(self.settings.start - self.settings.stop)
            elif self.settings.startCenter == 1:
                self.settings.start = self.settings.center - self.settings.span/2
                self.settings.stop = self.settings.center + self.settings.span/2
            self.startBox.setStyleSheet("")
            self.stopBox.setStyleSheet("")
            self.calculateSteps(self.settings)
            self.setSteps(self.settings, False)
        except Exception:
            self.startBox.setStyleSheet("MagnitudeSpinBox {background: #ffa0a0;}")
            self.stopBox.setStyleSheet("MagnitudeSpinBox {background: #ffa0a0;}")
            
                
    def setSteps( self, settings, writeInput=False ):
        if settings.stepsSelect == 0:
            if writeInput:
                self.stepsBox.setValue(settings.steps)
            self.stepsLabel.setText( str(settings.stepSize) )
        else:
            if writeInput:
                self.stepsBox.setValue(settings.stepSize)
            self.stepsLabel.setText( str(settings.steps) )
        self.updateSaveStatus()

        
    def calculateSteps(self, settings):
        logger = logging.getLogger(__name__)
        if settings.stepsSelect == 0:
            try:
                settings.stepSize = abs(settings.stop - settings.start)/(settings.steps - 1)
                valueAs( settings.stepSize, settings.start )
            except Exception:
                logger.exception("calculateSteps")
                settings.stepSize = None
        else:
            try:
                settings.steps = int( round( abs(settings.stop - settings.start)/settings.stepSize ) ) + 1
            except Exception:
                logger.exception("calculateSteps")
                settings.steps = None
        
    def onLoadPP(self, ppname):
        logger = logging.getLogger(__name__)
        self.settings.loadPPName = str(ppname)
        logger.debug( "ScanControl.onLoadPP {0} {1} {2}".format( self.settings.loadPP, bool(self.settings.loadPPName), self.settings.loadPPName ) )
        if self.settings.loadPP and self.settings.loadPPName and hasattr(self,"pulseProgramUi"):
            self.pulseProgramUi.onFilenameChange( self.settings.loadPPName )
        self.updateSaveStatus()
            
    def onRecentPPFilesChanged(self, name):
        logger = logging.getLogger(__name__)
        logger.exception("calculateSteps")
        logger.debug( "ScanControl.onRecentPPFilesChanged" )
        if self.loadPPComboBox.findText(name)<0:
            self.loadPPComboBox.addItem(name)
        self.updateSaveStatus()
#        if self.settings.loadPPName: 
#            self.loadPPComboBox.setCurrentIndex( self.loadPPComboBox.findText(self.settings.loadPPName))
        
    def setPulseProgramUi(self, pulseProgramUi ):
        logger = logging.getLogger(__name__)
        logger.debug( "ScanControl.setPulseProgramUi {0}".format(pulseProgramUi.configParams.recentFiles.keys()) )
        self.pulseProgramUi = pulseProgramUi
        with BlockSignals(self.loadPPComboBox):
            self.loadPPComboBox.clear()
            if hasattr(pulseProgramUi.configParams,'recentFiles'):
                self.loadPPComboBox.addItems(pulseProgramUi.configParams.recentFiles.keys())
            if self.settings.loadPPName: 
                self.loadPPComboBox.setCurrentIndex( self.loadPPComboBox.findText(self.settings.loadPPName))
        self.pulseProgramUi.recentFilesChanged.connect( self.onRecentPPFilesChanged, QtCore.Qt.UniqueConnection )

        if not self.gateSequenceUi:
            self.gateSequenceUi = GateSequenceUi.GateSequenceUi()
            self.gateSequenceUi.valueChanged.connect( self.updateSaveStatus )
            self.gateSequenceUi.postInit('test',self.config,self.pulseProgramUi.pulseProgram )
            self.gateSequenceUi.setupUi(self.gateSequenceUi)
            self.toolBox.addItem(self.gateSequenceUi,"Gate Sets")
        if pulseProgramUi.variabledict:
            self.gateSequenceUi.setVariables( pulseProgramUi.variabledict )
        self.gateSequenceUi.setSettings( self.settings.gateSequenceSettings )


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
    
    def onCurrentIndexChanged(self, attribute, index):
        self.beginChange()
        setattr( self.settings, attribute, index )
        self.commitChange()
        self.updateSaveStatus()
        
    def onModeChanged(self, index):
        self.beginChange()
        self.settings.scanMode = index
        self.startBox.setEnabled(index ==0)
        self.stopBox.setEnabled(index ==0)
        self.stepsBox.setEnabled( index in [0,1] )
        self.scanTypeCombo.setEnabled(index in [0,2])
        self.scanRepeatComboBox.setEnabled( index in [0,2] )
        self.xUnitEdit.setEnabled( index==0)
        self.comboBoxParameter.setEnabled( index==0 )
        self.commitChange()       
        self.updateSaveStatus()
    
    def onValueChanged(self, attribute, value):
        self.beginChange()
        setattr( self.settings, attribute, MagnitudeUtilit.mg(value) )
        self.commitChange()
        self.updateSaveStatus()
        
    def onStartStopChanged(self, attribute, value):
        self.beginChange()
        setattr( self.settings, attribute, MagnitudeUtilit.mg(value) )
        self.calculateSteps( self.settings )
        self.setSteps( self.settings )
        self.commitChange()
        self.updateSaveStatus()

    def onStepsSelectChanged(self, select ):
        self.settings.stepsSelect = select
        self.calculateSteps( self.settings )
        self.setSteps( self.settings, True )
        self.updateSaveStatus()
        
    def onStepsValueChanged( self, value ):
        if self.settings.stepsSelect==0:
            self.settings.steps = int(value)
            self.stepsBox.setStyleSheet("")
        else: 
            self.settings.stepSize = value
            if MagnitudeUtilit.haveSameDimension(self.settings.stepSize, self.settings.start):
                self.stepsBox.setStyleSheet("")
            else:
                self.stepsBox.setStyleSheet("MagnitudeSpinBox {background: #ffa0a0;}")
        self.calculateSteps(self.settings)
        self.setSteps( self.settings )
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
        updateComboBoxItems( self.comboBoxParameter, scannames ) 
        if self.settings.scanParameter:
            self.comboBoxParameter.setCurrentIndex( self.comboBoxParameter.findText(self.settings.scanParameter))
        self.updateSaveStatus()
                
    def getScan(self):
        scan = copy.deepcopy(self.settings)
        scan.type = [ ScanList.ScanType.LinearUp, ScanList.ScanType.LinearDown, ScanList.ScanType.Randomized][self.settings.scantype]
        scan.list = ScanList.scanList( scan.start, scan.stop, scan.steps if scan.stepsSelect==0 else scan.stepSize, 
                                       scan.type, scan.stepsSelect )
        scan.evalAlgorithmList = copy.deepcopy( self.evalAlgorithmList )
        scan.gateSequenceUi = self.gateSequenceUi
        scan.settingsName = self.settingsName
        self.onCommit()
        return scan
        
    def saveConfig(self):
        self.config[self.configname] = self.settings
        self.config[self.configname+'.dict'] = self.settingsDict
        self.config[self.configname+'.settingsName'] = self.settingsName
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
    
    def onSave(self):
        self.settingsName = str(self.comboBox.currentText())
        if self.settingsName != '':
            if self.settingsName not in self.settingsDict:
                if self.comboBox.findText(self.settingsName)==-1:
                    self.comboBox.addItem(self.settingsName)
            self.settingsDict[self.settingsName] = copy.deepcopy(self.settings)
        self.updateSaveStatus()

    def onRemove(self):
        name = str(self.comboBox.currentText())
        if name != '':
            if name in self.settingsDict:
                self.settingsDict.pop(name)
            idx = self.comboBox.findText(name)
            if idx>=0:
                self.comboBox.removeItem(idx)
        
    
    def onLoad(self,name):
        self.settingsName = str(name)
        if self.settingsName !='' and self.settingsName in self.settingsDict:
            self.setSettings(self.settingsDict[self.settingsName])
        self.updateSaveStatus()

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
        