import PyQt4.uic
from PyQt4 import QtGui, QtCore
from fit.FitFunctionBase import fitFunctionMap, ResultRecord
import copy
from fit.FitUiTableModel import FitUiTableModel
import logging
from MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.MagnitudeUtilit import value
from fit.FitResultsTableModel import FitResultsTableModel
from modules.HashableDict import HashableDict

fitForm, fitBase = PyQt4.uic.loadUiType(r'ui\FitUi.ui')

class AnalysisDefinition(object):
    def __init__(self, name=None, fitfunctionName=None ):
        self.name = name
        self.fitfunctionName = fitfunctionName
        self.startParameters = tuple()
        self.parameterEnabled = tuple()
        self.results = HashableDict()

    def fitfunction(self):
        fitfunction = fitFunctionMap[self.fitfunctionName]()
        fitfunction.startParameters = list(self.startParameters)
        fitfunction.parameterEnabled = list(self.parameterEnabled)
        for result in self.results.values():
            fitfunction.results[result.name].push = result.push
            fitfunction.results[result.name].globalname = result.globalname
        return fitfunction
    
    @classmethod
    def fromFitfunction(cls, fitfunction):
        instance = cls( name=None, fitfunctionName=fitfunction.name )
        instance.startParameters = tuple(fitfunction.startParameters)
        instance.parameterEnabled = tuple(fitfunction.parameterEnabled)
        for result in fitfunction.results.values():
            instance.results[result.name] = ResultRecord(name=result.name, definition=result.definition, globalname=result.globalname, push=result.push)
        return instance
     
    stateFields = ['name', 'fitfunctionName', 'startParameters', 'parameterEnabled', 'results'] 
        
    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(getattr(self,field) for field in self.stateFields))
        
            
class FitUi(fitForm, QtGui.QWidget):
    def __init__(self, traceui, config, parentname, parent=None):
        QtGui.QWidget.__init__(self,parent)
        fitForm.__init__(self)
        self.config = config
        self.parentname = parentname
        self.fitfunction = None
        self.traceui = traceui
        self.configname = "FitUi.{0}.".format(parentname)
        self.fitfunctionCache = self.config.get(self.configname+"FitfunctionCache", dict() )
        self.analysisDefinitions = self.config.get(self.configname+"AnalysisDefinitions", dict())
            
    def setupUi(self,widget):
        fitForm.setupUi(self,widget)
        self.fitButton.clicked.connect( self.onFit )
        self.plotButton.clicked.connect( self.onPlot )
        self.removePlotButton.clicked.connect( self.onRemoveFit )
        self.extractButton.clicked.connect( self.onExtractFit )
        self.copyButton.clicked.connect( self.onCopy )
        self.removeAnalysisButton.clicked.connect( self.onRemoveAnalysis )
        self.saveButton.clicked.connect( self.onSaveAnalysis )
        self.fitSelectionComboBox.addItems( fitFunctionMap.keys() )
        self.fitSelectionComboBox.currentIndexChanged[QtCore.QString].connect( self.onFitfunctionChanged )
        self.fitfunctionTableModel = FitUiTableModel(self.config)
        self.parameterTableView.setModel(self.fitfunctionTableModel)
        self.parameterTableView.setItemDelegateForColumn(2,MagnitudeSpinBoxDelegate())
        self.fitResultsTableModel = FitResultsTableModel(self.config)
        self.resultsTableView.setModel(self.fitResultsTableModel)
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
            self.fitfunction = fitfunction
            self.fitSelectionComboBox.setCurrentIndex( self.fitSelectionComboBox.findText(self.fitfunction.name) )

       
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
        self.fitfunctionTableModel.setFitfunction(self.fitfunction)
        self.fitResultsTableModel.setFitfunction(self.fitfunction)
        self.parameterTableView.resizeColumnsToContents()
        self.descriptionLabel.setText( self.fitfunction.functionString )
        if str(self.fitSelectionComboBox.currentText())!= self.fitfunction.name:
            self.fitSelectionComboBox.setCurrentIndex(self.fitSelectionComboBox.findText(self.fitfunction.name))
        self.resultsTableView.resizeColumnsToContents()
        
    def onFit(self):
        for plot in self.traceui.selectedPlottedTraces(defaultToLastLine=True):
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
                
    def onPlot(self):
        for plot in self.traceui.selectedPlottedTraces(defaultToLastLine=True):
            fitfunction = copy.deepcopy(self.fitfunction)
            fitfunction.parameters = [value(param) for param in fitfunction.startParameters]
            plot.fitFunction = fitfunction
            plot.plot(-2)
            fitfunction.finalize(fitfunction.parameters)
                
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
    
    def onSaveAnalysis(self):
        name = str(self.analysisNameComboBox.currentText())       
        definition = AnalysisDefinition.fromFitfunction(self.fitfunction)
        definition.name = name
        self.analysisDefinitions[name] = definition
        if self.analysisNameComboBox.findText(name)<0:
            self.analysisNameComboBox.addItem(name)
        
    def onLoadAnalysis(self, name):
        name = str(name)
        if name in self.analysisDefinitions:
            if AnalysisDefinition.fromFitfunction(self.fitfunction) != self.analysisDefinitions[name]:
                self.setFitfunction( self.analysisDefinitions[name].fitfunction() )
        
