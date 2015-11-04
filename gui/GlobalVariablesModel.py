# -*- coding: utf-8 -*-
"""
Created on Fri Feb 08 22:02:08 2013

@author: pmaunz
"""
import logging

from PyQt4 import QtCore, QtGui
import sip

from modules import Expression
import modules.magnitude as magnitude
from modules import MagnitudeUtilit
from modules.MagnitudeParser import isIdentifier
from functools import partial
from uiModules.CategoryTree import CategoryTreeModel, nodeTypes
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.enum import enum
from modules.PyqtUtility import textSize

api2 = sip.getapi("QVariant") == 2

gridColor = QtGui.QColor(215, 215, 215, 255) #light gray

class GridDelegateMixin(object):
    def paint(self, painter, option, index):
        if index.model().nodeFromIndex(index).nodeType == nodeTypes.data:
            painter.save()
            painter.setPen(gridColor)
            painter.drawRect(option.rect)
            painter.restore()
        QtGui.QStyledItemDelegate.paint(self, painter, option, index)

    def sizeHint(self, option, index):
        text = str(index.data(QtCore.Qt.DisplayRole).toString())
        width = 1.05*textSize(text).width()
        height = 30
        size = QtCore.QSize(width, height)
        return size


class MagnitudeSpinBoxGridDelegate(MagnitudeSpinBoxDelegate, GridDelegateMixin):
    paint = GridDelegateMixin.paint
    sizeHint = GridDelegateMixin.sizeHint


class GridDelegate(QtGui.QStyledItemDelegate, GridDelegateMixin):
    paint = GridDelegateMixin.paint
    sizeHint = GridDelegateMixin.sizeHint


class GlobalVariablesModel(CategoryTreeModel):
    valueChanged = QtCore.pyqtSignal(object)
    expression = Expression.Expression()
    def __init__(self, config, variables, parent=None):
        super(GlobalVariablesModel, self).__init__(variables, parent)
        self.config = config
        self.variables = variables
        self.columnNames = ['name', 'value']
        self.numColumns = len(self.columnNames)
        self.column = enum(*self.columnNames)
        self.headerLookup.update({
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.name): "Name",
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.value): "Value"
            })
        self.dataLookup.update({
            (QtCore.Qt.DisplayRole, self.column.name): lambda node: node.content.name,
            (QtCore.Qt.DisplayRole, self.column.value): lambda node: str(node.content.value),
            (QtCore.Qt.EditRole, self.column.name): lambda node: node.content.name,
            (QtCore.Qt.EditRole, self.column.value): lambda node: str(node.content.value)
            })
        self.setDataLookup.update({
            (QtCore.Qt.EditRole, self.column.name): self.setName,
            (QtCore.Qt.EditRole, self.column.value): self.setValue
            })
        self.flagsLookup = {
            self.column.name: QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled,
            self.column.value: QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
            }
        self.allowReordering = True
        self.allowDeletion = True
        self.connectAllVariableSignals()

    def connectAllVariableSignals(self):
        for item in self.variables:
            try:
                item.valueChanged.connect(self.onValueChanged, QtCore.Qt.UniqueConnection)
            except:
                pass

    def endResetModel(self):
        super(GlobalVariablesModel, self).endResetModel()
        self.connectAllVariableSignals()

    def onValueChanged(self, name, value, origin):
        self.valueChanged.emit(name)

    def setName(self, index, value):
        logger = logging.getLogger(__name__)
        node = self.nodeFromIndex(index)
        var = node.content
        try:
            strvalue = str(value if api2 else str(value.toString())).strip()
            if isIdentifier(strvalue):
                listind = self.variables.keyindex(var.name)
                self.variables.updateKey(listind, strvalue)
                return True
            else:
                logger.warning("'{0}' is not a valid identifier".format(strvalue))
                return False
        except Exception:
            logger.exception("No match for {0}".format(str(value.toString())))
            return False

    def setValue(self, index, value):
        node = self.nodeFromIndex(index)
        var = node.content
        name = var.name
        old = self.variables.map[name]
        if not old.isIdenticalTo(value):
            self.variables.map[name] = value

    def getVariables(self):
        return self.variables.map
 
    def getVariableValue(self, name):
        return self.variables.map[name]
    
    def addVariable(self, name, categories):
        if name=="":
            name = 'NewGlobalVariable'
        if name not in self.variables.map and isIdentifier(name):
            self.variables.map[name] = magnitude.mg(0, '')
            self.variables.map.valueChanged(name).connect(partial(self.onValueChanged, name))
            var = self.variables.varFromName(name)
            var.categories = categories
            node = self.addNode(var)
#            var.node = node #store pointer to tree node in global variable itself
        return len(self.variables) - 1

    def removeNode(self, node):
        var = node.content
        super(GlobalVariablesModel, self).removeNode(node)
        self.variables.map.pop(var.name)
        return var.name
        
    def dropVariableByName(self, name):
        if name in self.variables.map:
            var = self.variables.varFromName(name)
            node = self.nodeFromContent(var)
            return self.removeNode(node)

    def dropVariableByIndex(self, row):
        if 0 <= row < len(self.variables):
            var = self.variables[row]
            node = self.nodeFromContent(var)
            return self.removeNode(node)

    def update(self, updlist):
        for destination, name, value in updlist:
            value = MagnitudeUtilit.mg(value)
            if destination=='Global' and name in self.variables.map:
                old = self.variables.map[name]
                if value.dimension() != old.dimension() or value != old:
                    self.variables.map[name] = value
                    var = self.variables.varFromName(name)
                    node = self.nodeFromContent(var)
                    ind = self.indexFromNode(node, col=self.column.value)
                    self.dataChanged.emit(ind, ind)
    #
    # def nodeFromContent(self, content):
    #     return content.node