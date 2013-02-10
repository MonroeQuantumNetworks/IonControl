# -*- coding: utf-8 -*-
"""
Created on Sat Feb 09 17:28:11 2013

@author: pmaunz
"""

from PyQt4 import QtGui, QtCore
import re
import magnitude

class MagnitudeSpinBox(QtGui.QAbstractSpinBox):
    def validate(self, inputstring, pos):
        print "validate"
        m = re.match("\s*([-+0-9.]+)\s*(\w*)\s*",str(inputstring))
        if m:
            return (QtGui.QValidator.Acceptable,pos)
        return (QtGui.QValidator.Intermediate,pos)
        
    def stepBy(self, steps ):
        print steps
        
    def interpretText(self):
        print "interpret text"
        
    def fixup(self,inputstring):
        print inputstring
        
    def stepEnabled(self):
        print "stepEnabled"
        return QtGui.QAbstractSpinBox.StepUpEnabled | QtGui.QAbstractSpinBox.StepDownEnabled