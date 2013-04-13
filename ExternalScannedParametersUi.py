# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 23:45:54 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui

UiForm, UiBase = PyQt4.uic.loadUiType(r'ui\ExternalScannedParameterUi.ui')

import MagnitudeSpinBox

class ControlUi(UiForm,UiBase):
    
    def __init__(self, parent=None):
        UiBase.__init__(self,parent)
        UiForm.__init__(self)
        self.spacerItem = None
        self.myLabelList = list()
        self.myBoxList = list()
    
    def setupUi(self,EnabledParameters,MainWindow):
        UiForm.setupUi(self,MainWindow)
        self.setupParameters(EnabledParameters)
        
    def setupParameters(self,EnabledParameters):
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
                self.gridLayout.addWidget( label, 1+index, 1, 1, 1 )
            parameter = self.enabledParameters.get(name)
            if index<len(self.myBoxList):
                self.myBoxList[index].valueChanged.disconnect()
                self.myBoxList[index].setValue( parameter.currentValue() )
                self.myBoxList[index].valueChanged.connect( parameter.setValue )
                self.myBoxList[index].show()
            else:
                Box = MagnitudeSpinBox(self)
                Box.setValue( parameter.currentValue()  )
                Box.valueChanged.connect( parameter.setValue )
                self.gridLayout.addWidget( Box, 1+index, 2, 1, 1 )
                self.myBoxList.append( Box )
        for index in range( len(self.enabledParameters), len(self.myLabelList)):
            self.myLabelList[index].hide()
            self.myBoxList[index].hide()
        self.gridLayout.addItem(self.spacerItem, len(self.enabledParameters)+1, 1, 1, 1)
