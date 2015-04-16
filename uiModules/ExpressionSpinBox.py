'''
Created on Apr 13, 2015

@author: pmaunz
'''
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
        self.expressionValue.string = self.text()
        self.expressionValue.value = self.value()
        super(ExpressionSpinBox, self).focusOutEvent(event)
        if self.expressionValue:
            self.setValue( self.expressionValue.value )
            self.updateStyleSheet()

    def setExpression(self, expressionValue):
        if self.expressionValue:
            self.expressionValue.observable.unsubscribe(self.dependentUpdate)
        self.expressionValue = expressionValue
        self.setValue( expressionValue.value )
        self.expressionValue.observable.subscribe(self.dependentUpdate)
        self.updateStyleSheet()
        
    def updateStyleSheet(self):
        self.setStyleSheet("ExpressionSpinBox { background-color: #bfffbf; }") if self.expressionValue.hasDependency and not self.hasFocus() else self.lineEdit().setStyleSheet("")
        
    def onEditingFinished(self):
        if self.hasFocus():
            cursorPosition = self.lineEdit().cursorPosition()
            self.expressionValue.string = self.text()
            self.expressionValue.value = self.value()     
            self.lineEdit().setCursorPosition(cursorPosition)      
        self.expressionChanged.emit( self.expressionValue )
        self.updateStyleSheet()

    def onStepBy(self, newvalue ):
        if newvalue:
            self.expressionValue._value = newvalue
            self.expressionValue.string = None
            self.expressionChanged.emit( self.expressionValue )
            self.updateStyleSheet()
        
    def dependentUpdate(self, event):
        self.setValue( self.expressionValue.value )
        self.expressionChanged.emit( self.expressionValue )
        