from functools import partial

from PyQt4 import QtGui, QtCore


class ComboBoxDelegate(QtGui.QStyledItemDelegate):
    """Class for combo box editors in models"""
    def __init__(self):
        QtGui.QStyledItemDelegate.__init__(self)
        
    def createEditor(self, parent, option, index ):
        """Create the combo box editor"""
        editor = QtGui.QComboBox(parent)
        if hasattr(index.model(),'comboBoxEditable'):
            editor.setEditable(index.model().comboBoxEditable(index))
        choice = index.model().choice(index) if hasattr(index.model(),'choice') else None
        if choice:
            editor.addItems( choice )
        editor.currentIndexChanged['QString'].connect( partial( index.model().setValue, index ))
        return editor
        
    def setEditorData(self, editor, index):
        """Set the data in the editor based on the model"""
        value = index.model().data(index, QtCore.Qt.EditRole)
        if value:
            editor.setCurrentIndex( editor.findText(value) )
         
    def setModelData(self, editor, model, index):
        """Set the data in the model based on the editor"""
        value = editor.currentText()
        model.setData(index, value, QtCore.Qt.EditRole)
         
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


