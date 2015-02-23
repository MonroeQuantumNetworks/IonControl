'''
Created on Feb 20, 2015

@author: pmaunz
'''

from PyQt4.Qsci import QsciScintilla, QsciLexerPython
from PyQt4.QtGui import QFont, QFontMetrics, QColor


class MyPythonLexer(QsciLexerPython):
    def keywords(self, keyset):
        if keyset == 1:
            return 'counter var shutter parameter masked_shutter exitcode const ' + QsciLexerPython.keywords(self, keyset)
        return QsciLexerPython.keywords(self, keyset)


class QPPPEditor(QsciScintilla):
    ARROW_MARKER_NUM = 8

    def __init__(self, parent=None):
        super(QPPPEditor, self).__init__(parent)

        # Set the default font
        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(10)
        self.setFont(font)
        self.setMarginsFont(font)
        
        boldfont = QFont(font)
        boldfont.setBold(True)

        # Margin 0 is used for line numbers
        fontmetrics = QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.width("00000") + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#cccccc"))

        # Clickable margin 1 for showing markers
        self.setMarginSensitivity(1, True)
        self.marginClicked.connect(self.on_margin_clicked)
        self.markerDefine(QsciScintilla.RightArrow,self.ARROW_MARKER_NUM)
        self.setMarkerBackgroundColor(QColor("#ee1111"),self.ARROW_MARKER_NUM)

        # Brace matching: enable for a brace immediately before or after
        # the current position
        #
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # Current line visible with special background color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#ffe4e4"))

        # Set Python lexer
        # Set style for Python comments (style number 1) to a fixed-width
        # courier.
        #
        lexer = MyPythonLexer()
        lexer.setDefaultFont(font)
        lexer.setColor( QColor('red'), 4 )
        lexer.setFont( boldfont, 5)
        self.setLexer(lexer)
        self.SendScintilla(QsciScintilla.SCI_STYLESETFONT, 1, 'Courier')

        # Don't want to see the horizontal scrollbar at all
        # Use raw message to Scintilla here (all messages are documented
        # here: http://www.scintilla.org/ScintillaDoc.html)
        self.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 0)
        
        self.SendScintilla(QsciScintilla.SCI_SETINDENT, 4)
        self.SendScintilla(QsciScintilla.SCI_SETTABINDENTS, True)
        self.SendScintilla(QsciScintilla.SCI_SETINDENTATIONGUIDES, QsciScintilla.SC_IV_LOOKFORWARD )
         

        # not too small
        self.setMinimumSize(200, 100)
        self.errorIndicators = list()

    def on_margin_clicked(self, nmargin, nline, modifiers):
        # Toggle marker for the line the margin was clicked on
        if self.markersAtLine(nline) != 0:
            self.markerDelete(nline, self.ARROW_MARKER_NUM)
        else:
            self.markerAdd(nline, self.ARROW_MARKER_NUM)

    def setPlainText(self, text ):
        self.setText(text)
        
    def toPlainText(self):
        return self.text()
    
    def cursorPosition(self):
        return self.getCursorPosition()
    
    def scrollPosition(self):
        return self.firstVisibleLine()
    
    def setScrollPosition(self, line):
        self.setFirstVisibleLine(line)
    
    def highlightError(self, line, col, toline, tocol):
        tocolumn = self.lineLength(toline-1) if tocol<0 else tocol
        self.fillIndicatorRange(line-1, col-1, toline-1, tocolumn, 2)
        self.errorIndicators.append( (line-1,col-1,toline-1,tocolumn) )
    
    def clearError(self):
        for line, col, toline, tocol in self.errorIndicators:
            self.clearIndicatorRange(line, col, toline, tocol, 2)
        self.errorIndicators = list()