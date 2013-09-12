# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
import copy
import functools
from PyQt4 import QtCore, QtGui
import CountEvaluation
from MagnitudeSpinBox import MagnitudeSpinBox
       
ScanControlForm, ScanControlBase = PyQt4.uic.loadUiType(r'ui\ScanControlUi.ui')

import ScanList
from modules import enum, MagnitudeUtilit
from magnitude import mg

class Scan:
    def __init__(self):
        # Scan
        self.scanParameter = None
        self.start = 0
        self.stop = 0
        self.steps = 0
        self.stepsSelect = 0
        self.scantype = 0
        self.scanMode = 0
        self.scanRepeat = 0
        self.rewriteDDS = False
        self.filename = ""
        self.autoSave = False
        self.xUnit = ""
        self.loadPP = False
        self.loadPPName = ""
        # Evaluation
        self.histogramBins = 50
        self.integrateHistogram = False
        self.counterChannel = 0
        self.evalName = 'Mean'
        self.errorBars = False
        # Timestamps
        self.enableTimestamps = False
        self.binwidth =  mg(1,'us')
        self.roiStart =  mg(0,'us')
        self.roiWidth =  mg(1,'ms')
        self.integrateTimestamps = 0
        self.timestampsChannel = 0
        self.saveRawData = False
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault('xUnit', '')
        self.__dict__.setdefault('scanRepeat', 0)
        self.__dict__.setdefault('loadPP', False)
        self.__dict__.setdefault('loadPPName', "")
        self.__dict__.setdefault('evalName','Mean')
        
    def __eq__(self,other):
        return ( self.scanParameter == other.scanParameter and
                self.start == other.start and
                self.stop == other.stop and
                self.steps == other.steps and
                self.stepsSelect == other.stepsSelect and
                self.scantype == other.scantype and
                self.scanMode == other.scanMode and 
                self.scanRepeat == other.scanRepeat and 
                self.rewriteDDS == other.rewriteDDS and
                self.filename == other.filename and
                self.autoSave == other.autoSave and
                self.xUnit == other.xUnit and
                self.loadPP == other.loadPP and
                self.loadPPName == other.loadPPName and
                self.histogramBins == other.histogramBins and
                self.integrateHistogram == other.integrateHistogram and
                self.counterChannel == other.counterChannel and
                self.evalName == other.evalName and
                self.errorBars == other.errorBars and
                self.enableTimestamps == other.enableTimestamps and
                self.binwidth == other.binwidth and
                self.roiStart == other.roiStart and
                self.integrateTimestamps == other.integrateTimestamps and
                self.timestampsChannel == other.timestampsChannel and
                self.saveRawData == other.saveRawData)

        
    def __repr__(self):
        r = "Scanning parameter: {0}\nScanning From: {1}\nScanning To: {2}\n".format(self.scanParameter,self.start,self.stop)
        r+= "Scanning Steps: {0}\nScanning type: {1}\nScanning rewriteDDS: {2}\n".format(self.steps,self.scantype,self.rewriteDDS)
        r+= "Scanning mode: {0}".format(self.scanMode)
        return r


