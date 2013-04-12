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
    def __init__(self):
        self.project = ""
        self.histogramBins = 50
        self.integrate = False
        self.counter = 0
        self.evalName = 'Mean'
        
    def upgrade(self):
        self.__dict__.setdefault( 'project', '')
        self.__dict__.setdefault( 'histogramBins', 50)
        self.__dict__.setdefault( 'integrate', False)
        self.__dict__.setdefault( 'counter', 0)
        self.__dict__.setdefault( 'evalName', 'Mean')

class ScanExperimentSettings(ScanExperimentSettingsForm, ScanExperimentSettingsBase ):
    def __init__(self,config,parentname,parent=0):
        ScanExperimentSettingsForm.__init__(self,parent)
        ScanExperimentSettingsBase.__init__(self)
        self.config = config
        self.configname = 'ScanExperimentSettings.'+parentname
        self._settings = self.config.get(self.configname,Settings())
        self._settings.upgrade()

    @property
    def settings(self):
        self._settings.evalAlgo = self.algorithms.get( self._settings.evalName )
        return self._settings

    def setupUi(self, parent):
        ScanExperimentSettingsForm.setupUi(self,parent)
        self.projectEdit.setText(self._settings.project)
        self.projectEdit.editingFinished.connect(self.onProjectEditingFinished)
        self.histogramBinsBox.setValue(self._settings.histogramBins)
        self.histogramBinsBox.valueChanged.connect(self.onHistogramBinsChanged)
        self.integrateHistogramButton.setChecked( self._settings.integrate )
        self.integrateHistogramButton.clicked.connect( self.onIntegrateHistogramClicked )
        self.counterSpinBox.setValue( self._settings.counter )
        self.counterSpinBox.valueChanged.connect( self.onCounterChanged )
        self.evalMethodCombo.addItems( CountEvaluation.EvaluationAlgorithms.keys() )
        self.evalMethodCombo.setCurrentIndex( self.evalMethodCombo.findText(self._settings.evalName) )
        self.evalMethodCombo.currentIndexChanged['QString'].connect( self.onCurrentIndexChanged )
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
        self.evalStackedWidget.setCurrentIndex( self.evalMethodCombo.findText(self._settings.evalName) )

    def onParamValueChanged(self, algo, name, value):
        self.algorithms[algo].parameters[name] = value

    def onIntegrateHistogramClicked(self):
        self._settings.integrate = self.integrateHistogramButton.isChecked()

    def onProjectEditingFinished(self):
        self._settings.project = str(self.projectEdit.text())
        
    def onHistogramBinsChanged(self, bins):
        self._settings.histogramBins = bins
        
    def onCounterChanged(self, value):
        self._settings.counter = value
    
    def onClose(self):
        self.config[self.configname] = self._settings
        
    def onCurrentIndexChanged(self, name):
        self._settings.evalName = str(name)
        self.evalStackedWidget.setCurrentIndex(self.evalMethodCombo.currentIndex())
        