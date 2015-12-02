from cgitb import text
import copy
import logging
import time

from PyQt4 import QtGui, QtCore
from PyQt4.Qt import QString
import PyQt4.uic

from AWG.AWGTableModel import AWGTableModel
from modules.firstNotNone import firstNotNone
from modules.magnitude import mg, MagnitudeError
from uiModules.CoordinatePlotWidget import CoordinatePlotWidget
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.PyqtUtility import BlockSignals

import os
uipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\AWG.ui')
AWGForm, AWGBase = PyQt4.uic.loadUiType(uipath)

class Settings(object):
    def __init__(self):
        self.setScanParam = False
        self.scanParam = ""
        self.plotEnabled = True
        self.continuous = False
        self.programOnScanStart = False
        self.waveform = None

    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault('plotEnabled', True)
        self.__dict__.setdefault('continuous', False)
        self.__dict__.setdefault('programOnScanStart', False)
        self.__dict__.setdefault('waveform', None)

    stateFields = ['setScanParam', 'scanParam', 'plotEnabled', 'continuous', 'programOnScanStart', 'waveform']

    def __eq__(self,other):
        return tuple(getattr(self,field) for field in self.stateFields)==tuple(getattr(other,field) for field in self.stateFields)

    def __ne__(self, other):
        return not self == other

