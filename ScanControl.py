# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
import copy
import functools
from PyQt4 import QtCore, QtGui
import CountEvaluation
from MagnitudeSpinBox import MagnitudeSpinBox
from modules.MagnitudeUtilit import valueAs
from pyqtgraph.parametertree import ParameterTree
 
ScanControlForm, ScanControlBase = PyQt4.uic.loadUiType(r'ui\ScanControlUi.ui')

import ScanList
from modules import MagnitudeUtilit
from modules.magnitude import mg, MagnitudeError
from modules.enum import enum
import GateSetUi
from modules.PyqtUtility import BlockSignals, updateComboBoxItems
from EvaluationTableModel import EvaluationTableModel
from ComboBoxDelegate import ComboBoxDelegate
import logging

def unique(seq):
    seen = set()
    return [ x for x in seq if x not in seen and not seen.add(x)]

class EvaluationDefinition:
    def __init__(self):
        self.counter = None
        self.evaluation = None
        self.settings = dict()
        self.name = None
        self.plotname = None
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault('plotname', None)        
        
    stateFields = ['counter', 'evaluation', 'settings', 'name', 'plotname'] 
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))
 

class Scan:
    ScanMode = enum('ParameterScan','StepInPlace','GateSetScan')
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
        self.rewriteDDS = False
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
        # GateSet Settings
        self.gateSetSettings = GateSetUi.Settings()
        
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
        self.__dict__.setdefault('gateSetSettings',GateSetUi.Settings())
        self.__dict__.setdefault('evalList',list())

    def __eq__(self,other):
        try:
            equal = tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)
        except MagnitudeError as e:
            equal = False
        return equal

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))
        
    stateFields = ['scanParameter', 'start', 'stop', 'steps', 'stepSize', 'stepsSelect', 'scantype', 'scanMode', 'scanRepeat', 'rewriteDDS', 
                'filename', 'autoSave', 'xUnit', 'loadPP', 'loadPPName', 'histogramBins', 'integrateHistogram', 'counterChannel', 
                'enableTimestamps', 'binwidth', 'roiStart', 'roiWidth', 'integrateTimestamps', 'timestampsChannel', 'saveRawData', 'gateSetSettings',
                'center', 'span', 'startCenter', 'evalList']

    documentationList = [ 'scanParameter', 'start', 'stop', 'steps', 'stepSize', 'scantype', 'scanMode', 'scanRepeat', 'rewriteDDS', 
                'xUnit', 'loadPP', 'loadPPName', 'counterChannel' ]
        
    def documentationString(self):
        r = "\r\n".join( [ "{0}\t{1}".format(field,getattr(self,field)) for field in self.documentationList] )
        r += self.gateSetSettings.documentationString()
        return r


class ScanControl(ScanControlForm, ScanControlBase ):
    ScanModes = enum('SingleScan','RepeatedScan','StepInPlace','GateSetScan')
    integrationMode = enum('IntegrateAll','IntegrateRun','NoIntegration')
    logger = logging.getLogger(__name__)
    def __init__(self,config,parentname, plotnames=None, parent=None):
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
        self.gateSetUi = None
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
        self.reloadButton.clicked.connect( self.onReload )
        self.evalTableModel = EvaluationTableModel(plotnames=self.plotnames)
        self.evalTableModel.dataChanged.connect( self.updateSaveStatus )
        self.evalTableView.setModel( self.evalTableModel )
        self.evalTableView.setItemDelegateForColumn(3, ComboBoxDelegate() )
        self.evalAlgorithmCombo.addItems( CountEvaluation.EvaluationAlgorithms.keys() )
        self.addEvaluationButton.clicked.connect( self.onAddEvaluation )
        self.removeEvaluationButton.clicked.connect( self.onRemoveEvaluation )
        self.evalTableView.selectionModel().currentChanged.connect( self.onActiveEvalChanged )
        
        try:
            self.setSettings( self.settings )
        except AttributeError as e:
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
        self.rewriteDDSCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'rewriteDDS') )
        self.autoSaveCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'autoSave') )
        self.scanModeComboBox.currentIndexChanged[int].connect( self.onModeChanged )
        self.filenameEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.filenameEdit, 'filename') )
        self.xUnitEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.xUnitEdit, 'xUnit') )
        self.scanRepeatComboBox.currentIndexChanged[int].connect( functools.partial(self.onCurrentIndexChanged,'scanRepeat') )
        self.startCenterCombo.currentIndexChanged[int].connect( self.onStartCenterChanged )
        # Evaluation
        self.histogramBinsBox.valueChanged.connect(self.onHistogramBinsChanged)
        self.integrateHistogramButton.clicked.connect( self.onIntegrateHistogramClicked )
        self.counterSpinBox.valueChanged.connect( functools.partial(self.onIntValueChanged,'counterChannel') )
