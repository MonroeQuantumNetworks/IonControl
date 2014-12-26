'''
Created on Dec 19, 2014

@author: pmaunz
'''
import PyQt4.uic
import logging
from modules.SequenceDict import SequenceDict
from scan.AnalysisTableModel import AnalysisTableModel             #@UnresolvedImport
from modules.GuiAppearance import saveGuiState, restoreGuiState    #@UnresolvedImport
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from uiModules.ComboBoxDelegate import ComboBoxDelegate
from scan.PushVariable import PushVariable                         #@UnresolvedImport
from modules.Utility import unique
import copy
from PyQt4 import QtCore, QtGui
from scan.PushVariableTableModel import PushVariableTableModel     #@UnresolvedImport
from scan.DatabasePushDestination import DatabasePushDestination   #@UnresolvedImport
from modules.firstNotNone import firstNotNone
from fit.FitUiTableModel import FitUiTableModel
from fit.FitResultsTableModel import FitResultsTableModel
from fit.FitFunctionBase import fitFunctionMap
from fit.StoredFitFunction import StoredFitFunction                #@UnresolvedImport
from modules.MagnitudeUtilit import value
from modules.PyqtUtility import BlockSignals

ControlForm, ControlBase = PyQt4.uic.loadUiType(r'ui\AnalysisControl.ui')

class AnalysisDefinitionElement(object):
    def __init__(self):
        self.enabled = True
        self.evaluation = None
        self.fitfunctionName = None
        self.pushVariables = SequenceDict()
        self.fitfunction = None
        self.fitfunctionCache = dict()
        
    def __setstate__(self, state):
        self.__dict__ = state
        
    stateFields = ['enabled', 'evaluation', 'fitfunctionName', 'pushVariables', 'fitfunction', 'fitfunctionCache'] 
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))
    
    def pushVariableValues(self):
        """get all push variable values that are within the bounds, no re-evaluation"""
        pushVarValues = list()
        for pushvar in self.pushVariables.values():
            pushVarValues.extend( pushvar.pushRecord() )
        return pushVarValues
    
    def updatePushVariables(self, replacements ):
        for pushvar in self.pushVariables.itervalues():
            pushvar.evaluate( replacements )
            
class AnalysisControlParameters(object):
    def __init__(self):
        self.autoSave = False

