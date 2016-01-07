"""
Created on 09 Dec 2015 at 8:38 PM

author: jmizrahi
"""
from PyQt4 import QtCore, QtGui

from modules.Expression import Expression
from modules.firstNotNone import firstNotNone
from modules.enum import enum
from modules.MagnitudeParser import isIdentifier
from uiModules.CategoryTree import CategoryTreeModel
import sip
api2 = sip.getapi("QVariant")==2

class AWGSegment(object):
    def __init__(self):
        self.enabled = True
        self.amplitude = 'V0'
        self.duration = 'T0'

class AWGSegmentModel(CategoryTreeModel):
    """Model for displaying AWG segments when the AWGUi is in segment mode"""
    segmentChanged = QtCore.pyqtSignal()
    def __init__(self, channel, settings, globalDict, parent=None):
        self.channel = channel
        self.settings = settings
        self.globalDict = globalDict
        CategoryTreeModel.__init__(self, [], parent)
        self.root.children = self.settings.channelSettingsList[self.channel]['segmentData']
        self.updateNodeDict()
        self.columnNames = ['enabled', 'amplitude', 'duration']
        self.numColumns = len(self.columnNames)
        self.column = enum(*self.columnNames)
        self.allowDeletion=True
        self.headerLookup = {
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.enabled): "",
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.amplitude): "Amplitude",
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.duration): "Duration"
            }
        self.dataLookup = {
            (QtCore.Qt.CheckStateRole,self.column.enabled): lambda node: QtCore.Qt.Checked if node.content.enabled else QtCore.Qt.Unchecked,
            (QtCore.Qt.DisplayRole, self.column.amplitude): lambda node: node.content.amplitude,
            (QtCore.Qt.DisplayRole, self.column.duration): lambda node: node.content.duration,
            (QtCore.Qt.EditRole, self.column.amplitude): lambda node: node.content.amplitude,
            (QtCore.Qt.EditRole, self.column.duration): lambda node: node.content.duration
            }
        self.setDataLookup = {
            (QtCore.Qt.CheckStateRole, self.column.enabled): lambda index, value: self.setEnabled(index, value),
            (QtCore.Qt.EditRole, self.column.amplitude): lambda index, value: self.setValue(index, value, 'amplitude'),
            (QtCore.Qt.EditRole, self.column.duration): lambda index, value: self.setValue(index, value, 'duration')
            }
        self.flagsLookup = {
            self.column.enabled: QtCore.Qt.ItemIsEnabled |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable,
            self.column.amplitude: QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable,
            self.column.duration: QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable
            }

    def updateNodeDict(self):
        self.nodeDict.clear()
        self.nodeDict[self.root.id] = self.root
        self.addToNodeDict(self.root.children)

    def addToNodeDict(self, nodeList):
        for node in nodeList:
            self.nodeDict[node.id] = node
            if node.children:
                self.updateNodeDict(node.children)

    def setEnabled(self, index, value):
        node = self.nodeFromIndex(index)
        node.content.enabled = value==QtCore.Qt.Checked
        self.dataChanged.emit(index, index)
        self.segmentChanged.emit()
        self.settings.saveIfNecessary()
        return True

    def setValue(self, index, value, key):
        node = self.nodeFromIndex(index)
        strvalue = str((value if api2 else value.toString()) if isinstance(value, QtCore.QVariant) else value)
        if strvalue in self.globalDict:
            logger.warning("'{0}' is already a global variable name".format(strvalue))
            return False
        elif not isIdentifier(strvalue):
            logger.warning("'{0}' is not a valid variable name".format(strvalue))
            return False
        else:
            setattr(node.content, key, strvalue)
            self.dataChanged.emit(index, index)
            self.segmentChanged.emit()
            self.settings.saveIfNecessary()
            return True

    def addSegment(self):
        newSegment = AWGSegment()
        self.addNode(newSegment)