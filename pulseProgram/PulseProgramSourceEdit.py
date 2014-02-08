# -*- coding: utf-8 -*-
"""
Created on Fri May 24 17:32:35 2013

@author: pmaunz
"""

import functools

from PyQt4 import uic, QtCore, QtGui

from pulseProgram.PPSyntaxHighlighter import PPHighlighter


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
        self.errorFormat = QtGui.QTextCharFormat()
        self.errorFormat.setBackground(QtCore.Qt.red)
        self.defaultFormat = QtGui.QTextCharFormat()
        self.defaultFormat.setBackground(QtCore.Qt.white)
        self.errorCursor = None
        self.cursorStack = list()
        
    def setupUi(self,parent):
        Form.setupUi(self,parent)
        self.findLineEdit.textChanged.connect( self.onFindTextChanged )
        self.findCloseButton.clicked.connect( self.onFindClose )
        self.findMatchCaseCheckBox.stateChanged.connect( self.onFindFlagsChanged )
        self.findNextButton.clicked.connect( self.onFind )
        self.findPreviousButton.clicked.connect( functools.partial(self.onFind , True))
        self.highlighter = PPHighlighter( self.textEdit, "Classic" )
        self.errorDisplay.hide()
        self.closeErrorButton.clicked.connect( self.clearHighlightError )
        
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
        elif event.matches(QtGui.QKeySequence.FindNext):
            self.findWidgetFrame.show()
        elif event.matches(QtGui.QKeySequence.FindPrevious):
            self.findWidgetFrame.show()
        else:
            Base.keyReleaseEvent(self,event)
            
    def highlightError(self, message, line, text):
        self.errorLabel.setText( message )
        self.errorDisplay.show()
        self.errorCursor = self.textEdit.textCursor()
        self.errorCursor.setPosition(0)
        if line>0:
            self.errorCursor.movePosition( QtGui.QTextCursor.NextBlock,  QtGui.QTextCursor.MoveAnchor, line-1 )
        self.errorCursor.movePosition( QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.KeepAnchor );
        line = str(self.errorCursor.selectedText())
        errorcol = line.find(text)
        if errorcol>=0:
            self.errorCursor.movePosition( QtGui.QTextCursor.StartOfBlock, QtGui.QTextCursor.MoveAnchor)
            self.errorCursor.movePosition( QtGui.QTextCursor.Right, QtGui.QTextCursor.MoveAnchor, errorcol)
            self.errorCursor.movePosition( QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, len(text))
        self.errorCursor.setCharFormat( self.errorFormat );
        self.textEdit.setTextCursor( self.errorCursor )
        temp = self.textEdit.textCursor()
        temp.clearSelection()
        self.textEdit.setTextCursor( temp )
        
    def clearHighlightError(self):
        self.errorDisplay.hide()
        if self.errorCursor:
            self.errorCursor.setCharFormat( self.defaultFormat )
                    
            
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = PulseProgramSourceEdit()
    ui.setupUi(ui)
    ui.show()
    sys.exit(app.exec_())
