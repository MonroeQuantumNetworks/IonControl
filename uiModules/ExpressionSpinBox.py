'''
Created on Apr 13, 2015

@author: pmaunz
'''
from modules.firstNotNone import firstNotNone
from uiModules.MagnitudeSpinBox import MagnitudeSpinBox
from PyQt4 import QtGui, QtCore


class ExpressionSpinBox(MagnitudeSpinBox):
    expressionChanged = QtCore.pyqtSignal(object)

    def __init__(self, parent=None, globalDict=None, valueChangedOnEditingFinished=True, emptyStringValue=0):
        super(ExpressionSpinBox,self).__init__(parent, globalDict, valueChangedOnEditingFinished, emptyStringValue)    
        self.expressionValue = None
        self.valueChanged.connect( self.onStepBy )
    
    def focusInEvent(self, event):
        super(ExpressionSpinBox, self).focusInEvent(event)
        if self.expressionValue:
            self.setValue( self.expressionValue.string )
            self.updateStyleSheet()

    def focusOutEvent(self, event):
        super(ExpressionSpinBox, self).focusOutEvent(event)
        if self.text() != self.expressionValue.string:
            cursorPosition = self.lineEdit().cursorPosition()
            self.expressionValue.string = self.text()
            self.expressionValue.value = super(ExpressionSpinBox, self).value()
            self.lineEdit().setCursorPosition(cursorPosition)
            self.expressionChanged.emit( self.expressionValue )
        if self.expressionValue:
            self.setValue( self.expressionValue.value )
            self.updateStyleSheet(False)

    def setExpression(self, expressionValue):
        if self.expressionValue:
            self.expressionValue.valueChanged.disconnect(self.dependentUpdate)
        self.expressionValue = expressionValue
        self.setValue(expressionValue.value)
        self.expressionValue.valueChanged.connect(self.dependentUpdate)
        self.updateStyleSheet()
        
    def updateStyleSheet(self, hasFocus=None):
        hasFocus = firstNotNone(hasFocus, self.hasFocus())
        self.setStyleSheet("ExpressionSpinBox { background-color: #bfffbf; }") if self.expressionValue.hasDependency and not hasFocus else self.setStyleSheet("")

    def onEditingFinished(self):
        # if self.hasFocus():
        #     cursorPosition = self.lineEdit().cursorPosition()
        #     self.expressionValue.string = self.text()
        #     self.expressionValue.value = super(ExpressionSpinBox, self).value()
        #     self.lineEdit().setCursorPosition(cursorPosition)
        #     self.expressionChanged.emit( self.expressionValue )
        self.updateStyleSheet()

    def onStepBy(self, newvalue ):
        if newvalue:
            self.expressionValue._value = newvalue
            self.expressionValue.string = None
            self.expressionChanged.emit( self.expressionValue )
            self.updateStyleSheet()
        
    def dependentUpdate(self, name, value, string, origin):
        self.setValue( self.expressionValue.value )
        self.expressionChanged.emit( self.expressionValue )

    def value(self):
        return self.expressionValue