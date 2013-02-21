# -*- coding: utf-8 -*-
"""
Created on Sat Feb 09 17:28:11 2013

@author: pmaunz
"""

from PyQt4 import QtGui
import PyQt4.uic
from modules import Expression

debug = False

class MagnitudeSpinBox(QtGui.QAbstractSpinBox):
    def __init__(self,parent=0):
        super(MagnitudeSpinBox,self).__init__(parent)
        self.expression = Expression.Expression()
        
    def validate(self, inputstring, pos):
        #print "validate"
        try:
            self.expression.evaluate(str(inputstring))
            return (QtGui.QValidator.Acceptable,pos)
        except Exception as e:
            print e
            return (QtGui.QValidator.Intermediate,pos)
        
    def stepBy(self, steps ):
        print steps
        
    def interpretText(self):
        print "interpret text"
        
    def fixup(self,inputstring):
        print inputstring
        
    def stepEnabled(self):
        #print "stepEnabled"
        return QtGui.QAbstractSpinBox.StepUpEnabled | QtGui.QAbstractSpinBox.StepDownEnabled
        
    def value(self):
        value = self.expression.evaluate( str( self.lineEdit().text() ))
        print value
        return value
        
    def setText(self,string):
        self.lineEdit().setText( string )
        
    def setValue(self,value):
        self.lineEdit().setText( str(value) )
        
if __name__ == "__main__":
    debug = True
    TestWidget, TestBase = PyQt4.uic.loadUiType('MagnitudeSpinBoxTest.ui')

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
