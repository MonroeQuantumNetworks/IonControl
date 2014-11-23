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

from scan.EvaluationAlgorithms import EvaluationAlgorithms
from EvaluationTableModel import EvaluationTableModel
from modules import MagnitudeUtilit
from modules.HashableDict import HashableDict
from modules.Utility import unique
from modules.magnitude import mg, MagnitudeError
from uiModules.ComboBoxDelegate import ComboBoxDelegate
from modules.enum import enum

ControlForm, ControlBase = PyQt4.uic.loadUiType(r'ui\EvaluationControl.ui')

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
 

class Evaluation:
    def __init__(self):
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
        
    def __setstate__(self, state):
        """this function ensures that the given fields are present in the class object
        after unpickling. Only new class attributes need to be added here.
        """
        self.__dict__ = state
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
        
    stateFields = [ 'histogramBins', 'integrateHistogram', 'enableTimestamps', 'binwidth', 'roiStart', 'roiWidth', 'integrateTimestamps', 'timestampsChannel', 
                    'saveRawData', 'evalList' , 'counterChannel']
   

class EvaluationControlParameters:
    def __init__(self):
        self.autoSave = False

class EvaluationControl(ControlForm, ControlBase ):
    evaluationConfigurationChanged = QtCore.pyqtSignal( object )
    integrationMode = enum('IntegrateAll','IntegrateRun','NoIntegration')
    logger = logging.getLogger(__name__)
    def __init__(self, config, globalVariablesUi, parentname, plotnames=None, parent=None, analysisNames=None):
        logger = logging.getLogger(__name__)
        ControlForm.__init__(self)
        ControlBase.__init__(self,parent)
        self.config = config
        self.configname = 'EvaluationControl.'+parentname
        self.globalDict = globalVariablesUi.variables
        # History and Dictionary
        try:
            self.settingsDict = self.config.get(self.configname+'.dict',dict())
        except TypeError:
            logger.info( "Unable to read scan control settings dictionary. Setting to empty dictionary." )
            self.settingsDict = dict()
        self.evaluationConfigurationChanged.emit( self.settingsDict )
        try:
            self.settings = self.config.get(self.configname,Evaluation())
        except TypeError:
            logger.info( "Unable to read scan control settings. Setting to new scan." )
            self.settings = Evaluation()
        self.settingsName = self.config.get(self.configname+'.settingsName',None)
        self.evalAlgorithmList = list()
        self.plotnames = plotnames
        self.analysisNames = analysisNames
        self.pulseProgramUi = None
        self.parameters = self.config.get( self.configname+'.parameters', EvaluationControlParameters() )
        self.globalVariablesUi = globalVariablesUi
        
    def setupUi(self, parent):
        ControlForm.setupUi(self,parent)
        # History and Dictionary
        self.saveButton.clicked.connect( self.onSave )
        self.removeButton.clicked.connect( self.onRemove )
        self.reloadButton.clicked.connect( self.onReload )
        self.evalTableModel = EvaluationTableModel( self.checkSettingsSavable, plotnames=self.plotnames, analysisNames=self.analysisNames )
        self.evalTableModel.dataChanged.connect( self.checkSettingsSavable )
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
       
#        try:
        self.setSettings( self.settings )