class ScanControl(ScanControlForm, ScanControlBase ):
    ScanModes = enum.enum('SingleScan','RepeatedScan','StepInPlace','GateSetScan')
    integrationMode = enum.enum('IntegrateAll','IntegrateRun','NoIntegration')    
    def __init__(self,config,parentname,parent=None):
        ScanControlForm.__init__(self)
        ScanControlBase.__init__(self,parent)
        self.config = config
        self.configname = 'ScanControl.'+parentname
        # History and Dictionary
        self.settingsDict = self.config.get(self.configname+'.dict',dict())
        #print self.settingsDict
        self.settingsHistory = list()
        self.settingsHistoryPointer = None
        self.historyFinalState = None

    def setupUi(self, parent):
        ScanControlForm.setupUi(self,parent)
        # History and Dictionary
        self.saveButton.clicked.connect( self.onSave )
        self.undoButton.clicked.connect( self.onUndo )
        self.redoButton.clicked.connect( self.onRedo )
        self.comboBox.currentIndexChanged['QString'].connect( self.onLoad )
        try:
            self.setSettings( self.config.get(self.configname,Scan()) )
        except AttributeError as e:
            print "Ignoring exception",e
        for name in self.settingsDict:
            self.comboBox.addItem(name)
        # update connections
        self.comboBoxParameter.currentIndexChanged['QString'].connect( self.onCurrentTextChanged )        
        self.startBox.valueChanged.connect( functools.partial(self.onValueChanged,'start') )
        self.stopBox.valueChanged.connect( functools.partial(self.onValueChanged,'stop') )
        self.stepsBox.valueChanged.connect( functools.partial(self.onValueChanged,'steps') )
        self.stepsCombo.currentIndexChanged[int].connect( functools.partial(self.onCurrentIndexChanged,'stepsSelect') )
        self.scanTypeCombo.currentIndexChanged[int].connect( functools.partial(self.onCurrentIndexChanged,'scantype') )
        self.rewriteDDSCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'rewriteDDS') )
        self.autoSaveCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'autoSave') )
        self.scanModeComboBox.currentIndexChanged[int].connect( self.onModeChanged )
        self.filenameEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.filenameEdit, 'filename') )
        self.xUnitEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.xUnitEdit, 'xUnit') )
        self.scanRepeatComboBox.currentIndexChanged[int].connect( functools.partial(self.onCurrentIndexChanged,'scanRepeat') )
        # Evaluation
        self.histogramBinsBox.valueChanged.connect(self.onHistogramBinsChanged)
        self.integrateHistogramButton.clicked.connect( self.onIntegrateHistogramClicked )
        self.counterSpinBox.valueChanged.connect( functools.partial(self.onIntValueChanged,'counterChannel') )
        self.evalMethodCombo.addItems( CountEvaluation.EvaluationAlgorithms.keys() )
        self.evalMethodCombo.currentIndexChanged['QString'].connect( self.onAlgorithmNameChanged )
        self.algorithms = dict()
        self.errorBarCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'errorBars') )
        for name, algo in CountEvaluation.EvaluationAlgorithms.iteritems():
            self.algorithms[name] = algo(self.config)
            parameters = self.algorithms[name].parameters
            algoWidget = QtGui.QWidget(self.evalStackedWidget)
            gridLayout = QtGui.QGridLayout(algoWidget)
            for num, paramname in enumerate( parameters ):
                gridLayout.addWidget( QtGui.QLabel(paramname), num, 0, 1, 1)
                Box = MagnitudeSpinBox(self)
                Box.setValue( parameters[paramname] )
                Box.valueChanged.connect( functools.partial(self.onAlgorithmValueChanged, name, paramname) )
                gridLayout.addWidget( Box, num, 1, 1, 1)                
            spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
            gridLayout.addItem(spacerItem, len(parameters), 0, 1, 1)
            algoWidget.setLayout(gridLayout)
            self.evalStackedWidget.addWidget( algoWidget )
        self.evalStackedWidget.setCurrentIndex( self.evalMethodCombo.findText(self.settings.evalName) )
        
        # Timestamps
        self.binwidthSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'binwidth') )
        self.roiStartSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'roiStart') )
        self.roiWidthSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'roiWidth') )
        self.enableCheckBox.stateChanged.connect( functools.partial(self.onStateChanged, 'enableTimestamps' ) )
        self.saveRawDataCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'saveRawData' ) )
        self.integrateCombo.currentIndexChanged[int].connect( self.onIntegrationChanged )
        self.channelSpinBox.valueChanged.connect( functools.partial(self.onValueChanged, 'timestampsChannel') )
        self.loadPPcheckBox.stateChanged.connect( functools.partial(self.onStateChanged, 'loadPP' ) )
        self.loadPPComboBox.currentIndexChanged['QString'].connect( self.onLoadPP )
        
    def setSettings(self, settings):
        self.settings = copy.deepcopy(settings)
        #print "setSettings", id(self.settings), self.settings
        self.scanModeComboBox.setCurrentIndex( self.settings.scanMode )
        self.startBox.setValue(self.settings.start)
        self.stopBox.setValue(self.settings.stop)
        self.stepsBox.setValue(self.settings.steps)
        self.stepsCombo.setCurrentIndex(self.settings.stepsSelect)
        self.scanTypeCombo.setCurrentIndex(self.settings.scantype )
        self.rewriteDDSCheckBox.setChecked( self.settings.rewriteDDS )
        self.autoSaveCheckBox.setChecked(self.settings.autoSave)
        self.progressBar.setVisible( False )
        if self.settings.scanParameter: self.comboBoxParameter.setCurrentIndex( self.comboBoxParameter.findText(self.settings.scanParameter))
        self.filenameEdit.setText( getattr(self.settings,'filename','') )
        self.startBox.setEnabled(self.settings.scanMode in [0,1])
        self.stopBox.setEnabled(self.settings.scanMode in [0,1])
        self.scanTypeCombo.setEnabled(self.settings.scanMode in [0,1])
        self.xUnitEdit.setText( self.settings.xUnit )
        self.scanRepeatComboBox.setCurrentIndex( self.settings.scanRepeat )
        self.loadPPcheckBox.setChecked( self.settings.loadPP )
        if self.settings.loadPPName: 
            self.loadPPComboBox.setCurrentIndex( self.loadPPComboBox.findText(self.settings.loadPPName))
            self.onLoadPP(self.settings.loadPPName)
        # Evaluation
        self.histogramBinsBox.setValue(self.settings.histogramBins)
        self.integrateHistogramButton.setChecked( self.settings.integrateHistogram )
        self.counterSpinBox.setValue( self.settings.counterChannel )
        self.evalMethodCombo.setCurrentIndex( self.evalMethodCombo.findText(self.settings.evalName) )
        self.errorBarCheckBox.setChecked( self.settings.errorBars)
        # Timestamps
        self.enableCheckBox.setChecked(self.settings.enableTimestamps )
        self.saveRawDataCheckBox.setChecked(self.settings.saveRawData)
        self.binwidthSpinBox.setValue(self.settings.binwidth)
        self.roiStartSpinBox.setValue(self.settings.roiStart)
        self.roiWidthSpinBox.setValue(self.settings.roiWidth)
        self.integrateCombo.setCurrentIndex( self.settings.integrateTimestamps )
        self.channelSpinBox.setValue( self.settings.timestampsChannel )
        self.onModeChanged(self.settings.scanMode)
        
    def onLoadPP(self, ppname):
        self.settings.loadPPName = str(ppname)
        print "ScanControl.onLoadPP", self.settings.loadPP, bool(self.settings.loadPPName), self.settings.loadPPName
        if self.settings.loadPP and self.settings.loadPPName and hasattr(self,"pulseProgramUi"):
            self.pulseProgramUi.onFilenameChange( self.settings.loadPPName )
            
    def onRecentPPFilesChanged(self, name):
        print "ScanControl.onRecentPPFilesChanged"
        self.loadPPComboBox.addItem(name)
