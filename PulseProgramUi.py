# -*- coding: utf-8 -*-
"""
Created on Thu Feb 07 22:55:28 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtCore, QtGui


PulseProgramWidget, PulseProgramBase = PyQt4.uic.loadUiType('ui/PulseProgram.ui')

class PulseProgramUi(PulseProgramWidget):
    pass

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    widget = QtGui.QWidget()
    ui = PulseProgramUi()
    ui.setupUi(widget)
    MainWindow.setCentralWidget(widget)
    MainWindow.show()
    sys.exit(app.exec_())
