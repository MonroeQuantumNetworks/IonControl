# -*- coding: utf-8 -*-
"""
Created on Fri May 24 17:32:35 2013

@author: pmaunz
"""

from PyQt4 import uic, QtCore, QtGui
import functools

Form, Base = uic.loadUiType(r'ui\PulseProgramEdit.ui')

class PulseProgramSourceEdit(Form, Base):
    def __init__(self,parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        self.highlighted = QtGui.QTextCharFormat()
        self.highlighted.setBackground( QtGui.QBrush(QtCore.Qt.cyan))
        self.selections = list()
        self.findFlags = QtGui.QTextDocument.FindFlag()
        self.findText = None
        
    def setupUi(self,parent):
        Form.setupUi(self,parent)
        self.findLineEdit.textChanged.connect( self.onFindTextChanged )
        self.findCloseButton.clicked.connect( self.onFindClose )
        self.findMatchCaseCheckBox.stateChanged.connect( self.onFindFlagsChanged )
        self.findNextButton.clicked.connect( self.onFind )
        self.findPreviousButton.clicked.connect( functools.partial(self.onFind , True))

    def onFindFlagsChanged(self):
        self.findFlags = QtGui.QTextDocument.FindCaseSensitively if self.findMatchCaseCheckBox.isChecked() else QtGui.QTextDocument.FindFlag()
        self.findFlags |= QtGui.QTextDocument.FindWholeWords if self.findWholeWordsCheckBox.isChecked() else QtGui.QTextDocument.FindFlag()
        
    def onFindClose(self):
        self.findWidgetFrame.hide()
        self.textEdit.setExtraSelections([])

    def setPlainText(self, text):
        self.textEdit.setPlainText(text)

    def toPlainText(self):
        return self.textEdit.toPlainText()
        
    def onFind(self,backward=False):
        if self.textEdit.find(self.findText,(self.findFlags | QtGui.QTextDocument.FindBackward) if backward else self.findFlags):
            cursor = self.textEdit.textCursor()
            selection = QtGui.QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = self.highlighted
            self.textEdit.setExtraSelections( [selection] )
            self.findLineEdit.setStyleSheet('')
            if backward:
                cursor.setPosition( cursor.anchor() )
            else:
                cursor.clearSelection()
            self.textEdit.setTextCursor( cursor )
        
    def onFindTextChanged(self, text):
        self.findText = str(text)
        if self.textEdit.find(text,self.findFlags) or self.textEdit.find(text, self.findFlags | QtGui.QTextDocument.FindBackward):
            cursor = self.textEdit.textCursor()
            selection = QtGui.QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = self.highlighted
            self.textEdit.setExtraSelections( [selection] )
            cursor.setPosition( cursor.anchor() )
            self.textEdit.setTextCursor( cursor )
            self.findLineEdit.setStyleSheet('')
        else:
            if len(self.findText)>0:
                self.findLineEdit.setStyleSheet('QLineEdit{background: orange;}')
            else:
                self.findLineEdit.setStyleSheet('')
        
    def keyReleaseEvent(self, event):
        if event.matches(QtGui.QKeySequence.Find):
            self.findWidgetFrame.show()
            self.findLineEdit.setFocus(QtCore.Qt.ShortcutFocusReason)
            print "Find"
        elif event.matches(QtGui.QKeySequence.FindNext):
            self.findWidgetFrame.show()
            print "FindNext"
        elif event.matches(QtGui.QKeySequence.FindPrevious):
            self.findWidgetFrame.show()
            print "FindPrevious"
        else:
            Base.keyReleaseEvent(self,event)
            
    
            
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = PulseProgramSourceEdit()
    ui.setupUi(ui)
    ui.show()
    sys.exit(app.exec_())