#        self.evalMethodCombo.currentIndexChanged['QString'].connect( self.onAlgorithmNameChanged )
                
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
        self.rewriteDDSCheckBox.setChecked( self.settings.rewriteDDS )
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
        self.integrateHistogramButton.setChecked( self.settings.integrateHistogram )
        self.counterSpinBox.setValue( self.settings.counterChannel )
        # Timestamps
        self.enableCheckBox.setChecked(self.settings.enableTimestamps )
        self.saveRawDataCheckBox.setChecked(self.settings.saveRawData)
        self.binwidthSpinBox.setValue(self.settings.binwidth)
        self.roiStartSpinBox.setValue(self.settings.roiStart)
        self.roiWidthSpinBox.setValue(self.settings.roiWidth)
        self.integrateCombo.setCurrentIndex( self.settings.integrateTimestamps )
        self.channelSpinBox.setValue( self.settings.timestampsChannel )
        self.onModeChanged(self.settings.scanMode)
        if self.gateSetUi:
            self.gateSetUi.setSettings( self.settings.gateSetSettings )
        self.updateSaveStatus()
        self.evalTableModel.setEvalList( self.settings.evalList )
        for eval in self.settings.evalList:
            self.addEvaluation(eval)
        self.evalTableView.resizeColumnsToContents()
        self.evalTableView.horizontalHeader().setStretchLastSection(True)

    def addEvaluation(self, eval):
        algo =  CountEvaluation.EvaluationAlgorithms[eval.evaluation]()
        algo.subscribe( self.updateSaveStatus )
        algo.setSettings( eval.settings )
        self.evalAlgorithmList.append(algo)      

    def onAddEvaluation(self):
        evaluation = EvaluationDefinition()
        evaluation.counter = self.counterSelectSpinBox.value()
        evaluation.evaluation = str(self.evalAlgorithmCombo.currentText())
        self.settings.evalList.append( evaluation )
        self.addEvaluation( evaluation )
        self.evalTableModel.setEvalList( self.settings.evalList )
        self.evalTableView.resizeColumnsToContents()
        self.evalTableView.horizontalHeader().setStretchLastSection(True)

    def removeEvaluation(self, index):
         del self.evalAlgorithmList[index]

    def onRemoveEvaluation(self):
        for index in sorted(unique([ i.row() for i in self.evalTableView.selectedIndexes() ]),reverse=True):
            del self.settings.evalList[index]
            self.removeEvaluation(index)
        self.evalTableModel.setEvalList( self.settings.evalList )
        
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
        except Exception as e:
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
            except Exception as e:
                logger.exception("calculateSteps")
                settings.stepSize = None
        else:
            try:
                settings.steps = int( round( abs(settings.stop - settings.start)/settings.stepSize ) ) + 1
            except Exception as e:
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

        if not self.gateSetUi:
            self.gateSetUi = GateSetUi.GateSetUi()
            self.gateSetUi.valueChanged.connect( self.updateSaveStatus )
            self.gateSetUi.postInit('test',self.config,self.pulseProgramUi.pulseProgram )
            self.gateSetUi.setupUi(self.gateSetUi)
            self.toolBox.addItem(self.gateSetUi,"Gate Sets")
        if pulseProgramUi.variabledict:
            self.gateSetUi.setVariables( pulseProgramUi.variabledict )
        self.gateSetUi.setSettings( self.settings.gateSetSettings )


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
        oldParameterName = self.settings.scanParameter
        with BlockSignals(self.comboBoxParameter):
            self.comboBoxParameter.clear()
            for name, var in iter(sorted(variabledict.iteritems())):
                if var.type == "parameter":
                    self.comboBoxParameter.addItem(var.name)
        if self.settings.scanParameter:
            self.comboBoxParameter.setCurrentIndex(self.comboBoxParameter.findText(self.settings.scanParameter) )
        elif self.comboBoxParameter.count()>0:  # if scanParameter is None set it to the current selection
            self.settings.scanParameter = self.comboBoxParameter.currentText()
        if self.gateSetUi:
            self.gateSetUi.setVariables(variabledict)
        self.updateSaveStatus()
            
    def setScanNames(self, scannames):
        self.comboBoxParameter.clear()
        for name in scannames:
            self.comboBoxParameter.addItem(name)
        self.comboBoxParameter.setCurrentIndex( self.comboBoxParameter.findText(self.settings.scanParameter))
        self.updateSaveStatus()
                
    def getScan(self):
        scan = copy.deepcopy(self.settings)
        scan.type = [ ScanList.ScanType.LinearUp, ScanList.ScanType.LinearDown, ScanList.ScanType.Randomized][self.settings.scantype]
        scan.list = ScanList.scanList( scan.start, scan.stop, scan.steps if scan.stepsSelect==0 else scan.stepSize, 
                                       scan.type, scan.stepsSelect )
        scan.evalAlgorithmList = copy.deepcopy( self.evalAlgorithmList )
        scan.gateSetUi = self.gateSetUi
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

    def onIntegrateHistogramClicked(self):
        self.beginChange()
        self.settings.integrateHistogram = self.integrateHistogramButton.isChecked()
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
        