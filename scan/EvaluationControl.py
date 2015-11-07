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

from scan.EvaluationBase import EvaluationAlgorithms
from EvaluationTableModel import EvaluationTableModel
from modules import MagnitudeUtilit, DataDirectory
from modules.HashableDict import HashableDict
from modules.Utility import unique
from modules.magnitude import mg, MagnitudeError
from uiModules.ComboBoxDelegate import ComboBoxDelegate
from modules.enum import enum
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from uiModules.CamelionDelegate import CamelionDelegate
from cPickle import UnpicklingError
from scan.AbszisseType import AbszisseType
import xml.etree.ElementTree as ElementTree
from modules.XmlUtilit import prettify, xmlEncodeAttributes, xmlEncodeDictionary,\
    xmlParseAttributes, xmlParseDictionary
from ProjectConfig.Project import getProject

import os
uipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\EvaluationControl.ui')
ControlForm, ControlBase = PyQt4.uic.loadUiType(uipath)


class EvaluationDefinition(object):
    AbszisseType = enum( 'x', 'time', 'index' )
    XMLTagName = "EvaluationItem"
    def __init__(self):
        self.counter = None
        self.evaluation = None
        self.settings = HashableDict()
        self.name = None
        self.plotname = None
        self.settingsCache = HashableDict()
        self.showHistogram = False
        self.analysis = None
        self.counterId = 0
        self.type = 'Counter'
        self.abszisse = AbszisseType.x
        
    def __setstate__(self, state):
        self.__dict__ = state
        if 'errorBars' in self.settings:   # remove errorBars property in old unpickled instances
            self.settings.pop('errorBars')
        self.__dict__.setdefault( 'analysis', None )
        self.__dict__.setdefault( 'counterId', 0 )
        self.__dict__.setdefault( 'type', 'Counter' )
        self.__dict__.setdefault( 'abszisse', AbszisseType.x )
        
    stateFields = ['counterId', 'type', 'counter', 'evaluation', 'settings', 'settingsCache', 'name', 'plotname', 'showHistogram', 'analysis', 'abszisse'] 
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        if not isinstance(self.settings,HashableDict):
            logging.getLogger(__name__).info("Replacing dict with hashable dict")
            self.settings = HashableDict(self.settings)
        return hash(tuple(getattr(self,field) for field in self.stateFields))
 
    @property
    def channelKey(self):
        if self.type=='Counter':
            return ((self.counterId&0xff)<<8) | (self.counter & 0xff)
        else:
            return (self.counter & 0xff)
        
    def getChannelData(self, data ):
        if self.type=='Counter':
            return data.count[self.channelKey]  
        elif data.result is not None:
            return data.result[self.channelKey]
        return []

    def exportXml(self, element):
        myElement = ElementTree.SubElement(element, self.XMLTagName )
        xmlEncodeAttributes( self.__dict__, myElement )
        xmlEncodeDictionary( self.settings, myElement, "Parameter")
        return myElement 
    
    @staticmethod
    def fromXmlElement( element, flat=False ):
        myElement = element if flat else element.find( EvaluationDefinition.XMLTagName )
        e = EvaluationDefinition()
        e.__dict__.update( xmlParseAttributes( myElement ))
        e.settings = xmlParseDictionary( myElement, "Parameter")
        return e   

class Evaluation:
    XMLTagName = "Evaluation"
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
        self.__dict__.setdefault('histogramBins',50)

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
    
    def exportXml(self, element, attrib):
        myElement = ElementTree.SubElement(element, Evaluation.XMLTagName, attrib=attrib )
        xmlEncodeAttributes(self.__dict__, myElement)
        for evaluation in self.evalList:
            evaluation.exportXml(myElement)
        return myElement     
    
    @staticmethod
    def fromXmlElement( element ):
        myElement = element if element.tag==Evaluation.XMLTagName else element.find(Evaluation.XMLTagName)
        e = Evaluation()
        e.__dict__.update( xmlParseAttributes(myElement) )
        e.evalList = [ EvaluationDefinition.fromXmlElement(e, flat=True) for e in myElement.findall(EvaluationDefinition.XMLTagName)]
        return (myElement.attrib['name'],e)

class EvaluationControlParameters:
    def __init__(self):
        self.autoSave = True

