# -*- coding: utf-8 -*-
"""
Created on Sat May 25 09:02:02 2013

@author: pmaunz
"""

import sys
from PyQt4.QtGui import QSyntaxHighlighter, QTextCharFormat, QBrush, QFont
from PyQt4.QtCore import Qt, QRegExp, QStringList
from PulseProgram import OPS

class PPHighlighter( QSyntaxHighlighter ):

    def __init__( self, parent, theme ):
      QSyntaxHighlighter.__init__( self, parent )
      self.parent = parent
      keyword = QTextCharFormat()
      comment = QTextCharFormat()
      define = QTextCharFormat()

      self.highlightingRules = []


      # FPGA commands
      brush = QBrush( Qt.darkBlue, Qt.SolidPattern )
      keyword.setForeground( brush )
      keyword.setFontWeight( QFont.Bold )
      keywords = QStringList( OPS.keys() )
      for word in keywords:
        pattern = QRegExp("\\b" + word + "\\b")
        rule = HighlightingRule( pattern, keyword )
        self.highlightingRules.append( rule )

      # define and include
      brush = QBrush( Qt.darkMagenta, Qt.SolidPattern )
      pattern = QRegExp( "#define [^\n]*" )
      define.setForeground( brush )
      rule = HighlightingRule( pattern, define )
      self.highlightingRules.append( rule )

      # comment
      brush = QBrush( Qt.darkGreen, Qt.SolidPattern )
      pattern = QRegExp( "#(?!(define)|(include))[^\n]*" )
      comment.setForeground( brush )
      rule = HighlightingRule( pattern, comment )
      self.highlightingRules.append( rule )

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
  def __init__( self, pattern, format ):
    self.pattern = pattern
    self.format = format
    


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
