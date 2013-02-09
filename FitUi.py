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

fitForm, fitBase = PyQt4.uic.loadUiType(r'ui\FitUi.ui')

fitFunctionList = [ FitFunctions.CosFit ]

class FitFunctionUi(object):
    def __init__(self,fitfunction):
        self.fitfunction = fitfunction
        self.startParameters = [0]* len(fitfunction.parameters)
        self.fittedParametersUi = [None]* len(fitfunction.parameters)
            
class FitUi(fitForm, QtGui.QWidget):
    def __init__(self,traceui,parent=None):
        QtGui.QWidget.__init__(self,parent)
        fitForm.__init__(self)
        self.fitFunctions = list()
        self.traceui = traceui
        for fitclass in fitFunctionList:
            self.fitFunctions.append( FitFunctionUi(fitclass()) )
            
    def setParameter(self,fitfunction,index,value):
        fitfunction.startParameters[index] = value

    def setupUi(self,widget):
        fitForm.setupUi(self,widget)
        self.guiList = list()
        for fitfunction in self.fitFunctions:
            fitfunction.page = QtGui.QWidget()
            fitfunction.gridLayout = QtGui.QGridLayout(fitfunction.page)
            label = QtGui.QLabel(fitfunction.fitfunction.functionString,fitfunction.page)
            fitfunction.gridLayout.addWidget(label, 0, 0, 1, 3)
            self.comboBox.addItem(fitfunction.fitfunction.name)
            for line, paramname in enumerate(fitfunction.fitfunction.parameterNames):
                label = QtGui.QLabel(paramname,fitfunction.page)
                label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                fitfunction.gridLayout.addWidget(label, line+1, 0, 1, 1)
                doubleSpinBox = pyqtgraph.SpinBox(fitfunction.page,dec=True)
                fitfunction.gridLayout.addWidget(doubleSpinBox, line+1, 1, 1, 1)
                doubleSpinBox.valueChanged.connect( functools.partial( self.setParameter, fitfunction, line ) )
                doubleSpinBox = pyqtgraph.SpinBox(fitfunction.page,dec=True)
                fitfunction.gridLayout.addWidget(doubleSpinBox, line+1,2, 1, 1)   
                fitfunction.fittedParametersUi[line] = doubleSpinBox
            self.stackedWidget.addWidget(fitfunction.page)
        self.pushButton.clicked.connect( self.onFit )
        
    def onFit(self):
        index = self.stackedWidget.currentIndex()
        functionui = self.fitFunctions[index]
        for name, value in zip(functionui.fitfunction.parameterNames, functionui.startParameters):
            print name, value
        for plot in self.traceui.selectedPlottedTraces():
            params = functionui.fitfunction.leastsq(plot.trace.x,plot.trace.y,functionui.startParameters)
            plot.trace.fitfunction = functionui.fitfunction
            plot.plot(-2)
            for i,p in enumerate(params):
                functionui.fittedParametersUi[i].setValue(p)
            
            
            
        
