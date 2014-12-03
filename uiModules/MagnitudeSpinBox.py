# -*- coding: utf-8 -*-
"""
Created on Sat Feb 09 17:28:11 2013

A QSpinBox for Physical quantities. It accepts for example "10 MHz"
Features are: up-down arrows will increase/decrease the digit left to the cursor position


@author: pmaunz
"""

import logging

from PyQt4 import QtGui, QtCore
import PyQt4.uic
import sip

from modules import Expression
from modules import MagnitudeParser
from modules import magnitude


debug = False
api2 = sip.getapi("QString")==2

class DimensionMismatch(Exception):
    pass

class MagnitudeSpinBox(QtGui.QAbstractSpinBox):
    valueChanged = QtCore.pyqtSignal(object)
    expression = Expression.Expression()
    
    def __init__(self, parent=None, globalDict=None, valueChangedOnEditingFinished=True):
        super(MagnitudeSpinBox,self).__init__(parent)
        self.setButtonSymbols( QtGui.QAbstractSpinBox.NoButtons )
        if valueChangedOnEditingFinished:
            self.editingFinished.connect( self.onEditingFinished )
        self.redTextPalette = QtGui.QPalette()
        self.redTextPalette.setColor( QtGui.QPalette.Text, QtCore.Qt.red )
        self.orangeTextPalette = QtGui.QPalette()
        self.orangeTextPalette.setColor( QtGui.QPalette.Text, QtGui.QColor(0x7d,0x05,0x52) )
        self.blackTextPalette = QtGui.QPalette()
        self.blackTextPalette.setColor( QtGui.QPalette.Text, QtCore.Qt.black )
        self._dimension = None   # if not None enforces the dimension
        self.globalDict = globalDict if globalDict is not None else dict()

    @property
    def dimension(self):
        return self._dimension
    
    @dimension.setter
    def dimension(self, dim):
        if isinstance(dim, magnitude.Magnitude) or dim is None:
            self._dimension = dim
        else:
            self._dimension = magnitude.Magnitude(1)
            self._dimension = self._dimension.sunit2mag(dim)
        
    def validate(self, inputstring, pos):
        try:
            value = self.expression.evaluateAsMagnitude(str(inputstring), self.globalDict)
            if api2:
                if self._dimension is not None and value.unit != self._dimension.unit:
                    self.lineEdit().setPalette( self.orangeTextPalette )
                    return (QtGui.QValidator.Intermediate,inputstring,pos)
                else: 
                    self.lineEdit().setPalette( self.blackTextPalette )
                    return (QtGui.QValidator.Acceptable,inputstring,pos)
            else:
                if self._dimension is not None and value.unit != self._dimension.unit:
                    self.lineEdit().setPalette( self.orangeTextPalette )
                    return (QtGui.QValidator.Intermediate,pos)
                else: 
                    self.lineEdit().setPalette( self.blackTextPalette )
                    return (QtGui.QValidator.Acceptable,pos)                
        except Exception:
            self.lineEdit().setPalette( self.redTextPalette )
            if api2:
                return (QtGui.QValidator.Intermediate,inputstring,pos)
            else:
                return (QtGui.QValidator.Intermediate,pos)
                
        
    def stepBy(self, steps ):
        try:
            lineEdit = self.lineEdit()
            value, delta, pos, decimalpos = MagnitudeParser.parseDelta( str(lineEdit.text()), lineEdit.cursorPosition())
            newvalue = value + (steps * delta)
            newvalue.copy_format( value )
            #self.setValue( newvalue )
            self.lineEdit().setText( newvalue.toString( newvalue.Format.precision ) )
            value, delta, _, newdecimalpos = MagnitudeParser.parseDelta( str(lineEdit.text()), lineEdit.cursorPosition())
            lineEdit.setCursorPosition( pos + newdecimalpos - decimalpos )
            self.valueChanged.emit( newvalue )
        except Exception:
            pass # logging.getLogger(__name__).exception(e)
            
        
    def interpretText(self):
        logging.getLogger(__name__).debug("interpret text")
        
    def fixup(self,inputstring):
        logging.getLogger(__name__).debug("fixup '{0}'".format(inputstring))
        
    def stepEnabled(self):
        return QtGui.QAbstractSpinBox.StepUpEnabled | QtGui.QAbstractSpinBox.StepDownEnabled
        
    def value(self):
        try:
            text = str( self.lineEdit().text() )
            if len(text)>0:
                value = self.expression.evaluateAsMagnitude(text, self.globalDict )
                if self._dimension is not None and value.unit != self._dimension.unit:
                    raise DimensionMismatch("Got unit {0} expected {1}".format(value.unit,self._dimension.unit))
            else:
                value = 0
        except Exception as e:
            self.lineEdit().setPalette( self.redTextPalette )
            logging.getLogger(__name__).exception("value")
            raise e
        self.lineEdit().setPalette( self.blackTextPalette )
        return value
        
    def text(self):
        return str(self.lineEdit().text())
        
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
#        # The event needs to be accepted here
#        de.accept()
#
#    def dragEnterEvent(self, event):
#        # Set the drop action to be the proposed action.
#        event.acceptProposedAction()
#
#    def dropEvent(de):
#        # Unpack dropped data and handle it the way you want
       
        
if __name__ == "__main__":
    debug = True
    TestWidget, TestBase = PyQt4.uic.loadUiType(r'..\ui\MagnitudeSpinBoxTest.ui')

    class TestUi(TestWidget,TestBase):
        def __init__(self):
            TestWidget.__init__(self)
            TestBase.__init__(self)
        
        def setupUi(self,parent):
            super(TestUi,self).setupUi(parent)
            self.updateButton.clicked.connect(self.onUpdate)
            self.magnitudeSpinBox.dimension = "MHz"
            
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
