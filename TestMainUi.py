# -*- coding: utf-8 -*-
"""
Created on Sat Dec 22 17:37:41 2012

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui

TestMainForm, TestMainBase = PyQt4.uic.loadUiType(r'ui\TestMain.ui')

class TestMainUi(TestMainBase,TestMainForm):
    def __init__(self):
        super(TestMainUi, self).__init__()
    
    def setupUi(self, parent):
        super(TestMainUi,self).setupUi(parent)
        
    def close(self):
        print "quit"
        
    def closeEvent(self,e):
        print "closeEvent"

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = TestMainUi()
    ui.setupUi(ui)
    ui.show()
    sys.exit(app.exec_())
