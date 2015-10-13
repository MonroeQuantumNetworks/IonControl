# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import math

from PyQt4 import QtCore
import PyQt4.uic

import modules.magnitude as magnitude

import os
uipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\DedicatedDisplay.ui')
DedicatedDisplayForm, DedicatedDisplayBase = PyQt4.uic.loadUiType(uipath)


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
        self.settings = Settings() #self.config.get("DedicatedDisplay."+self.name,Settings())
        self.sum = [0]*4
        self.sumnum = 0

    def setupUi(self, parent):
        DedicatedDisplayForm.setupUi(self,parent)
        self.averageCheck.setChecked( self.settings.average )
        self.averageCheck.stateChanged.connect( self.onAverageChanged )
            
    def onAverageChanged(self, state ):
        self.settings.average = state == QtCore.Qt.Checked
        self.sum = [None]*4
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
            self.sum = [(a+b if b is not None else None) if a is not None else b for a,b in zip(self.sum,values)  ]
            self.sumnum += 1
            for index, label in enumerate([self.label0, self.label1, self.label2, self.label3]):
                if self.sum[index] is None:
                    self._values[index] = None
                    label.setText("None")
                else:
                    if self.sum[index] is not None:
                        if isinstance(self.sum[index], magnitude.Magnitude):
                            self._values[index] =  self.sum[index]/self.sumnum
                            label.setText("{0}".format(self._values[index].ounit(values[index].out_unit)))
                        else:
                            self._values[index] =  self.sum[index]*1.0/self.sumnum
                            prec = int(math.ceil(-math.log10(math.sqrt(self.sum[index])/self.sumnum))) if self.sum[index]>0 else 0
                            fs = "{{0:.{0}f}}".format(prec)
                            label.setText(fs.format(self._values[index]))
                    else:
                        label.setText("0")                        
            self.numPointsLabel.setText("{0} points".format(self.sumnum))
        else:
            for index, label in enumerate([self.label0, self.label1, self.label2, self.label3]):
                label.setText(str(values[index]))
            self._values = values
      
