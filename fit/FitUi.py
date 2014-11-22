import copy
import logging

from PyQt4 import QtGui, QtCore
import PyQt4.uic

from fit.FitFunctionBase import fitFunctionMap, ResultRecord, PushVariable
from fit.FitResultsTableModel import FitResultsTableModel
from fit.FitUiTableModel import FitUiTableModel
from modules.HashableDict import HashableDict
from modules.MagnitudeUtilit import value
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.SequenceDict import SequenceDict
from PushVariableTableModel import PushVariableTableModel
from modules.Utility import unique
from uiModules.ComboBoxDelegate import ComboBoxDelegate
from externalParameter.persistence import DBPersist
import time
from modules.magnitude import is_magnitude
from modules.PyqtUtility import BlockSignals

fitForm, fitBase = PyQt4.uic.loadUiType(r'ui\FitUi.ui')

class DatabasePushDestination:
    def __init__(self, space):
        self.persist = DBPersist()
        self.space = space
    
    def update(self, pushlist, upd_time=None ):
        upd_time = time.time() if upd_time is None else upd_time
        for _, variable, value in pushlist:
            if is_magnitude(value):
                value, unit = value.toval(returnUnit=True)
            else:
                unit = None
            self.persist.persist(self.space, variable, upd_time, value, unit)
    
    def keys(self):
        return (source for (space,source) in self.persist.sourceDict().keys() if space == self.space) 
    

