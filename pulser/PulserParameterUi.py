# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 23:45:54 2013

@author: pmaunz
"""

from PyQt4 import QtCore, QtGui
import PyQt4.uic

from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from uiModules.CategoryTree import CategoryTreeModel, nodeTypes
from modules.firstNotNone import firstNotNone
from modules.Expression import Expression
from modules.GuiAppearance import restoreGuiState, saveGuiState
from gui.ExpressionValue import ExpressionValue
from _functools import partial
from _collections import defaultdict
from pulseProgram import PulseProgram
import logging

UiForm, UiBase = PyQt4.uic.loadUiType(r'ui\PulserParameterUi.ui')

class PulserParameter(ExpressionValue):
    def __init__(self, name=None, address=0, string=None, onChange=None, bitmask=0xffffffffffffffff,
                 shift=0, encoding=None, globalDict=None, categories=None):
        super(PulserParameter, self).__init__(name=name, globalDict=globalDict)
        self.address = address
        if onChange is not None:
            self.observable.subscribe(onChange)
        self.string = string
        self.bitmask = bitmask
        self.shift = shift
        self.encoding = encoding
        self._magnitude = None
        self.categories = categories
        self.name = name

    @property
    def encodedValue(self):
        return (PulseProgram.encode( self.value, self.encoding ) & self.bitmask) << self.shift
    
    def setBits(self, inputMask):
        shiftedMask = self.bitmask << self.shift
        return inputMask & (~shiftedMask) | self.encodedValue


class PulserParameterTreeModel(CategoryTreeModel):
    expression = Expression()
    def __init__(self, parameterList, parent=None):
        super(PulserParameterTreeModel, self).__init__(parameterList, parent)
        self.headerLookup.update({
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 0): 'Name',
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 1): 'Value'
            })
        self.dataLookup.update({
            (nodeTypes.data, QtCore.Qt.DisplayRole, 0): lambda node: node.content.name,
            (nodeTypes.data, QtCore.Qt.DisplayRole, 1): lambda node: str(node.content.value),
            (nodeTypes.data, QtCore.Qt.EditRole, 1): lambda node: node.content.string
            })
        self.setDataLookup.update({
            (nodeTypes.data, QtCore.Qt.EditRole, 1): lambda node, value: self.setValue(node, value),
            (nodeTypes.data, QtCore.Qt.UserRole, 1): lambda node, value: self.setStrValue(node, value)
            })
        self.flagsLookup.update({
            (nodeTypes.data, 0): QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable,
            (nodeTypes.data, 1): QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable
            })
        self.numColumns = 2

    def setValue(self, node, value):
        node.content.value = value
        return True
         
    def setStrValue(self, node, strValue):
        node.content.string = strValue
        return True
        

class PulserParameterUi(UiForm,UiBase):
    def __init__(self, pulser, config, globalDict=None, parent=None):
        UiBase.__init__(self,parent)
        UiForm.__init__(self)
        self.isSetup = False
        self.globalDict = firstNotNone( globalDict, dict() )
        self.config = config
        self.configName = 'PulserParameterUi'
        self.pulser = pulser
        oldValues = self.config.get( 'PulserParameterValues', dict() )
        self.parameterList = list()
        pulserconfig = self.pulser.pulserConfiguration()
        self.currentWireValues = defaultdict( lambda: 0 )
        if pulserconfig:
            for index, extendedWireIn in enumerate(pulserconfig.extendedWireIns):
                value, string = oldValues.get(extendedWireIn.name,(extendedWireIn.default,None))
                parameter = PulserParameter(name=extendedWireIn.name, address=extendedWireIn.address, string=string,
                                            bitmask=extendedWireIn.bitmask, shift=extendedWireIn.shift, encoding=extendedWireIn.encoding,
                                            categories=extendedWireIn.categories, onChange=partial(self.onChange,index), globalDict=self.globalDict)
                self.parameterList.append( parameter )
                parameter.value = value
        
    def setupUi(self):
        UiForm.setupUi(self, self)
        self.model = PulserParameterTreeModel(self.parameterList)
        self.categoryTreeView.setModel(self.model)
        self.delegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.categoryTreeView.setItemDelegateForColumn(1,self.delegate)
        restoreGuiState( self, self.config.get(self.configName+'.guiState'))
        try:
            self.categoryTreeView.restoreTreeState( self.config.get(self.configName+'.treeState',(None,None)) )
        except Exception as e:
            logging.getLogger(__name__).error("unable to restore tree state in {0}: {1}".format(self.configName, e))
        self.isSetup = True

    def saveConfig(self):
        self.config['PulserParameterValues'] = dict( (p.name,(p.value,p.string if p.hasDependency else None)) for p in self.parameterList )
        self.config[self.configName+'.guiState'] = saveGuiState(self)
        try:
            self.config[self.configName+'.treeState'] = self.categoryTreeView.treeState()
        except Exception as e:
            logging.getLogger(__name__).error("unable to save tree state in {0}: {1}".format(self.configName, e))

    def onChange(self, index, event ):
        parameter = self.parameterList[index]
        self.currentWireValues[parameter.address] = parameter.setBits(self.currentWireValues[parameter.address])
        self.pulser.setExtendedWireIn( parameter.address, self.currentWireValues[parameter.address] )
        if self.isSetup and event.origin!='value':
            node = self.nodes[parameter.name]
            ind = self.model.createIndex(node.row, 1, node)
            self.model.dataChanged.emit(ind, ind)
