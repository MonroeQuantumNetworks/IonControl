import copy
from ctypes import *
import logging
import math
import time

from PyQt4 import QtGui, QtCore
import PyQt4.uic
from sympy.parsing.sympy_parser import parse_expr

from externalParameter.ExternalParameterBase import ExternalParameterBase
from externalParameter.ExternalParameterSelection import Settings
from externalParameter.persistence import DBPersist
import magnitude as magnitude
from modules.Expression import Expression
from modules.Observable import Observable
from modules.firstNotNone import firstNotNone
from modules.magnitude import mg, MagnitudeError
import numpy as np
import sympy as sp
from uiModules.CoordinatePlotWidget import CoordinatePlotWidget
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate


AWGForm, AWGBase = PyQt4.uic.loadUiType(r'ui\AWGUi.ui')

class SEGMENT(Structure):
    _fields_ = [("SegmentNum", c_ulong),
                ("SegmentPtr", POINTER(c_ulong)),
                ("NumPoints", c_ulong),
                ("NumLoops", c_ulong),
                ("BeginPadVal ", c_ulong), # Not used
                ("EndingPadVal", c_ulong), # Not used
                ("TrigEn", c_ulong),
                ("NextSegNum", c_ulong)]
    
da = WinDLL ("DA12000_DLL64.dll")

class AWGWaveform(object):
    expression = Expression()
    def __init__(self):
        self.__equation = "t"
        self.__points = 64;
        self.stack = []
        self.vars = dict()
       
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
        self.vars = dict((i,  {'value': oldvars[i]['value'] if oldvars.has_key(i) else mg(0),
                               'text': oldvars[i]['text'] if oldvars.has_key(i) else None}) for i in self.expression.findDependencies(
                        self.stack))
        self.vars.pop('t')
        self.vars['Duration'] = {'value': oldvars['Duration']['value'] if oldvars.has_key('Duration') else mg(1, 'us'), 'text': None}
    
    def evaluate(self):        
        if not self.vars.has_key('Duration'): self.vars['Duration'] = {'value': mg(1, 'us'), 'text': None}
        self.points = int(self.vars['Duration']['value'].ounit('ns').toval())
        
        vard = dict((k, v['value'].to_base_units().val) for k, v in self.vars.iteritems())
        vard.pop('Duration')
        vard['t'] = sp.Symbol("t")
        
        spExpr = parse_expr(self.equation, vard)
        f = sp.lambdify(vard['t'], spExpr, "numpy")
        
        step = mg(1, "ns").val
        if self.points > 4000000: self.points = 4000000
        wf = np.clip(f(np.arange(self.points)*step).astype(int), 0, 4095)
        wf = wf.tolist() + [2047]*(64+64*int(math.ceil(self.points/64.0)) - self.points)
        return wf
        
class AWGTableModel(QtCore.QAbstractTableModel):
    headerDataLookup = ["Variable", "Value"]
    valueChanged = QtCore.pyqtSignal( object, object )
    
    def __init__(self, waveform, globalDict, parent=None, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.waveform = waveform
        self.globalDict = globalDict
        self.defaultBG = QtGui.QColor(QtCore.Qt.white)
        self.textBG = QtGui.QColor(QtCore.Qt.green).lighter(175)
        
        self.dataLookup = {
            (QtCore.Qt.DisplayRole, 0): lambda row: self.waveform.vars.keys()[row],
            (QtCore.Qt.DisplayRole, 1): lambda row: str(self.waveform.vars.values()[row]['value']),
            (QtCore.Qt.EditRole, 1): lambda row: firstNotNone( self.waveform.vars.values()[row]['text'], str(self.waveform.vars.values()[row]['value'])),
            (QtCore.Qt.BackgroundColorRole,1): lambda row: self.defaultBG if self.waveform.vars.values()[row]['text'] is None else self.textBG,
        }
        self.setDataLookup =  { 
            (QtCore.Qt.EditRole,1): self.setValue,
            (QtCore.Qt.UserRole,1): self.setText
        }
        
    def setValue(self, index, value):
        self.waveform.vars[self.waveform.vars.keys()[index.row()]]['value'] = value
        self.valueChanged.emit(self.waveform.vars.keys()[index.row()], value)
        return True
    
    def setText(self, index, value):
        self.waveform.vars[self.waveform.vars.keys()[index.row()]]['text'] = value
        return True
    
    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.waveform.vars) 
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 2
    
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role, index.column()), lambda row: None)(index.row())
        return None
    
    def setWaveform(self, waveform):
        self.beginResetModel()
        self.waveform = waveform
        self.endResetModel()
        
    def setData(self, index, value, role):
        return self.setDataLookup.get((role,index.column()), lambda index, value: False )(index, value)
        
    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled if index.column()==0 else QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable

    def headerData(self, section, orientation, role):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
            elif (orientation == QtCore.Qt.Vertical):
                return str(section)
        return None  # QtCore.QVariant()
 
