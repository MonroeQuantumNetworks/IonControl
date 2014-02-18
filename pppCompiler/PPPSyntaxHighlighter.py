# -*- coding: utf-8 -*-
"""
Created on Sat May 25 09:02:02 2013

@author: pmaunz
"""

import sys

from PyQt4.QtCore import Qt, QRegExp
from PyQt4.QtGui import QSyntaxHighlighter, QTextCharFormat, QBrush, QFont

class PPPHighlighter( QSyntaxHighlighter ):

    def __init__( self, parent, theme ):
        QSyntaxHighlighter.__init__(self, parent)
        self.parent = parent
        keyword = QTextCharFormat()
        comment = QTextCharFormat()
        types = QTextCharFormat()        
        self.highlightingRules = []
        
        # keywords
        brush = QBrush(Qt.darkBlue, Qt.SolidPattern)
        keyword.setForeground(brush)
        keyword.setFontWeight(QFont.Bold)
        keywords = ['not','if','else','while','def']
        for word in keywords:
            pattern = QRegExp("\\b" + word + "\\b")
            rule = HighlightingRule(pattern, keyword)
            self.highlightingRules.append(rule)
        
        # variable types
        brush = QBrush(Qt.darkMagenta, Qt.SolidPattern)
        types.setForeground(brush)
        types.setFontWeight(QFont.Bold)
        typekeywords = ['var','const','parameter','shutter','masked_shutter','trigger','counter','exitcode']
        for word in typekeywords:
            pattern = QRegExp("\\b" + word + "\\b")
            rule = HighlightingRule(pattern, types)
            self.highlightingRules.append(rule)
        
        # comment
        brush = QBrush(Qt.darkGreen, Qt.SolidPattern)
        pattern = QRegExp("#[^\n]*")
        comment.setForeground(brush)
        rule = HighlightingRule(pattern, comment)
        self.highlightingRules.append(rule)

    def highlightBlock( self, text ):
        for rule in self.highlightingRules:
            expression = QRegExp( rule.pattern )
            index = expression.indexIn( text )
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat( index, length, rule.format )
                index = text.indexOf( expression, index + length )
        self.setCurrentBlockState( 0 )

class HighlightingRule():
    def __init__( self, pattern, myformat ):
        self.pattern = pattern
        self.format = myformat
    


if __name__ == "__main__":
    from PyQt4.QtGui import QMainWindow, QTextEdit, QApplication
    class TestApp( QMainWindow ):
        def __init__(self):
            QMainWindow.__init__(self)
            font = QFont()
            font.setFamily( "Courier" )
            font.setFixedPitch( True )
            font.setPointSize( 12 )
            editor = QTextEdit()
            editor.setFont( font )
            self.highlighter = PPHighlighter( editor, "Classic" )
            self.setCentralWidget( editor )
            self.setWindowTitle( "Syntax Highlighter" )
            with open("prog\Ions-samples\DriveD5half.pp","r") as f:
                data = f.readlines()
                data = "".join(data)
                editor.setPlainText(data)
            
        
    app = QApplication( sys.argv )
    window = TestApp()
    window.show()
    sys.exit( app.exec_() )
