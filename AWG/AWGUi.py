from cgitb import text
import copy
import logging
import math
import time

from PyQt4 import QtGui, QtCore
from PyQt4.Qt import QString
import PyQt4.uic
from sympy.parsing.sympy_parser import parse_expr

from AWG.AWGTableModel import AWGTableModel
from externalParameter.InstrumentSettings import InstrumentSettings
from externalParameter.persistence import DBPersist
from modules.Expression import Expression
from modules.firstNotNone import firstNotNone
from modules.SequenceDict import SequenceDict
from modules.magnitude import mg, MagnitudeError
import numpy as np
import sympy as sp
from uiModules.CoordinatePlotWidget import CoordinatePlotWidget
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate

import os
uipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\AWG.ui')
AWGForm, AWGBase = PyQt4.uic.loadUiType(uipath)

class AWGWaveform(object):
    expression = Expression()
    def __init__(self):
        self.__equation = "sin(w*t)"
        self.__points = 64
        self.stack = []
        self.vars = SequenceDict()
       
    @property
    def points(self):
        return self.__points
    
    @points.setter
    def points(self, points):
        #self.__points = 64*int(math.ceil(points/64.0))
        self.__points = points
       
    @property
    def equation(self):
        return self.__equation
        
    @equation.setter
    def equation(self, equation):
        oldvars = self.vars
        self.__equation = equation
        self.stack = self.expression._parse_expression(self.__equation)
        self.vars = SequenceDict( [(i,  {'value': oldvars[i]['value'] if oldvars.has_key(i) else mg(0),
                   'text': oldvars[i]['text'] if oldvars.has_key(i) else None}) for i in self.expression.findDependencies(self.stack)] )
        self.vars.pop('t')
        self.vars['Duration'] = {'value': oldvars['Duration']['value'] if oldvars.has_key('Duration') else mg(1, 'us'), 'text': None}
        self.vars.sort(key = lambda val: -1 if val[0]=='Duration' else ord( str(val[0])[0] ))

    def evaluate(self):
        if not self.vars.has_key('Duration'): self.vars['Duration'] = {'value': mg(1, 'us'), 'text': None}
        self.points = int(self.vars['Duration']['value'].ounit('ns').toval())
        
        # first test expression with dummy variable to see if units match up, so user is warned otherwise
        self.expression.variabledict = dict((k, v['value']) for k, v in self.vars.iteritems())
        self.expression.variabledict.update({'t':mg(1, 'us')})
        self.expression.evaluateWithStack(self.stack[:])
        
        vard = dict((k, v['value'].to_base_units().val) for k, v in self.vars.iteritems())
        vard.pop('Duration')
        vard['t'] = sp.Symbol("t")
        
        spExpr = parse_expr(self.equation, vard)
        f = sp.lambdify(vard['t'], spExpr, "numpy")
        
        step = mg(1, "ns").val
        if self.points > 4000000: self.points = 4000000
        res = f(np.arange(self.points)*step)
        if isinstance(res, (int, long, float, complex)):
            resArray = np.empty(self.points)
            resArray.fill(res)
            res = resArray
        wf = np.clip(res.astype(int), 0, 4095)
        wf = wf.tolist() + [2047]*(64+64*int(math.ceil(self.points/64.0)) - self.points)
        return wf

class Parameters(object):
    def __init__(self):
        self.autoSave = True
        self.setScanParam = False
        self.scanParam = ""
        self.plotEnabled = True

    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault('plotEnabled', True)

