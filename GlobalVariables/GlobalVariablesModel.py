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
from GlobalVariable import GlobalVariable

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
    globalRemoved = QtCore.pyqtSignal()
    expression = Expression.Expression()
    def __init__(self, config, _globalDict_, parent=None):
        super(GlobalVariablesModel, self).__init__(_globalDict_.values(), parent)
        self.config = config
        self._globalDict_ = _globalDict_
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
        for item in self._globalDict_.values():
            try:
                item.valueChanged.connect(self.onValueChanged, QtCore.Qt.UniqueConnection)
            except:
                pass

    def endResetModel(self):
        super(GlobalVariablesModel, self).endResetModel()
        self.connectAllVariableSignals()

    def onValueChanged(self, name, value, origin):
        self.valueChanged.emit(name)

    def sort(self, column, order):
        if column==self.column.name:
            self.beginResetModel()
            self.sortChildren(self.root)
            self.endResetModel()

    def sortChildren(self, node):
        node.children.sort(key=self.nodeSortKey)
        for child in node.children:
            self.sortChildren(child)

    @staticmethod
    def nodeSortKey(node):
        nodeName = getattr(node.content, 'name', node.content)
        return nodeName if node.children==[] else '0_'+nodeName

    def setName(self, index, value):
        logger = logging.getLogger(__name__)
        node = self.nodeFromIndex(index)
        var = node.content
        newName = str(value if api2 else str(value.toString())).strip()
        if isIdentifier(newName):
            del self._globalDict_[var.name]
            var.name = newName
            self._globalDict_[newName] = var
            return True
        else:
            logger.warning("'{0}' is not a valid identifier".format(newName))
            return False

    def setValue(self, index, value):
        name = self.nodeFromIndex(index).content.name
        oldValue = self._globalDict_[name].value
        if not oldValue.isIdenticalTo(value):
            self._globalDict_[name].value = value

    def addVariable(self, name, categories=None):
        if name=="":
            name = 'NewGlobalVariable'
        if name not in self._globalDict_ and isIdentifier(name):
            newGlobal = GlobalVariable(name, magnitude.mg(0, ''))
            newGlobal.categories = categories
            newGlobal.valueChanged.connect( partial(self.onValueChanged, name) )
            node = self.addNode(newGlobal)
            self._globalDict_[name] = newGlobal
            return node

    def addNode(self, content, name=None):
        """make sure nodeID property of global variable is set whenever a node is added"""
        node = super(GlobalVariablesModel, self).addNode(content, name)
        node.content.nodeID = node.id #store ID to tree node in global variable itself for fast lookup
        return node

    def removeNode(self, node):
        if node.nodeType==nodeTypes.data:
            parent = node.parent
            var = node.content
            deletedID = super(GlobalVariablesModel, self).removeNode(node)
            del self._globalDict_[var.name]
            self.removeAllEmptyParents(parent)
            self.globalRemoved.emit()
        elif node.nodeType==nodeTypes.category and node.children==[]: #deleting whole categories of global variables with one keystroke is a bad idea
            deletedID = super(GlobalVariablesModel, self).removeNode(node)
        else:
            deletedID = None
        return deletedID

    def changeCategory(self, node, categories=None, deleteOldIfEmpty=True):
        node, oldDeleted, deletedCategoryNodeIDs = super(GlobalVariablesModel, self).changeCategory(node, categories, deleteOldIfEmpty)
        #update global variable to reflect category change
        var = node.content
        var.nodeID = node.id
        var.categories = categories
        return node, oldDeleted, deletedCategoryNodeIDs

    def update(self, updlist):
        for destination, name, value in updlist:
            value = MagnitudeUtilit.mg(value)
            if destination=='Global' and name in self._globalDict_:
                oldValue = self._globalDict_[name].value
                if value.dimension() != oldValue.dimension() or value != oldValue:
                    var = self._globalDict_[name]
                    var.value = value
                    node = self.nodeFromContent(var)
                    ind = self.indexFromNode(node, col=self.column.value)
                    self.dataChanged.emit(ind, ind)

    def nodeFromContent(self, content):
        return self.nodeDict[content.nodeID]