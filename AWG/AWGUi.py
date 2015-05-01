import copy
import logging

from PyQt4 import QtGui, QtCore
import PyQt4.uic

import math
import numpy

from pyqtgraph.dockarea import DockArea, Dock
from uiModules.CoordinatePlotWidget import CoordinatePlotWidget

from externalParameter.persistence import DBPersist
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.GuiAppearance import restoreGuiState, saveGuiState   #@UnresolvedImport
from modules.Expression import Expression
from modules.magnitude import is_magnitude, mg
from modules.firstNotNone import firstNotNone
from functools import partial

AWGForm, AWGBase = PyQt4.uic.loadUiType(r'ui\AWGUi.ui')

class AWGWaveform(object):
    expression = Expression()
    def __init__(self):
        self.__equation = ""
        self.__points = 64;
        self.stack = []
        self.vars = dict()
       
    @property
    def points(self):
        return self.__points
    
    @points.setter
    def points(self, points):
        self.__points = 64*int(math.ceil(points/64.0))
       
    @property
    def equation(self):
        return self.__equation
        
    @equation.setter
    def equation(self, equation):
        self.__equation = equation
        self.stack = self.expression._parse_expression(self.__equation)
        self.vars = dict((i,  {'value': mg(0), 'text': None}) for i in self.expression.findDependencies(
                        self.stack))
    
    def evaluate(self):
        def f(stack, expression, x):
            vard = dict((k, v['value']) for k, v in self.vars.iteritems())
            vard['x'] = x
            expression.variabledict = vard
            expression.evaluateWithStack(stack[:])
        return map(partial(f, self.stack, self.expression), range(self.points))
        
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
 
        
class AWGUi(AWGForm, AWGBase):
    analysisNamesChanged = QtCore.pyqtSignal(object)
    def __init__(self, pulser, config, globalDict, parent = None):
        AWGBase.__init__(self, parent)
        AWGForm.__init__(self)
        self.config = config
        self.persistence = DBPersist()
        self.globalDict = globalDict
            
    def setupUi(self,parent):
        AWGForm.setupUi(self,parent)
        
        # Persistence
        self.waveform = self.config.get('AWGUi.waveform', AWGWaveform())
        
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
        #restoreGuiState( self, self.config.get(self.configname+".guiState") )
        #self.autoSave()
        
    def onEval(self):
        self.waveform.equation = str(self.eqnbox.text())
        del self.AWGTableModel
        self.AWGTableModel = AWGTableModel(self.waveform, self.globalDict)
        self.tableView.setModel( self.AWGTableModel )
        self.AWGTableModel.valueChanged.connect( self.onValue )
        
        print self.waveform.equation, self.waveform.points
        print self.waveform.stack
        
    def onValue(self, var, value):
        self.plot.getItem(0,0).plot(self.waveform.evaluate())
#         if self.autoApply: self.onApply()
#         self.decimation[(0,channel)].decimate( time.time(), value, partial(self.persistCallback, "Frequency:{0}".format(self.ddsChannels[channel].name if self.ddsChannels[channel].name else channel)) )