class AWGUi(AWGForm, AWGBase):
    varDictChanged = QtCore.pyqtSignal(object)
    analysisNamesChanged = QtCore.pyqtSignal(object)
    def __init__(self, deviceClass, config, globalDict, parent=None):
        AWGBase.__init__(self, parent)
        AWGForm.__init__(self)
        self.config = config

        self.configname = 'AWGUi.' + deviceClass.displayName
        self.persistence = DBPersist()
        self.globalDict = globalDict
        self.parameters = self.config.get(self.configname+"parameters", Parameters())
        self.parameters.device = deviceClass.displayName
        try:
            self.waveform = self.config.get(self.configname+'waveform', AWGWaveform())
        except (TypeError, AttributeError):
            logger.warn( "Unable to read scan control settings. Setting to new scan." )
            self.waveform = AWGWaveform()
        self.device = deviceClass(self.waveform, parent=self)

    def setupUi(self,parent):
        logger = logging.getLogger(__name__)
        AWGForm.setupUi(self,parent)
        self.setWindowTitle(self.device.displayName)
        
        # History and Dictionary
        self.saveButton.clicked.connect( self.onSave )
        self.removeButton.clicked.connect( self.onRemove )
        self.reloadButton.clicked.connect( self.onReload )
        
        self.settingsDict = self.config.get(self.configname+'dict',dict())
        self.settingsName = self.config.get(self.configname+'settingsName',None)
        
        self.settingsComboBox.addItems( sorted(self.settingsDict.keys()))
        if self.settingsName and self.settingsComboBox.findText(self.settingsName):
            self.settingsComboBox.setCurrentIndex( self.settingsComboBox.findText(self.settingsName) )
        self.settingsComboBox.currentIndexChanged[QtCore.QString].connect( self.onLoad )
        self.settingsComboBox.lineEdit().editingFinished.connect( self.checkSettingsSavable )
        
        # Table
        self.tableModel = AWGTableModel(self.waveform, self.globalDict)
        self.tableView.setModel( self.tableModel )
        self.tableModel.valueChanged.connect( self.onValue )
        self.delegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.tableView.setItemDelegateForColumn(1,self.delegate)
        
        # Graph
        self.plot = CoordinatePlotWidget(self, name="Plot")
        self.plot.setTimeAxis(False)
        self.infoLayout.addWidget(self.plot)
        self.plotCheckbox.setChecked(self.parameters.plotEnabled)
        self.plot.setVisible(self.parameters.plotEnabled)
        self.plotCheckbox.stateChanged.connect(self.onPlotCheckbox)

        # Buttons
        self.evalButton.clicked.connect(self.onEvalEqn)
        self.equationEdit.returnPressed.connect(self.onEvalEqn)
        self.programButton.clicked.connect(self.onProgram)
        if not hasattr(self.parameters, 'enabled'):
            self.parameters.enabled = False
        self.enabledCheckbox.stateChanged.connect(self.onEnable)
        self.enabledCheckbox.setChecked(self.parameters.enabled)
        self.onEnable(self.parameters.enabled)
        
        # Context Menu
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.autoSaveAction = QtGui.QAction( "auto save" , self)
        self.autoSaveAction.setCheckable(True)
        self.autoSaveAction.setChecked(self.parameters.autoSave )
        self.autoSaveAction.triggered.connect( self.onAutoSave )
        self.addAction( self.autoSaveAction )
        
        # continuous check box
        if not hasattr(self.parameters, 'continuous'): self.parameters.continuous = False
        self.continuousCheckBox.setChecked(self.parameters.continuous )
        self.continuousCheckBox.stateChanged.connect( self.onContinuousCheckBox )
        
        # Set scan param
        self.setScanParam.setChecked(self.parameters.setScanParam )
        self.setScanParam.stateChanged.connect( self.onSetScanParamCheck )
        self.scanParam.setEnabled(self.parameters.setScanParam)
        self.scanParam.setText(self.parameters.scanParam)
        self.scanParam.textChanged.connect(self.onScanParam)
        
        try:
            self.setWaveform(self.waveform)
        except (TypeError, AttributeError):
            logger.info( "Improper waveform!" )
            self.waveform = AWGWaveform()
            self.equationEdit.setText(self.waveform.equation)
            self.setWaveform(self.waveform)

        self.checkSettingsSavable()
            
    def checkSettingsSavable(self, savable=None):
        if not isinstance(savable, bool):
            currentText = str(self.settingsComboBox.currentText())
            try:
                if currentText is None or currentText=="":
                    savable = False
                elif self.settingsName and self.settingsName in self.settingsDict:
                    savable = self.settingsDict[self.settingsName]!=self.waveform or currentText!=self.settingsName
                else:
                    savable = True
                if self.parameters.autoSave and savable:
                    self.onSave()
                    savable = False
            except MagnitudeError:
                pass
        self.saveButton.setEnabled( savable )
    
    def varDict(self):
        return self.device.varDict
    
    def setWaveform(self, waveform):
        self.waveform = waveform
        self.equationEdit.setText(self.waveform.equation)
        self.tableModel.setWaveform(waveform)
        self.replot()

    def saveConfig(self):
        self.config[self.configname+'waveform'] = self.waveform
        self.config[self.configname+'dict'] = self.settingsDict
        self.config[self.configname+'settingsName'] = self.settingsName
        self.config[self.configname+'parameters'] = self.parameters

    def onSave(self):
        self.settingsName = str(self.settingsComboBox.currentText())
        if self.settingsName != '':
            if self.settingsName not in self.settingsDict:
                if self.settingsComboBox.findText(self.settingsName)==-1:
                    self.settingsComboBox.addItem(self.settingsName)
            self.settingsDict[self.settingsName] = copy.deepcopy(self.waveform)
        self.checkSettingsSavable(savable=False)

    def onRemove(self):
        name = str(self.settingsComboBox.currentText())
        if name != '':
            if name in self.settingsDict:
                self.settingsDict.pop(name)
            idx = self.settingsComboBox.findText(name)
            if idx>=0:
                self.settingsComboBox.removeItem(idx)
                
    def onReload(self):
        self.onLoad( self.settingsComboBox.currentText() )
       
    def onLoad(self,name):
        self.settingsName = str(name)
        if self.settingsName !='' and self.settingsName in self.settingsDict:
            self.setWaveform(self.settingsDict[self.settingsName])
            self.refreshWF()
        self.checkSettingsSavable()
    
    def onAutoSave(self, checked):
        self.parameters.autoSave = checked
        if self.parameters.autoSave:
            self.onSave()
        
    def onEvalEqn(self):
        self.tableModel.beginResetModel()
        self.waveform.equation = str(self.equationEdit.text())
        self.refreshWF()
        self.varDictChanged.emit(self.varDict())
        self.checkSettingsSavable()
        self.tableModel.endResetModel()

    def onValue(self, var, value):
        self.refreshWF()
        
    def onSetScanParamCheck(self, state):
        if state == QtCore.Qt.Checked:
            self.scanParam.setEnabled(True)
            self.parameters.setScanParam = True
        else:
            self.scanParam.setEnabled(False)
            self.parameters.setScanParam = False
        
    def onScanParam(self, text):
        self.parameters.scanParam = text
        
    def onEnable(self, checked):
        if checked:
            self.parameters.enabled = True
            self.enabledCheckbox.setText("Auto AWG program enabled")
            self.enabledCheckbox.setStyleSheet('background-color: rgb(85, 255, 127);')
        else:
            self.parameters.enabled = False
            self.enabledCheckbox.setText("Auto AWG program disabled")
            self.enabledCheckbox.setStyleSheet('background-color: rgb(255, 166, 168);')
        
    def onContinuousCheckBox(self, checked):
        self.parameters.continuous = checked
        
    def onProgram(self):
        self.device.program(self.continuousCheckBox.isChecked())
        
    def refreshWF(self):
        self.device.waveform = self.waveform
        self.replot()
        self.checkSettingsSavable()
        
    def replot(self):
        logger = logging.getLogger(__name__)
        if self.parameters.plotEnabled:
            try:
                waveform = self.waveform.evaluate()
                self.plot.getItem(0,0).clear()
                self.plot.getItem(0,0).plot(waveform)
            except (MagnitudeError, NameError, IndexError) as e:
                logger.warning(e.__class__.__name__ + ": " + str(e))

    def evaluate(self, name):
        self.tableModel.evaluate(name)

    def onPlotCheckbox(self, checked):
        self.parameters.plotEnabled = checked
        if not checked:
            self.plot.getItem(0,0).clear()
        elif checked:
            self.replot()
        self.plot.setVisible(checked)