class ChaseDA12000(ExternalParameterBase):
    """
    The AWG does not fit into the external parameter framework,
    but given a waveform, the variables can act as external
    parameters. This class wraps a waveform into an external
    parameter-based device.
    """
    className = "Microwave Synthesizer"
    _outputChannels = {}
    _waveform = None
    
    def __init__(self,name,config,waveform):
        ExternalParameterBase.__init__(self,name,config)
        da.da12000_Open(1)
        self.setWaveform(waveform)
        
    def setWaveform(self, waveform):
        self._waveform = waveform
        self.setDefaults()
        self.displayValueObservable = dict([(name,Observable()) for name in self._outputChannels])
        vardict = {k: "" if v['value'].dimensionless() else str(v['value']).split(" ")[1] for (k, v) in self._waveform.vars.iteritems()}
        self._outputChannels = vardict
        for (k, v) in vardict.iteritems():
            self.settings.value[k] = self._waveform.vars[k]['value']
    
    def fullName(self, channel):
        return "{0}".format(channel)

    def setDefaults(self):
        ExternalParameterBase.setDefaults(self)
        self.settings.__dict__.setdefault('stepsize' , magnitude.mg(1,''))
                
    def _setValue(self, channel, v, continuous):
        self._waveform.vars[channel]['value'] = v
        
        pts = self._waveform.evaluate()
        seg_pts = (c_ulong * len(pts))(*pts)
        seg1 = SEGMENT(0, seg_pts, len(pts), 0, 2048, 2048, 1, 0)
        seg = (SEGMENT*1)(seg1)
        
        da.da12000_CreateSegments(1, 1, 1, seg)
        da.da12000_SetTriggerMode(1, 1 if continuous else 2, 0)
        
    def setValue(self, channel, value, continuous=False):
        """
        This function returns True if the value is reached. Otherwise
        it should return False. The user should call repeatedly until the intended value is reached
        and True is returned.
        """
        self._setValue(channel, value, continuous)
        
        #self.setWaveform(self._waveform)
        
        return True
        
    def paramDef(self):
        """
        return the parameter definition used by pyqtgraph parametertree to show the gui
        """
        superior = ExternalParameterBase.paramDef(self)
        superior.append({'name': 'stepsize', 'type': 'magnitude', 'value': self.settings.stepsize})
        return superior

    def close(self):
        da.da12000_Close(1)

class Parameters(object):
    def __init__(self):
        self.autoSave = False
        
