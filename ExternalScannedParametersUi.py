# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 23:45:54 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore

UiForm, UiBase = PyQt4.uic.loadUiType(r'ui\ExternalScannedParametersUi.ui')

import ExternalScannedParameters
import ExternalScannedParametersConfig
import functools

class SelectionUi(UiForm,UiBase):
    
    def __init__(self, parent=None):
        UiBase.__init__(self,parent)
        UiForm.__init__(self)
    
    def setupUi(self,MainWindow):
        UiForm.setupUi(self,MainWindow)
 