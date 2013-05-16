# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
import PyQt4.uic
       
DedicatedDisplayForm, DedicatedDisplayBase = PyQt4.uic.loadUiType(r'ui\DedicatedDisplay.ui')


class DedicatedDisplay(DedicatedDisplayForm,DedicatedDisplayBase ):
    def __init__(self,config,parent=None):
        DedicatedDisplayForm.__init__(self)
        DedicatedDisplayBase.__init__(self,parent)
        self.config = config
        self._values = [0]*8

    def setupUi(self, parent):
        DedicatedDisplayForm.setupUi(self,parent)
            
    @property
    def values(self):
        return self._values
            
    @values.setter
    def values(self,values):
        for index, label in enumerate([self.label0, self.label1, self.label2, self.label3]):
            label.setText(str(values[index]))
        self._values = values
      
