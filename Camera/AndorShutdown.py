"""
Author: Nate Dudley

Simple progress display of Andor EMCCD shutdown procedure.
"""

from PyQt5 import QtGui, QtCore, QtWidgets
import PyQt5.uic


class AndorShutDown(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self, parent = None)
        self.layout = QtWidgets.QVBoxLayout()
        self.warmProg = QtWidgets.QProgressBar()
        self.layout.addWidget(self.warmProg)
        self.setWindowTitle('Shutdown')
        self.setLayout(self.layout)
        self.show()

    def setProgress(self, min, max):
        self.warmProg.setMinimum(min)
        self.warmProg.setMaximum(max)
        self.warmProg.setValue(min)
        self.warmProg.show()

    def updateTemp(self, temp):
        self.warmProg.setValue(temp)

    def setShutdown(self):
        self.layout.addWidget(QtWidgets.QLabel().setText('Shutting Down...'))

