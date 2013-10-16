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
from modules.MagnitudeUtilit import valueAs
       
ScanControlForm, ScanControlBase = PyQt4.uic.loadUiType(r'ui\ScanControlUi.ui')

import ScanList
from modules import MagnitudeUtilit
from modules.magnitude import mg
from modules.enum import enum
import GateSetUi
from modules.PyqtUtility import BlockSignals, updateComboBoxItems

class Scan:
    ScanMode = enum('ParameterScan','StepInPlace','GateSetScan')
    ScanType = enum('LinearStartToStop','LinearStopToStart','Randomized')
    ScanRepeat = enum('SingleScan','RepeatedScan')
    def __init__(self):
        # Scan
        self.scanParameter = None
        self.start = 0
        self.stop = 0
        self.center = 0
        self.span = 0
        self.steps = 0
        self.stepSize = 1
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
        self.startCenter = 0    # 0: start, stop;  1:center, span
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
        # GateSet Settings
        self.gateSetSettings = GateSetUi.Settings()
        
    def __setstate__(self, state):
        """this function ensures that the given fields are present in the class object
        after unpickling. Only new class attributes need to be added here.
        """
        self.__dict__ = state
        self.__dict__.setdefault('xUnit', '')
        self.__dict__.setdefault('scanRepeat', 0)
        self.__dict__.setdefault('loadPP', False)
        self.__dict__.setdefault('loadPPName', "")
        self.__dict__.setdefault('evalName','Mean')
        self.__dict__.setdefault('stepSize',1)
        self.__dict__.setdefault('center',0)
        self.__dict__.setdefault('span',0)
        self.__dict__.setdefault('startCenter',0)        
        self.__dict__.setdefault('gateSetSettings',GateSetUi.Settings())
        
    def __eq__(self,other):
        return ( self.scanParameter == other.scanParameter and
                self.start == other.start and
                self.stop == other.stop and
                self.steps == other.steps and
                self.stepSize == other.stepSize and
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
                self.saveRawData == other.saveRawData and
                self.gateSetSettings == other.gateSetSettings and
                self.center == other.center and
                self.span == other.span and
                self.startCenter == other.startCenter )
        
    def __hash__(self):
        return hash( (self.scanParameter, self.start, self.stop, self.steps, self.stepSize, self.stepsSelect, self.scantype, self.scanMode,
                      self.scanRepeat, self.rewriteDDS, self.filename, self.autoSave, self.xUnit, self.loadPP, self.loadPPName, self.histogramBins,
                      self.integrateHistogram, self.counterChannel, self.evalName, self.errorBars, self.enableTimestamps, self.binwidth,
                      self.roiStart, self.integrateTimestamps, self.timestampsChannel, self.saveRawData, self.center, self.span, self.startCeneter) )

    documentationList = [ 'scanParameter', 'start', 'stop', 'steps', 'stepSize', 'scantype', 'scanMode', 'scanRepeat', 'rewriteDDS', 
                'xUnit', 'loadPP', 'loadPPName', 'counterChannel', 'evalName' ]
        
    def documentationString(self):
        r = "\r\n".join( [ "{0}\t{1}".format(field,getattr(self,field)) for field in self.documentationList] )
        r += self.gateSetSettings.documentationString()
        return r


