# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
import CountEvaluation
from PyQt4 import QtGui
from MagnitudeSpinBox import MagnitudeSpinBox
import functools 
       
ScanExperimentSettingsForm, ScanExperimentSettingsBase = PyQt4.uic.loadUiType(r'ui\ScanExperimentSettings.ui')


class Scan:
    pass

class Settings:
    project = ""
    histogramBins = 50
    integrate = False
    counter = 0
    evaluationIndex = 0
    evaluationAlgorithm = None

class ScanExperimentSettings(ScanExperimentSettingsForm, ScanExperimentSettingsBase ):
    def __init__(self,config,parentname,parent=0):
        ScanExperimentSettingsForm.__init__(self,parent)
        ScanExperimentSettingsBase.__init__(self)
        self.config = config
        self.configname = 'ScanExperimentSettings.'+parentname
        self.settings = self.config.get(self.configname,Settings())

    def setupUi(self, parent):
        ScanExperimentSettingsForm.setupUi(self,parent)
        self.projectEdit.setText(self.settings.project)
        self.projectEdit.editingFinished.connect(self.onProjectEditingFinished)
        self.histogramBinsBox.setValue(self.settings.histogramBins)
        self.histogramBinsBox.valueChanged.connect(self.onHistogramBinsChanged)
        self.integrateHistogramButton.setChecked( self.settings.integrate )
        self.integrateHistogramButton.clicked.connect( self.onIntegrateHistogramClicked )
        self.counterSpinBox.setValue( self.settings.counter )
        self.counterSpinBox.valueChanged.connect( self.onCounterChanged )
        self.evalMethodCombo.addItems( CountEvaluation.EvaluationAlgorithms.keys() )
        self.evalMethodCombo.setCurrentIndex( self.settings.evaluationIndex )
        self.evalMethodCombo.currentIndexChanged[int].connect( self.onCurrentIndexChanged )
        self.algorithms = dict()
        for name, algo in CountEvaluation.EvaluationAlgorithms.iteritems():
            self.algorithms[name] = algo()
            parameters = self.algorithms[name].parameters
            algoWidget = QtGui.QWidget(self.evalStackedWidget)
            gridLayout = QtGui.QGridLayout(algoWidget)
            for num, paramname in enumerate( parameters ):
                gridLayout.addWidget( QtGui.QLabel(paramname), num, 0, 1, 1)
                Box = MagnitudeSpinBox(self)
                Box.setValue( parameters[paramname] )
                Box.valueChanged.connect( functools.partial(self.onParamValueChanged, name, paramname) )
                gridLayout.addWidget( Box, num, 1, 1, 1)                
            spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
            gridLayout.addItem(spacerItem, len(parameters), 0, 1, 1)
            algoWidget.setLayout(gridLayout)
            self.evalStackedWidget.addWidget( algoWidget )

    def onParamValueChanged(self, algo, name, value):
        self.algorithms[algo].parameters[name] = value

    def onIntegrateHistogramClicked(self):
        self.settings.integrate = self.integrateHistogramButton.isChecked()

    def onProjectEditingFinished(self):
        self.settings.project = str(self.projectEdit.text())
        
    def onHistogramBinsChanged(self, bins):
        self.settings.histogramBins = bins
        
    def onCounterChanged(self, value):
        self.settings.counter = value
    
    def onClose(self):
        self.config[self.configname] = self.settings
        
    def onCurrentIndexChanged(self, index):
        self.settings.evaluationIndex = index
        self.settings.evaluationAlgorithm = CountEvaluation.EvaluationAlgorithms.get( str(self.evalMethodCombo.currentText()), 'Mean' )
        self.evalStackedWidget.setCurrentIndex(index)
        