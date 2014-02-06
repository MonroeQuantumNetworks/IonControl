import PyQt4.uic
from PyQt4 import QtGui, QtCore
import FitFunctions
import copy
from modules.round import roundToNDigits
from modules.round import roundToStdDev
from itertools import izip_longest
from FitUiTableModel import FitUiTableModel
import logging
from MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.MagnitudeUtilit import value

fitForm, fitBase = PyQt4.uic.loadUiType(r'ui\FitUiTables.ui')

class AnalysisDefinition(object):
    def __init__(self):
        self.name = None
        self.fitfunctionName = None
        self.startParameters = list()
        self.enabledParameters = list()

class FitFunctionUi(AnalysisDefinition):
    def __init__(self,fitfunction):
        self.fitfunction = fitfunction
        self.startParameters = fitfunction.startParameters
        
    def fittedParameterSetValue(self):
        for i,(p,conf) in enumerate(izip_longest(self.fitfunction.parameters,self.fitfunction.parametersConfidence)):
            self.fittedParametersUi[i].setValue(p)
            if conf:
                self.parametersConfidenceLabel[i].setText(repr(roundToNDigits(conf,2)))

    def startParameterSetValue(self):
        for i,p in enumerate(self.fitfunction.startParameters):
            self.startParametersUi[i].setValue(p)        
            
class FitUiTables(fitForm, QtGui.QWidget):
    def __init__(self, traceui, config, parentname, parent=None):
        QtGui.QWidget.__init__(self,parent)
        fitForm.__init__(self)
        self.config = config
        self.parentname = parentname
        self.fitfunction = None
        self.traceui = traceui
        self.fitfunctionCache = self.config.get("FitUi.FitfunctionCache", dict() )
            
    def setupUi(self,widget):
        fitForm.setupUi(self,widget)
        self.fitButton.clicked.connect( self.onFit )
        self.plotButton.clicked.connect( self.onPlot )
        self.removePlotButton.clicked.connect( self.onRemoveFit )
        self.extractButton.clicked.connect( self.onExtractFit )
        self.copyButton.clicked.connect( self.onCopy )
        self.fitSelectionComboBox.addItems( FitFunctions.fitFunctionMap.keys() )
        self.fitSelectionComboBox.currentIndexChanged[QtCore.QString].connect( self.onFitfunctionChanged )
        self.fitfunctionTableModel = FitUiTableModel(self.config)
        self.parameterTableView.setModel(self.fitfunctionTableModel)
        self.parameterTableView.setItemDelegateForColumn(2,MagnitudeSpinBoxDelegate())
        self.onFitfunctionChanged(str(self.fitSelectionComboBox.currentText()))
        
    def onFitfunctionChanged(self, name):
        name = str(name)
        if self.fitfunction:
            self.fitfunctionCache[self.fitfunction.name] = self.fitfunction
        if name in self.fitfunctionCache:
            self.setFitfunction( self.fitfunctionCache[name] )
        else:
            self.setFitfunction( FitFunctions.fitFunctionMap[name]() )
        
    def setFitfunction(self, fitfunction):
        self.fitfunction = fitfunction
        self.fitfunctionTableModel.setFitfunction(self.fitfunction)
        self.parameterTableView.resizeColumnsToContents()
        self.descriptionLabel.setText( self.fitfunction.functionString )
        
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
        self.config["FitUi.FitfunctionCache"] = self.fitfunctionCache
            
        