class ScanControl(ScanControlForm, ScanControlBase ):
    ScanModes = enum('SingleScan','RepeatedScan','StepInPlace','GateSetScan')
    integrationMode = enum('IntegrateAll','IntegrateRun','NoIntegration')    
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
        self.settings = self.config.get(self.configname,Scan())
        self.gateSetUi = None
        self.settingsName = None

    def setupUi(self, parent):
        ScanControlForm.setupUi(self,parent)
        # History and Dictionary
        self.saveButton.clicked.connect( self.onSave )
        self.undoButton.clicked.connect( self.onUndo )
        self.redoButton.clicked.connect( self.onRedo )
        self.reloadButton.clicked.connect( self.onReload )
        self.comboBox.currentIndexChanged['QString'].connect( self.onLoad )
        try:
            self.setSettings( self.settings )
        except AttributeError as e:
            print "Ignoring exception",e
        for name in self.settingsDict:
            self.comboBox.addItem(name)
        # update connections
        self.comboBoxParameter.currentIndexChanged['QString'].connect( self.onCurrentTextChanged )        
        self.startBox.valueChanged.connect( self.onStartChanged )
        self.stopBox.valueChanged.connect( self.onStopChanged )
        self.stepsBox.valueChanged.connect( self.onStepsValueChanged )
        self.stepsCombo.currentIndexChanged[int].connect( self.onStepsSelectChanged )
        self.scanTypeCombo.currentIndexChanged[int].connect( functools.partial(self.onCurrentIndexChanged,'scantype') )
        self.rewriteDDSCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'rewriteDDS') )
        self.autoSaveCheckBox.stateChanged.connect( functools.partial(self.onStateChanged,'autoSave') )
        self.scanModeComboBox.currentIndexChanged[int].connect( self.onModeChanged )
        self.filenameEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.filenameEdit, 'filename') )
        self.xUnitEdit.editingFinished.connect( functools.partial(self.onEditingFinished, self.xUnitEdit, 'xUnit') )
        self.scanRepeatComboBox.currentIndexChanged[int].connect( functools.partial(self.onCurrentIndexChanged,'scanRepeat') )
        self.startCenterCombo.currentIndexChanged[int].connect( self.onStartCenterChanged )
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
        self.setStartCenter()
        self.calculateSteps( self.settings )
        self.setSteps( self.settings, True )
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
        self.evalStackedWidget.setCurrentIndex( self.evalMethodCombo.findText(self.settings.evalName) )
        # Timestamps
        self.enableCheckBox.setChecked(self.settings.enableTimestamps )
        self.saveRawDataCheckBox.setChecked(self.settings.saveRawData)
        self.binwidthSpinBox.setValue(self.settings.binwidth)
        self.roiStartSpinBox.setValue(self.settings.roiStart)
        self.roiWidthSpinBox.setValue(self.settings.roiWidth)
        self.integrateCombo.setCurrentIndex( self.settings.integrateTimestamps )
        self.channelSpinBox.setValue( self.settings.timestampsChannel )
        self.onModeChanged(self.settings.scanMode)
        if self.gateSetUi:
            self.gateSetUi.setSettings( self.settings.gateSetSettings )
            
    def onStartCenterChanged(self, value):   
        self.settings.startCenter = value 
        self.calculateBoundaries()
        self.setStartCenter()
        
    def setStartCenter(self):
        if self.settings.startCenter == 0:
            self.startBox.setValue(self.settings.start)
            self.stopBox.setValue(self.settings.stop)
            self.startCenterCombo.setCurrentIndex(0)
            self.stopLabel.setText("Stop")
        elif self.settings.startCenter == 1:
            self.startBox.setValue(self.settings.center)
            self.stopBox.setValue(self.settings.span)
            self.startCenterCombo.setCurrentIndex(1)
            self.stopLabel.setText("Span")        
        
    def onStartChanged(self, value):
        if self.settings.startCenter == 0:
            self.settings.start = value
        elif self.settings.startCenter == 1:
            self.settings.center = value
        self.calculateBoundaries()

    def onStopChanged(self, value):
        if self.settings.startCenter == 0:
            self.settings.stop = value
        elif self.settings.startCenter == 1:
            self.settings.span = value
        self.calculateBoundaries()
            
    def calculateBoundaries(self):
        if self.settings.startCenter == 0:
            self.settings.center = (self.settings.start + self.settings.stop)/2
            self.settings.span = abs(self.settings.start - self.settings.stop)
        elif self.settings.startCenter == 1:
            self.settings.start = self.settings.center - self.settings.span/2
            self.settings.stop = self.settings.center + self.settings.span/2
        
        
    def setSteps( self, settings, writeInput=False ):
        if settings.stepsSelect == 0:
            if writeInput:
                self.stepsBox.setValue(settings.steps)
            self.stepsLabel.setText( str(settings.stepSize) )
        else:
            if writeInput:
                self.stepsBox.setValue(settings.stepSize)
            self.stepsLabel.setText( str(settings.steps) )

        
    def calculateSteps(self, settings):
        print "calculateSteps", settings.stepsSelect
        if settings.stepsSelect == 0:
            try:
                settings.stepSize = abs(settings.stop - settings.start)/(settings.steps - 1)
                valueAs( settings.stepSize, settings.start )
            except Exception as e:
                print e
                settings.stepSize = None
        else:
            try:
                settings.steps = int( round( abs(settings.stop - settings.start)/settings.stepSize ) ) + 1
            except Exception as e:
                print e
                settings.steps = None
        
    def onLoadPP(self, ppname):
        self.settings.loadPPName = str(ppname)
        print "ScanControl.onLoadPP", self.settings.loadPP, bool(self.settings.loadPPName), self.settings.loadPPName
        if self.settings.loadPP and self.settings.loadPPName and hasattr(self,"pulseProgramUi"):
            self.pulseProgramUi.onFilenameChange( self.settings.loadPPName )
            
    def onRecentPPFilesChanged(self, name):
        print "ScanControl.onRecentPPFilesChanged"
        if self.loadPPComboBox.findText(name)<0:
            self.loadPPComboBox.addItem(name)
