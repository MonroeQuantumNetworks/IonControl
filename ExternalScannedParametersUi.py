# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 23:45:54 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore
import functools

UiForm, UiBase = PyQt4.uic.loadUiType(r'ui\ExternalScannedParameterUi.ui')

import MagnitudeSpinBox

class ControlUi(UiForm,UiBase):
    
    def __init__(self, parent=None):
        UiBase.__init__(self,parent)
        UiForm.__init__(self)
        self.spacerItem = None
        self.myLabelList = list()
        self.myBoxList = list()
        self.myDisplayList = list()
        self.targetValue = dict()
        self.currentValue = dict()
        self.displayWidget = dict()
    
    def setupUi(self,EnabledParameters,MainWindow):
        UiForm.setupUi(self,MainWindow)
        self.setupParameters(EnabledParameters)
        
    def setupParameters(self,EnabledParameters):
        print "ControlUi.setupParameters", EnabledParameters
        self.targetValue = dict()
        self.enabledParameters = EnabledParameters
        if self.spacerItem:
            self.gridLayout.removeItem( self.spacerItem )
        else:
            self.spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        for index, name in enumerate(self.enabledParameters.keys()):
            if index<len(self.myLabelList):
                self.myLabelList[index].setText(name)
                self.myLabelList[index].show()
            else:
                label = QtGui.QLabel(self)
                label.setText(name)
                self.myLabelList.append(label)
                self.gridLayout.addWidget( label, 1+index, 0, 1, 1 )
            parameter = self.enabledParameters.get(name)
            self.targetValue[name] = parameter.currentValue()
            if index<len(self.myBoxList):
                self.myBoxList[index].valueChanged.disconnect()
                self.myBoxList[index].setValue( parameter.currentValue() )
                self.myBoxList[index].valueChanged.connect( functools.partial(self.setValue, name) )
                self.myBoxList[index].show()
            else:
                Box = MagnitudeSpinBox.MagnitudeSpinBox(self)
                Box.setValue( parameter.currentValue()  )
                Box.valueChanged.connect( functools.partial(self.setValue, name) )
                self.gridLayout.addWidget( Box, 1+index, 1, 1, 1 )
                self.myBoxList.append( Box )
            if index<len(self.myDisplayList):
                Display = self.myDisplayList[index]
                Display.setText("")
                Display.show()
            else:
                Display = QtGui.QLabel(self)
                Display.setText("")
                self.myDisplayList.append(Display)
                self.gridLayout.addWidget( Display, 1+index, 2, 1, 1 )
            self.enabledParameters[name].displayValueCallback = functools.partial(self.showValue,Display)
        for index in range( len(self.enabledParameters), len(self.myLabelList)):
            self.myLabelList[index].hide()
            self.myBoxList[index].hide()
        self.gridLayout.addItem(self.spacerItem, len(self.enabledParameters)+1, 1, 1, 1)
        
    def setValue(self, name, value):
        print "setValue", value
        self.targetValue[name] = value
        self.setValueFollowup(name)
        
    def showValue(self, display, value):
        if display:
            display.setText("{0}".format(value));       
    
    def setValueFollowup(self, name):
        print "setValueFollowup", self.enabledParameters[name].currentValue()
        delay = int( 1000* self.enabledParameters[name].__dict__.get('delay',0.1) )
        if not self.enabledParameters[name].setValue( self.targetValue[name] ):
            QtCore.QTimer.singleShot(delay,functools.partial(self.setValueFollowup,name) )

    