class AnalysisDefinition(object):
    def __init__(self, name=None, fitfunctionName=None ):
        self.name = name
        self.fitfunctionName = fitfunctionName
        self.startParameters = tuple()
        self.parameterEnabled = tuple()
        self.results = HashableDict()
        self.pushVariables = tuple()
        self.startParameterExpressions = None
        self.useSmartStartValues = False

    def fitfunction(self):
        fitfunction = fitFunctionMap[self.fitfunctionName]()
        fitfunction.startParameters = list(self.startParameters)
        fitfunction.parameterEnabled = list(self.parameterEnabled)
        fitfunction.pushVariables = SequenceDict( (v.key, copy.deepcopy(v)) for v in self.pushVariables) 
        fitfunction.useSmartStartValues = self.useSmartStartValues
        fitfunction.startParameterExpressions = list(self.startParameterExpressions) if self.startParameterExpressions is not None else [None]*len(self.startParameters)
        return fitfunction
    
    @classmethod
    def fromFitfunction(cls, fitfunction):
        instance = cls( name=None, fitfunctionName=fitfunction.name )
        instance.startParameters = tuple(fitfunction.startParameters)
        instance.parameterEnabled = tuple(fitfunction.parameterEnabled)
        instance.startParameterExpressions = tuple(fitfunction.startParameterExpressions) if fitfunction.startParameterExpressions is not None else tuple([None]*len(fitfunction.startParameters))
        instance.useSmartStartValues = fitfunction.useSmartStartValues
        for result in fitfunction.results.values():
            instance.results[result.name] = ResultRecord(name=result.name, definition=result.definition)
        instance.pushVariables = tuple( (copy.deepcopy(v) for v in fitfunction.pushVariables.values()) )
        return instance
     
    stateFields = ['name', 'fitfunctionName', 'startParameters', 'parameterEnabled', 'results', 'pushVariables', 'useSmartStartValues', 'startParameterExpressions'] 
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault( 'pushVariables', tuple() )
        self.__dict__.setdefault( 'startParameterExpressions', None )
        self.__dict__.setdefault( 'useSmartStartValues', False )
            
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
        self.fitfunctionCache = self.config.get(self.configname+"FitfunctionCache", dict() )
        self.analysisDefinitions = self.config.get(self.configname+"AnalysisDefinitions", dict())
        self.pushDestinations = dict()
        self.globalDict = globalDict
            
    def setupUi(self,widget):
        fitForm.setupUi(self,widget)
        self.fitButton.clicked.connect( self.onFit )
        self.plotButton.clicked.connect( self.onPlot )
        self.pushToGlobalButton.clicked.connect( self.onPush )
        self.removePlotButton.clicked.connect( self.onRemoveFit )
        self.extractButton.clicked.connect( self.onExtractFit )
        self.copyButton.clicked.connect( self.onCopy )
        self.removeAnalysisButton.clicked.connect( self.onRemoveAnalysis )
        self.saveButton.clicked.connect( self.onSaveAnalysis )
        self.reloadButton.clicked.connect( self.onLoadAnalysis )
        self.fitSelectionComboBox.addItems( sorted(fitFunctionMap.keys()) )
        self.fitSelectionComboBox.currentIndexChanged[QtCore.QString].connect( self.onFitfunctionChanged )
        self.fitfunctionTableModel = FitUiTableModel(self.config)
        self.parameterTableView.setModel(self.fitfunctionTableModel)
        self.magnitudeDelegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.parameterTableView.setItemDelegateForColumn(2,self.magnitudeDelegate)
        self.fitResultsTableModel = FitResultsTableModel(self.config)
        self.resultsTableView.setModel(self.fitResultsTableModel)
        self.pushTableModel = PushVariableTableModel(self.config)
        self.pushTableView.setModel( self.pushTableModel )
        self.pushItemDelegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.pushComboDelegate = ComboBoxDelegate()
        self.pushTableView.setItemDelegateForColumn(1,self.pushComboDelegate)
        self.pushTableView.setItemDelegateForColumn(2,self.pushComboDelegate)
        self.pushTableView.setItemDelegateForColumn(4,self.pushItemDelegate)
        self.pushTableView.setItemDelegateForColumn(5,self.pushItemDelegate)
        self.pushTableView.setItemDelegateForColumn(6,self.pushItemDelegate)
        self.onFitfunctionChanged(str(self.fitSelectionComboBox.currentText()))
        if self.configname+'splitter' in self.config:
            self.splitter.restoreState( self.config[self.configname+'splitter'])
        # Analysis stuff
        lastAnalysisName = self.config.get(self.configname+"LastAnalysis", None)
        self.analysisNameComboBox.addItems( self.analysisDefinitions.keys() )
        self.analysisNameComboBox.currentIndexChanged[QtCore.QString].connect( self.onLoadAnalysis )
        if lastAnalysisName and lastAnalysisName in self.analysisDefinitions:
            self.analysisNameComboBox.setCurrentIndex( self.analysisNameComboBox.findText(lastAnalysisName))
        fitfunction = self.config.get(self.configname+"LastFitfunction",None)
        if fitfunction:
            self.setFitfunction( fitfunction )
            self.fitSelectionComboBox.setCurrentIndex( self.fitSelectionComboBox.findText(self.fitfunction.name) )
        self.addPushVariable.clicked.connect( self.onAddPushVariable )
        self.removePushVariable.clicked.connect( self.onRemovePushVariable )
        self.checkBoxUseSmartStartValues.stateChanged.connect( self.onUseSmartStartValues )
        self.pushDestinations['Database'] = DatabasePushDestination('fit')
        


    def onUseSmartStartValues(self, state):
        self.fitfunction.useSmartStartValues = state==QtCore.Qt.Checked

    def onAddPushVariable(self):
        self.pushTableModel.addVariable( PushVariable() )
    
    def onRemovePushVariable(self):
        for index in sorted(unique([ i.row() for i in self.pushTableView.selectedIndexes() ]),reverse=True):
            self.pushTableModel.removeVariable(index)
             
    def onFitfunctionChanged(self, name):
        name = str(name)
        if self.fitfunction:
            self.fitfunctionCache[self.fitfunction.name] = self.fitfunction
        if name in self.fitfunctionCache:
            self.setFitfunction( self.fitfunctionCache[name] )
        else:
            self.setFitfunction( fitFunctionMap[name]() )
        
    def setFitfunction(self, fitfunction):
        self.fitfunction = fitfunction
        self.fitfunction.updatePushVariables( self.globalDict )
        self.fitfunctionTableModel.setFitfunction(self.fitfunction)
        self.fitResultsTableModel.setFitfunction(self.fitfunction)
        self.pushTableModel.setFitfunction(self.fitfunction)
        self.parameterTableView.resizeColumnsToContents()
        self.descriptionLabel.setText( self.fitfunction.functionString )
        if str(self.fitSelectionComboBox.currentText())!= self.fitfunction.name:
            self.fitSelectionComboBox.setCurrentIndex(self.fitSelectionComboBox.findText(self.fitfunction.name))
        self.resultsTableView.resizeColumnsToContents()
        self.pushTableView.resizeColumnsToContents()
        self.checkBoxUseSmartStartValues.setChecked( self.fitfunction.useSmartStartValues )
        self.evaluate()
        
    def onFit(self):
        for plot in self.traceui.selectedPlottedTraces(defaultToLastLine=True, allowUnplotted=False):
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
            self.pushTableModel.fitDataChanged( self.globalDict )
            
    def addPushDestination(self, name, destination ):
        self.pushDestinations[name] = destination
        self.pushTableModel.updateDestinations(self.pushDestinations )

    def onPush(self):
        for destination, variable, value in self.fitfunction.pushVariableValues():
            if destination in self.pushDestinations:
                self.pushDestinations[destination].update( [(destination,variable,value)] )
                
    def pushVariables(self, pushVariables):
        for destination, variable, value in pushVariables:
            if destination in self.pushDestinations:
                self.pushDestinations[destination].update( [(destination,variable,value)] )

    def showAnalysis(self, analysis, fitfunction):
        if analysis in self.analysisDefinitions:
            with BlockSignals(self.analysisNameComboBox):
                self.analysisNameComboBox.setCurrentIndex( self.analysisNameComboBox.findText(analysis) )
            self.setFitfunction( fitfunction )
                
    def onPlot(self):
        for plot in self.traceui.selectedPlottedTraces(defaultToLastLine=True, allowUnplotted=False):
            fitfunction = copy.deepcopy(self.fitfunction)
            fitfunction.parameters = [value(param) for param in fitfunction.startParameters]
            plot.fitFunction = fitfunction
            plot.plot(-2)
            fitfunction.update()
                
    def onRemoveFit(self):
        for plot in self.traceui.selectedPlottedTraces(defaultToLastLine=True):
            plot.fitFunction = None
            plot.plot(-2)
    
    def onExtractFit(self):
        logger = logging.getLogger(__name__)
        plots = self.traceui.selectedPlottedTraces(defaultToLastLine=True)
        logger.debug( "onExtractFit {0} plots selected".format(len(plots) ) )
        if plots:
            plot = plots[0]
            self.setFitfunction( copy.deepcopy(plot.fitFunction))
            self.fitSelectionComboBox.setCurrentIndex( self.fitSelectionComboBox.findText(self.fitfunction.name))
            self.fitfunction.updatePushVariables()
    
    def onCopy(self):
        self.fitfunction.startParameters = copy.deepcopy(self.fitfunction.parameters)
        self.fitfunctionTableModel.startDataChanged()
    
    def saveConfig(self):
        if self.fitfunction is not None:
            self.fitfunctionCache[self.fitfunction.name] = self.fitfunction
        self.config[self.configname+"FitfunctionCache"] = self.fitfunctionCache
        self.config[self.configname+'Splitter'] = self.splitter.saveState()
        self.config[self.configname+"AnalysisDefinitions"] = self.analysisDefinitions
        self.config[self.configname+"LastAnalysis"] = str(self.analysisNameComboBox.currentText()) 
        self.config[self.configname+"LastFitfunction"] = self.fitfunction
            
    def saveState(self):
        pass
    
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
        definition = AnalysisDefinition.fromFitfunction(self.fitfunction)
        definition.name = name
        isNew = name not in self.analysisDefinitions
        self.analysisDefinitions[name] = definition
        if self.analysisNameComboBox.findText(name)<0:
            self.analysisNameComboBox.addItem(name)
        if isNew:
            self.analysisNamesChanged.emit( self.analysisDefinitions.keys() )
        
    def onLoadAnalysis(self, name=None):
        name = str(name) if name is not None else str(self.analysisNameComboBox.currentText())
        if name in self.analysisDefinitions:
            if AnalysisDefinition.fromFitfunction(self.fitfunction) != self.analysisDefinitions[name]:
                self.setFitfunction( self.analysisDefinitions[name].fitfunction() )
        
    def analysisNames(self):
        return self.analysisDefinitions.keys()
    
    def analysisFitfunction(self, name):
        return self.analysisDefinitions[name].fitfunction()

    def evaluate(self, name=None):
        self.fitfunction.evaluate( self.globalDict )
        self.fitfunctionTableModel.update()
        self.parameterTableView.viewport().repaint()
        self.pushTableModel.update()
        self.pushTableView.viewport().repaint()
            
