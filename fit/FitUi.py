import copy
import logging

from PyQt4 import QtGui, QtCore
import PyQt4.uic

from fit.FitFunctionBase import fitFunctionMap
from fit.FitResultsTableModel import FitResultsTableModel
from fit.FitUiTableModel import FitUiTableModel
from modules.MagnitudeUtilit import value
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.PyqtUtility import BlockSignals
from modules.GuiAppearance import restoreGuiState, saveGuiState   #@UnresolvedImport
from fit.StoredFitFunction import StoredFitFunction               #@UnresolvedImport

import os
uipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\FitUi.ui')
fitForm, fitBase = PyQt4.uic.loadUiType(uipath)
            
class Parameters(object):
    def __init__(self):
        self.autoSave = False       

            
class FitUi(fitForm, QtGui.QWidget):
    analysisNamesChanged = QtCore.pyqtSignal(object)
    def __init__(self, traceui, config, parentname, globalDict=None, parent=None):
        QtGui.QWidget.__init__(self,parent)
        fitForm.__init__(self)
        self.config = config
        self.parentname = parentname
        self.fitfunction = None
        self.traceui = traceui
        self.configname = "FitUi.{0}.".format(parentname)
        try:
            self.fitfunctionCache = self.config.get(self.configname+"FitfunctionCache", dict() )
        except Exception:
            self.fitfunctionCache = dict()
        try:
            self.analysisDefinitions = self.config.get(self.configname+"AnalysisDefinitions", dict())
        except Exception:
            self.analysisDefinitions = dict()
        self.parameters = self.config.get(self.configname+".Parameters", Parameters())
        self.globalDict = globalDict
            
    def setupUi(self,widget, showCombos=True ):
        fitForm.setupUi(self,widget)
        self.fitButton.clicked.connect( self.onFit )
        self.plotButton.clicked.connect( self.onPlot )
        self.removePlotButton.clicked.connect( self.onRemoveFit )
        self.extractButton.clicked.connect( self.onExtractFit )
        self.getSmartStartButton.clicked.connect( self.onGetSmartStart )
        self.copyButton.clicked.connect( self.onCopy )
        self.removeAnalysisButton.clicked.connect( self.onRemoveAnalysis )
        self.saveButton.clicked.connect( self.onSaveAnalysis )
        self.reloadButton.clicked.connect( self.onLoadAnalysis )
        self.fitSelectionComboBox.addItems( sorted(fitFunctionMap.keys()) )
        self.fitSelectionComboBox.currentIndexChanged[QtCore.QString].connect( self.onFitfunctionChanged )
        self.fitfunctionTableModel = FitUiTableModel(self.config)
        self.fitfunctionTableModel.parametersChanged.connect( self.autoSave )
        self.parameterTableView.setModel(self.fitfunctionTableModel)
        self.magnitudeDelegate = MagnitudeSpinBoxDelegate(self.globalDict, emptyStringValue=None)
        self.parameterTableView.setItemDelegateForColumn(2,self.magnitudeDelegate)
        self.parameterTableView.setItemDelegateForColumn(3,self.magnitudeDelegate)
        self.parameterTableView.setItemDelegateForColumn(4,self.magnitudeDelegate)
        self.fitResultsTableModel = FitResultsTableModel(self.config)
        self.resultsTableView.setModel(self.fitResultsTableModel)
        self.onFitfunctionChanged(str(self.fitSelectionComboBox.currentText()))
        # Analysis stuff
        lastAnalysisName = self.config.get(self.configname+"LastAnalysis", None)
        self.analysisNameComboBox.addItems( self.analysisDefinitions.keys() )
        self.analysisNameComboBox.currentIndexChanged[QtCore.QString].connect( self.onLoadAnalysis )
        if lastAnalysisName and lastAnalysisName in self.analysisDefinitions:
            self.analysisNameComboBox.setCurrentIndex( self.analysisNameComboBox.findText(lastAnalysisName))
        try:
            fitfunction = self.config.get(self.configname+"LastFitfunction",None)
        except Exception:
            fitfunction = None
        if fitfunction:
            self.setFitfunction( fitfunction )
            self.fitSelectionComboBox.setCurrentIndex( self.fitSelectionComboBox.findText(self.fitfunction.name) )
        self.checkBoxUseSmartStartValues.stateChanged.connect( self.onUseSmartStartValues )
        self.useErrorBarsCheckBox.stateChanged.connect( self.onUseErrorBars )
        # Context Menu
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.autoSaveAction = QtGui.QAction( "auto save" , self)
        self.autoSaveAction.setCheckable(True)
        self.autoSaveAction.setChecked(self.parameters.autoSave )
        self.autoSaveAction.triggered.connect( self.onAutoSave )
        self.addAction( self.autoSaveAction )
        restoreGuiState( self, self.config.get(self.configname+".guiState") )
        if not showCombos:
            self.fitSelectionComboBox.setVisible( False )
            self.widget.setVisible( False )
        self.autoSave()
            
    def onAutoSave(self, state):
        self.parameters.autoSave = state
        self.autoSave()
            
    def onShowAnalysisEnabled(self, status):
        self.showAnalysisEnabled = status==QtCore.Qt.Checked
        
    def onUseSmartStartValues(self, state):
        self.fitfunction.useSmartStartValues = state==QtCore.Qt.Checked
        self.autoSave()

    def onUseErrorBars(self, state):
        self.fitfunction.useErrorBars = state==QtCore.Qt.Checked
        self.autoSave()

    def onFitfunctionChanged(self, name):
        name = str(name)
        if self.fitfunction:
            self.fitfunctionCache[self.fitfunction.name] = self.fitfunction
        if name in self.fitfunctionCache:
            self.setFitfunction( self.fitfunctionCache[name] )
        else:
            self.setFitfunction( fitFunctionMap[name]() )
        self.autoSave()
        
    def setFitfunction(self, fitfunction):
        self.fitfunction = fitfunction
        self.fitfunctionTableModel.setFitfunction(self.fitfunction)
        self.fitResultsTableModel.setFitfunction(self.fitfunction)
        self.descriptionLabel.setText( self.fitfunction.functionString )
        if str(self.fitSelectionComboBox.currentText())!= self.fitfunction.name:
            self.fitSelectionComboBox.setCurrentIndex(self.fitSelectionComboBox.findText(self.fitfunction.name))
        self.fitfunction.useSmartStartValues = self.fitfunction.useSmartStartValues and self.fitfunction.hasSmartStart
        self.checkBoxUseSmartStartValues.setChecked( self.fitfunction.useSmartStartValues )
        self.checkBoxUseSmartStartValues.setEnabled( self.fitfunction.hasSmartStart )
        self.useErrorBarsCheckBox.setChecked( self.fitfunction.useErrorBars )
        self.evaluate()
        
    def onGetSmartStart(self):
        for plot in self.traceui.selectedTraces(useLastIfNoSelection=True, allowUnplotted=False):
            smartParameters = self.fitfunction.enabledSmartStartValues(plot.x,plot.y,self.fitfunction.parameters)
            self.fitfunction.startParameters = list(smartParameters)
            self.fitfunctionTableModel.startDataChanged()     
        
    def onFit(self):
        for plot in self.traceui.selectedTraces(useLastIfNoSelection=True, allowUnplotted=False):
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
            
    def showAnalysis(self, analysis, fitfunction):
        if self.showAnalysisEnabled and analysis in self.analysisDefinitions:
            with BlockSignals(self.analysisNameComboBox):
                self.analysisNameComboBox.setCurrentIndex( self.analysisNameComboBox.findText(analysis) )
            self.setFitfunction( fitfunction )
                
    def onPlot(self):
        for plot in self.traceui.selectedTraces(useLastIfNoSelection=True, allowUnplotted=False):
            fitfunction = copy.deepcopy(self.fitfunction)
            fitfunction.parameters = [value(param) for param in fitfunction.startParameters]
            plot.fitFunction = fitfunction
            plot.plot(-2)
            fitfunction.update()
                
    def onRemoveFit(self):
        for plot in self.traceui.selectedTraces(useLastIfNoSelection=True):
            plot.fitFunction = None
            plot.plot(-2)
    
    def onExtractFit(self):
        logger = logging.getLogger(__name__)
        plots = self.traceui.selectedTraces(useLastIfNoSelection=True)
        logger.debug( "onExtractFit {0} plots selected".format(len(plots) ) )
        if plots:
            plot = plots[0]
            self.setFitfunction( copy.deepcopy(plot.fitFunction))
            self.fitSelectionComboBox.setCurrentIndex( self.fitSelectionComboBox.findText(self.fitfunction.name))
    
    def onCopy(self):
        self.fitfunction.startParameters = copy.deepcopy(self.fitfunction.parameters)
        self.fitfunctionTableModel.startDataChanged()
    
    def saveConfig(self):
        if self.fitfunction is not None:
            self.fitfunctionCache[self.fitfunction.name] = self.fitfunction
        self.config[self.configname+"FitfunctionCache"] = self.fitfunctionCache
        self.config[self.configname+"AnalysisDefinitions"] = self.analysisDefinitions
        self.config[self.configname+"LastAnalysis"] = str(self.analysisNameComboBox.currentText()) 
        self.config[self.configname+"LastFitfunction"] = self.fitfunction
        self.config[self.configname+".Parameters"] = self.parameters
        self.config[self.configname+".guiState"] = saveGuiState( self )
                
    def onRemoveAnalysis(self):
        name = str(self.analysisNameComboBox.currentText())
        if name in self.analysisDefinitions:
            self.analysisDefinitions.pop(name)
            index = self.analysisNameComboBox.findText(name)
            if index>=0:
                self.analysisNameComboBox.removeItem(index)
            self.analysisNamesChanged.emit( self.analysisDefinitions.keys() )

    def onSaveAnalysis(self):
        name = str(self.analysisNameComboBox.currentText())
        if name:
            definition = StoredFitFunction.fromFitfunction(self.fitfunction)
            definition.name = name
            isNew = name not in self.analysisDefinitions
            self.analysisDefinitions[name] = definition
            if self.analysisNameComboBox.findText(name)<0:
                self.analysisNameComboBox.addItem(name)
            if isNew:
                self.analysisNamesChanged.emit( self.analysisDefinitions.keys() )
            self.saveButton.setEnabled( False )
        
    def autoSave(self):
        if self.parameters.autoSave:
            self.onSaveAnalysis()
            self.saveButton.setEnabled( False )
        else:
            self.saveButton.setEnabled( self.saveable() )
 
    def saveable(self):
        name = str(self.analysisNameComboBox.currentText())       
        definition = StoredFitFunction.fromFitfunction(self.fitfunction)
        definition.name = name
        return name != '' and ( name not in self.analysisDefinitions or not (self.analysisDefinitions[name] == definition) )             
                       
    def onLoadAnalysis(self, name=None):
        name = str(name) if name is not None else str(self.analysisNameComboBox.currentText())
        if name in self.analysisDefinitions:
            if StoredFitFunction.fromFitfunction(self.fitfunction) != self.analysisDefinitions[name]:
                self.setFitfunction( self.analysisDefinitions[name].fitfunction() )
        
    def analysisNames(self):
        return self.analysisDefinitions.keys()
    
    def analysisFitfunction(self, name):
        return self.analysisDefinitions[name].fitfunction()

    def evaluate(self, name=None):
        self.fitfunction.evaluate( self.globalDict )
        self.fitfunctionTableModel.update()
        self.parameterTableView.viewport().repaint()
            
