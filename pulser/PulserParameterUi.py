# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 23:45:54 2013

@author: pmaunz
"""

from PyQt4 import QtCore, QtGui
import PyQt4.uic

from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from modules.firstNotNone import firstNotNone
from modules.Expression import Expression
from modules.GuiAppearance import restoreGuiState, saveGuiState
from gui.ExpressionValue import ExpressionValue
from _functools import partial
from _collections import defaultdict
from pulseProgram import PulseProgram

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


class PulserParameterTreeNode:
    def __init__(self, type, content, parent, row):
        self.type = type
        self.content = content
        self.parent = parent
        self.row = row
        self.children = []
        self.childNames = []

    def childCount(self):
        return len(self.children)

    def child(self, row):
        if 0 <= row < self.childCount():
            return self.children[row]


class PulserParameterTreeModel( QtCore.QAbstractItemModel ):
    expression = Expression()
    backgroundLookup = {True:QtGui.QColor(QtCore.Qt.green).lighter(175), False:QtGui.QColor(QtCore.Qt.white)}
    def __init__(self, parameterList, parent=None):
        super(PulserParameterTreeModel, self).__init__(parent)
        self.parameterList = parameterList
        self.headerLookup = ['Name', 'Value']
        self.setDataLookup = {
                             (QtCore.Qt.EditRole,1): lambda index, value: self.setValue( index, value ),
                             (QtCore.Qt.UserRole,1): lambda index, value: self.setStrValue( index, value ),
                              }
        self.dataLookup = {
                           ('parameter', QtCore.Qt.DisplayRole, 0): lambda node: node.content.name,
                           ('parameter', QtCore.Qt.DisplayRole, 1): lambda node: node.content.value,
                           ('parameter', QtCore.Qt.EditRole,1): lambda node: node.content.string,
                           ('parameter', QtCore.Qt.BackgroundRole,1): lambda node: self.backgroundLookup[node.content.hasDependency],
                           ('category', QtCore.Qt.DisplayRole, 0): lambda node: node.content

                            }
        self.flagsLookup = {
                            ('parameter', 0): QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable,
                            ('parameter', 1): QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable,
                            ('category', 0): QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
                            }

        self.root = PulserParameterTreeNode('root', None, None, 0)
        self.nodes = {'root': self.root}
        for parameter in parameterList: #make the tree
            if parameter.categories:
                for ind, category in enumerate(parameter.categories):
                    parent = self.nodes[parameter.categories[ind-1]] if ind!=0 else self.root
                    if category not in parent.childNames:
                        row = parent.childCount()
                        node = PulserParameterTreeNode('category', category, parent, row)
                        parent.children.append(node)
                        parent.childNames.append(category)
                        self.nodes[category] = node
                parent = self.nodes[parameter.categories[-1]]
            else:
                parent = self.root
            row = parent.childCount()
            node = PulserParameterTreeNode('parameter', parameter, parent, row)
            parent.children.append(node)
            parent.childNames.append(parameter.name)
            self.nodes[parameter.name] = node

    def rowCount(self, index):
        node = self.nodeFromIndex(index)
        return node.childCount()

    def columnCount(self, index):
        return 2

    def data(self, index, role):
        node = self.nodeFromIndex(index)
        col = index.column()
        return self.dataLookup.get((node.type, role, col), lambda node: None)(node)

    def setData(self, index, value, role):
        node = self.nodeFromIndex(index)
        col = index.column()
        if node.type == 'parameter':
            return self.setDataLookup.get( (role,col), lambda index, value: False)(index, value)

    def nodeFromIndex(self, index):
        return index.internalPointer() if index.isValid() else self.root

    def index(self, row, column, parentIndex):
        if not self.hasIndex(row, column, parentIndex):
            ind = QtCore.QModelIndex()
        else:
            parentNode = self.nodeFromIndex(parentIndex)
            node = parentNode.child(row)
            if node == None:
                ind = QtCore.QModelIndex()
            else:
                ind = self.createIndex(row, column, node)
        return ind

    def parent(self, index):
        node = self.nodeFromIndex(index)
        if node == self.root:
            ind = QtCore.QModelIndex()
        else:
            parentNode = node.parent
            ind = QtCore.QModelIndex() if parentNode == self.root else self.createIndex(parentNode.row, 0, parentNode)
        return ind

    def flags(self, index ):
        node = self.nodeFromIndex(index)
        col = index.column()
        return self.flagsLookup.get((node.type, col), QtCore.Qt.NoItemFlags)

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole) and (orientation == QtCore.Qt.Horizontal):
            return self.headerLookup[section]

    def setValue(self, index, value):
        node = self.nodeFromIndex(index)
        result = False
        if node.type == 'parameter':
            node.content.value = value
            result = True
        return result
         
    def setStrValue(self, index, strValue):
        node = self.nodeFromIndex(index)
        result = False
        if node.type == 'parameter':
            node.content.string = strValue
            result = True
        return result
        

class PulserParameterUi(UiForm,UiBase):
    def __init__(self, pulser, config, globalDict=None, parent=None):
        UiBase.__init__(self,parent)
        UiForm.__init__(self)
        self.isSetup = False
        self.globalDict = firstNotNone( globalDict, dict() )
        self.config = config
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
        self.treeView.setModel( self.model )
        self.delegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.treeView.setItemDelegateForColumn(1,self.delegate)
        restoreGuiState( self, self.config.get('PulserParameterUi.guiState'))
        self.isSetup = True
        
    def saveConfig(self):
        self.config['PulserParameterValues'] = dict( (p.name,(p.value,p.string if p.hasDependency else None)) for p in self.parameterList )
        self.config['PulserParameterUi.guiState'] = saveGuiState(self)
    
    def onChange(self, index, event ):
        parameter = self.parameterList[index]
        self.currentWireValues[parameter.address] = parameter.setBits(self.currentWireValues[parameter.address])
        self.pulser.setExtendedWireIn( parameter.address, self.currentWireValues[parameter.address] )
        if self.isSetup and event.origin!='value':
            node = self.nodes[parameter.name]
            ind = self.model.createIndex(node.row, 1, node)
            self.model.dataChanged.emit(ind, ind)
