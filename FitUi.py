# -*- coding: utf-8 -*-
"""
Created on Sat Jan 19 14:52:23 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore
import FitFunctions
import functools
import pyqtgraph
import copy
import MagnitudeSpinBox
from modules.round import roundToNDigits
from modules.round import roundToStdDev
from itertools import izip_longest

fitForm, fitBase = PyQt4.uic.loadUiType(r'ui\FitUi.ui')

#fitFunctionList = [  FitFunctions.GaussianFit, FitFunctions.CosFit, FitFunctions.LorentzianFit,
#                   FitFunctions.TruncatedLorentzianFit ]

class FitFunctionUi(object):
    def __init__(self,fitfunction):
        self.fitfunction = fitfunction
        self.startParameters = fitfunction.startParameters
        self.fittedParametersUi = [None]* len(fitfunction.parameters)
        self.startParametersUi = [None]* len(fitfunction.parameters)
        self.resultsUi = [None]* len(fitfunction.resultNames)
        self.parametersConfidenceLabel  = [None]* len(fitfunction.parameters)
        
    def fittedParameterSetValue(self):
        for i,(p,conf) in enumerate(izip_longest(self.fitfunction.parameters,self.fitfunction.parametersConfidence)):
            self.fittedParametersUi[i].setValue(p)
            print repr(roundToNDigits(conf,2))
            if conf:
                self.parametersConfidenceLabel[i].setText(repr(roundToNDigits(conf,2)))

    def startParameterSetValue(self):
        for i,p in enumerate(self.fitfunction.startParameters):
            self.startParametersUi[i].setValue(p)        
            
class FitUi(fitForm, QtGui.QWidget):
    def __init__(self,traceui,config,parentname,parent=None):
        QtGui.QWidget.__init__(self,parent)
        fitForm.__init__(self)
        self.config = config
        self.parentname = parentname
        self.fitFunctions = list()
        self.traceui = traceui
        for fitclass in FitFunctions.fitFunctionMap.values():
            self.fitFunctions.append( FitFunctionUi(fitclass()) )
            
    def setParameter(self,fitfunction,index,value):
        fitfunction.startParameters[index] = value
        
    def setConstant(self,fitfunction,parametername,value):
        fitfunction.fitfunction.setConstant(parametername,value)

    def setupUi(self,widget):
        fitForm.setupUi(self,widget)
        self.guiList = list()
        for fitfunction in self.fitFunctions:
            fitfunction.page = QtGui.QWidget()
            fitfunction.gridLayout = QtGui.QGridLayout(fitfunction.page)
            label = QtGui.QLabel(fitfunction.fitfunction.functionString,fitfunction.page)
            label.setWordWrap(True)
            fitfunction.gridLayout.addWidget(label, 0, 0, 1, 3)
            self.comboBox.addItem(fitfunction.fitfunction.name)
            #print fitfunction.fitfunction.startParameters
            for line, paramname in enumerate(fitfunction.fitfunction.parameterNames):
                label = QtGui.QLabel(paramname,fitfunction.page)
                label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                fitfunction.gridLayout.addWidget(label, line+1, 0, 1, 1)
                doubleSpinBox = pyqtgraph.SpinBox(fitfunction.page,dec=True)
                doubleSpinBox.setValue(fitfunction.fitfunction.startParameters[line])
                fitfunction.gridLayout.addWidget(doubleSpinBox, line+1, 1, 1, 1)
                doubleSpinBox.valueChanged.connect( functools.partial( self.setParameter, fitfunction, line ) )
                fitfunction.startParametersUi[line] = doubleSpinBox
                doubleSpinBox = pyqtgraph.SpinBox(fitfunction.page,dec=True)
                doubleSpinBox.setReadOnly(True)
                doubleSpinBox.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
                fitfunction.gridLayout.addWidget(doubleSpinBox, line+1,2, 1, 1)   
                fitfunction.fittedParametersUi[line] = doubleSpinBox
                confidenceLabel = QtGui.QLabel("",fitfunction.page)
                fitfunction.gridLayout.addWidget(confidenceLabel, line+1, 3, 1, 1)
                fitfunction.parametersConfidenceLabel[line] = confidenceLabel
            line2 = 0
            for line2, paramname in enumerate(fitfunction.fitfunction.constantNames):
                label = QtGui.QLabel(paramname,fitfunction.page)
                label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                fitfunction.gridLayout.addWidget(label, line+2+line2, 0, 1, 1)
                doubleSpinBox = MagnitudeSpinBox.MagnitudeSpinBox(fitfunction.page)
                doubleSpinBox.setValue(getattr(fitfunction.fitfunction,paramname))
                fitfunction.gridLayout.addWidget(doubleSpinBox, line+2+line2, 1, 1, 1)
                doubleSpinBox.valueChanged.connect( functools.partial( self.setConstant, fitfunction, paramname ) )
            line3 = 0
            for line3, paramname in enumerate(fitfunction.fitfunction.resultNames):
                label = QtGui.QLabel(paramname,fitfunction.page)
                label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                fitfunction.gridLayout.addWidget(label, line+3+line2+line3, 0, 1, 1)
                doubleSpinBox = MagnitudeSpinBox.MagnitudeSpinBox(fitfunction.page)
                doubleSpinBox.setValue(getattr(fitfunction.fitfunction,paramname))
                fitfunction.gridLayout.addWidget(doubleSpinBox, line+3+line2+line3, 1, 1,2)
                doubleSpinBox.setEnabled(False)
                fitfunction.resultsUi[line3] = doubleSpinBox
            fitfunction.gridLayout.addItem(QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), line+3+line2, 1, 1, 1)                
            self.stackedWidget.addWidget(fitfunction.page)
        self.pushButton.clicked.connect( self.onFit )
        self.plotButton.clicked.connect( self.onPlot )
        self.removeButton.clicked.connect( self.onRemoveFit )
        self.extractButton.clicked.connect( self.onExtractFit )
        self.copyButton.clicked.connect( self.onCopy )
        
    def onFit(self):
        index = self.stackedWidget.currentIndex()
        functionui = self.fitFunctions[index]
        for name, value in zip(functionui.fitfunction.parameterNames, functionui.startParameters):
            print name, value
        for plot in self.traceui.selectedPlottedTraces(defaultToLastLine=True):
            sigma = None
            if plot.hasHeightColumn:
                sigma = plot.height
            elif plot.hasTopColumn and plot.hasBottomColumn:
                sigma = abs(plot.top + plot.bottom)
            params = functionui.fitfunction.leastsq(plot.x,plot.y,functionui.startParameters,sigma=sigma)
            plot.fitFunction = copy.deepcopy(functionui.fitfunction)
            plot.plot(-2)
            for i,(p,conf,relconf) in enumerate(zip(params,functionui.fitfunction.parametersConfidence,functionui.fitfunction.parametersRelConfidence)):
                functionui.fittedParametersUi[i].setValue(roundToStdDev(p,conf))
                functionui.parametersConfidenceLabel[i].setText(repr(roundToNDigits(conf,2))+'%')

            for index, name in enumerate(functionui.fitfunction.resultNames):
                functionui.resultsUi[index].setValue(getattr(functionui.fitfunction,name))
                
#    def parameterSetValue(self,index):
#        index = self.stackedWidget.currentIndex()
#        functionui = self.fitFunctions[index]
#        for i,p in enumerate(functionui.fitfunction.parameters):
#            functionui.fittedParametersUi[i].setValue(p)        
            
    def onPlot(self):
        index = self.stackedWidget.currentIndex()
        functionui = self.fitFunctions[index]
        for plot in self.traceui.selectedPlottedTraces(defaultToLastLine=True):
            functionui.fitfunction.parameters = functionui.startParameters
            plot.fitFunction = functionui.fitfunction
            plot.plot(-2)
            functionui.fitfunction.finalize(functionui.fitfunction.parameters)
            for index, name in enumerate(functionui.fitfunction.resultNames):
                functionui.resultsUi[index].setValue(getattr(functionui.fitfunction,name))
                
    def onRemoveFit(self):
        for plot in self.traceui.selectedPlottedTraces(defaultToLastLine=True):
            plot.fitFunction = None
            plot.plot(-2)
    
    def onExtractFit(self):
        plots = self.traceui.selectedPlottedTraces(defaultToLastLine=True)
        print "onExtractFit {0} plots selected".format(len(plots) )
        if plots:
            plot = plots[0]
            fitFunction = plot.fitFunction
            for i, function in enumerate(self.fitFunctions):
                if function.fitfunction.name == fitFunction.name:
                    print "compare names {0} == {1}".format(function.fitfunction.name,fitFunction.name)
                    self.comboBox.setCurrentIndex(i)
                    function.fitfunction.parameters = fitFunction.parameters
                    function.fitfunction.parametersConfidence = fitFunction.parametersConfidence
                    print "Extracted parameters {0} for '{1}'".format(function.fitfunction.parameters,function.fitfunction.name)
                    self.fitFunctions[i].fittedParameterSetValue()                
    
    def onCopy(self):
        index = self.stackedWidget.currentIndex()
        functionui = self.fitFunctions[index]
        functionui.fitfunction.startParameters = copy.deepcopy(functionui.fitfunction.parameters)
        functionui.startParameterSetValue()
    
    
            
        