class AWGUi(AWGForm, AWGBase):
    varDictChanged = QtCore.pyqtSignal(object)
    def __init__(self, deviceClass, config, globalDict, parent=None):
        AWGBase.__init__(self, parent)
        AWGForm.__init__(self)
        self.config = config
        self.configname = 'AWGUi.' + deviceClass.displayName
        self.globalDict = globalDict
        self.autoSave = self.config.get(self.configname+'.autoSave', True)
        self.settingsDict = self.config.get(self.configname+'.settingsDict', dict())
        self.settingsName = self.config.get(self.configname+'.settingsName', '')
        self.settings = copy.deepcopy(self.settingsDict[self.settingsName]) if self.settingsName in self.settingsDict else Settings()
        self.device = deviceClass(self.settings.waveform, parent=self)
        self.settings.waveform = self.device.waveform

    def setupUi(self,parent):
        logger = logging.getLogger(__name__)
        AWGForm.setupUi(self,parent)
        self.setWindowTitle(self.device.displayName)
        
        # History and Dictionary
        self.saveButton.clicked.connect( self.onSave )
        self.removeButton.clicked.connect( self.onRemove )
        self.reloadButton.clicked.connect( self.onReload )

        self.settingsModel = QtGui.QStringListModel()
        self.settingsComboBox.setModel(self.settingsModel)
        self.settingsModel.setStringList( sorted(self.settingsDict.keys()) )
        self.settingsComboBox.setCurrentIndex( self.settingsComboBox.findText(self.settingsName) )
        self.settingsComboBox.currentIndexChanged[str].connect( self.onLoad )
        self.settingsComboBox.lineEdit().editingFinished.connect( self.onComboBoxEditingFinished )
        
        # Table
        self.tableModel = AWGTableModel(self.settings.waveform, self.globalDict)
        self.tableView.setModel( self.tableModel )
        self.tableModel.valueChanged.connect( self.onValue )
        self.delegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.tableView.setItemDelegateForColumn(1,self.delegate)
        
        # Graph and equation
        self.equationEdit.setText(self.settings.waveform.equation)
        self.plot = CoordinatePlotWidget(self, name="Plot")
        self.plot.setTimeAxis(False)
        self.infoLayout.addWidget(self.plot)
        self.plotCheckbox.setChecked(self.settings.plotEnabled)
        self.plot.setVisible(self.settings.plotEnabled)
        self.plotCheckbox.stateChanged.connect(self.onPlotCheckbox)

        # Buttons
        self.evalButton.clicked.connect(self.onEvalEqn)
        self.equationEdit.returnPressed.connect(self.onEvalEqn)
        self.programButton.clicked.connect(self.onProgram)
        self.triggerButton.clicked.connect(self.onTrigger)
        self.programOnScanCheckbox.stateChanged.connect(self.onProgramOnScan)
        self.programOnScanCheckbox.setChecked(self.settings.programOnScanStart)
        self.onProgramOnScan(self.settings.programOnScanStart)
        
        # Context Menu
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.autoSaveAction = QtGui.QAction( "auto save" , self)
        self.autoSaveAction.setCheckable(True)
        self.autoSaveAction.setChecked(self.autoSave )
        self.saveButton.setEnabled( not self.autoSave )
        self.autoSaveAction.triggered.connect( self.onAutoSave )
        self.addAction( self.autoSaveAction )
        
        # continuous check box
        self.continuousCheckBox.setChecked(self.settings.continuous )
        self.continuousCheckBox.stateChanged.connect( self.onContinuousCheckBox )
        
        # Set scan param
        self.setScanParam.setChecked(self.settings.setScanParam )
        self.setScanParam.stateChanged.connect( self.onSetScanParamCheck )
        self.scanParam.setEnabled(self.settings.setScanParam)
        self.scanParam.setText(self.settings.scanParam)
        self.scanParam.textChanged.connect(self.onScanParam)

        self.replot()

    def onComboBoxEditingFinished(self):
        self.settingsName = str(self.settingsComboBox.currentText())
        if self.settingsName not in self.settingsDict:
            self.settingsDict[self.settingsName] = copy.deepcopy(self.settings)
        self.onLoad(self.settingsName)

    def saveIfNecessary(self):
        """save the current settings if autosave is on and something has changed"""
        currentText = str(self.settingsComboBox.currentText())
        if self.settingsDict.get(self.settingsName)!=self.settings or currentText!=self.settingsName:
            if self.autoSave:
                self.onSave()
            else:
                self.saveButton.setEnabled(True)

    def onSave(self):
        self.settingsName = str(self.settingsComboBox.currentText())
        self.settingsDict[self.settingsName] = copy.deepcopy(self.settings)
        with BlockSignals(self.settingsComboBox) as w:
            self.settingsModel.setStringList( sorted(self.settingsDict.keys()) )
            w.setCurrentIndex(w.findText(self.settingsName))
        self.saveButton.setEnabled(False)

    def saveConfig(self):
        self.config[self.configname+'.settingsDict'] = self.settingsDict
        self.config[self.configname+'.settingsName'] = self.settingsName
        self.config[self.configname+'.autoSave'] = self.autoSave

    def onRemove(self):
        name = str(self.settingsComboBox.currentText())
        if name in self.settingsDict:
            self.settingsDict.pop(name)
            self.settingsName = self.settingsDict.keys()[0] if self.settingsDict else ''
            with BlockSignals(self.settingsComboBox) as w:
                self.settingsModel.setStringList( sorted(self.settingsDict.keys()) )
                w.setCurrentIndex(w.findText(self.settingsName))

    def onReload(self):
        name = str(self.settingsComboBox.currentText())
        self.onLoad(name)
       
    def onLoad(self, name):
        name = str(name)
        if name in self.settingsDict:
            self.settingsName = name
            self.settings = copy.deepcopy(self.settingsDict[self.settingsName])
            self.refreshWaveform()
            self.plotCheckbox.setChecked(self.settings.plotEnabled)
            self.setScanParam.setChecked(self.settings.setScanParam)
            self.scanParam.setText(self.settings.scanParam)
            self.continuousCheckBox.setChecked(self.settings.continuous)
            self.programOnScanCheckbox.setChecked(self.settings.programOnScanStart)
            self.saveButton.setEnabled(False)
            self.replot()
            self.saveIfNecessary()

    def refreshWaveform(self):
        self.tableModel.beginResetModel()
        self.device.waveform = self.settings.waveform
        self.tableModel.waveform = self.settings.waveform
        self.tableModel.endResetModel()

    def onAutoSave(self, checked):
        self.autoSave = checked
        self.saveButton.setEnabled(not checked)
        if checked:
            self.onSave()

    def onEvalEqn(self):
        self.tableModel.beginResetModel()
        self.settings.waveform.equation = str(self.equationEdit.text())
        self.replot()
        self.varDictChanged.emit(self.settings.waveform.varDimensionDict)
        self.saveIfNecessary()
        self.tableModel.endResetModel()

    def onValue(self, var, value):
        self.saveIfNecessary()
        self.replot()
        
    def onSetScanParamCheck(self, state):
        if state == QtCore.Qt.Checked:
            self.scanParam.setEnabled(True)
            self.settings.setScanParam = True
        else:
            self.scanParam.setEnabled(False)
            self.settings.setScanParam = False
        self.saveIfNecessary()
        
    def onScanParam(self, text):
        self.settings.scanParam = text
        self.saveIfNecessary()
        
    def onProgramOnScan(self, checked):
        if checked:
            self.settings.programOnScanStart = True
            self.programOnScanCheckbox.setText("Auto AWG program enabled")
            self.programOnScanCheckbox.setStyleSheet('background-color: rgb(85, 255, 127);')
        else:
            self.settings.programOnScanStart = False
            self.programOnScanCheckbox.setText("Auto AWG program disabled")
            self.programOnScanCheckbox.setStyleSheet('background-color: rgb(255, 166, 168);')
        self.saveIfNecessary()
        
    def onContinuousCheckBox(self, checked):
        self.settings.continuous = checked
        self.saveIfNecessary()
        
    def onProgram(self):
        self.device.program(self.settings.continuous)

    def onTrigger(self):
        self.device.trigger()

    def replot(self):
        logger = logging.getLogger(__name__)
        if self.settings.plotEnabled:
            try:
                waveform = self.device.waveform.evaluate()
                self.plot.getItem(0,0).clear()
                self.plot.getItem(0,0).plot(waveform)
            except (MagnitudeError, NameError, IndexError) as e:
                logger.warning(e.__class__.__name__ + ": " + str(e))

    def evaluate(self, name):
        self.tableModel.evaluate(name)

    def onPlotCheckbox(self, checked):
        self.settings.plotEnabled = checked
        if not checked:
            self.plot.getItem(0,0).clear()
        elif checked:
            self.replot()
        self.plot.setVisible(checked)
        self.saveIfNecessary()
