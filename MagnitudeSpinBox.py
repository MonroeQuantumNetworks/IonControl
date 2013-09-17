# -*- coding: utf-8 -*-
"""
Created on Sat Feb 09 17:28:11 2013

A QSpinBox for Physical quantities. It accepts for example "10 MHz"
Features are: up-down arrows will increase/decrease the digit left to the cursor position


@author: pmaunz
"""

from PyQt4 import QtGui, QtCore
import PyQt4.uic
from modules import Expression
from modules import MagnitudeParser
import sip

debug = False
api2 = sip.getapi("QString")==2

class MagnitudeSpinBox(QtGui.QAbstractSpinBox):
    valueChanged = QtCore.pyqtSignal(object)
    
    def __init__(self,parent=None):
        super(MagnitudeSpinBox,self).__init__(parent)
        self.expression = Expression.Expression()
        self.setButtonSymbols( QtGui.QAbstractSpinBox.NoButtons )
        self.editingFinished.connect( self.onEditingFinished )
        self.lineEdit().setDragEnabled(True)
        self.lineEdit().setAcceptDrops(True)
        
    def validate(self, inputstring, pos):
        #print "validate"
        try:
            self.expression.evaluate(str(inputstring))
            if api2:
                return (QtGui.QValidator.Acceptable,inputstring,pos)
            else:
                return (QtGui.QValidator.Acceptable,pos)                
        except Exception as e:
            print e
            if api2:
                return (QtGui.QValidator.Intermediate,inputstring,pos)
            else:
                return (QtGui.QValidator.Intermediate,pos)
                
        
    def stepBy(self, steps ):
        try:
            lineEdit = self.lineEdit()
            #print steps, lineEdit.cursorPosition()
            value, delta, pos = MagnitudeParser.parseDelta( str(lineEdit.text()), lineEdit.cursorPosition())
            #print value, delta
            newvalue = value + (steps * delta)
            newvalue.ounit( value.out_unit )
            newvalue.output_prec( value.oprec )
            self.setValue( newvalue )
            lineEdit.setCursorPosition(pos)
            self.valueChanged.emit( newvalue )
        except Exception:
            pass
            #print e
            
        
    def interpretText(self):
        print "interpret text"
        
    def fixup(self,inputstring):
        print "fixup" , inputstring
        
    def stepEnabled(self):
        #print "stepEnabled"
        return QtGui.QAbstractSpinBox.StepUpEnabled | QtGui.QAbstractSpinBox.StepDownEnabled
        
    def value(self):
        value = self.expression.evaluate( str( self.lineEdit().text() ))
        #print value
        return value
        
    def setText(self,string):
        self.lineEdit().setText( string )
        
    def setValue(self,value):
        self.lineEdit().setText( str(value) )
        
    def onEditingFinished(self):
        self.valueChanged.emit( self.value() )
        
    def sizeHint(self):
        fontMetrics = QtGui.QFontMetrics( self.font() )
        size = fontMetrics.boundingRect(self.lineEdit().text()).size()
        size += QtCore.QSize( 8,0)
        return size
 
#    def makeDrag(self):
#        print "makeDrag"
#        dr = QtGui.QDrag(self)
#        # The data to be transferred by the drag and drop operation is contained in a QMimeData object
#        data = QtCore.QMimeData()
#        data.setText("This is a test")
#        # Assign ownership of the QMimeData object to the QDrag object.
#        dr.setMimeData(data)
#        # Start the drag and drop operation
#        dr.start()
# 
#    def dragMoveEvent(self, de):
#        print "dragMove"
#        # The event needs to be accepted here
#        de.accept()
#
#    def dragEnterEvent(self, event):
#        print "dragEnterEvent"
#        # Set the drop action to be the proposed action.
#        event.acceptProposedAction()
#
#    def dropEvent(de):
#        # Unpack dropped data and handle it the way you want
#        print "Contents: {0}".format(de.mimeData().text().toLatin1().data())
       
        
if __name__ == "__main__":
    debug = True
    TestWidget, TestBase = PyQt4.uic.loadUiType(r'ui\MagnitudeSpinBoxTest.ui')

    class TestUi(TestWidget,TestBase):
        def __init__(self):
            TestWidget.__init__(self)
            TestBase.__init__(self)
        
        def setupUi(self,parent):
            super(TestUi,self).setupUi(parent)
            self.updateButton.clicked.connect(self.onUpdate)
            
        def onUpdate(self):
            self.lineEdit.setText( str(self.magnitudeSpinBox.value()) )

    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = TestUi()
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
