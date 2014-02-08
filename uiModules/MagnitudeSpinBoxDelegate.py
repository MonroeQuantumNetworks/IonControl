from functools import partial
import re

from PyQt4 import QtGui, QtCore

from MagnitudeSpinBox import MagnitudeSpinBox


class MagnitudeSpinBoxDelegate(QtGui.QItemDelegate):
  
    """
    This class is responsible for the combo box editor in the trace table,
    which is used to select which pen to use in drawing the trace on the plot.
    The pen icons are in the array penicons, which is determined when the delegate
    is constructed.
    """    
    
    def __init__(self):
        """Construct the TraceComboDelegate object, and set the penicons array."""
        QtGui.QItemDelegate.__init__(self)
        
    def createEditor(self, parent, option, index ):
        """Create the combo box editor used to select which pen icon to use.
           The for loop adds each pen icon into the combo box."""
        editor = MagnitudeSpinBox(parent)
        editor.dimension = index.model().data(index,QtCore.Qt.UserRole)
        editor.valueChanged.connect( partial( index.model().setValue, index.row() ))
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
        model.setData(index, value, QtCore.Qt.EditRole)
         
    def updateEditorGeometry(self, editor, option, index ):
        editor.setGeometry(option.rect)