class AnalysisControl(ControlForm, ControlBase ):
    def __init__(self, config, globalDict, parentname, evaluationNames, parent=None):
        ControlForm.__init__(self)
        ControlBase.__init__(self,parent)
        self.config = config
        self.configname = 'AnalysisControl.'+parentname
        self.globalDict = globalDict.variables
        self.evaluationNames = evaluationNames
        # History and Dictionary
        try:
            self.analysisDefinitionDict = self.config.get(self.configname+'.dict',dict())
        except TypeError:
            logging.getLogger(__name__).info( "Unable to read scan control settings dictionary. Setting to empty dictionary." )
            self.analysisDefinitionDict = dict()
        try:
            self.analysisDefinition = self.config.get(self.configname,list())
        except Exception:
            logging.getLogger(__name__).info( "Unable to read scan control settings. Setting to new scan." )
            self.analysisDefinition = list()
        self.pushDestinations = dict()
        self.currentAnalysisName =  self.config.get(self.configname+'.settingsName',None)
        self.currentEvaluation = None
        self.fitfunction = None
        self.plottedTraceDict = None
        self.parameters = self.config.get( self.configname+'.parameters', AnalysisControlParameters() )
        
    def setupUi(self, parent):
        ControlForm.setupUi(self,parent)
        # History and Dictionary
        self.removeAnalysisConfigurationButton.clicked.connect( self.onRemoveAnalysisConfiguration )
        self.saveButton.clicked.connect( self.onSave )
        self.reloadButton.clicked.connect( self.onReload )
        self.addAnalysisButton.clicked.connect( self.onAddAnalysis )
        self.removeAnalysisButton.clicked.connect( self.onRemoveAnalysis )
        self.addPushButton.clicked.connect( self.onAddPushVariable )
        self.removePushButton.clicked.connect( self.onRemovePushVariable )
        self.pushButton.clicked.connect( self.onPush )
        self.fitButton.clicked.connect( self.onFit )
        self.fitAllButton.clicked.connect( self.onFitAll )
        self.plotButton.clicked.connect( self.onPlot )
        self.removePlotButton.clicked.connect( self.onRemoveFit )
        self.extractButton.clicked.connect( self.onExtractFit )
        self.fitToStartButton.clicked.connect( self.onFitToStart )
        self.checkBoxUseSmartStartValues.stateChanged.connect( self.onUseSmartStart )
        self.analysisComboDelegate = ComboBoxDelegate()
        self.analysisTableModel = AnalysisTableModel(self.analysisDefinition, self.config, self.globalDict, self.evaluationNames )
        self.analysisTableModel.fitfunctionChanged.connect( self.onFitfunctionChanged )
        self.analysisTableModel.analysisChanged.connect( self.autoSave )
        self.analysisTableView.setModel( self.analysisTableModel )
        self.analysisTableView.selectionModel().currentChanged.connect( self.onActiveAnalysisChanged )
        self.analysisTableView.setItemDelegateForColumn(1,self.analysisComboDelegate)
        self.analysisTableView.setItemDelegateForColumn(2,self.analysisComboDelegate)
        self.pushTableModel = PushVariableTableModel(self.config, self.globalDict)
        self.pushTableModel.pushChanged.connect( self.autoSave )
        self.pushTableView.setModel( self.pushTableModel )
        self.pushItemDelegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.pushComboDelegate = ComboBoxDelegate()
        for column in range(1,3):
            self.pushTableView.setItemDelegateForColumn(column,self.pushComboDelegate)
        for column in range(3,7):
            self.pushTableView.setItemDelegateForColumn(column,self.pushItemDelegate)
        self.pushDestinations['Database'] = DatabasePushDestination('fit')

        self.analysisConfigurationComboBox.addItems( self.analysisDefinitionDict.keys() )
        if self.currentAnalysisName in self.analysisDefinitionDict:
            self.analysisConfigurationComboBox.setCurrentIndex( self.analysisConfigurationComboBox.findText(self.currentAnalysisName))
        else:
            self.currentAnalysisName = str( self.analysisConfigurationComboBox.currentText() )
        self.analysisConfigurationComboBox.currentIndexChanged[QtCore.QString].connect( self.onLoadAnalysisConfiguration )
        # FitUi
        self.fitfunctionTableModel = FitUiTableModel(self.config)
        self.parameterTableView.setModel(self.fitfunctionTableModel)
        self.fitfunctionTableModel.parametersChanged.connect( self.autoSave )
        self.magnitudeDelegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.parameterTableView.setItemDelegateForColumn(2,self.magnitudeDelegate)
        self.fitResultsTableModel = FitResultsTableModel(self.config)
        self.resultsTableView.setModel(self.fitResultsTableModel)
        restoreGuiState( self, self.config.get(self.configname+'.guiState') )
        self.setButtonEnabledState()
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.autoSaveAction = QtGui.QAction( "auto save" , self)
        self.autoSaveAction.setCheckable(True)
        self.autoSaveAction.setChecked(self.parameters.autoSave )
        self.autoSaveAction.triggered.connect( self.onAutoSave )
        self.addAction( self.autoSaveAction )
        self.autoSave()

    def onUseSmartStart(self, state):
        if self.fitfunction is not None:
            self.fitfunction.useSmartStartValues = state==QtCore.Qt.Checked
            self.autoSave()

    def setButtonEnabledState(self):
        allEnable = self.plottedTraceDict is not None
        currentEnable = self.plottedTraceDict is not None and self.currentEvaluation is not None and self.currentEvaluation.evaluation in self.plottedTraceDict
        self.fitAllButton.setEnabled( allEnable )
        self.getSmartStartButton.setEnabled( currentEnable )
        self.fitButton.setEnabled( currentEnable ) 
        self.plotButton.setEnabled( currentEnable )
        self.removePlotButton.setEnabled( currentEnable )
        self.extractButton.setEnabled( currentEnable )
            
    def onFitfunctionChanged(self, row, newfitname ):
        """Swap out the fitfunction on the current analysis"""
        self.currentEvaluation.fitfunctionCache[self.fitfunction.name] = StoredFitFunction.fromFitfunction( self.fitfunction )
        self.currentEvaluation.fitfunctionName = newfitname
        if newfitname in self.currentEvaluation.fitfunctionCache:
            self.currentEvaluation.fitfunction = self.currentEvaluation.fitfunctionCache[newfitname]
            self.setFitfunction(  self.currentEvaluation.fitfunction.fitfunction() )
        else:
            self.setFitfunction( fitFunctionMap[newfitname]() )
            self.currentEvaluation.fitfunction = StoredFitFunction.fromFitfunction(self.fitfunction)
        self.pushTableModel.setPushVariables(self.currentEvaluation.pushVariables, self.fitfunction)
            
    def onActiveAnalysisChanged(self, selected, deselected=None):
        if deselected and self.fitfunction:
            self.currentEvaluation.fitfunction = StoredFitFunction.fromFitfunction(self.fitfunction)
        self.currentEvaluation = self.analysisDefinition[selected.row()]
        self.currentEvaluationLabel.setText( "{0} - {1}".format(self.currentEvaluation.evaluation, self.currentEvaluation.fitfunctionName) )
        if self.currentEvaluation.fitfunction:
            self.setFitfunction( self.currentEvaluation.fitfunction.fitfunction() )
        self.pushTableModel.setPushVariables(self.currentEvaluation.pushVariables, self.fitfunction)
        self.setButtonEnabledState()
            
    def onRemoveAnalysis(self):
        for index in sorted(unique([ i.row() for i in self.analysisTableView.selectedIndexes() ]),reverse=True):
            self.analysisTableModel.removeAnalysis(index)
    
    def onAddAnalysis(self):
        self.analysisTableModel.addAnalysis( AnalysisDefinitionElement() )
        
    def onAddPushVariable(self):
        self.pushTableModel.addVariable( PushVariable() )
    
    def onRemovePushVariable(self):
        for index in sorted(unique([ i.row() for i in self.pushTableView.selectedIndexes() ]),reverse=True):
            self.pushTableModel.removeVariable(index)

    def addPushDestination(self, name, destination ):
        self.pushDestinations[name] = destination
        self.pushTableModel.updateDestinations(self.pushDestinations )

    def onPush(self):
        self.push(self.currentEvaluation)

    def push(self, evaluation ):
        for destination, variable, value in evaluation.pushVariableValues():
            if destination in self.pushDestinations:
                self.pushDestinations[destination].update( [(destination,variable,value)] )
                
    def pushAll(self):
        for analysis in self.analysisDefinition:
            self.push( analysis )
                
    def pushVariables(self, pushVariables):
        for destination, variable, value in pushVariables:
            if destination in self.pushDestinations:
                self.pushDestinations[destination].update( [(destination,variable,value)] )

    def onAutoSave(self, checked):
        self.parameters.autoSave = checked
        self.autoSave()
        
    def autoSave(self):
        if self.parameters.autoSave:
            self.onSave()
            self.saveButton.setEnabled( False )
        else:
            self.saveButton.setEnabled( self.saveable() )
            
    def saveable(self):
        analysisName = str(self.analysisConfigurationComboBox.currentText())
        if self.currentEvaluation is not None and self.fitfunction is not None:
            self.currentEvaluation.fitfunction = StoredFitFunction.fromFitfunction( self.fitfunction )
        return analysisName != '' and not (self.analysisDefinitionDict[self.currentAnalysisName] == self.analysisDefinition)            
                
    def saveConfig(self):
        self.config[self.configname+'.dict'] = self.analysisDefinitionDict
        self.config[self.configname] = self.analysisDefinition
        self.config[self.configname+'.settingsName'] = self.currentAnalysisName
        self.config[self.configname+'.guiState'] = saveGuiState( self )
        self.config[self.configname+'.parameters'] = self.parameters
    
    def onSave(self):
        self.currentAnalysisName = str(self.analysisConfigurationComboBox.currentText())
        if self.currentAnalysisName != '':
            if self.currentAnalysisName not in self.analysisDefinitionDict:
                if self.analysisConfigurationComboBox.findText(self.currentAnalysisName)==-1:
                    self.analysisConfigurationComboBox.addItem(self.currentAnalysisName)
            self.analysisDefinitionDict[self.currentAnalysisName] = copy.deepcopy(self.analysisDefinition)
            self.saveButton.setEnabled( False )
        
    def onRemoveAnalysisConfiguration(self):
        name = str(self.analysisConfigurationComboBox.currentText())
        if name != '':
            if name in self.analysisDefinitionDict:
                self.analysisDefinitionDict.pop(name)
            idx = self.analysisConfigurationComboBox.findText(name)
            if idx>=0:
                self.analysisConfigurationComboBox.removeItem(idx)
       
    def onLoadAnalysisConfiguration(self,name):
        name = str(name)
        if name and name in self.analysisDefinitionDict:
            self.currentAnalysisName = name
            self.setAnalysisDefinition( self.analysisDefinitionDict[name] )
            self.onActiveAnalysisChanged(self.analysisTableModel.createIndex(0,0) )
            self.autoSave()
            if self.analysisConfigurationComboBox.currentText()!=name:
                with BlockSignals(self.analysisConfigurationComboBox):
                    self.analysisConfigurationComboBox.setCurrentIndex( self.analysisConfigurationComboBox.findText(name) )

    def setAnalysisDefinition(self, analysisDef ):
        self.analysisDefinition = copy.deepcopy(analysisDef)
        self.analysisTableModel.setAnalysisDefinition( self.analysisDefinition)

    def onReload(self):
        self.onLoadAnalysisConfiguration( self.analysisConfigurationComboBox.currentText() )
   
    def updatePushVariables(self, extraDict=None ):
        myReplacementDict = self.replacementDict()
        if extraDict is not None:
            myReplacementDict.update( extraDict )
        for pushvar in self.pushVariables.values():
            try:          
                pushvar.evaluate(myReplacementDict)
            except Exception as e:
                logging.getLogger(__name__).error( str(e) )

    def onFit(self):
        self.fit( self.currentEvaluation )

    def fit(self, evaluation):
        if self.currentEvaluation is not None and evaluation == self.currentEvaluation:
            plot = self.plottedTraceDict.get( evaluation.evaluation )
            if plot is not None:
                sigma = None
                if plot.hasHeightColumn:
                    sigma = plot.height
                elif plot.hasTopColumn and plot.hasBottomColumn:
                    sigma = abs(plot.top + plot.bottom)
                self.fitfunction.leastsq(plot.x,plot.y,sigma=sigma)
                plot.fitFunction = copy.deepcopy(self.fitfunction)
                plot.plot(-2)
                self.fitfunctionTableModel.fitDataChanged()
                self.fitResultsTableModel.fitDataChanged()
                replacements = self.fitfunction.replacementDict()
                replacements.update( self.globalDict )
                evaluation.updatePushVariables( replacements )
        else:
            fitfunction = evaluation.fitfunction.fitfunction()
            fitfunction.evaluate( self.globalDict )
            plot = self.plottedTraceDict.get( evaluation.evaluation )
            if plot is not None:
                sigma = None
                if plot.hasHeightColumn:
                    sigma = plot.height
                elif plot.hasTopColumn and plot.hasBottomColumn:
                    sigma = abs(plot.top + plot.bottom)
                fitfunction.leastsq(plot.x,plot.y,sigma=sigma)
                plot.fitFunction = fitfunction
                plot.plot(-2)
                evaluation.fitfunction = StoredFitFunction.fromFitfunction(fitfunction)
                self.fitfunctionTableModel.fitDataChanged()
                self.fitResultsTableModel.fitDataChanged()
                replacements = fitfunction.replacementDict()
                replacements.update( self.globalDict )
                evaluation.updatePushVariables( replacements )
            
    def onPlot(self):
        if self.currentEvaluation is not None:
            plot = self.plottedTraceDict.get( self.currentEvaluation.evaluation )
            fitfunction = copy.deepcopy(self.fitfunction)
            fitfunction.parameters = [value(param) for param in fitfunction.startParameters]
            plot.fitFunction = fitfunction
            plot.plot(-2)
            fitfunction.update()
                    
    def onFitAll(self):
        self.fitAll()
        
    def fitAll(self):
        for evaluation in self.analysisDefinition:
            self.fit(evaluation)
    
    def onLoadFitFunction(self, name=None):
        name = str(name) if name is not None else str(self.analysisNameComboBox.currentText())
        if name in self.analysisDefinitions:
            if StoredFitFunction.fromFitfunction(self.fitfunction) != self.analysisDefinitions[name]:
                self.setFitfunction( self.analysisDefinitions[name].fitfunction() )

    def setFitfunction(self, fitfunction):
        self.fitfunction = fitfunction
        self.fitfunctionTableModel.setFitfunction(self.fitfunction)
        self.fitResultsTableModel.setFitfunction(self.fitfunction)
        self.descriptionLabel.setText( self.fitfunction.functionString )
        self.fitfunction.useSmartStartValues = self.fitfunction.useSmartStartValues and self.fitfunction.hasSmartStart
        self.checkBoxUseSmartStartValues.setChecked( self.fitfunction.useSmartStartValues )
        self.checkBoxUseSmartStartValues.setEnabled( self.fitfunction.hasSmartStart )
        self.evaluate()

    def setPlottedTraceDict(self, plottedTraceDict):
        self.plottedTraceDict = plottedTraceDict
        self.setButtonEnabledState()

    def analyze(self, plottedTraceDict ):
        self.setPlottedTraceDict(plottedTraceDict)
        self.fitAll()
        self.pushAll()

    def evaluate(self, name=None):
        if self.fitfunction is not None:
            self.fitfunction.evaluate( self.globalDict )
            self.fitfunctionTableModel.update()
            self.parameterTableView.viewport().repaint()
            replacements = self.fitfunction.replacementDict()
            replacements.update( self.globalDict )
            self.currentEvaluation.updatePushVariables( replacements )
        
    def onRemoveFit(self):
        if self.currentEvaluation is not None:
            plot = self.plottedTraceDict.get( self.currentEvaluation.evaluation )
            plot.fitFunction = None
            plot.plot(-2)

    def onExtractFit(self):
        if self.currentEvaluation is not None:
            plot = self.plottedTraceDict.get( self.currentEvaluation.evaluation )
            self.setFitfunction( copy.deepcopy(plot.fitFunction))
            
    def onFitToStart(self):
        if self.fitfunction is not None:
            self.fitfunction.startParameters = copy.deepcopy(self.fitfunction.parameters)
            self.fitfunctionTableModel.startDataChanged()
    
if __name__=="__main__":
    import sys
    from PyQt4 import QtGui
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = AnalysisControl(config,dict(),"parent")
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())