class AWGUi(AWGForm, AWGBase):
    outputChannelsChanged = QtCore.pyqtSignal(object)
    analysisNamesChanged = QtCore.pyqtSignal(object)
    def __init__(self, pulser, config, globalDict, parent = None):
        AWGBase.__init__(self, parent)
        AWGForm.__init__(self)
        self.config = config
        self.configname = 'AWGUi.'
        self.persistence = DBPersist()
        self.globalDict = globalDict
        self.parameters = self.config.get(self.configname+"parameters", Parameters())
            
    def setupUi(self,parent):
        logger = logging.getLogger(__name__)
        AWGForm.setupUi(self,parent)
        
        # History and Dictionary
        self.saveButton.clicked.connect( self.onSave )
        self.removeButton.clicked.connect( self.onRemove )
        self.reloadButton.clicked.connect( self.onReload )
        
        # Persistence
        try:
            self.waveform = self.config.get(self.configname+'waveform', AWGWaveform())
        except (TypeError, AttributeError):
            logger.info( "Unable to read scan control settings. Setting to new scan." )
            self.waveform = AWGWaveform()
        
        self.device = ChaseDA12000(None, Settings(), self.waveform)
        
        self.settingsDict = self.config.get(self.configname+'dict',dict())
        self.settingsName = self.config.get(self.configname+'settingsName',None)
        
        self.comboBox.addItems( sorted(self.settingsDict.keys()))
        if self.settingsName and self.comboBox.findText(self.settingsName):
            self.comboBox.setCurrentIndex( self.comboBox.findText(self.settingsName) )
        self.comboBox.currentIndexChanged[QtCore.QString].connect( self.onLoad )
        self.comboBox.lineEdit().editingFinished.connect( self.checkSettingsSavable )
        
        # Table
        self.AWGTableModel = AWGTableModel(self.waveform, self.globalDict)
        self.tableView.setModel( self.AWGTableModel )
        self.AWGTableModel.valueChanged.connect( self.onValue )
        self.delegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.tableView.setItemDelegateForColumn(1,self.delegate)
        
        # Graph
        self.plot = CoordinatePlotWidget(self, name="Plot")
        self.plot.setTimeAxis(False)
        self.infoLayout.addWidget(self.plot)
        
        # Buttons
        self.evalButton.clicked.connect(self.onEval)
        
        # Context Menu
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.autoSaveAction = QtGui.QAction( "auto save" , self)
        self.autoSaveAction.setCheckable(True)
        self.autoSaveAction.setChecked(self.parameters.autoSave )
        self.autoSaveAction.triggered.connect( self.onAutoSave )
        self.addAction( self.autoSaveAction )
        
        try:
            self.setWaveform(self.waveform)
        except (TypeError, AttributeError):
            logger.info( "Improper waveform!" )
            self.waveform = AWGWaveform()
            self.setWaveform(self.waveform)
    
    def checkSettingsSavable(self, savable=None):
        if not isinstance(savable, bool):
            currentText = str(self.comboBox.currentText())
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
    
    def outputChannels(self):  
        return dict(self.device.outputChannels())
    
    def setWaveform(self, waveform):
        self.waveform = waveform
        self.eqnbox.setText(self.waveform.equation)
        self.AWGTableModel.setWaveform(waveform)
        self.replot()

    def saveConfig(self):
        self.config[self.configname+'waveform'] = self.waveform
        self.config[self.configname+'dict'] = self.settingsDict
        self.config[self.configname+'settingsName'] = self.settingsName
        self.config[self.configname+'parameters'] = self.parameters

    def onSave(self):
        self.settingsName = str(self.comboBox.currentText())
        if self.settingsName != '':
            if self.settingsName not in self.settingsDict:
                if self.comboBox.findText(self.settingsName)==-1:
                    self.comboBox.addItem(self.settingsName)
            self.settingsDict[self.settingsName] = copy.deepcopy(self.waveform)
        self.checkSettingsSavable(savable=False)

    def onRemove(self):
        name = str(self.comboBox.currentText())
        if name != '':
            if name in self.settingsDict:
                self.settingsDict.pop(name)
            idx = self.comboBox.findText(name)
            if idx>=0:
                self.comboBox.removeItem(idx)
                
    def onReload(self):
        self.onLoad( self.comboBox.currentText() )
       
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
        
    def onEval(self):
        self.waveform.equation = str(self.eqnbox.text())
        del self.AWGTableModel
        self.AWGTableModel = AWGTableModel(self.waveform, self.globalDict)
        self.tableView.setModel( self.AWGTableModel )
        self.AWGTableModel.valueChanged.connect( self.onValue )
        
        self.outputChannelsChanged.emit( self.outputChannels() )
        self.checkSettingsSavable()
        
    def onValue(self, var, value):
        self.refreshWF()
        
    def refreshWF(self):
        self.device.setWaveform(self.waveform)
        self.outputChannelsChanged.emit( self.outputChannels() )

        self.replot()
        self.checkSettingsSavable()
        
    def replot(self):
        logger = logging.getLogger(__name__)
        self.plot.getItem(0,0).clear()
        try:
            self.plot.getItem(0,0).plot(self.waveform.evaluate())
        except MagnitudeError as e:
            logger.warn(e)
            