#        if self.settings.loadPPName: 
#            self.loadPPComboBox.setCurrentIndex( self.loadPPComboBox.findText(self.settings.loadPPName))
        
    def setPulseProgramUi(self, pulseProgramUi ):
        print "ScanControl.setPulseProgramUi", pulseProgramUi.configParams.recentFiles.keys()
        self.pulseProgramUi = pulseProgramUi
        oldstate = self.loadPPComboBox.blockSignals(True)
        self.loadPPComboBox.clear()
        if hasattr(pulseProgramUi.configParams,'recentFiles'):
            self.loadPPComboBox.addItems(pulseProgramUi.configParams.recentFiles.keys())
        if self.settings.loadPPName: 
            self.loadPPComboBox.setCurrentIndex( self.loadPPComboBox.findText(self.settings.loadPPName))
        self.loadPPComboBox.blockSignals(oldstate)
        self.pulseProgramUi.recentFilesChanged.connect( self.onRecentPPFilesChanged, QtCore.Qt.UniqueConnection )

    def onEditingFinished(self,edit,attribute):
        self.beginChange()
        #print id(self.settings), attribute, "->", str(edit.text())
        setattr( self.settings, attribute, str(edit.text())  )
        self.commitChange()
                
    def beginChange(self):
        self.tempSettings = copy.deepcopy( self.settings )

    def commitChange(self): 
        pass
        #if self.tempSettings!=self.settings:
        #    self.comboBox.setEditText('')
        
    def onStateChanged(self, attribute, state):
        self.beginChange()
        setattr( self.settings, attribute, (state == QtCore.Qt.Checked)  )
        self.commitChange()
        
    def onCurrentTextChanged(self, text):
        self.beginChange()
        self.settings.scanParameter = str(text)
        self.commitChange()
    
    def onCurrentIndexChanged(self, attribute, index):
        self.beginChange()
        setattr( self.settings, attribute, index )
        self.commitChange()
        
    def onModeChanged(self, index):
        self.beginChange()
        self.settings.scanMode = index
        self.startBox.setEnabled(index ==0)
        self.stopBox.setEnabled(index ==0)
        self.stepsBox.setEnabled( index==0)
        self.scanTypeCombo.setEnabled(index in [0,2])
        self.scanRepeatComboBox.setEnabled( index in [0,2] )
        self.xUnitEdit.setEnabled( index==0)
        self.comboBoxParameter.setEnabled( index==0 )
        self.commitChange()       
    
    def onValueChanged(self, attribute, value):
        self.beginChange()
        setattr( self.settings, attribute, MagnitudeUtilit.mg(value) )
        #print id(self.settings), "Variable '{0}' set to {1}".format(attribute, MagnitudeUtilit.mg(value))
        self.commitChange()

    def onIntValueChanged(self, attribute, value):
        self.beginChange()
        setattr( self.settings, attribute, value )
        #print id(self.settings), "Variable '{0}' set to {1}".format(attribute, MagnitudeUtilit.mg(value))
        self.commitChange()
        
    def setVariables(self, variabledict):
        self.variabledict = variabledict
        #oldParameterName = self.comboBoxParameter.currentText()
        oldParameterName = self.settings.scanParameter
        self.comboBoxParameter.clear()
        for name, var in iter(sorted(variabledict.iteritems())):
            if var.type == "parameter":
                self.comboBoxParameter.addItem(var.name)
        if oldParameterName and oldParameterName!="":
            self.comboBoxParameter.setCurrentIndex(self.comboBoxParameter.findText(oldParameterName) )
            
    def setScanNames(self, scannames):
        self.comboBoxParameter.clear()
        for name in scannames:
            self.comboBoxParameter.addItem(name)
        self.comboBoxParameter.setCurrentIndex( self.comboBoxParameter.findText(self.settings.scanParameter))
        print self.configname,"activating", self.settings.scanParameter
                
    def getScan(self):
        scan = copy.deepcopy(self.settings)
        scan.type = [ ScanList.ScanType.LinearUp, ScanList.ScanType.LinearDown, ScanList.ScanType.Randomized][self.settings.scantype]
        scan.list = ScanList.scanList( scan.start, scan.stop, scan.steps, scan.type, scan.stepsSelect )
        scan.evalAlgo = self.algorithms[scan.evalName]
        self.onCommit()
        return scan
        
    def onClose(self):
        self.config[self.configname] = self.settings
        self.config[self.configname+'.dict'] = self.settingsDict
               
    # History stuff
    
    def onRedo(self):
        if self.settingsHistoryPointer<len(self.settingsHistory):
            self.settingsHistoryPointer += 1
            if self.settingsHistoryPointer<len(self.settingsHistory):
                self.setSettings( self.settingsHistory[self.settingsHistoryPointer])
            elif self.historyFinalState:
                self.setSettings( self.historyFinalState )
                self.historyFinalState = None
     
    def onUndo(self):
        if self.settingsHistoryPointer>0:
            if self.settingsHistoryPointer==len(self.settingsHistory):
                self.historyFinalState = copy.deepcopy( self.settings )
            self.settingsHistoryPointer -= 1
            self.setSettings( self.settingsHistory[self.settingsHistoryPointer] )
    
    def onSave(self):
        name = str(self.comboBox.currentText())
        #print "onSave", name, id(self.settings), self.settings
        if name != '':
            if name not in self.settingsDict:
                if self.comboBox.findText(name)==-1:
                    self.comboBox.addItem(name)
                print self.configname, "adding to combo", name
            self.settingsDict[name] = copy.deepcopy(self.settings)
    
    def onLoad(self,name):
        name = str(name)
        #print self.configname, "onLoad", name
        if name !='' and name in self.settingsDict:
            self.setSettings(self.settingsDict[name])
        else:
            print self.configname, self.settingsDict

   
    def onCommit(self):
        if len(self.settingsHistory)==0 or self.settings!=self.settingsHistory[-1]:
            self.settingsHistory.append(copy.deepcopy(self.settings))
            self.settingsHistoryPointer = len(self.settingsHistory)
                
    def onIntegrationChanged(self, value):
        self.beginChange()
        self.settings.integrateTimestamps = value
        self.commitChange()
        
    def onAlgorithmValueChanged(self, algo, name, value):
        self.beginChange()
        self.algorithms[algo].setParameter(name, value)
        self.commitChange()

    def onIntegrateHistogramClicked(self):
        self.beginChange()
        self.settings.integrateHistogram = self.integrateHistogramButton.isChecked()
        self.commitChange()
 
    def onHistogramBinsChanged(self, bins):
        self.beginChange()
        self.settings.histogramBins = bins
        self.commitChange()
        
    def onAlgorithmNameChanged(self, name):
        self.beginChange()
        self.settings.evalName = str(name)
        self.evalStackedWidget.setCurrentIndex(self.evalMethodCombo.currentIndex())
        self.commitChange()
        

if __name__=="__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = ScanControl(config,"parent")
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
        