#        if self.settings.loadPPName: 
#            self.loadPPComboBox.setCurrentIndex( self.loadPPComboBox.findText(self.settings.loadPPName))
        
    def setPulseProgramUi(self, pulseProgramUi ):
        print "ScanControl.setPulseProgramUi", pulseProgramUi.configParams.recentFiles.keys()
        self.pulseProgramUi = pulseProgramUi
        with BlockSignals(self.loadPPComboBox):
            self.loadPPComboBox.clear()
            if hasattr(pulseProgramUi.configParams,'recentFiles'):
                self.loadPPComboBox.addItems(pulseProgramUi.configParams.recentFiles.keys())
            if self.settings.loadPPName: 
                self.loadPPComboBox.setCurrentIndex( self.loadPPComboBox.findText(self.settings.loadPPName))
        self.pulseProgramUi.recentFilesChanged.connect( self.onRecentPPFilesChanged, QtCore.Qt.UniqueConnection )

        if not self.gateSetUi:
            self.gateSetUi = GateSetUi.GateSetUi()
            self.gateSetUi.postInit('test',self.config,self.pulseProgramUi.pulseProgram )
            self.gateSetUi.setupUi(self.gateSetUi)
            self.toolBox.addItem(self.gateSetUi,"Gate Sets")
        if pulseProgramUi.variabledict:
            self.gateSetUi.setVariables( pulseProgramUi.variabledict )
        self.gateSetUi.setSettings( self.settings.gateSetSettings )


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
        self.stepsBox.setEnabled( index in [0,1] )
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
        
    def onStartStopChanged(self, attribute, value):
        self.beginChange()
        setattr( self.settings, attribute, MagnitudeUtilit.mg(value) )
        self.calculateSteps( self.settings )
        self.setSteps( self.settings )
        self.commitChange()

    def onStepsSelectChanged(self, select ):
        print "onStepsSelectChanged", select
        self.settings.stepsSelect = select
        self.calculateSteps( self.settings )
        self.setSteps( self.settings, True )
        
    def onStepsValueChanged( self, value ):
        if self.settings.stepsSelect==0:
            self.settings.steps = int(value)
        else: 
            self.settings.stepSize = value
        self.calculateSteps(self.settings)
        self.setSteps( self.settings )

    def onIntValueChanged(self, attribute, value):
        self.beginChange()
        setattr( self.settings, attribute, value )
        #print id(self.settings), "Variable '{0}' set to {1}".format(attribute, MagnitudeUtilit.mg(value))
        self.commitChange()
        
    def setVariables(self, variabledict):
        self.variabledict = variabledict
        oldParameterName = self.settings.scanParameter
        with BlockSignals(self.comboBoxParameter):
            self.comboBoxParameter.clear()
            for name, var in iter(sorted(variabledict.iteritems())):
                if var.type == "parameter":
                    self.comboBoxParameter.addItem(var.name)
        if self.settings.scanParameter:
            self.comboBoxParameter.setCurrentIndex(self.comboBoxParameter.findText(self.settings.scanParameter) )
        if self.gateSetUi:
            self.gateSetUi.setVariables(variabledict)
            
    def setScanNames(self, scannames):
        self.comboBoxParameter.clear()
        for name in scannames:
            self.comboBoxParameter.addItem(name)
        self.comboBoxParameter.setCurrentIndex( self.comboBoxParameter.findText(self.settings.scanParameter))
        print self.configname,"activating", self.settings.scanParameter
                
    def getScan(self):
        scan = copy.deepcopy(self.settings)
        scan.type = [ ScanList.ScanType.LinearUp, ScanList.ScanType.LinearDown, ScanList.ScanType.Randomized][self.settings.scantype]
        scan.list = ScanList.scanList( scan.start, scan.stop, scan.steps if scan.stepsSelect==0 else scan.stepSize, 
                                       scan.type, scan.stepsSelect )
        scan.evalAlgo = self.algorithms[scan.evalName]
        scan.gateSetUi = self.gateSetUi
        scan.settingsName = self.settingsName
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
        self.settingsName = str(self.comboBox.currentText())
        #print "onSave", name, id(self.settings), self.settings
        if self.settingsName != '':
            if self.settingsName not in self.settingsDict:
                if self.comboBox.findText(self.settingsName)==-1:
                    self.comboBox.addItem(self.settingsName)
                #print self.configname, "adding to combo", self.settingsName
            self.settingsDict[self.settingsName] = copy.deepcopy(self.settings)
    
    def onLoad(self,name):
        self.settingsName = str(name)
        #print self.configname, "onLoad", name
        if self.settingsName !='' and self.settingsName in self.settingsDict:
            self.setSettings(self.settingsDict[self.settingsName])
        else:
            print self.configname, self.settingsDict

    def onReload(self):
        self.onLoad( self.comboBox.currentText() )
   
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
        
    def documentationString(self):
        return self.settings.documentationString()

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
        