#         except AttributeError:
#             logger.error( "Ignoring exception" )
        self.comboBox.addItems( sorted(self.settingsDict.keys()))
        if self.settingsName and self.comboBox.findText(self.settingsName):
            self.comboBox.setCurrentIndex( self.comboBox.findText(self.settingsName) )
        self.comboBox.currentIndexChanged['QString'].connect( self.onLoad )
        self.comboBox.lineEdit().editingFinished.connect( self.checkSettingsSavable ) 
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
                
    def setAnalysisNames(self, names):
        self.evalTableModel.setAnalysisNames(names)
        
    def setSettings(self, settings):
        self.settings = copy.deepcopy(settings)
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
        self.checkSettingsSavable()
        self.evalAlgorithmList = []
        for evaluation in self.settings.evalList:
            self.addEvaluation(evaluation)
        assert len(self.settings.evalList)==len(self.evalAlgorithmList), "EvalList and EvalAlgoithmList length mismatch"
        self.evalTableModel.setEvalList( self.settings.evalList, self.evalAlgorithmList )
        self.evalTableView.resizeColumnsToContents()

    def addEvaluation(self, evaluation):
        algo =  EvaluationAlgorithms[evaluation.evaluation]()
        algo.subscribe( self.checkSettingsSavable )   # track changes of the algorithms settings so the save status is displayed correctly
        algo.setSettings( evaluation.settings, evaluation.name )
        self.evalAlgorithmList.append(algo)      

    def onAddEvaluation(self):
        evaluation = EvaluationDefinition()
        evaluation.counter = 0
        evaluation.plotname = "Scan Data" #Default to "Scan Data" plot
        evaluation.evaluation = EvaluationAlgorithms.keys()[0]
        self.settings.evalList.append( evaluation )
        self.addEvaluation( evaluation )
        assert len(self.settings.evalList)==len(self.evalAlgorithmList), "EvalList and EvalAlgoithmList length mismatch"
        self.evalTableModel.setEvalList( self.settings.evalList, self.evalAlgorithmList )
        self.evalTableView.resizeColumnsToContents()
        self.evalTableView.horizontalHeader().setStretchLastSection(True)
        self.checkSettingsSavable()
 
    def removeEvaluation(self, index):
        del self.evalAlgorithmList[index]

    def onRemoveEvaluation(self):
        for index in sorted(unique([ i.row() for i in self.evalTableView.selectedIndexes() ]),reverse=True):
            del self.settings.evalList[index]
            self.removeEvaluation(index)
        assert len(self.settings.evalList)==len(self.evalAlgorithmList), "EvalList and EvalAlgoithmList length mismatch"
        self.evalTableModel.setEvalList( self.settings.evalList, self.evalAlgorithmList )
        self.checkSettingsSavable()
        
    def onActiveEvalChanged(self, modelIndex, modelIndex2 ):
        self.evalParamTreeWidget.setParameters( self.evalAlgorithmList[modelIndex.row()].parameter)

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
            
    def onStateChanged(self, attribute, state):
        setattr( self.settings, attribute, (state == QtCore.Qt.Checked)  )
        self.checkSettingsSavable()
        
    def onValueChanged(self, attribute, value):
        setattr( self.settings, attribute, MagnitudeUtilit.mg(value) )
        self.checkSettingsSavable()

    def onBareValueChanged(self, attribute, value):
        setattr( self.settings, attribute, value )
        self.checkSettingsSavable()
              
    def getEvaluation(self):
        evaluation = copy.deepcopy(self.settings)
        evaluation.evalAlgorithmList = copy.deepcopy( self.evalAlgorithmList )
        evaluation.settingsName = self.settingsName
        return evaluation
        
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
            self.evaluationConfigurationChanged.emit( self.settingsDict )
        self.checkSettingsSavable(False)
        
    def onRemove(self):
        name = str(self.comboBox.currentText())
        if name != '':
            if name in self.settingsDict:
                self.settingsDict.pop(name)
            idx = self.comboBox.findText(name)
            if idx>=0:
                self.comboBox.removeItem(idx)
            self.evaluationConfigurationChanged.emit( self.settingsDict )
       
    def onLoad(self,name):
        self.settingsName = str(name)
        if self.settingsName !='' and self.settingsName in self.settingsDict:
            self.setSettings(self.settingsDict[self.settingsName])
        self.checkSettingsSavable()

    def loadSetting(self, name):
        if name and self.comboBox.findText(name)>=0:
            self.comboBox.setCurrentIndex( self.comboBox.findText(name) )  
            self.onLoad(name)      

    def onReload(self):
        self.onLoad( self.comboBox.currentText() )
   
    def onIntegrationChanged(self, value):
        self.settings.integrateTimestamps = value
        self.checkSettingsSavable()
        
    def onAlgorithmValueChanged(self, algo, name, value):
        self.checkSettingsSavable()

    def onIntegrateHistogramClicked(self, state):
        self.settings.integrateHistogram = self.integrateHistogramCheckBox.isChecked()
        self.checkSettingsSavable()
 
    def onHistogramBinsChanged(self, bins):
        self.settings.histogramBins = bins
        self.checkSettingsSavable()
        
    def onAlgorithmNameChanged(self, name):
        self.checkSettingsSavable()
        
    def editEvaluationTable(self, index):
        if index.column() in [0,1,2,4]:
            self.evalTableView.edit(index)
            
if __name__=="__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = EvaluationControl(config,"parent")
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
        