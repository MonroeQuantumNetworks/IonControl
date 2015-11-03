from functools import partial
import re

from PyQt4 import QtGui, QtCore

from MagnitudeSpinBox import MagnitudeSpinBox
from modules.MagnitudeParser import isValueExpression

class MagnitudeSpinBoxDelegateMixin(object):
    def createEditor(self, parent, option, index ):
        if hasattr( index.model(), 'localReplacementDict' ):
            localDict = dict( self.globalDict )
            localDict.update( index.model().localReplacementDict() )
        else:
            localDict = self.globalDict
        editor = MagnitudeSpinBox(parent, globalDict = localDict, valueChangedOnEditingFinished=False, emptyStringValue=self.emptyStringValue)
        editor.dimension = index.model().data(index,QtCore.Qt.UserRole)
        editor.valueChanged.connect( partial( index.model().setValue, index ))
        completer = QtGui.QCompleter( localDict.keys(), self )
        completer.setCaseSensitivity(QtCore.Qt.CaseSensitive)
        completer.setCompletionMode(QtGui.QCompleter.InlineCompletion)
        editor.lineEdit().setCompleter( completer )
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, QtCore.Qt.EditRole)
        editor.setValue(value)
        editor.lineEdit().setCursorPosition(0)
        try:
            numberlen = len(re.split("([+-]?[0-9\.]+(?:[eE][0-9]+)?)(.*)",str(value))[1])
            editor.lineEdit().cursorForward(True,numberlen)
        except:
            editor.lineEdit().cursorWordForward(True)

    def setModelData(self, editor, model, index):
        value = editor.value()
        text = str(editor.text())
        model.setData(index, text if not isValueExpression(text) else None , QtCore.Qt.UserRole )  # is parsable thus must be a magnitude without math
        model.setData(index, value, QtCore.Qt.EditRole )    # DisplayRole would be better, for backwards compatibility we leave it at EditRole and distinguish there by type


class MagnitudeSpinBoxDelegate(QtGui.QStyledItemDelegate, MagnitudeSpinBoxDelegateMixin):

    def __init__(self, globalDict=None, emptyStringValue=0):
        QtGui.QStyledItemDelegate.__init__(self)
        self.globalDict = globalDict if globalDict is not None else dict()
        self.emptyStringValue = emptyStringValue

    createEditor = MagnitudeSpinBoxDelegateMixin.createEditor
    setEditorData = MagnitudeSpinBoxDelegateMixin.setEditorData
    setModelData = MagnitudeSpinBoxDelegateMixin.setModelData

    def updateEditorGeometry(self, editor, option, index ):
        editor.setGeometry(option.rect)
        
    def setGlobalVariables(self, variables):
        self.globalDict = variables
