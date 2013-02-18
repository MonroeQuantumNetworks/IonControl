# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtGui, QtCore
        
ScanExperimentForm, ScanExperimentBase = PyQt4.uic.loadUiType(r'ui\ScanParameters.ui')

import ScanList

class Scan:
    pass

class ScanParameters(ScanExperimentForm, ScanExperimentBase ):
    pass

    def setVariables(self, variabledict):
        self.variabledict = variabledict
        for name, var in variabledict.iteritems():
            if var.type == "parameter":
                self.comboBoxParameter.addItem(var.name)
                
    def getScan(self):
        Scan.name = str(self.comboBoxParameter.currentText())
        Scan.start = self.minimumBox.value()
        Scan.stop = self.maximumBox.value()
        Scan.steps = self.stepsBox.value()
        Scan.type = [ ScanList.ScanType.LinearUp, ScanList.ScanType.LinearDown, ScanList.ScanType.Randomized][self.scanTypeCombo.currentIndex]
        Scan.list = ScanList.scanList( Scan.start, Scan.stop, Scan.steps, Scan.type )
        return Scan
        