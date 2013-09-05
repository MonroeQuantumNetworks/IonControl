# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
from PyQt4 import QtCore
       
DedicatedDisplayForm, DedicatedDisplayBase = PyQt4.uic.loadUiType(r'ui\DedicatedDisplay.ui')


class Settings:
    def __init__(self):
        self.average = False

class DedicatedDisplay(DedicatedDisplayForm,DedicatedDisplayBase ):
    def __init__(self,config,name,parent=None):
        DedicatedDisplayForm.__init__(self)
        DedicatedDisplayBase.__init__(self,parent)
        self.config = config
        self.name = name
        self._values = [0]*8
        self.settings = self.config.get("DedicatedDisplay."+self.name,Settings())
        self.sum = [0]*4
        self.sumnum = 0

    def setupUi(self, parent):
        DedicatedDisplayForm.setupUi(self,parent)
        self.averageCheck.setChecked( self.settings.average )
        self.averageCheck.stateChanged.connect( self.onAverageChanged )
            
    def onAverageChanged(self, state ):
        self.settings.average = state == QtCore.Qt.Checked
        self.sum = [0]*4
        self.sumnum = 0
        if not self.settings.average:
            self.numPointsLabel.setText("")
        else:
            self.numPointsLabel.setText("{0} points".format(self.sumnum))
            
            
    @property
    def values(self):
        return self._values
            
    @values.setter
    def values(self,values):
        if self.settings.average:
            self.sum = [a+b for a,b in zip(self.sum,values) ]
            self.sumnum += 1
            self._values = [a*1.0/b for a,b in zip(self.sum,self.sumnum)]
            for index, label in enumerate([self.label0, self.label1, self.label2, self.label3]):
                label.setText(str(self._values[index]))
            self.numPointsLabel.setText("{0} points".format(self.sumnum))
        else:
            for index, label in enumerate([self.label0, self.label1, self.label2, self.label3]):
                label.setText(str(values[index]))
            self._values = values
      
