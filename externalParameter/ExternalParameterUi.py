# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 23:45:54 2013

@author: pmaunz
"""

import functools
import logging

from PyQt4 import QtCore, QtGui
import PyQt4.uic

from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.SequenceDict import SequenceDict
from modules.firstNotNone import firstNotNone
from modules.Expression import Expression
from modules.Observable import Observable
from modules.GuiAppearance import restoreGuiState, saveGuiState
from modules.magnitude import MagnitudeError
from uiModules.CategoryTree import CategoryTreeModel, CategoryTreeView
from copy import deepcopy

class ExternalParameterControlModel(CategoryTreeModel):
    valueChanged = QtCore.pyqtSignal(str, object)
    expression = Expression()
    def __init__(self, controlUi, parameterList=[], parent=None):
        super(ExternalParameterControlModel, self).__init__(parameterList, parent, nodeNameAttr='displayName')
        self.parameterList=parameterList
        self.controlUi = controlUi
        for parameter in parameterList:
            parameter.categories = parameter.device.name
        self.headerLookup.update({
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 0): 'Name',
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 1): 'Control',
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, 2): 'External'
            })
        self.dataLookup.update({
            (QtCore.Qt.DisplayRole,0): lambda node: node.content.displayName,
            (QtCore.Qt.DisplayRole,1): lambda node: str(node.content.targetValue),
            (QtCore.Qt.EditRole,1): lambda node: firstNotNone( node.content.strValue, str(node.content.targetValue) ),
            (QtCore.Qt.UserRole,1): lambda node: node.content.dimension,
            (QtCore.Qt.DisplayRole,2): lambda node: str(node.content.lastExternalValue),
            (QtCore.Qt.BackgroundRole,1): self.backgroundFunction,
            (QtCore.Qt.ToolTipRole,1): self.toolTipFunction
            })
        self.setDataLookup.update({
            (QtCore.Qt.EditRole,1): lambda index, value: self.setValue(index, value),
            (QtCore.Qt.UserRole,1): lambda index, value: self.setStrValue(index, value),
            })
        self.flagsLookup = {
            1:QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable
        }
        self.adjustingDevices = 0
        self.doneAdjusting = Observable()
        self.numColumns = 3
        self.allowReordering = True

    def setParameterList(self, outputChannelDict):
        self.beginResetModel()
        self.parameterList = outputChannelDict.values()
        for listIndex,inst in enumerate(self.parameterList):
            inst.multipleChannels = len(inst.device._outputChannels)>1
            inst.categories = inst.device.name if inst.multipleChannels else None
            inst.displayName = inst.channelName if inst.multipleChannels else inst.device.name
            inst.targetValue = deepcopy(inst.value)
            inst.lastExternalValue = deepcopy(inst.externalValue)
            inst.toolTip = None
            inst.observable.clear()
            inst.observable.subscribe( functools.partial( self.showValue, listIndex ) )
        self.clear()
        self.endResetModel()
        self.addNodeList(self.parameterList)

    def showValue(self, listIndex, value, tooltip=None):
        inst=self.parameterList[listIndex]
        inst.lastExternalValue = value.value
        inst.toolTip = tooltip
        id=inst.name if inst.multipleChannels else inst.device.name
        node = self.nodeDict[id]
        modelIndex=self.indexFromNode(node, 2)
        self.dataChanged.emit(modelIndex,modelIndex)
            
    def setValue(self, index, value):
        node=self.nodeFromIndex(index)
        self._setValue(node.content, value)

    def _setValue(self, inst, value):
        logger = logging.getLogger(__name__)
        logger.debug( "setValue {0}".format(value))
        if inst.targetValue is None or value != inst.targetValue:
            inst.targetValue = value
            self.adjustingDevices += 1
            logger.debug("Increased adjusting instruments to {0}".format(self.adjustingDevices))
            self.setValueFollowup(inst)
        return True
 
    def setStrValue(self, index, strValue):
        node=self.nodeFromIndex(index)
        node.content.strValue = strValue
        return True
        
    def setValueFollowup(self, inst):
        try:
            logger = logging.getLogger(__name__)
            logger.debug( "setValueFollowup {0}".format( inst.value ) )
            delay = int( inst.delay.toval('ms') )
            if not inst.setValue(inst.targetValue):
                QtCore.QTimer.singleShot(delay,functools.partial(self.setValueFollowup,inst))
            else:
                self.adjustingDevices -= 1
                logger.debug("Decreased adjusting instruments to {0}".format(self.adjustingDevices))
                if self.adjustingDevices==0:
                    self.doneAdjusting.firebare()
                    self.doneAdjusting.callbacks = list()
        except Exception as e:
            logger.exception(e)
            logger.warning( "Exception during setValueFollowup, number of adjusting devices likely to be faulty")

    def update(self, iterable):
        for destination, name, value in iterable:
            if destination=='External':
                for inst in self.parameterList:
                    if inst.name==name:
                        break
                inst.savedValue = value    # set saved value to make this new value the default
                node = self.nodeFromContent(inst)
                self.setValue(self.indexFromNode(node,1), value)
                inst.strValue = None
                logging.info("Pushed to external parameter {0} value {1}".format(name,value)) 
                
    def evaluate(self, name):
        for inst in self.parameterList:
            expr = inst.strValue
            if expr is not None:
                value = self.expression.evaluateAsMagnitude(expr, self.controlUi.globalDict)
                self._setValue(inst, value)
                inst.savedValue = value   # set saved value to make this new value the default
                node = self.nodeFromContent(inst)
                index = self.indexFromNode(node,1)
                self.dataChanged.emit(index, index)

class ControlUi(CategoryTreeView):
    def __init__(self, config, globalDict=None, parent=None):
        super(ControlUi, self).__init__(parent)
        self.spacerItem = None
        self.myLabelList = list()
        self.myBoxList = list()
        self.myDisplayList = list()
        self.targetValue = dict()
        self.currentValue = dict()
        self.displayWidget = dict()
        self.tagetValue = dict()
        self.globalDict = firstNotNone( globalDict, dict() )
        self.config = config
        self.configName = 'ControlUi'
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
    
    def setupUi(self, outputChannels):
        model = ExternalParameterControlModel(self)
        self.setModel(model)
        self.delegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.setItemDelegateForColumn(1,self.delegate)
        self.setupParameters(outputChannels)
        restoreGuiState(self, self.config.get(self.configName+'.guiState'))
        try:
            self.restoreTreeState( self.config.get(self.configName+'.treeState',tuple([None]*4)) )
        except Exception as e:
            logging.getLogger(__name__).error("unable to restore tree state in {0}: {1}".format(self.configName, e))

    def setupParameters(self, outputChannels):
        oldState=self.treeState()
        oldNodeDictKeys=self.model().nodeDict.keys()
        self.model().setParameterList(outputChannels)
        self.header().setStretchLastSection(True)
        self.restoreTreeState(oldState)
        for key, node in self.model().nodeDict.iteritems():
            if key not in oldNodeDictKeys: #Expand any new nodes
                index = self.model().indexFromNode(node)
                self.expand(index)
        try:
            self.evaluate(None)
        except (KeyError, MagnitudeError) as e:
            logging.getLogger(__name__).warning(str(e))
        
    def keys(self):
        pList = self.model().parameterList
        return [p.name for p in pList]
    
    def update(self, iterable):
        self.model().update(iterable)
        self.viewport().repaint()
        
    def evaluate(self, name):
        self.model().evaluate(name)
        
    def isAdjusting(self):
        return self.model().adjustingDevices>0
    
    def callWhenDoneAdjusting(self, callback):
        if self.isAdjusting():
            self.model().doneAdjusting.subscribe(callback)
        else:
            QtCore.QTimer.singleShot(0, callback)
            
    def saveConfig(self):
        self.config[self.configName+'.guiState'] = saveGuiState(self)
        try:
            self.config[self.configName+'.treeState'] = self.treeState()
        except Exception as e:
            logging.getLogger(__name__).error("unable to save tree state in {0}: {1}".format(self.configName, e))

    
