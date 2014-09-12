from functools import partial

from PyQt4 import QtGui, QtCore


class ComboBoxDelegate(QtGui.QItemDelegate):
  
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
        editor = QtGui.QComboBox(parent)
        choice = index.model().choice(index) if hasattr(index.model(),'choice') else None
        if choice:
            editor.addItems( choice )
        editor.currentIndexChanged['QString'].connect( partial( index.model().setValue, index ))
        return editor
        
    def setEditorData(self, editor, index):
        value = index.model().data(index, QtCore.Qt.EditRole)
        if value:
            editor.setCurrentIndex( editor.findText(value) )
         
    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, QtCore.Qt.EditRole)
         
    def updateEditorGeometry(self, editor, option, index ):
        editor.setGeometry(option.rect)


