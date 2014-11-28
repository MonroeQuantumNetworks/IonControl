'''
Created on Nov 23, 2014

@author: pmaunz
'''


from PyQt4 import QtGui, QtCore


class PlainTextEdit( QtGui.QPlainTextEdit ):
    editingFinished = QtCore.pyqtSignal(object)
    def __init__(self, *args, **kwargs):
        super( PlainTextEdit, self).__init__(*args, **kwargs)
        
    def focusOutEvent(self, focusEvent):
        if self.document().isModified():
            self.editingFinished.emit(self.document())
        return QtGui.QPlainTextEdit.focusOutEvent(self, focusEvent)
    
    def setModified(self, modified):
        self.document().setModified( modified )