class EvaluationControl(ControlForm, ControlBase ):
    evaluationConfigurationChanged = QtCore.pyqtSignal( object )
    currentEvaluationChanged = QtCore.pyqtSignal( object )
    integrationMode = enum('IntegrateAll','IntegrateRun','NoIntegration')
    logger = logging.getLogger(__name__)
    def __init__(self, config, globalDict, parentname, plotnames=None, parent=None, analysisNames=None, counterNames=None):
        logger = logging.getLogger(__name__)
        ControlForm.__init__(self)
        ControlBase.__init__(self,parent)
        self.config = config
        self.configname = 'EvaluationControl.'+parentname
        self.globalDict = globalDict
        self.ppDict = None
        self.counterNames = counterNames
        # History and Dictionary
        try:
            self.settingsDict = self.config.get(self.configname+'.dict',dict())
        except (TypeError, UnpicklingError):
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
        self.project = getProject()
        self.timestampsEnabled = self.project.isEnabled('software', 'Timestamps')

    def setupUi(self, parent):
        ControlForm.setupUi(self,parent)
        # History and Dictionary
        self.saveButton.clicked.connect( self.onSave )
        self.removeButton.clicked.connect( self.onRemove )
        self.reloadButton.clicked.connect( self.onReload )
        self.evalTableModel = EvaluationTableModel( self.checkSettingsSavable, plotnames=self.plotnames, analysisNames=self.analysisNames, counterNames=self.counterNames )
        self.evalTableModel.dataChanged.connect( self.checkSettingsSavable )
        self.evalTableModel.dataChanged.connect( self.onActiveEvalChanged )
        self.evalTableView.setModel( self.evalTableModel )
        self.delegate = ComboBoxDelegate()
        self.magnitudeDelegate = MagnitudeSpinBoxDelegate()
        self.camelionDelegate = CamelionDelegate()
        self.evalTableView.setItemDelegateForColumn(0, self.delegate)
        self.evalTableView.setItemDelegateForColumn(1, self.magnitudeDelegate)
        self.evalTableView.setItemDelegateForColumn(2, self.camelionDelegate)
        self.evalTableView.setItemDelegateForColumn(3, self.delegate )
        self.evalTableView.setItemDelegateForColumn(6, self.delegate )
        self.evalTableView.setItemDelegateForColumn(7, self.delegate )
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
        if self.timestampsEnabled:
            self.binwidthSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'binwidth') )
            self.roiStartSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'roiStart') )
            self.roiWidthSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'roiWidth') )
            self.enableCheckBox.stateChanged.connect( functools.partial(self.onStateChanged, 'enableTimestamps' ) )
            self.saveRawDataCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'saveRawData' ) )
            self.integrateCombo.currentIndexChanged[int].connect( self.onIntegrationChanged )
            self.channelSpinBox.valueChanged.connect( functools.partial(self.onBareValueChanged, 'timestampsChannel') )
        else:
            self.settings.enableTimestamps = False
            timestampsWidget = self.toolBox.widget(1)
            self.toolBox.removeItem(1) #Remove timestamps from toolBox
            timestampsWidget.deleteLater() #Delete timestamps widget

        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.autoSaveAction = QtGui.QAction( "auto save" , self)
        self.autoSaveAction.setCheckable(True)
        self.autoSaveAction.setChecked(self.parameters.autoSave )
        self.autoSaveAction.triggered.connect( self.onAutoSave )
        self.addAction( self.autoSaveAction )
        self.currentEvaluationChanged.emit( self.settingsName )
        self.exportXmlButton.clicked.connect( self.onExportXml )

    def onExportXml(self, element=None, writeToFile=True):
        root = element if element is not None else ElementTree.Element('EvaluationList')
        for name, setting in self.settingsDict.iteritems():
            setting.exportXml(root,{'name':name})
        if writeToFile:
            filename = DataDirectory.DataDirectory().sequencefile("EvaluationList.xml")[0]
            with open(filename,'w') as f:
                f.write(prettify(root))
        return root
        
    def onImportXml(self, filename=None, mode="Add"):
        filename = filename if filename is not None else QtGui.QFileDialog.getOpenFileName(self, 'Import XML file', filer="*.xml" )
        tree = ElementTree.parse(filename)
        element = tree.getroot()
        self.importXml(element, mode=mode)
            
    def importXml(self, element, mode="Add"):   # modes: Replace, Update, Add
        newSettingsDict = dict( Evaluation.fromXmlElement(e) for e in element.findall(Evaluation.XMLTagName) )
        if mode == "Replace":
            self.settingsDict = newSettingsDict
        elif mode == "Update":
            self.settingsDict.update( newSettingsDict )
        elif mode == "Add":
            newSettingsDict.update( self.settingsCache )
            self.settingsDict = newSettingsDict

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
        if self.timestampsEnabled:
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
        algo =  EvaluationAlgorithms[evaluation.evaluation](globalDict=self.globalDict)
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
                    try:
                        savable = self.settingsDict[self.settingsName]!=self.settings or currentText!=self.settingsName
                    except AttributeError:
                        savable = True
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
        self.currentEvaluationChanged.emit( self.settingsName )        
        
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
        self.currentEvaluationChanged.emit( self.settingsName )

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
            
    def evaluationNames(self):
        return [e.name for e in self.settings.evalList]
            
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
        