from functools import partial
import re

from PyQt4 import QtGui, QtCore

from MagnitudeSpinBox import MagnitudeSpinBox
from modules.MagnitudeParser import isValueExpression


class MagnitudeSpinBoxDelegate(QtGui.QItemDelegate):
  
    """
    This class is responsible for the combo box editor in the trace table,
    which is used to select which pen to use in drawing the trace on the plot.
    The pen icons are in the array penicons, which is determined when the delegate
    is constructed.
    """    
    
    def __init__(self, globalDict=None):
        """Construct the TraceComboDelegate object, and set the penicons array."""
        QtGui.QItemDelegate.__init__(self)
        self.globalDict = globalDict if globalDict is not None else dict()
        
    def createEditor(self, parent, option, index ):
        """Create the combo box editor used to select which pen icon to use.
           The for loop adds each pen icon into the combo box."""
        editor = MagnitudeSpinBox(parent, globalDict = self.globalDict, valueChangedOnEditingFinished=False)
        editor.dimension = index.model().data(index,QtCore.Qt.UserRole)
        editor.valueChanged.connect( partial( index.model().setValue, index ))
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
         
    def updateEditorGeometry(self, editor, option, index ):
        editor.setGeometry(option.rect)
        
    def setGlobalVariables(self, variables):
        self.globalDict = variables
